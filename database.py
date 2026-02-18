"""
Модуль для работы с базой данных SQLite.
Содержит все функции для создания, чтения, обновления данных.
"""

# Импорт необходимых модулей
import sqlite3
import os
import re
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path

# ============================================
# НАСТРОЙКИ БЕЗОПАСНОСТИ
# ============================================

# Имя файла базы данных
DB_NAME = 'clinic.db'

# Файл для аудита
AUDIT_LOG = 'audit.log'

# Соль для хеширования
SALT = "clinic_salt_2026_change_this"

# Настройка логирования
logging.basicConfig(
    filename=AUDIT_LOG,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_action(action, details, user="SYSTEM"):
    """
    Логирование важных действий для аудита.
    
    Args:
        action (str): действие (ADD, DELETE, UPDATE, etc.)
        details (str): детали действия
        user (str): пользователь (по умолчанию SYSTEM)
    """
    logging.info(f"{user} | {action} | {details}")

def hash_sensitive_data(data):
    """
    Хеширование чувствительных данных (для защиты).
    
    Args:
        data (str): данные для хеширования
    
    Returns:
        str: хеш данных (первые 16 символов)
    """
    if not data:
        return None
    salted = data + SALT
    return hashlib.sha256(salted.encode()).hexdigest()[:16]

def validate_policy_number(policy):
    """
    Валидация номера полиса.
    
    Args:
        policy (str): номер полиса
    
    Returns:
        tuple: (bool, str) - (валиден ли, сообщение об ошибке)
    """
    if not policy or not policy.strip():
        return False, "Номер полиса обязателен"
    
    policy = policy.strip()
    
    if len(policy) < 10 or len(policy) > 20:
        return False, "Номер полиса должен содержать от 10 до 20 символов"
    
    if not re.match(r'^[0-9\-\s]+$', policy):
        return False, "Номер полиса может содержать только цифры, дефисы и пробелы"
    
    return True, "OK"

def validate_phone(phone):
    """
    Валидация номера телефона.
    
    Args:
        phone (str): номер телефона
    
    Returns:
        tuple: (bool, str) - (валиден ли, сообщение об ошибке)
    """
    if not phone:
        return True, "OK"
    
    phone = phone.strip()
    
    if len(phone) > 20:
        return False, "Номер телефона слишком длинный"
    
    if not re.match(r'^[\d\+\-\s\(\)]+$', phone):
        return False, "Телефон содержит недопустимые символы"
    
    return True, "OK"

def validate_name(name):
    """
    Валидация ФИО.
    
    Args:
        name (str): ФИО
    
    Returns:
        tuple: (bool, str) - (валиден ли, сообщение об ошибке)
    """
    if not name or not name.strip():
        return False, "ФИО обязательно для заполнения"
    
    name = name.strip()
    
    if len(name) > 200:
        return False, "ФИО слишком длинное"
    
    if len(name) < 2:
        return False, "ФИО слишком короткое"
    
    if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-\.]+$', name):
        return False, "ФИО может содержать только буквы, пробелы, дефисы и точки"
    
    return True, "OK"

def validate_date(date_str):
    """
    Валидация даты.
    
    Args:
        date_str (str): дата в формате ГГГГ-ММ-ДД
    
    Returns:
        tuple: (bool, str) - (валиден ли, сообщение об ошибке)
    """
    if not date_str:
        return True, "OK"
    
    date_str = date_str.strip()
    
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False, "Дата должна быть в формате ГГГГ-ММ-ДД"
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True, "OK"
    except ValueError:
        return False, "Некорректная дата"

def sanitize_input(text, max_length=1000):
    """
    Очистка входных данных от потенциально опасных символов.
    
    Args:
        text (str): входной текст
        max_length (int): максимальная длина
    
    Returns:
        str: очищенный текст
    """
    if not text:
        return ""
    
    text = str(text)[:max_length]
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text.strip()

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БД
# ============================================

def get_connection():
    """
    Создаёт и возвращает соединение с базой данных.
    
    Returns:
        connection: объект соединения с SQLite
    """
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    
    return conn

