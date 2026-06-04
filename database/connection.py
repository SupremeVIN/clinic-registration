"""
Управление соединением с базой данных.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

from database.config import DB_NAME, BACKUP_DIR, DB_PATH, DATA_DIR, BACKUP_DIR_PATH, ensure_data_dir
from database.security import log_action

SCHEMA_VERSION = 2

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
            # Проверяем, существует ли колонка cancel_reason
            cursor = conn.execute("PRAGMA table_info(appointments)")
            columns = [row['name'] for row in cursor.fetchall()]
            
            if 'cancel_reason' in columns:
                # SQLite не поддерживает DROP COLUMN напрямую, нужно создать новую таблицу
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
                        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
                        UNIQUE(doctor_id, date, time)
                    )
                ''')
                
                # Копируем данные
                conn.execute('''
                    INSERT INTO appointments_new 
                    SELECT id, patient_id, doctor_id, date, time, status, created_by, created_at, cancelled_at, cancelled_by
                    FROM appointments
                ''')
                
                # Удаляем старую таблицу
                conn.execute("DROP TABLE appointments")
                
                # Переименовываем новую
                conn.execute("ALTER TABLE appointments_new RENAME TO appointments")
                
                # Восстанавливаем индексы
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id)")
                
                log_action("MIGRATION", "Removed column cancel_reason from appointments")
        except sqlite3.OperationalError as e:
            log_action("MIGRATION_ERROR", f"Error removing cancel_reason: {str(e)}")
        
        set_schema_version(conn, 2)
        log_action("MIGRATION", "Database migrated to version 2")

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
            import shutil
            shutil.copy2(DB_PATH, str(backup_file))
            log_action("BACKUP", f"Created backup: {backup_file}")
            return str(backup_file)
    except Exception as e:
        log_action("BACKUP_ERROR", f"Failed to create backup: {str(e)}")
    
    return None

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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
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
                    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
                    UNIQUE(doctor_id, date, time)
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
            print("  - Индексы созданы")
            
            # Проверяем и создаем начальных пользователей
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            
            if result and result['count'] == 0:
                # Импортируем функцию хеширования
                from database.users import hash_password
                
                # Создаем пользователей с хешированными паролями
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
            
            # Проверяем и создаем начальных врачей (без привязки к пользователям)
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