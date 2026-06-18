"""
Функции для работы с записями на приём.
"""

import re
import sqlite3
import csv
import json
from pathlib import Path
from datetime import datetime, timedelta
from database.connection import get_connection
from database.security import log_action, sanitize_input, validate_date
from database.doctors import get_doctor_schedule

# Путь к конфигурационному файлу расписания
CONFIG_DIR = Path(__file__).parent.parent / "config"
SCHEDULE_CONFIG_FILE = CONFIG_DIR / "schedule.json"

# Значения по умолчанию (если файл конфигурации не найден)
DEFAULT_SCHEDULE = {
    'work_start_hour': 9,
    'work_end_hour': 18,
    'slot_duration_minutes': 30,
    'lunch_start_hour': 13,
    'lunch_end_hour': 14,
    'break_between_slots': 0,
    'working_days': [1, 2, 3, 4, 5]
}

def ensure_config_dir():
    """Создаёт директорию конфигурации, если её нет"""
    CONFIG_DIR.mkdir(exist_ok=True)

def load_schedule_config():
    """Загружает настройки расписания из JSON файла"""
    ensure_config_dir()
    
    if not SCHEDULE_CONFIG_FILE.exists():
        save_schedule_config(DEFAULT_SCHEDULE)
        log_action("CONFIG", f"Created default schedule config at {SCHEDULE_CONFIG_FILE}")
        return DEFAULT_SCHEDULE.copy()
    
    try:
        with open(SCHEDULE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        for key, default_value in DEFAULT_SCHEDULE.items():
            if key not in config:
                config[key] = default_value
        
        return config
    except Exception as e:
        log_action("CONFIG_ERROR", f"Error loading schedule config: {str(e)}")
        return DEFAULT_SCHEDULE.copy()

def save_schedule_config(config):
    """Сохраняет настройки расписания в JSON файл"""
    ensure_config_dir()
    
    try:
        with open(SCHEDULE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        log_action("CONFIG", f"Saved schedule config to {SCHEDULE_CONFIG_FILE}")
        return True
    except Exception as e:
        log_action("CONFIG_ERROR", f"Error saving schedule config: {str(e)}")
        return False

def get_work_schedule(doctor_id=None):
    """Получает настройки рабочего расписания"""
    if doctor_id:
        doctor_schedule = get_doctor_schedule(doctor_id)
        if doctor_schedule and doctor_schedule.get('is_custom'):
            return doctor_schedule
    
    return load_schedule_config()

def is_working_day(date, doctor_id=None):
    """Проверяет, является ли дата рабочим днём"""
    schedule = get_work_schedule(doctor_id)
    working_days = schedule.get('working_days', [1, 2, 3, 4, 5])
    return (date.weekday() + 1) in working_days

def generate_time_slots(schedule=None, date=None):
    """Генерирует список временных слотов"""
    if schedule is None:
        schedule = get_work_schedule()
    
    all_times = []
    start = schedule['work_start_hour']
    end = schedule['work_end_hour']
    slot = schedule['slot_duration_minutes']
    lunch_start = schedule.get('lunch_start_hour')
    lunch_end = schedule.get('lunch_end_hour')
    
    for hour in range(start, end):
        for minute in range(0, 60, slot):
            time_str = f"{hour:02d}:{minute:02d}"
            
            if lunch_start is not None and lunch_end is not None:
                if lunch_start <= hour < lunch_end:
                    continue
                if hour == lunch_start - 1 and minute + slot > 60:
                    continue
            
            all_times.append(time_str)
    
    return all_times

def get_free_time(doctor_id, date):
    """Возвращает список свободного времени"""
    valid, msg = validate_date(date)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid date for free time: {msg}")
        return []
    
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        if not is_working_day(date_obj, doctor_id):
            return []
        
        schedule = get_work_schedule(doctor_id)
        all_times = generate_time_slots(schedule, date_obj)
        
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

def add_appointment(patient_id, doctor_id, date, time, created_by=None):
    """Создаёт новую запись на приём"""
    valid, msg = validate_date(date)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid appointment date: {msg}")
        return None
    
    if not re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', time):
        log_action("VALIDATION_ERROR", f"Invalid time format: {time}")
        return None
    
    schedule = get_work_schedule(doctor_id)
    valid_times = generate_time_slots(schedule)
    if time not in valid_times:
        log_action("VALIDATION_ERROR", f"Time {time} outside working hours for doctor {doctor_id}")
        return None
    
    try:
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        if appointment_date < datetime.now().date():
            log_action("VALIDATION_ERROR", "Attempt to book appointment in the past")
            return None
    except ValueError:
        return None
    
    with get_connection() as conn:
        conn.execute("BEGIN TRANSACTION")
        
        try:
            patient = conn.execute(
                "SELECT id FROM patients WHERE id = ?", 
                (patient_id,)
            ).fetchone()
            doctor = conn.execute(
                "SELECT id FROM doctors WHERE id = ? AND is_deleted = 0", 
                (doctor_id,)
            ).fetchone()
            
            if not patient or not doctor:
                log_action("VALIDATION_ERROR", f"Invalid patient or doctor ID")
                conn.execute("ROLLBACK")
                return None
            
            existing = conn.execute('''
                SELECT id FROM appointments 
                WHERE doctor_id = ? AND date = ? AND time = ? AND status = 'запланирован'
            ''', (doctor_id, date, time)).fetchone()
            
            if existing:
                log_action("DUPLICATE_APPOINTMENT", 
                          f"Attempt to book occupied slot: doctor {doctor_id} at {date} {time}")
                conn.execute("ROLLBACK")
                return None
            
            cursor = conn.execute('''
                INSERT INTO appointments (patient_id, doctor_id, date, time, status, created_by)
                VALUES (?, ?, ?, ?, 'запланирован', ?)
            ''', (patient_id, doctor_id, date, time, created_by))
            
            conn.commit()
            
            appointment_id = cursor.lastrowid
            log_action("ADD_APPOINTMENT", 
                      f"Created appointment ID:{appointment_id} for patient:{patient_id} doctor:{doctor_id} by {created_by}")
            
            return appointment_id
            
        except sqlite3.IntegrityError as e:
            conn.execute("ROLLBACK")
            log_action("DUPLICATE_APPOINTMENT", f"IntegrityError: {str(e)}")
            return None
        except sqlite3.DatabaseError as e:
            conn.execute("ROLLBACK")
            log_action("DB_ERROR", f"Error adding appointment: {str(e)}")
            return None

def get_all_appointments(doctor_id=None, status=None, date_from=None, date_to=None):
    """Возвращает записи на приём с фильтрацией"""
    try:
        query = '''
            SELECT 
                a.id,
                p.full_name as patient_name,
                p.policy_number,
                d.full_name as doctor_name,
                d.specialty,
                d.room_number,
                a.date,
                a.time,
                a.status,
                a.created_by,
                a.cancelled_by,
                a.cancelled_at,
                d.is_deleted as doctor_deleted
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE 1=1
        '''
        params = []
        
        if doctor_id:
            query += " AND a.doctor_id = ?"
            params.append(doctor_id)
        
        if status:
            query += " AND a.status = ?"
            params.append(status)
        
        if date_from:
            query += " AND a.date >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND a.date <= ?"
            params.append(date_to)
        
        query += " ORDER BY a.date DESC, a.time DESC LIMIT 1000"
        
        with get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting appointments: {str(e)}")
        return []

def search_appointments(search_text, doctor_id=None):
    """Ищет записи по ФИО пациента или номеру полиса"""
    search_text = sanitize_input(search_text, 100)
    
    if not search_text or len(search_text) < 2:
        return []
    
    try:
        query = '''
            SELECT 
                a.id,
                p.full_name as patient_name,
                p.policy_number,
                d.full_name as doctor_name,
                d.specialty,
                d.room_number,
                a.date,
                a.time,
                a.status,
                a.created_by
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            WHERE (p.full_name LIKE ? OR p.policy_number LIKE ?)
        '''
        params = [f'%{search_text}%', f'%{search_text}%']
        
        if doctor_id:
            query += " AND a.doctor_id = ?"
            params.append(doctor_id)
        
        query += " ORDER BY a.date DESC, a.time DESC LIMIT 100"
        
        with get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error searching appointments: {str(e)}")
        return []

def cancel_appointment(appointment_id, cancelled_by=None):
    """Отменяет запись на приём"""
    try:
        with get_connection() as conn:
            appointment = conn.execute(
                "SELECT id, status FROM appointments WHERE id = ?", 
                (appointment_id,)
            ).fetchone()
            
            if not appointment:
                log_action("CANCEL_ERROR", f"Appointment {appointment_id} not found")
                return False
            
            if appointment['status'] == 'отменён':
                log_action("CANCEL_ERROR", f"Appointment {appointment_id} already cancelled")
                return False
            
            conn.execute('''
                UPDATE appointments 
                SET status = 'отменён', 
                    cancelled_at = CURRENT_TIMESTAMP,
                    cancelled_by = ?
                WHERE id = ?
            ''', (cancelled_by, appointment_id))
            conn.commit()
            
            log_action("CANCEL_APPOINTMENT", f"Cancelled appointment ID:{appointment_id} by {cancelled_by}")
            return True
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error cancelling appointment {appointment_id}: {str(e)}")
        return False

def delete_old_appointments(days=30):
    """Удаляет только отменённые записи старше указанного количества дней"""
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        with get_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.execute('''
                DELETE FROM appointments 
                WHERE date < ? AND status = 'отменён'
            ''', (cutoff_date,))
            conn.commit()
            deleted_count = cursor.rowcount
            log_action("CLEANUP", f"Deleted {deleted_count} old cancelled appointments")
            return deleted_count
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error deleting old appointments: {str(e)}")
        return 0

def export_data(filepath, data_type='all', doctor_id=None):
    """
    Экспортирует данные в CSV файл с правильной кодировкой и форматированием.
    
    Args:
        filepath (str): путь к файлу
        data_type (str): 'patients', 'doctors', 'appointments' или 'all'
        doctor_id (int): ID врача для фильтрации (опционально)
    
    Returns:
        bool: True при успехе
    """
    def escape_csv_value(value):
        """Экранирует значение для CSV"""
        if value is None:
            return ''
        value = str(value)
        if ',' in value or ';' in value or '"' in value or '\n' in value:
            value = value.replace('"', '""')
            value = f'"{value}"'
        return value
    
    def format_date(date_str):
        """Форматирует дату в читаемый вид"""
        if not date_str:
            return ''
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d.%m.%Y')
        except:
            return date_str
    
    def format_datetime(dt_str):
        """Форматирует дату и время"""
        if not dt_str:
            return ''
        try:
            dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            return dt_obj.strftime('%d.%m.%Y %H:%M:%S')
        except:
            return dt_str
    
    try:
        delimiter = ';'
        
        with get_connection() as conn:
            if data_type == 'patients' or data_type == 'all':
                cursor = conn.execute('''
                    SELECT id, full_name, birth_date, phone, policy_number, created_at 
                    FROM patients ORDER BY id
                ''')
                patients = cursor.fetchall()
                
                filepath_patients = f"{filepath}_patients.csv"
                with open(filepath_patients, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f, delimiter=delimiter)
                    writer.writerow(['ID', 'ФИО', 'Дата рождения', 'Телефон', 'Номер полиса', 'Дата создания'])
                    
                    for row in patients:
                        writer.writerow([
                            escape_csv_value(row['id']),
                            escape_csv_value(row['full_name']),
                            escape_csv_value(format_date(row['birth_date'])),
                            escape_csv_value(row['phone']),
                            escape_csv_value(row['policy_number']),
                            escape_csv_value(format_datetime(row['created_at']))
                        ])
                
                log_action("EXPORT", f"Exported {len(patients)} patients to {filepath_patients}")
            
            if data_type == 'doctors' or data_type == 'all':
                cursor = conn.execute('''
                    SELECT id, full_name, specialty, room_number, created_at, is_deleted, deleted_at 
                    FROM doctors ORDER BY id
                ''')
                doctors = cursor.fetchall()
                
                filepath_doctors = f"{filepath}_doctors.csv"
                with open(filepath_doctors, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f, delimiter=delimiter)
                    writer.writerow(['ID', 'ФИО', 'Специальность', 'Кабинет', 'Дата создания', 'Удалён', 'Дата удаления'])
                    
                    for row in doctors:
                        writer.writerow([
                            escape_csv_value(row['id']),
                            escape_csv_value(row['full_name']),
                            escape_csv_value(row['specialty']),
                            escape_csv_value(row['room_number']),
                            escape_csv_value(format_datetime(row['created_at'])),
                            escape_csv_value('Да' if row['is_deleted'] else 'Нет'),
                            escape_csv_value(format_datetime(row['deleted_at']) if row['deleted_at'] else '')
                        ])
                
                log_action("EXPORT", f"Exported {len(doctors)} doctors to {filepath_doctors}")
            
            if data_type == 'appointments' or data_type == 'all':
                # Если указан doctor_id - экспортируем только его записи
                if doctor_id:
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
                            a.status, 
                            a.created_by,
                            a.created_at,
                            a.cancelled_by,
                            a.cancelled_at
                        FROM appointments a
                        JOIN patients p ON a.patient_id = p.id
                        JOIN doctors d ON a.doctor_id = d.id
                        WHERE a.doctor_id = ?
                        ORDER BY a.date DESC, a.time DESC
                    ''', (doctor_id,))
                else:
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
                            a.status, 
                            a.created_by,
                            a.created_at,
                            a.cancelled_by,
                            a.cancelled_at
                        FROM appointments a
                        JOIN patients p ON a.patient_id = p.id
                        JOIN doctors d ON a.doctor_id = d.id
                        ORDER BY a.date DESC, a.time DESC
                    ''')
                appointments = cursor.fetchall()
                
                filepath_appointments = f"{filepath}_appointments.csv"
                with open(filepath_appointments, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f, delimiter=delimiter)
                    writer.writerow([
                        'ID', 'Пациент', 'Номер полиса', 'Врач', 'Специальность', 
                        'Кабинет', 'Дата', 'Время', 'Статус', 'Кто создал', 
                        'Дата создания', 'Кто отменил', 'Дата отмены'
                    ])
                    
                    for row in appointments:
                        writer.writerow([
                            escape_csv_value(row['id']),
                            escape_csv_value(row['patient_name']),
                            escape_csv_value(row['policy_number']),
                            escape_csv_value(row['doctor_name']),
                            escape_csv_value(row['specialty']),
                            escape_csv_value(row['room_number']),
                            escape_csv_value(format_date(row['date'])),
                            escape_csv_value(row['time']),
                            escape_csv_value(row['status']),
                            escape_csv_value(row['created_by']),
                            escape_csv_value(format_datetime(row['created_at'])),
                            escape_csv_value(row['cancelled_by']),
                            escape_csv_value(format_datetime(row['cancelled_at']) if row['cancelled_at'] else '')
                        ])
                
                log_action("EXPORT", f"Exported {len(appointments)} appointments to {filepath_appointments}")
        
        return True
    except Exception as e:
        log_action("EXPORT_ERROR", f"Error exporting data: {str(e)}")
        return False

# ============================================
# ФУНКЦИИ ДЛЯ ИМПОРТА ДАННЫХ
# ============================================

def detect_csv_format(filepath):
    """
    Определяет формат CSV файла: разделитель, кодировку, заголовки.
    
    Args:
        filepath (str): путь к файлу
    
    Returns:
        tuple: (delimiter, encoding, headers)
    """
    delimiters = [';', ',']
    encodings = ['utf-8-sig', 'utf-8', 'cp1251']
    
    for encoding in encodings:
        for delimiter in delimiters:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    sample = f.read(4096)
                    if delimiter in sample:
                        f.seek(0)
                        reader = csv.reader(f, delimiter=delimiter)
                        first_row = next(reader, [])
                        if len(first_row) >= 2:
                            return delimiter, encoding, first_row
            except:
                continue
    
    return ';', 'utf-8-sig', None

def import_patients_from_csv(filepath):
    """
    Импортирует пациентов из CSV файла с поддержкой разных форматов.
    
    Args:
        filepath (str): путь к файлу
    
    Returns:
        tuple: (успешно, количество, ошибки)
    """
    imported = 0
    errors = []
    
    try:
        delimiter, encoding, _ = detect_csv_format(filepath)
        
        header_mapping = {
            'full_name': ['full_name', 'ФИО', 'Full Name', 'Имя', 'Пациент', 'patient_name'],
            'birth_date': ['birth_date', 'Дата рождения', 'Birth Date', 'Дата', 'Date of birth'],
            'phone': ['phone', 'Телефон', 'Phone', 'Номер телефона', 'Phone number'],
            'policy_number': ['policy_number', 'Номер полиса', 'Policy Number', 'Полис', 'Policy']
        }
        
        with open(filepath, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            if not reader.fieldnames:
                return False, 0, ["Файл не содержит заголовков"]
            
            available_fields = {k.lower(): k for k in reader.fieldnames}
            
            column_mapping = {}
            for db_field, possible_names in header_mapping.items():
                for name in possible_names:
                    if name.lower() in available_fields:
                        column_mapping[db_field] = available_fields[name.lower()]
                        break
            
            if 'full_name' not in column_mapping or 'policy_number' not in column_mapping:
                return False, 0, ["Файл должен содержать колонки: ФИО и Номер полиса"]
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    full_name = row.get(column_mapping.get('full_name', ''), '').strip()
                    policy = row.get(column_mapping.get('policy_number', ''), '').strip()
                    
                    if not full_name or not policy:
                        errors.append(f"Строка {row_num}: отсутствует ФИО или номер полиса")
                        continue
                    
                    birth_date = row.get(column_mapping.get('birth_date', ''), '').strip()
                    if birth_date:
                        for date_format in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                            try:
                                date_obj = datetime.strptime(birth_date, date_format)
                                birth_date = date_obj.strftime('%Y-%m-%d')
                                break
                            except:
                                continue
                        else:
                            birth_date = None
                    else:
                        birth_date = None
                    
                    phone = row.get(column_mapping.get('phone', ''), '').strip()
                    if not phone:
                        phone = None
                    
                    if len(policy) != 16 or not policy.isdigit():
                        errors.append(f"Строка {row_num}: неверный формат полиса (должен быть 16 цифр)")
                        continue
                    
                    with get_connection() as conn:
                        existing = conn.execute(
                            "SELECT id FROM patients WHERE policy_number = ?",
                            (policy,)
                        ).fetchone()
                        
                        if existing:
                            errors.append(f"Строка {row_num}: пациент с полисом {policy} уже существует")
                            continue
                        
                        conn.execute('''
                            INSERT INTO patients (full_name, birth_date, phone, policy_number)
                            VALUES (?, ?, ?, ?)
                        ''', (full_name, birth_date, phone, policy))
                        conn.commit()
                        imported += 1
                        
                except Exception as e:
                    errors.append(f"Строка {row_num}: {str(e)}")
        
        log_action("IMPORT", f"Imported {imported} patients from {filepath}, errors: {len(errors)}")
        return True, imported, errors
        
    except Exception as e:
        log_action("IMPORT_ERROR", f"Error importing patients: {str(e)}")
        return False, 0, [str(e)]

def import_doctors_from_csv(filepath):
    """
    Импортирует врачей из CSV файла.
    
    Args:
        filepath (str): путь к файлу
    
    Returns:
        tuple: (успешно, количество, ошибки)
    """
    imported = 0
    errors = []
    
    try:
        delimiter, encoding, _ = detect_csv_format(filepath)
        
        header_mapping = {
            'full_name': ['full_name', 'ФИО', 'Full Name', 'Имя', 'Врач'],
            'specialty': ['specialty', 'Специальность', 'Specialty', 'Специализация'],
            'room_number': ['room_number', 'Кабинет', 'Room Number', 'Каб', 'Room']
        }
        
        with open(filepath, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            if not reader.fieldnames:
                return False, 0, ["Файл не содержит заголовков"]
            
            available_fields = {k.lower(): k for k in reader.fieldnames}
            
            column_mapping = {}
            for db_field, possible_names in header_mapping.items():
                for name in possible_names:
                    if name.lower() in available_fields:
                        column_mapping[db_field] = available_fields[name.lower()]
                        break
            
            if 'full_name' not in column_mapping:
                return False, 0, ["Файл должен содержать колонку: ФИО"]
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    full_name = row.get(column_mapping.get('full_name', ''), '').strip()
                    specialty = row.get(column_mapping.get('specialty', ''), '').strip()
                    room_number = row.get(column_mapping.get('room_number', ''), '').strip()
                    
                    if not full_name:
                        errors.append(f"Строка {row_num}: отсутствует ФИО")
                        continue
                    
                    with get_connection() as conn:
                        if room_number:
                            existing_room = conn.execute(
                                "SELECT id FROM doctors WHERE room_number = ? AND is_deleted = 0",
                                (room_number,)
                            ).fetchone()
                            if existing_room:
                                errors.append(f"Строка {row_num}: кабинет {room_number} уже занят")
                                continue
                        
                        existing = conn.execute(
                            "SELECT id FROM doctors WHERE full_name = ? AND is_deleted = 0",
                            (full_name,)
                        ).fetchone()
                        
                        if existing:
                            errors.append(f"Строка {row_num}: врач {full_name} уже существует")
                            continue
                        
                        conn.execute('''
                            INSERT INTO doctors (full_name, specialty, room_number, is_deleted)
                            VALUES (?, ?, ?, 0)
                        ''', (full_name, specialty or None, room_number or None))
                        conn.commit()
                        imported += 1
                        
                except Exception as e:
                    errors.append(f"Строка {row_num}: {str(e)}")
        
        log_action("IMPORT", f"Imported {imported} doctors from {filepath}, errors: {len(errors)}")
        return True, imported, errors
        
    except Exception as e:
        log_action("IMPORT_ERROR", f"Error importing doctors: {str(e)}")
        return False, 0, [str(e)]

def import_appointments_from_csv(filepath):
    """
    Импортирует записи на приём из CSV файла.
    
    Args:
        filepath (str): путь к файлу
    
    Returns:
        tuple: (успешно, количество, ошибки)
    """
    imported = 0
    errors = []
    
    try:
        delimiter, encoding, _ = detect_csv_format(filepath)
        
        header_mapping = {
            'patient_name': ['patient_name', 'Пациент', 'ФИО пациента', 'Patient'],
            'policy_number': ['policy_number', 'Номер полиса', 'Policy'],
            'doctor_name': ['doctor_name', 'Врач', 'Doctor'],
            'date': ['date', 'Дата', 'Date'],
            'time': ['time', 'Время', 'Time'],
            'status': ['status', 'Статус', 'Status']
        }
        
        with open(filepath, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            if not reader.fieldnames:
                return False, 0, ["Файл не содержит заголовков"]
            
            available_fields = {k.lower(): k for k in reader.fieldnames}
            
            column_mapping = {}
            for db_field, possible_names in header_mapping.items():
                for name in possible_names:
                    if name.lower() in available_fields:
                        column_mapping[db_field] = available_fields[name.lower()]
                        break
            
            required_fields = ['patient_name', 'doctor_name', 'date', 'time']
            missing = [f for f in required_fields if f not in column_mapping]
            if missing:
                return False, 0, [f"Файл должен содержать колонки: {', '.join(missing)}"]
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    patient_name = row.get(column_mapping.get('patient_name', ''), '').strip()
                    doctor_name = row.get(column_mapping.get('doctor_name', ''), '').strip()
                    date_str = row.get(column_mapping.get('date', ''), '').strip()
                    time_str = row.get(column_mapping.get('time', ''), '').strip()
                    status = row.get(column_mapping.get('status', ''), '').strip() or 'запланирован'
                    
                    if not patient_name or not doctor_name or not date_str or not time_str:
                        errors.append(f"Строка {row_num}: не все обязательные поля заполнены")
                        continue
                    
                    with get_connection() as conn:
                        patient = conn.execute(
                            "SELECT id FROM patients WHERE full_name = ?",
                            (patient_name,)
                        ).fetchone()
                        
                        if not patient:
                            errors.append(f"Строка {row_num}: пациент '{patient_name}' не найден")
                            continue
                        
                        doctor = conn.execute(
                            "SELECT id FROM doctors WHERE full_name = ? AND is_deleted = 0",
                            (doctor_name,)
                        ).fetchone()
                        
                        if not doctor:
                            errors.append(f"Строка {row_num}: врач '{doctor_name}' не найден")
                            continue
                        
                        for date_format in ['%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                            try:
                                date_obj = datetime.strptime(date_str, date_format)
                                date = date_obj.strftime('%Y-%m-%d')
                                break
                            except:
                                continue
                        else:
                            errors.append(f"Строка {row_num}: неверный формат даты")
                            continue
                        
                        if not re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', time_str):
                            errors.append(f"Строка {row_num}: неверный формат времени (ожидается HH:MM)")
                            continue
                        
                        existing = conn.execute('''
                            SELECT id FROM appointments 
                            WHERE doctor_id = ? AND date = ? AND time = ? AND status = 'запланирован'
                        ''', (doctor['id'], date, time_str)).fetchone()
                        
                        if existing:
                            errors.append(f"Строка {row_num}: время {date} {time_str} уже занято")
                            continue
                        
                        conn.execute('''
                            INSERT INTO appointments 
                            (patient_id, doctor_id, date, time, status, created_by)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (patient['id'], doctor['id'], date, time_str, status, 'import'))
                        conn.commit()
                        imported += 1
                        
                except Exception as e:
                    errors.append(f"Строка {row_num}: {str(e)}")
        
        log_action("IMPORT", f"Imported {imported} appointments from {filepath}, errors: {len(errors)}")
        return True, imported, errors
        
    except Exception as e:
        log_action("IMPORT_ERROR", f"Error importing appointments: {str(e)}")
        return False, 0, [str(e)]