def verify_database_integrity():
    """
    Проверяет целостность файла базы данных.
    
    Returns:
        bool: True если БД цела, False если повреждена
    """
    if not os.path.exists(DB_NAME):
        return True
    
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            if result and result[0] != "ok":
                log_action("INTEGRITY_CHECK", f"Database integrity check failed: {result[0]}")
                return False
            
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('patients', 'doctors', 'appointments')
            """)
            tables = cursor.fetchall()
            if len(tables) != 3:
                log_action("INTEGRITY_CHECK", f"Missing tables: found {len(tables)} of 3")
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
    backup_dir = "backups"
    try:
        Path(backup_dir).mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/clinic_backup_{timestamp}.db"
        
        if os.path.exists(DB_NAME):
            import shutil
            shutil.copy2(DB_NAME, backup_file)
            log_action("BACKUP", f"Created backup: {backup_file}")
            return backup_file
    except Exception as e:
        log_action("BACKUP_ERROR", f"Failed to create backup: {str(e)}")
    
    return None

def init_db():
    """
    Инициализирует базу данных.
    """
    print("Инициализация базы данных...")
    
    if os.path.exists(DB_NAME):
        if not verify_database_integrity():
            print("  База данных повреждена!")
            backup_database()
            os.remove(DB_NAME)
            print("  Повреждённый файл удалён")
        else:
            backup_database()
    
    db_exists = os.path.exists(DB_NAME)
    
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("  - Таблица 'doctors' готова")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT DEFAULT 'запланирован',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    cancel_reason TEXT,
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
            print("  - Индексы созданы")
            
            # Начальные данные
            cursor.execute("SELECT COUNT(*) as count FROM doctors")
            result = cursor.fetchone()
            
            if result and result['count'] == 0:
                doctors_data = [
                    ('Иванов Иван Иванович', 'Терапевт', '101'),
                    ('Петрова Анна Сергеевна', 'Окулист', '205'),
                    ('Сидоров Петр Петрович', 'Хирург', '310'),
                    ('Смирнова Елена Викторовна', 'Педиатр', '115'),
                    ('Козлов Дмитрий Николаевич', 'Невролог', '220')
                ]
                
                cursor.executemany(
                    "INSERT INTO doctors (full_name, specialty, room_number) VALUES (?,?,?)",
                    doctors_data
                )
                print(f"  - Добавлено {len(doctors_data)} врачей")
                log_action("INIT", f"Added {len(doctors_data)} default doctors")
            
            conn.commit()
            
            if db_exists:
                print("База данных успешно подключена")
            else:
                print("Новая база данных успешно создана")
                log_action("INIT", "New database created")
            
    except sqlite3.DatabaseError as e:
        log_action("INIT_ERROR", f"Database initialization error: {str(e)}")
        print(f"❌ Ошибка базы данных: {e}")

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПАЦИЕНТАМИ
# ============================================

def get_all_patients():
    """
    Возвращает список всех пациентов.
    
    Returns:
        list: список всех пациентов
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM patients ORDER BY full_name")
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting all patients: {str(e)}")
        return []

def search_patients(search_text):
    """
    Ищет пациентов по ФИО или номеру полиса.
    
    Args:
        search_text (str): текст для поиска
    
    Returns:
        list: список найденных пациентов
    """
    search_text = sanitize_input(search_text, 100)
    
    if not search_text or len(search_text) < 2:
        return []
    
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM patients 
                WHERE full_name LIKE ? OR policy_number LIKE ?
                ORDER BY full_name
                LIMIT 100
            ''', (f'%{search_text}%', f'%{search_text}%'))
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error searching patients: {str(e)}")
        return []

def add_patient(full_name, birth_date, phone, policy):
    """
    Добавляет нового пациента в базу данных.
    
    Args:
        full_name (str): ФИО пациента
        birth_date (str): дата рождения
        phone (str): телефон
        policy (str): номер полиса
    
    Returns:
        int: ID нового пациента или None в случае ошибки
    """
    valid, msg = validate_name(full_name)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid name: {msg}")
        return None
    
    valid, msg = validate_policy_number(policy)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid policy: {msg}")
        return None
    
    valid, msg = validate_phone(phone)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid phone: {msg}")
        return None
    
    valid, msg = validate_date(birth_date)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid birth date: {msg}")
        return None
    
    full_name = sanitize_input(full_name, 200)
    policy = sanitize_input(policy, 50)
    phone = sanitize_input(phone, 50) if phone else None
    birth_date = sanitize_input(birth_date, 20) if birth_date else None
    
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO patients (full_name, birth_date, phone, policy_number)
                VALUES (?, ?, ?, ?)
            ''', (full_name, birth_date, phone, policy))
            conn.commit()
            
            patient_id = cursor.lastrowid
            policy_hash = hash_sensitive_data(policy)
            log_action("ADD_PATIENT", f"Added patient ID:{patient_id}, policy_hash:{policy_hash}")
            
            return patient_id
    except sqlite3.IntegrityError:
        log_action("DUPLICATE_PATIENT", f"Attempt to add duplicate policy: {hash_sensitive_data(policy)}")
        return None
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error adding patient: {str(e)}")
        return None

