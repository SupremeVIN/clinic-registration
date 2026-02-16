"""
Модуль для работы с базой данных SQLite.
Содержит все функции для создания, чтения, обновления данных.
"""

# Импортируем необходимые модули
import sqlite3
import os
from datetime import datetime

# ============================================
# НАСТРОЙКИ БАЗЫ ДАННЫХ
# ============================================

# Имя файла базы данных (будет создан в той же папке)
DB_NAME = 'clinic.db'

def get_connection():
    """
    Создаёт и возвращает соединение с базой данных.
    
    Returns:
        connection: объект соединения с SQLite
    """
    # Подключаемся к базе (если файла нет, он создастся автоматически)
    conn = sqlite3.connect(DB_NAME)
    
    # Включаем поддержку внешних ключей (для связей между таблицами)
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Настраиваем возврат строк как словарей (удобно для работы)
    # Теперь к полям можно обращаться по имени: row['id'], row['full_name']
    conn.row_factory = sqlite3.Row
    
    return conn

# ============================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================

def init_db():
    """
    Инициализирует базу данных:
    1. Создаёт таблицы, если их нет
    2. Заполняет начальными данными (врачи)
    
    Эта функция вызывается при каждом запуске программы.
    """
    print("🔄 Инициализация базы данных...")
    
    # Проверяем, существует ли уже файл базы
    db_exists = os.path.exists(DB_NAME)
    
    try:
        # Подключаемся к базе
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # ========================================
            # 1. СОЗДАНИЕ ТАБЛИЦ
            # ========================================
            
            # Таблица пациентов
            # PRIMARY KEY - уникальный идентификатор
            # AUTOINCREMENT - автоматическое увеличение номера
            # NOT NULL - поле обязательно для заполнения
            # UNIQUE - значение должно быть уникальным
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    birth_date TEXT,
                    phone TEXT,
                    policy_number TEXT UNIQUE
                )
            ''')
            print("  - Таблица 'patients' готова")
            
            # Таблица врачей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    specialty TEXT,
                    room_number TEXT
                )
            ''')
            print("  - Таблица 'doctors' готова")
            
            # Таблица записей на приём
            # FOREIGN KEY - внешний ключ (ссылка на другую таблицу)
            # ON DELETE CASCADE - при удалении врача/пациента удаляются все его записи
            # UNIQUE(doctor_id, date, time) - нельзя записать двух пациентов к одному врачу на одно время
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT DEFAULT 'запланирован',
                    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
                    UNIQUE(doctor_id, date, time)
                )
            ''')
            print("  - Таблица 'appointments' готова")
            
            # ========================================
            # 2. ЗАПОЛНЕНИЕ НАЧАЛЬНЫМИ ДАННЫМИ
            # ========================================
            
            # Проверяем, есть ли врачи в таблице
            cursor.execute("SELECT COUNT(*) as count FROM doctors")
            result = cursor.fetchone()
            
            # Если врачей нет (count == 0), добавляем тестовых врачей
            if result and result['count'] == 0:
                doctors_data = [
                    ('Иванов Иван Иванович', 'Терапевт', '101'),
                    ('Петрова Анна Сергеевна', 'Окулист', '205'),
                    ('Сидоров Петр Петрович', 'Хирург', '310'),
                    ('Смирнова Елена Викторовна', 'Педиатр', '115'),
                    ('Козлов Дмитрий Николаевич', 'Невролог', '220')
                ]
                
                # Вставляем данные (?,?,?) - это плейсхолдеры для безопасности
                cursor.executemany(
                    "INSERT INTO doctors (full_name, specialty, room_number) VALUES (?,?,?)",
                    doctors_data
                )
                print(f"  - Добавлено {len(doctors_data)} врачей")
            
            # Сохраняем изменения
            conn.commit()
            
            if db_exists:
                print("✅ База данных успешно подключена")
            else:
                print("✅ Новая база данных успешно создана")
            
    except sqlite3.DatabaseError as e:
        # Если произошла ошибка, выводим её
        print(f"❌ Ошибка базы данных: {e}")
        
        # Если файл повреждён, удаляем его
        if os.path.exists(DB_NAME):
            print("🔄 Файл БД повреждён. Удаляем и создаём заново...")
            os.remove(DB_NAME)
            # Пробуем снова (рекурсивно)
            init_db()

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПАЦИЕНТАМИ
# ============================================

def get_all_patients():
    """
    Возвращает список всех пациентов.
    
    Returns:
        list: список всех пациентов (каждый пациент - словарь)
    """
    try:
        with get_connection() as conn:
            # ORDER BY full_name - сортируем по ФИО
            cursor = conn.execute("SELECT * FROM patients ORDER BY full_name")
            return cursor.fetchall()
    except sqlite3.DatabaseError:
        # В случае ошибки возвращаем пустой список
        return []

def search_patients(search_text):
    """
    Ищет пациентов по ФИО или номеру полиса.
    
    Args:
        search_text (str): текст для поиска
    
    Returns:
        list: список найденных пациентов
    """
    try:
        with get_connection() as conn:
            # LIKE '%текст%' - поиск по части слова
            cursor = conn.execute('''
                SELECT * FROM patients 
                WHERE full_name LIKE ? OR policy_number LIKE ?
                ORDER BY full_name
            ''', (f'%{search_text}%', f'%{search_text}%'))
            return cursor.fetchall()
    except sqlite3.DatabaseError:
        return []

def add_patient(full_name, birth_date, phone, policy):
    """
    Добавляет нового пациента в базу данных.
    
    Args:
        full_name (str): ФИО пациента
        birth_date (str): дата рождения (ГГГГ-ММ-ДД)
        phone (str): телефон
        policy (str): номер полиса (должен быть уникальным)
    
    Returns:
        int: ID нового пациента или None в случае ошибки
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO patients (full_name, birth_date, phone, policy_number)
                VALUES (?, ?, ?, ?)
            ''', (full_name, birth_date, phone, policy))
            conn.commit()
            # lastrowid - ID последней вставленной записи
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Ошибка целостности - полис уже существует
        return None
    except sqlite3.DatabaseError:
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
            cursor = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            return cursor.fetchone()
    except sqlite3.DatabaseError:
        return None

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
    except sqlite3.DatabaseError:
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
            cursor = conn.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
            return cursor.fetchone()
    except sqlite3.DatabaseError:
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
        list: список свободного времени (например, ['09:00', '09:30', ...])
    """
    try:
        # Генерируем все возможные слоты времени с 9:00 до 18:00 с шагом 30 минут
        all_times = []
        for hour in range(9, 18):  # с 9 до 18
            for minute in [0, 30]:  # каждые полчаса
                # Форматируем время с ведущими нулями (09:00, 09:30, ...)
                time_str = f"{hour:02d}:{minute:02d}"
                all_times.append(time_str)
        
        # Получаем занятое время из базы
        with get_connection() as conn:
            cursor = conn.execute('''
                SELECT time FROM appointments 
                WHERE doctor_id = ? AND date = ? AND status = 'запланирован'
            ''', (doctor_id, date))
            busy_times = [row['time'] for row in cursor.fetchall()]
        
        # Возвращаем свободное время (которого нет в списке занятых)
        free_times = [t for t in all_times if t not in busy_times]
        return free_times
    except sqlite3.DatabaseError:
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
        int: ID новой записи или None в случае ошибки
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO appointments (patient_id, doctor_id, date, time, status)
                VALUES (?, ?, ?, ?, 'запланирован')
            ''', (patient_id, doctor_id, date, time))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Нарушение уникальности - такое время уже занято
        return None
    except sqlite3.DatabaseError:
        return None

def get_all_appointments():
    """
    Возвращает все записи на приём с подробной информацией.
    Использует JOIN для объединения данных из трёх таблиц.
    
    Returns:
        list: список всех записей с информацией о пациенте и враче
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
            ''')
            return cursor.fetchall()
    except sqlite3.DatabaseError:
        return []

def get_appointments_by_date(date):
    """
    Возвращает записи на конкретную дату.
    
    Args:
        date (str): дата для поиска
    
    Returns:
        list: список записей на указанную дату
    """
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
    except sqlite3.DatabaseError:
        return []

def cancel_appointment(appointment_id):
    """
    Отменяет запись на приём (меняет статус на 'отменён').
    
    Args:
        appointment_id (int): ID записи для отмены
    
    Returns:
        bool: True в случае успеха, False при ошибке
    """
    try:
        with get_connection() as conn:
            conn.execute('''
                UPDATE appointments 
                SET status = 'отменён' 
                WHERE id = ?
            ''', (appointment_id,))
            conn.commit()
            return True
    except sqlite3.DatabaseError:
        return False

def delete_appointment(appointment_id):
    """
    Полностью удаляет запись из базы.
    
    Args:
        appointment_id (int): ID записи для удаления
    
    Returns:
        bool: True в случае успеха, False при ошибке
    """
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            conn.commit()
            return True
    except sqlite3.DatabaseError:
        return False