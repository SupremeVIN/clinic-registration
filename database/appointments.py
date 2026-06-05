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
    'working_days': [1, 2, 3, 4, 5]  # 1=пн, 5=пт
}

def ensure_config_dir():
    """Создаёт директорию конфигурации, если её нет"""
    CONFIG_DIR.mkdir(exist_ok=True)

def load_schedule_config():
    """
    Загружает настройки расписания из JSON файла.
    
    Returns:
        dict: настройки расписания
    """
    ensure_config_dir()
    
    # Если файла нет - создаём с настройками по умолчанию
    if not SCHEDULE_CONFIG_FILE.exists():
        save_schedule_config(DEFAULT_SCHEDULE)
        log_action("CONFIG", f"Created default schedule config at {SCHEDULE_CONFIG_FILE}")
        return DEFAULT_SCHEDULE.copy()
    
    try:
        with open(SCHEDULE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Проверяем и дополняем недостающие ключи значениями по умолчанию
        for key, default_value in DEFAULT_SCHEDULE.items():
            if key not in config:
                config[key] = default_value
        
        return config
    except Exception as e:
        log_action("CONFIG_ERROR", f"Error loading schedule config: {str(e)}")
        return DEFAULT_SCHEDULE.copy()

def save_schedule_config(config):
    """
    Сохраняет настройки расписания в JSON файл.
    
    Args:
        config (dict): настройки расписания
    
    Returns:
        bool: True при успехе
    """
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
    """
    Получает настройки рабочего расписания.
    Если указан doctor_id и есть индивидуальное расписание - использует его.
    
    Args:
        doctor_id (int): ID врача (опционально)
    
    Returns:
        dict: настройки расписания
    """
    if doctor_id:
        doctor_schedule = get_doctor_schedule(doctor_id)
        if doctor_schedule and doctor_schedule.get('is_custom'):
            return doctor_schedule
    
    return load_schedule_config()

def is_working_day(date, doctor_id=None):
    """
    Проверяет, является ли дата рабочим днём для конкретного врача.
    
    Args:
        date (datetime.date): дата для проверки
        doctor_id (int): ID врача (опционально)
    
    Returns:
        bool: True если рабочий день
    """
    schedule = get_work_schedule(doctor_id)
    working_days = schedule.get('working_days', [1, 2, 3, 4, 5])
    # weekday(): 0=пн, 1=вт, 2=ср, 3=чт, 4=пт, 5=сб, 6=вс
    return (date.weekday() + 1) in working_days

def generate_time_slots(schedule=None, date=None):
    """
    Генерирует список временных слотов на основе расписания.
    
    Args:
        schedule (dict): настройки расписания
        date (datetime.date): дата для проверки рабочих дней
    
    Returns:
        list: список времени в формате HH:MM
    """
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
            
            # Проверяем обеденный перерыв
            if lunch_start is not None and lunch_end is not None:
                if lunch_start <= hour < lunch_end:
                    continue
                # Если время начала слота до обеда, а конец попадает на обед
                if hour == lunch_start - 1 and minute + slot > 60:
                    continue
            
            all_times.append(time_str)
    
    return all_times

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
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Получаем расписание для конкретного врача
        schedule = get_work_schedule(doctor_id)
        
        # Проверяем, рабочий ли день для этого врача
        if not is_working_day(date_obj, doctor_id):
            return []  # В нерабочий день нет слотов
        
        all_times = generate_time_slots(schedule, date_obj)
        
        with get_connection() as conn:
            # Проверяем только запланированные записи (не отменённые)
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

def check_patient_duplicate(patient_id, doctor_id, date):
    """
    Проверяет, нет ли у пациента уже записи к этому врачу на эту дату.
    
    Args:
        patient_id (int): ID пациента
        doctor_id (int): ID врача
        date (str): дата
    
    Returns:
        tuple: (bool, str) - (есть ли дубликат, сообщение)
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                SELECT id, time FROM appointments 
                WHERE patient_id = ? AND doctor_id = ? AND date = ? AND status = 'запланирован'
            ''', (patient_id, doctor_id, date))
            existing = cursor.fetchone()
            
            if existing:
                return True, f"У пациента уже есть запись к этому врачу на {date} в {existing['time']}"
            return False, ""
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error checking duplicate: {str(e)}")
        return False, ""

def add_appointment(patient_id, doctor_id, date, time, created_by=None):
    """
    Создаёт новую запись на приём с использованием транзакции.
    
    Args:
        patient_id (int): ID пациента
        doctor_id (int): ID врача
        date (str): дата приёма
        time (str): время приёма
        created_by (str): кто создал запись
    
    Returns:
        int: ID новой записи или None
    """
    valid, msg = validate_date(date)
    if not valid:
        log_action("VALIDATION_ERROR", f"Invalid appointment date: {msg}")
        return None
    
    # Проверка формата времени
    if not re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', time):
        log_action("VALIDATION_ERROR", f"Invalid time format: {time}")
        return None
    
    # Проверяем, что время входит в рабочие часы для этого врача
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
    
    # Используем транзакцию для атомарности операций
    with get_connection() as conn:
        # Начинаем транзакцию явно
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
            
            # Проверяем, есть ли уже запланированная запись на это время
            existing = conn.execute('''
                SELECT id, status FROM appointments 
                WHERE doctor_id = ? AND date = ? AND time = ? AND status = 'запланирован'
            ''', (doctor_id, date, time)).fetchone()
            
            if existing:
                log_action("DUPLICATE_APPOINTMENT", 
                          f"Attempt to book occupied slot: doctor {doctor_id} at {date} {time}")
                conn.execute("ROLLBACK")
                return None
            
            # НОВАЯ ПРОВЕРКА: Пациент не может записаться к одному врачу дважды в один день
            has_duplicate, dup_msg = check_patient_duplicate(patient_id, doctor_id, date)
            if has_duplicate:
                log_action("DUPLICATE_PATIENT_APPOINTMENT", 
                          f"Patient {patient_id} already has appointment with doctor {doctor_id} on {date}")
                conn.execute("ROLLBACK")
                return None
            
            # Проверяем, есть ли отменённая запись на это время
            cancelled = conn.execute('''
                SELECT id FROM appointments 
                WHERE doctor_id = ? AND date = ? AND time = ? AND status = 'отменён'
            ''', (doctor_id, date, time)).fetchone()
            
            if cancelled:
                # Если есть отменённая запись, удаляем её
                conn.execute("DELETE FROM appointments WHERE id = ?", (cancelled['id'],))
            
            # Создаём новую запись
            cursor = conn.execute('''
                INSERT INTO appointments (patient_id, doctor_id, date, time, status, created_by)
                VALUES (?, ?, ?, ?, 'запланирован', ?)
            ''', (patient_id, doctor_id, date, time, created_by))
            
            # Фиксируем транзакцию
            conn.commit()
            
            appointment_id = cursor.lastrowid
            if cancelled:
                log_action("ADD_APPOINTMENT", 
                          f"Replaced cancelled appointment ID:{cancelled['id']} with new ID:{appointment_id} by {created_by}")
            else:
                log_action("ADD_APPOINTMENT", 
                          f"Created appointment ID:{appointment_id} for patient:{patient_id} doctor:{doctor_id} by {created_by}")
            
            return appointment_id
            
        except sqlite3.IntegrityError as e:
            conn.execute("ROLLBACK")
            log_action("DUPLICATE_APPOINTMENT", 
                      f"IntegrityError: doctor {doctor_id} at {date} {time} - {str(e)}")
            return None
        except sqlite3.DatabaseError as e:
            conn.execute("ROLLBACK")
            log_action("DB_ERROR", f"Error adding appointment: {str(e)}")
            return None

def get_all_appointments(doctor_id=None, status=None, date_from=None, date_to=None):
    """
    Возвращает записи на приём с возможностью фильтрации.
    
    Args:
        doctor_id (int): ID врача (опционально)
        status (str): статус записи (опционально)
        date_from (str): дата от
        date_to (str): дата до
    
    Returns:
        list: список записей
    """
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
    """
    Ищет записи по ФИО пациента или номеру полиса.
    
    Args:
        search_text (str): текст для поиска
        doctor_id (int): ID врача (опционально)
    
    Returns:
        list: список найденных записей
    """
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
    """
    Отменяет запись на приём.
    
    Args:
        appointment_id (int): ID записи
        cancelled_by (str): кто отменил запись
    
    Returns:
        bool: True при успехе
    """
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
            # Используем транзакцию для атомарного удаления
            conn.execute("BEGIN TRANSACTION")
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

def export_data(filepath, data_type='all'):
    """
    Экспортирует данные в CSV файл.
    
    Args:
        filepath (str): путь к файлу
        data_type (str): 'patients', 'doctors', 'appointments' или 'all'
    
    Returns:
        bool: True при успехе
    """
    try:
        with get_connection() as conn:
            if data_type == 'patients' or data_type == 'all':
                cursor = conn.execute("SELECT * FROM patients")
                patients = cursor.fetchall()
                with open(f"{filepath}_patients.csv", 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'full_name', 'birth_date', 'phone', 'policy_number', 'created_at'])
                    for row in patients:
                        writer.writerow([row['id'], row['full_name'], row['birth_date'], row['phone'], row['policy_number'], row['created_at']])
                log_action("EXPORT", f"Exported {len(patients)} patients to {filepath}_patients.csv")
            
            if data_type == 'doctors' or data_type == 'all':
                cursor = conn.execute("SELECT * FROM doctors")
                doctors = cursor.fetchall()
                with open(f"{filepath}_doctors.csv", 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'full_name', 'specialty', 'room_number', 'created_at', 'is_deleted', 'deleted_at'])
                    for row in doctors:
                        writer.writerow([row['id'], row['full_name'], row['specialty'], row['room_number'], row['created_at'], row['is_deleted'], row['deleted_at']])
                log_action("EXPORT", f"Exported {len(doctors)} doctors to {filepath}_doctors.csv")
            
            if data_type == 'appointments' or data_type == 'all':
                cursor = conn.execute("SELECT * FROM appointments")
                appointments = cursor.fetchall()
                with open(f"{filepath}_appointments.csv", 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'patient_id', 'doctor_id', 'date', 'time', 'status', 'created_by', 'created_at', 'cancelled_at', 'cancelled_by'])
                    for row in appointments:
                        writer.writerow([row['id'], row['patient_id'], row['doctor_id'], row['date'], row['time'], row['status'], row['created_by'], row['created_at'], row['cancelled_at'], row['cancelled_by']])
                log_action("EXPORT", f"Exported {len(appointments)} appointments to {filepath}_appointments.csv")
        
        return True
    except Exception as e:
        log_action("EXPORT_ERROR", f"Error exporting data: {str(e)}")
        return False

def import_patients_from_csv(filepath):
    """
    Импортирует пациентов из CSV файла.
    
    Args:
        filepath (str): путь к файлу
    
    Returns:
        tuple: (успешно, количество, ошибки)
    """
    imported = 0
    errors = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    with get_connection() as conn:
                        conn.execute('''
                            INSERT OR IGNORE INTO patients (full_name, birth_date, phone, policy_number)
                            VALUES (?, ?, ?, ?)
                        ''', (row.get('full_name'), row.get('birth_date'), row.get('phone'), row.get('policy_number')))
                        conn.commit()
                        imported += 1
                except Exception as e:
                    errors.append(str(e))
        
        log_action("IMPORT", f"Imported {imported} patients from {filepath}")
        return True, imported, errors
    except Exception as e:
        log_action("IMPORT_ERROR", f"Error importing patients: {str(e)}")
        return False, 0, [str(e)]