"""
Функции для работы с врачами.
"""

import sqlite3
import json
from database.connection import get_connection
from database.security import log_action

def get_all_doctors(include_deleted=False):
    """
    Возвращает список всех врачей.
    
    Args:
        include_deleted (bool): включать удаленных врачей
    
    Returns:
        list: список всех врачей
    """
    try:
        with get_connection() as conn:
            if include_deleted:
                cursor = conn.execute("SELECT * FROM doctors ORDER BY full_name")
            else:
                cursor = conn.execute("SELECT * FROM doctors WHERE is_deleted = 0 ORDER BY full_name")
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting all doctors: {str(e)}")
        return []

def get_doctor_by_id(doctor_id, include_deleted=False):
    """
    Получает данные врача по ID.
    
    Args:
        doctor_id (int): ID врача
        include_deleted (bool): включать удаленных врачей
    
    Returns:
        Row: данные врача или None
    """
    try:
        with get_connection() as conn:
            if include_deleted:
                cursor = conn.execute(
                    "SELECT * FROM doctors WHERE id = ?", 
                    (doctor_id,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM doctors WHERE id = ? AND is_deleted = 0", 
                    (doctor_id,)
                )
            return cursor.fetchone()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting doctor {doctor_id}: {str(e)}")
        return None

def check_room_unique(room_number, exclude_doctor_id=None):
    """
    Проверяет, свободен ли кабинет.
    
    Args:
        room_number (str): номер кабинета
        exclude_doctor_id (int): ID врача, которого исключаем из проверки (при редактировании)
    
    Returns:
        tuple: (bool, str) - (свободен ли, сообщение)
    """
    if not room_number:
        return True, "OK"
    
    try:
        with get_connection() as conn:
            if exclude_doctor_id:
                cursor = conn.execute(
                    "SELECT id, full_name FROM doctors WHERE room_number = ? AND id != ? AND is_deleted = 0",
                    (room_number, exclude_doctor_id)
                )
            else:
                cursor = conn.execute(
                    "SELECT id, full_name FROM doctors WHERE room_number = ? AND is_deleted = 0",
                    (room_number,)
                )
            
            existing = cursor.fetchone()
            if existing:
                return False, f"Кабинет {room_number} уже занят врачом {existing['full_name']}"
            
            return True, "OK"
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error checking room: {str(e)}")
        return False, f"Ошибка проверки кабинета: {str(e)}"

def add_doctor(full_name, specialty, room_number, user_id=None):
    """
    Добавляет нового врача.
    
    Args:
        full_name (str): ФИО врача
        specialty (str): специальность
        room_number (str): номер кабинета
        user_id (int): ID пользователя (если есть)
    
    Returns:
        int: ID врача или None
    """
    # Проверяем уникальность кабинета
    is_unique, msg = check_room_unique(room_number)
    if not is_unique:
        log_action("ADD_DOCTOR_ERROR", f"Room {room_number} is already occupied: {msg}")
        return None
    
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO doctors (full_name, specialty, room_number, user_id, is_deleted)
                VALUES (?, ?, ?, ?, 0)
            ''', (full_name, specialty, room_number, user_id))
            conn.commit()
            doctor_id = cursor.lastrowid
            log_action("ADD_DOCTOR", f"Added doctor ID:{doctor_id}, name:{full_name}, room:{room_number}")
            return doctor_id
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error adding doctor: {str(e)}")
        return None

def update_doctor(doctor_id, full_name, specialty, room_number):
    """
    Обновляет данные врача.
    
    Returns:
        bool: True при успехе
    """
    # Проверяем уникальность кабинета (исключая текущего врача)
    is_unique, msg = check_room_unique(room_number, doctor_id)
    if not is_unique:
        log_action("UPDATE_DOCTOR_ERROR", f"Room {room_number} is already occupied: {msg}")
        return False
    
    try:
        with get_connection() as conn:
            conn.execute('''
                UPDATE doctors 
                SET full_name = ?, specialty = ?, room_number = ?
                WHERE id = ?
            ''', (full_name, specialty, room_number, doctor_id))
            conn.commit()
            log_action("UPDATE_DOCTOR", f"Updated doctor ID:{doctor_id}")
            return True
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error updating doctor: {str(e)}")
        return False

def delete_doctor(doctor_id, keep_history=True):
    """
    Удаление врача с возможностью сохранения истории записей.
    
    Args:
        doctor_id (int): ID врача
        keep_history (bool): сохранять ли исторические записи
    
    Returns:
        dict: результат операции
    """
    try:
        with get_connection() as conn:
            # Проверяем, есть ли будущие записи
            cursor = conn.execute('''
                SELECT COUNT(*) as count FROM appointments 
                WHERE doctor_id = ? AND date >= date('now') AND status = 'запланирован'
            ''', (doctor_id,))
            result = cursor.fetchone()
            
            if result and result['count'] > 0:
                return {'success': False, 'future_appointments': result['count']}
            
            if keep_history:
                # Мягкое удаление - помечаем как удалённого
                conn.execute("""
                    UPDATE doctors 
                    SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (doctor_id,))
                
                # Обновляем будущие записи
                conn.execute("""
                    UPDATE appointments 
                    SET status = 'отменён', 
                        cancelled_at = CURRENT_TIMESTAMP,
                        cancelled_by = 'system: врач удалён'
                    WHERE doctor_id = ? AND date >= date('now') AND status = 'запланирован'
                """, (doctor_id,))
                
                log_action("DELETE_DOCTOR", 
                          f"Soft deleted doctor ID:{doctor_id} with history preservation")
            else:
                # Полное удаление
                conn.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
                log_action("DELETE_DOCTOR", f"Hard deleted doctor ID:{doctor_id} (history lost)")
            
            conn.commit()
            return {'success': True, 'history_preserved': keep_history}
            
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error deleting doctor: {str(e)}")
        return {'success': False, 'error': str(e)}

def get_doctor_appointments_history(doctor_id, limit=100):
    """
    Получает историю записей врача (включая удалённого).
    
    Args:
        doctor_id (int): ID врача
        limit (int): максимальное количество записей
    
    Returns:
        list: список записей
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                SELECT 
                    a.id, a.date, a.time, a.status,
                    p.full_name as patient_name,
                    p.policy_number
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                WHERE a.doctor_id = ?
                ORDER BY a.date DESC, a.time DESC
                LIMIT ?
            ''', (doctor_id, limit))
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting doctor history: {str(e)}")
        return []

# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ИНДИВИДУАЛЬНЫМ РАСПИСАНИЕМ ВРАЧА
# ============================================

def get_doctor_schedule(doctor_id):
    """
    Получает индивидуальное расписание врача.
    
    Args:
        doctor_id (int): ID врача
    
    Returns:
        dict: настройки расписания или None если не задано
    """
    try:
        with get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM doctor_schedules WHERE doctor_id = ?
            ''', (doctor_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'work_start_hour': row['work_start_hour'],
                    'work_end_hour': row['work_end_hour'],
                    'slot_duration_minutes': row['slot_duration_minutes'],
                    'lunch_start_hour': row['lunch_start_hour'],
                    'lunch_end_hour': row['lunch_end_hour'],
                    'break_between_slots': row['break_between_slots'],
                    'working_days': json.loads(row['working_days']),
                    'is_custom': row['is_custom']
                }
            return None
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting doctor schedule: {str(e)}")
        return None

def save_doctor_schedule(doctor_id, schedule):
    """
    Сохраняет индивидуальное расписание врача.
    
    Args:
        doctor_id (int): ID врача
        schedule (dict): настройки расписания
    
    Returns:
        bool: True при успехе
    """
    try:
        with get_connection() as conn:
            # Проверяем, существует ли уже запись
            existing = conn.execute(
                "SELECT id FROM doctor_schedules WHERE doctor_id = ?",
                (doctor_id,)
            ).fetchone()
            
            working_days_json = json.dumps(schedule.get('working_days', [1,2,3,4,5]))
            
            if existing:
                conn.execute('''
                    UPDATE doctor_schedules 
                    SET work_start_hour = ?,
                        work_end_hour = ?,
                        slot_duration_minutes = ?,
                        lunch_start_hour = ?,
                        lunch_end_hour = ?,
                        break_between_slots = ?,
                        working_days = ?,
                        is_custom = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE doctor_id = ?
                ''', (
                    schedule.get('work_start_hour', 9),
                    schedule.get('work_end_hour', 18),
                    schedule.get('slot_duration_minutes', 30),
                    schedule.get('lunch_start_hour'),
                    schedule.get('lunch_end_hour'),
                    schedule.get('break_between_slots', 0),
                    working_days_json,
                    doctor_id
                ))
            else:
                conn.execute('''
                    INSERT INTO doctor_schedules 
                    (doctor_id, work_start_hour, work_end_hour, slot_duration_minutes,
                     lunch_start_hour, lunch_end_hour, break_between_slots, working_days, is_custom)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    doctor_id,
                    schedule.get('work_start_hour', 9),
                    schedule.get('work_end_hour', 18),
                    schedule.get('slot_duration_minutes', 30),
                    schedule.get('lunch_start_hour'),
                    schedule.get('lunch_end_hour'),
                    schedule.get('break_between_slots', 0),
                    working_days_json
                ))
            
            conn.commit()
            log_action("SAVE_DOCTOR_SCHEDULE", f"Saved custom schedule for doctor ID:{doctor_id}")
            return True
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error saving doctor schedule: {str(e)}")
        return False

def delete_doctor_schedule(doctor_id):
    """
    Удаляет индивидуальное расписание врача (возврат к общему).
    
    Args:
        doctor_id (int): ID врача
    
    Returns:
        bool: True при успехе
    """
    try:
        with get_connection() as conn:
            conn.execute(
                "DELETE FROM doctor_schedules WHERE doctor_id = ?",
                (doctor_id,)
            )
            conn.commit()
            log_action("DELETE_DOCTOR_SCHEDULE", f"Deleted custom schedule for doctor ID:{doctor_id}")
            return True
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error deleting doctor schedule: {str(e)}")
        return False