def get_patient_by_id(patient_id):
    """
    Получает данные пациента по ID.
    
    Args:
        patient_id (int): ID пациента
    
    Returns:
        Row: данные пациента или None
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM patients WHERE id = ?", 
                (patient_id,)
            )
            return cursor.fetchone()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting patient {patient_id}: {str(e)}")
        return None

def update_patient(patient_id, full_name, birth_date, phone, policy):
    """
    Обновляет данные пациента.
    
    Returns:
        bool: True при успехе
    """
    valid, msg = validate_name(full_name)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid name for update: {msg}")
        return False
    
    valid, msg = validate_phone(phone)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid phone for update: {msg}")
        return False
    
    valid, msg = validate_date(birth_date)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid birth date for update: {msg}")
        return False
    
    full_name = sanitize_input(full_name, 200)
    phone = sanitize_input(phone, 50) if phone else None
    birth_date = sanitize_input(birth_date, 20) if birth_date else None
    
    try:
        with get_connection() as conn:
            conn.execute('''
                UPDATE patients 
                SET full_name = ?, birth_date = ?, phone = ?
                WHERE id = ?
            ''', (full_name, birth_date, phone, patient_id))
            conn.commit()
            
            log_action("UPDATE_PATIENT", f"Updated patient ID:{patient_id}")
            return True
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error updating patient {patient_id}: {str(e)}")
        return False

def delete_patient(patient_id):
    """
    Удаляет пациента.
    
    Returns:
        dict: результат операции
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) as count FROM appointments 
                WHERE patient_id = ? AND date >= date('now') AND status = 'запланирован'
            ''', (patient_id,))
            result = cursor.fetchone()
            
            if result and result['count'] > 0:
                log_action("DELETE_PATIENT_BLOCKED", 
                          f"Attempt to delete patient {patient_id} with {result['count']} future appointments")
                return {'success': False, 'future_appointments': result['count']}
            
            conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit()
            
            log_action("DELETE_PATIENT", f"Deleted patient ID:{patient_id}")
            return {'success': True}
            
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error deleting patient {patient_id}: {str(e)}")
        return {'success': False, 'error': str(e)}

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ВРАЧАМИ
# ============================================

def get_all_doctors():
    """
    Возвращает список всех врачей.
    
    Returns:
        list: список всех врачей
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM doctors ORDER BY full_name")
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting all doctors: {str(e)}")
        return []

def get_doctor_by_id(doctor_id):
    """
    Получает данные врача по ID.
    
    Args:
        doctor_id (int): ID врача
    
    Returns:
        Row: данные врача или None
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM doctors WHERE id = ?", 
                (doctor_id,)
            )
            return cursor.fetchone()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting doctor {doctor_id}: {str(e)}")
        return None

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАПИСЯМИ
# ============================================

def get_free_time(doctor_id, date):
    """
    Возвращает список свободного времени для конкретного врача на указанную дату.
    
    Args:
        doctor_id (int): ID врача
        date (str): дата в формате ГГГГ-ММ-ДД
    
    Returns:
        list: список свободного времени
    """
    valid, msg = validate_date(date)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid date for free time: {msg}")
        return []
    
    try:
        all_times = []
        for hour in range(9, 18):
            for minute in [0, 30]:
                time_str = f"{hour:02d}:{minute:02d}"
                all_times.append(time_str)
        
        with get_connection() as conn:
            cursor = conn.execute('''
                SELECT time FROM appointments 
                WHERE doctor_id = ? AND date = ? AND status = 'запланирован'
            ''', (doctor_id, date))
            busy_times = [row['time'] for row in cursor.fetchall()]
        
        free_times = [t for t in all_times if t not in busy_times]
        return free_times
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting free time: {str(e)}")
        return []

def add_appointment(patient_id, doctor_id, date, time):
    """
    Создаёт новую запись на приём.
    
    Args:
        patient_id (int): ID пациента
        doctor_id (int): ID врача
        date (str): дата приёма
        time (str): время приёма
    
    Returns:
        int: ID новой записи или None
    """
    valid, msg = validate_date(date)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid appointment date: {msg}")
        return None
    
    try:
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        if appointment_date < datetime.now().date():
            log_action("VALIDATION_ERROR", "Attempt to book appointment in the past")
            return None
    except ValueError:
        return None
    
    try:
        with get_connection() as conn:
            patient = conn.execute(
                "SELECT id FROM patients WHERE id = ?", 
                (patient_id,)
            ).fetchone()
            doctor = conn.execute(
                "SELECT id FROM doctors WHERE id = ?", 
                (doctor_id,)
            ).fetchone()
            
            if not patient or not doctor:
                log_action("VALIDATION_ERROR", f"Invalid patient or doctor ID")
                return None
            
            cursor = conn.execute('''
                INSERT INTO appointments (patient_id, doctor_id, date, time, status)
                VALUES (?, ?, ?, ?, 'запланирован')
            ''', (patient_id, doctor_id, date, time))
            conn.commit()
            
            appointment_id = cursor.lastrowid
            log_action("ADD_APPOINTMENT", 
                      f"Created appointment ID:{appointment_id} for patient:{patient_id} doctor:{doctor_id}")
            
            return appointment_id
    except sqlite3.IntegrityError:
        log_action("DUPLICATE_APPOINTMENT", 
                  f"Attempt to book occupied slot: doctor {doctor_id} at {date} {time}")
        return None
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error adding appointment: {str(e)}")
        return None

def get_all_appointments():
    """
    Возвращает все записи на приём с подробной информацией.
    
    Returns:
        list: список всех записей
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.id,
                    p.full_name as patient_name,
                    p.policy_number,
                    d.full_name as doctor_name,
                    d.specialty,
                    d.room_number,
                    a.date,
                    a.time,
                    a.status
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                ORDER BY a.date DESC, a.time DESC
                LIMIT 1000
            ''')
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting all appointments: {str(e)}")
        return []

