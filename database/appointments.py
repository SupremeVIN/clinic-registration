"""
Функции для работы с записями на приём.
"""

import sqlite3
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
                INSERT INTO appointments (patient_id, doctor_id, date, time, status)
                VALUES (?, ?, ?, ?, 'запланирован')
            ''', (patient_id, doctor_id, date, time))
            conn.commit()
            
            appointment_id = cursor.lastrowid
            log_action("ADD_APPOINTMENT", 
                      f"Created appointment ID:{appointment_id} for patient:{patient_id} doctor:{doctor_id}")
            
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
                    INSERT INTO appointments (patient_id, doctor_id, date, time, status)
                    VALUES (?, ?, ?, ?, 'запланирован')
                ''', (patient_id, doctor_id, date, time))
                conn2.commit()
                
                appointment_id = cursor.lastrowid
                log_action("ADD_APPOINTMENT", 
                          f"Replaced cancelled appointment ID:{cancelled['id']} with new ID:{appointment_id}")
                return appointment_id
        
        log_action("DUPLICATE_APPOINTMENT", 
                  f"IntegrityError: doctor {doctor_id} at {date} {time} - {str(e)}")
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
                "SELECT id, status, doctor_id, date, time FROM appointments WHERE id = ?", 
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