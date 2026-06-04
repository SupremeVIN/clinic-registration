"""
Функции для работы с записями на приём.
"""

import sqlite3
import csv
from datetime import datetime, timedelta
from database.connection import get_connection
from database.security import log_action, sanitize_input, validate_date

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

def add_appointment(patient_id, doctor_id, date, time, created_by=None):
    """
    Создаёт новую запись на приём.
    
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
            
            # Проверяем, есть ли уже запланированная запись на это время
            existing = conn.execute('''
                SELECT id, status FROM appointments 
                WHERE doctor_id = ? AND date = ? AND time = ? AND status = 'запланирован'
            ''', (doctor_id, date, time)).fetchone()
            
            if existing:
                log_action("DUPLICATE_APPOINTMENT", 
                          f"Attempt to book occupied slot: doctor {doctor_id} at {date} {time}")
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
        # Проверяем, что это не конфликт с отменённой записью
        with get_connection() as conn2:
            cancelled = conn2.execute('''
                SELECT id FROM appointments 
                WHERE doctor_id = ? AND date = ? AND time = ? AND status = 'отменён'
            ''', (doctor_id, date, time)).fetchone()
            
            if cancelled:
                # Если есть отменённая запись, удаляем её и создаём новую
                conn2.execute("DELETE FROM appointments WHERE id = ?", (cancelled['id'],))
                conn2.commit()
                
                # Создаём новую запись
                cursor = conn2.execute('''
                    INSERT INTO appointments (patient_id, doctor_id, date, time, status, created_by)
                    VALUES (?, ?, ?, ?, 'запланирован', ?)
                ''', (patient_id, doctor_id, date, time, created_by))
                conn2.commit()
                
                appointment_id = cursor.lastrowid
                log_action("ADD_APPOINTMENT", 
                          f"Replaced cancelled appointment ID:{cancelled['id']} with new ID:{appointment_id} by {created_by}")
                return appointment_id
        
        log_action("DUPLICATE_APPOINTMENT", 
                  f"IntegrityError: doctor {doctor_id} at {date} {time} - {str(e)}")
        return None
    except sqlite3.DatabaseError as e:
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
                a.created_by
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
                    writer.writerow(['id', 'full_name', 'specialty', 'room_number', 'created_at'])
                    for row in doctors:
                        writer.writerow([row['id'], row['full_name'], row['specialty'], row['room_number'], row['created_at']])
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