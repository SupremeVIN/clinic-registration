"""
Управление соединением с базой данных.
"""

import sqlite3
import os
import shutil
import glob
from pathlib import Path
from datetime import datetime

from database.config import DB_NAME, BACKUP_DIR, DB_PATH, DATA_DIR, BACKUP_DIR_PATH, ensure_data_dir
from database.security import log_action

SCHEMA_VERSION = 4  # Увеличена версия для миграции

def get_connection():
    """
    Создаёт и возвращает соединение с базой данных.
    
    Returns:
        connection: объект соединения с SQLite
    """
    ensure_data_dir()
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    
    return conn

def get_schema_version(conn):
    """Получает текущую версию схемы БД"""
    try:
        cursor = conn.execute("SELECT version FROM schema_version ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result['version'] if result else 0
    except sqlite3.OperationalError:
        # Таблица schema_version не существует
        return 0

def set_schema_version(conn, version):
    """Устанавливает версию схемы БД"""
    conn.execute('''
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()

def migrate_database(conn, current_version):
    """Выполняет миграции БД"""
    if current_version < 1:
        # Миграция до версии 1 - добавление колонок
        try:
            conn.execute("ALTER TABLE appointments ADD COLUMN created_by TEXT")
            log_action("MIGRATION", "Added column created_by to appointments")
        except sqlite3.OperationalError:
            pass
        
        try:
            conn.execute("ALTER TABLE appointments ADD COLUMN cancelled_by TEXT")
            log_action("MIGRATION", "Added column cancelled_by to appointments")
        except sqlite3.OperationalError:
            pass
        
        try:
            conn.execute("ALTER TABLE doctors ADD COLUMN user_id INTEGER")
            log_action("MIGRATION", "Added column user_id to doctors")
        except sqlite3.OperationalError:
            pass
        
        try:
            conn.execute("ALTER TABLE doctors ADD COLUMN is_deleted INTEGER DEFAULT 0")
            log_action("MIGRATION", "Added column is_deleted to doctors")
        except sqlite3.OperationalError:
            pass
        
        try:
            conn.execute("ALTER TABLE doctors ADD COLUMN deleted_at TIMESTAMP")
            log_action("MIGRATION", "Added column deleted_at to doctors")
        except sqlite3.OperationalError:
            pass
        
        set_schema_version(conn, 1)
        log_action("MIGRATION", "Database migrated to version 1")
        current_version = 1
    
    if current_version < 2:
        # Миграция до версии 2 - удаление колонки cancel_reason
        try:
            cursor = conn.execute("PRAGMA table_info(appointments)")
            columns = [row['name'] for row in cursor.fetchall()]
            
            if 'cancel_reason' in columns:
                conn.execute('''
                    CREATE TABLE appointments_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        doctor_id INTEGER NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        status TEXT DEFAULT 'запланирован',
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cancelled_at TIMESTAMP,
                        cancelled_by TEXT,
                        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL,
                        UNIQUE(doctor_id, date, time)
                    )
                ''')
                
                conn.execute('''
                    INSERT INTO appointments_new 
                    SELECT id, patient_id, doctor_id, date, time, status, created_by, created_at, cancelled_at, cancelled_by
                    FROM appointments
                ''')
                
                conn.execute("DROP TABLE appointments")
                conn.execute("ALTER TABLE appointments_new RENAME TO appointments")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id)")
                
                log_action("MIGRATION", "Removed column cancel_reason from appointments, changed ON DELETE to SET NULL")
        except sqlite3.OperationalError as e:
            log_action("MIGRATION_ERROR", f"Error removing cancel_reason: {str(e)}")
        
        set_schema_version(conn, 2)
        log_action("MIGRATION", "Database migrated to version 2")
        current_version = 2
    
    if current_version < 3:
        # Миграция до версии 3 - изменение внешнего ключа
        try:
            cursor = conn.execute("PRAGMA foreign_key_list(appointments)")
            fk_exists = False
            for fk in cursor.fetchall():
                if fk['from'] == 'doctor_id' and fk['to'] == 'doctors' and fk['on_delete'] == 'SET NULL':
                    fk_exists = True
                    break
            
            if not fk_exists:
                conn.execute('''
                    CREATE TABLE appointments_v3 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        doctor_id INTEGER,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        status TEXT DEFAULT 'запланирован',
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cancelled_at TIMESTAMP,
                        cancelled_by TEXT,
                        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL,
                        UNIQUE(doctor_id, date, time)
                    )
                ''')
                
                conn.execute('''
                    INSERT INTO appointments_v3 
                    SELECT id, patient_id, doctor_id, date, time, status, created_by, created_at, cancelled_at, cancelled_by
                    FROM appointments
                ''')
                
                conn.execute("DROP TABLE appointments")
                conn.execute("ALTER TABLE appointments_v3 RENAME TO appointments")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id)")
                
                log_action("MIGRATION", "Changed foreign key ON DELETE to SET NULL for appointments.doctor_id")
        except sqlite3.OperationalError as e:
            log_action("MIGRATION_ERROR", f"Error migrating to version 3: {str(e)}")
        
        set_schema_version(conn, 3)
        log_action("MIGRATION", "Database migrated to version 3")
        current_version = 3
    
    if current_version < 4:
        # Миграция до версии 4 - убираем UNIQUE constraint, добавляем частичный уникальный индекс
        try:
            # Проверяем, существует ли старый UNIQUE constraint
            cursor = conn.execute("PRAGMA index_list(appointments)")
            indexes = [row['name'] for row in cursor.fetchall()]
            
            # Удаляем старый UNIQUE constraint если есть
            if 'sqlite_autoindex_appointments_1' in indexes:
                # Создаём новую таблицу без UNIQUE constraint
                conn.execute('''
                    CREATE TABLE appointments_v4 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        doctor_id INTEGER,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        status TEXT DEFAULT 'запланирован',
                        created_by TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cancelled_at TIMESTAMP,
                        cancelled_by TEXT,
                        FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
                    )
                ''')
                
                # Копируем данные
                conn.execute('''
                    INSERT INTO appointments_v4 
                    SELECT id, patient_id, doctor_id, date, time, status, created_by, created_at, cancelled_at, cancelled_by
                    FROM appointments
                ''')
                
                # Удаляем старую таблицу
                conn.execute("DROP TABLE appointments")
                
                # Переименовываем новую
                conn.execute("ALTER TABLE appointments_v4 RENAME TO appointments")
                
                # Создаём частичный уникальный индекс только для активных записей
                conn.execute('''
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_appointments 
                    ON appointments(doctor_id, date, time) 
                    WHERE status = 'запланирован'
                ''')
                
                # Создаём обычные индексы
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id)")
                
                log_action("MIGRATION", "Removed UNIQUE constraint, added partial unique index for active appointments only")
        except sqlite3.OperationalError as e:
            log_action("MIGRATION_ERROR", f"Error migrating to version 4: {str(e)}")
        
        set_schema_version(conn, 4)
        log_action("MIGRATION", "Database migrated to version 4")

def verify_database_integrity():
    """
    Проверяет целостность файла базы данных.
    
    Returns:
        bool: True если БД цела, False если повреждена
    """
    ensure_data_dir()
    
    if not os.path.exists(DB_PATH):
        return True
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            if result and result[0] != "ok":
                log_action("INTEGRITY_CHECK", f"Database integrity check failed: {result[0]}")
                return False
            
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('patients', 'doctors', 'appointments', 'users')
            """)
            tables = cursor.fetchall()
            if len(tables) != 4:
                log_action("INTEGRITY_CHECK", f"Missing tables: found {len(tables)} of 4")
                return False
        
        return True
    except sqlite3.DatabaseError as e:
        log_action("INTEGRITY_CHECK", f"Database error: {str(e)}")
        return False

def backup_database():
    """
    Создаёт резервную копию базы данных.
    
    Returns:
        str: путь к файлу бэкапа или None
    """
    ensure_data_dir()
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = BACKUP_DIR_PATH / f"clinic_backup_{timestamp}.db"
        
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, str(backup_file))
            log_action("BACKUP", f"Created backup: {backup_file}")
            return str(backup_file)
    except Exception as e:
        log_action("BACKUP_ERROR", f"Failed to create backup: {str(e)}")
    
    return None

def get_backup_list():
    """
    Возвращает список всех доступных резервных копий с информацией о них.
    
    Returns:
        list: список словарей с информацией о бэкапах
    """
    ensure_data_dir()
    backups = []
    
    try:
        backup_files = sorted(
            BACKUP_DIR_PATH.glob("clinic_backup_*.db"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for backup_path in backup_files:
            stat = backup_path.stat()
            size_kb = stat.st_size // 1024
            
            # Извлекаем дату из имени файла
            name = backup_path.name
            timestamp_str = name.replace("clinic_backup_", "").replace(".db", "")
            try:
                backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                date_str = backup_date.strftime("%d.%m.%Y %H:%M:%S")
            except:
                date_str = "Неизвестно"
            
            backups.append({
                'path': str(backup_path),
                'name': name,
                'date': date_str,
                'size_kb': size_kb,
                'timestamp': stat.st_mtime
            })
        
        return backups
    except Exception as e:
        log_action("BACKUP_LIST_ERROR", f"Error getting backup list: {str(e)}")
        return []

def restore_from_backup(backup_path):
    """
    Восстанавливает базу данных из указанной резервной копии.
    
    Args:
        backup_path (str): путь к файлу бэкапа
    
    Returns:
        dict: результат операции с полями success, message, backup_created
    """
    ensure_data_dir()
    
    try:
        backup_path = Path(backup_path)
        
        # Проверяем, существует ли файл бэкапа
        if not backup_path.exists():
            return {'success': False, 'message': f"Файл бэкапа не найден: {backup_path}"}
        
        # Проверяем, что это действительно файл базы данных
        try:
            with sqlite3.connect(str(backup_path)) as conn:
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('patients', 'doctors', 'appointments', 'users')
                """)
                tables = cursor.fetchall()
                if len(tables) != 4:
                    return {
                        'success': False, 
                        'message': f"Файл не является корректной базой данных. Найдено таблиц: {len(tables)} из 4"
                    }
        except sqlite3.DatabaseError as e:
            return {'success': False, 'message': f"Файл повреждён или не является базой данных: {str(e)}"}
        
        # Создаём резервную копию текущей базы перед восстановлением
        current_backup = None
        if os.path.exists(DB_PATH):
            current_backup = backup_database()
        
        # Если текущая база существует, удаляем её или перемещаем
        if os.path.exists(DB_PATH):
            # Перемещаем текущую базу во временный файл
            temp_backup = BACKUP_DIR_PATH / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.move(DB_PATH, str(temp_backup))
            log_action("RESTORE", f"Moved current database to {temp_backup}")
        
        # Копируем бэкап на место основной базы
        shutil.copy2(str(backup_path), str(DB_PATH))
        
        # Проверяем целостность восстановленной базы
        if not verify_database_integrity():
            # Если восстановление не удалось, пытаемся вернуть старую базу
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            if os.path.exists(temp_backup):
                shutil.move(str(temp_backup), str(DB_PATH))
            return {'success': False, 'message': "Восстановленная база повреждена, выполнена откат"}
        
        log_action("RESTORE", f"Restored database from backup: {backup_path}")
        
        return {
            'success': True, 
            'message': f"База данных восстановлена из бэкапа",
            'backup_created': current_backup
        }
        
    except Exception as e:
        log_action("RESTORE_ERROR", f"Error restoring database: {str(e)}")
        return {'success': False, 'message': f"Ошибка восстановления: {str(e)}"}

def vacuum_database():
    """
    Очищает кэш базы данных и уменьшает размер файла.
    
    Returns:
        bool: True при успехе
    """
    try:
        backup_database()
        
        with get_connection() as conn:
            conn.execute("VACUUM")
            conn.commit()
        
        log_action("VACUUM", "Database optimized")
        return True
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error vacuuming database: {str(e)}")
        return False

def init_db():
    """
    Инициализирует базу данных.
    """
    ensure_data_dir()
    
    print("Инициализация базы данных...")
    print(f"  Директория данных: {DATA_DIR}")
    
    if os.path.exists(DB_PATH):
        if not verify_database_integrity():
            print("  База данных повреждена!")
            backup_database()
            os.remove(DB_PATH)
            print("  Повреждённый файл удалён")
        else:
            backup_database()
    
    db_exists = os.path.exists(DB_PATH)
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Создание таблиц
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    birth_date TEXT,
                    phone TEXT,
                    policy_number TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("  - Таблица 'patients' готова")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    specialty TEXT,
                    room_number TEXT,
                    user_id INTEGER,
                    is_deleted INTEGER DEFAULT 0,
                    deleted_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            print("  - Таблица 'doctors' готова")

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctor_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_id INTEGER NOT NULL UNIQUE,
                    work_start_hour INTEGER DEFAULT 9,
                    work_end_hour INTEGER DEFAULT 18,
                    slot_duration_minutes INTEGER DEFAULT 30,
                    lunch_start_hour INTEGER,
                    lunch_end_hour INTEGER,
                    break_between_slots INTEGER DEFAULT 0,
                    working_days TEXT DEFAULT '[1,2,3,4,5]',
                    is_custom INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
                )
            ''')
            print("  - Таблица 'doctor_schedules' готова")

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("  - Таблица 'users' готова")
            
            # Таблица appointments без UNIQUE constraint
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT DEFAULT 'запланирован',
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    cancelled_by TEXT,
                    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
                )
            ''')
            print("  - Таблица 'appointments' готова")
            
            # Индексы
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(full_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patients_policy ON patients(policy_number)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_doctors_deleted ON doctors(is_deleted)')
            
            # Частичный уникальный индекс только для активных записей
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_appointments 
                ON appointments(doctor_id, date, time) 
                WHERE status = 'запланирован'
            ''')
            print("  - Индексы созданы")
            
            # Проверяем и создаем начальных пользователей
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            
            if result and result['count'] == 0:
                from database.users import hash_password
                
                users_data = [
                    ('admin', hash_password('admin123'), 'admin', 'Администратор'),
                    ('user', hash_password('user123'), 'registrar', 'Регистратор')
                ]
                
                cursor.executemany(
                    "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                    users_data
                )
                print(f"  - Добавлено {len(users_data)} пользователей")
                log_action("INIT", f"Added {len(users_data)} default users")
            
            # Проверяем и создаем начальных врачей
            cursor.execute("SELECT COUNT(*) as count FROM doctors WHERE is_deleted = 0")
            result = cursor.fetchone()
            
            if result and result['count'] == 0:
                doctors_data = [
                    ('Иванов Иван Иванович', 'Терапевт', '101', None),
                    ('Петрова Анна Сергеевна', 'Окулист', '205', None),
                    ('Сидоров Петр Петрович', 'Хирург', '310', None),
                    ('Смирнова Елена Викторовна', 'Педиатр', '115', None),
                    ('Козлов Дмитрий Николаевич', 'Невролог', '220', None)
                ]
                
                cursor.executemany(
                    "INSERT INTO doctors (full_name, specialty, room_number, user_id) VALUES (?, ?, ?, ?)",
                    doctors_data
                )
                print(f"  - Добавлено {len(doctors_data)} врачей")
                log_action("INIT", f"Added {len(doctors_data)} default doctors")
            
            conn.commit()
            
            # Выполняем миграции
            current_version = get_schema_version(conn)
            if current_version < SCHEMA_VERSION:
                print(f"  - Обновление схемы с версии {current_version} до {SCHEMA_VERSION}")
                migrate_database(conn, current_version)
            
            if db_exists:
                print("База данных успешно подключена")
            else:
                print("Новая база данных успешно создана")
                log_action("INIT", "New database created")
            
    except sqlite3.DatabaseError as e:
        log_action("INIT_ERROR", f"Database initialization error: {str(e)}")
        print(f"Ошибка базы данных: {e}")