def get_appointments_by_date(date):
    """
    Возвращает записи на конкретную дату.
    
    Args:
        date (str): дата для поиска
    
    Returns:
        list: список записей на указанную дату
    """
    valid, msg = validate_date(date)
    if not valid:
        return []
    
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.id,
                    p.full_name as patient_name,
                    d.full_name as doctor_name,
                    d.specialty,
                    a.time,
                    a.status
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.date = ?
                ORDER BY a.time
            ''', (date,))
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting appointments by date: {str(e)}")
        return []

def cancel_appointment(appointment_id, reason=None):
    """
    Отменяет запись на приём.
    
    Args:
        appointment_id (int): ID записи
        reason (str): причина отмены
    
    Returns:
        bool: True при успехе
    """
    try:
        with get_connection() as conn:
            appointment = conn.execute(
                "SELECT status FROM appointments WHERE id = ?", 
                (appointment_id,)
            ).fetchone()
            
            if not appointment:
                log_action("CANCEL_ERROR", f"Appointment {appointment_id} not found")
                return False
            
            if appointment['status'] == 'отменён':
                log_action("CANCEL_ERROR", f"Appointment {appointment_id} already cancelled")
                return False
            
            reason = sanitize_input(reason, 200) if reason else None
            conn.execute('''
                UPDATE appointments 
                SET status = 'отменён', 
                    cancelled_at = CURRENT_TIMESTAMP,
                    cancel_reason = ?
                WHERE id = ?
            ''', (reason, appointment_id))
            conn.commit()
            
            log_action("CANCEL_APPOINTMENT", f"Cancelled appointment ID:{appointment_id}")
            return True
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error cancelling appointment {appointment_id}: {str(e)}")
        return False

def delete_old_appointments(days=30):
    """
    Удаляет записи старше указанного количества дней.
    
    Args:
        days (int): количество дней
    
    Returns:
        int: количество удаленных записей
    """
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        with get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM appointments 
                WHERE date < ?
            ''', (cutoff_date,))
            conn.commit()
            deleted_count = cursor.rowcount
            log_action("CLEANUP", f"Deleted {deleted_count} old appointments")
            return deleted_count
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error deleting old appointments: {str(e)}")
        return 0

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

def get_database_stats():
    """
    Возвращает статистику базы данных.
    
    Returns:
        dict: статистика
    """
    stats = {
        'patients': 0,
        'doctors': 0,
        'appointments': 0,
        'today_appointments': 0,
        'size_kb': 0,
        'last_backup': None
    }
    
    try:
        with get_connection() as conn:
            stats['patients'] = conn.execute(
                "SELECT COUNT(*) as count FROM patients"
            ).fetchone()['count']
            
            stats['doctors'] = conn.execute(
                "SELECT COUNT(*) as count FROM doctors"
            ).fetchone()['count']
            
            stats['appointments'] = conn.execute(
                "SELECT COUNT(*) as count FROM appointments"
            ).fetchone()['count']
            
            today = datetime.now().strftime('%Y-%m-%d')
            stats['today_appointments'] = conn.execute(
                "SELECT COUNT(*) as count FROM appointments WHERE date = ?",
                (today,)
            ).fetchone()['count']
        
        if os.path.exists(DB_NAME):
            stats['size_kb'] = os.path.getsize(DB_NAME) // 1024
        
        backup_dir = Path("backups")
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("clinic_backup_*.db"))
            if backups:
                stats['last_backup'] = backups[-1].name
        
        return stats
    except Exception as e:
        log_action("STATS_ERROR", f"Error getting database stats: {str(e)}")
        return stats