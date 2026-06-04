"""
Функции для работы с врачами.
"""

import sqlite3
from database.connection import get_connection
from database.security import log_action

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
                    "SELECT id, full_name FROM doctors WHERE room_number = ? AND id != ?",
                    (room_number, exclude_doctor_id)
                )
            else:
                cursor = conn.execute(
                    "SELECT id, full_name FROM doctors WHERE room_number = ?",
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
                INSERT INTO doctors (full_name, specialty, room_number, user_id)
                VALUES (?, ?, ?, ?)
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

def delete_doctor(doctor_id):
    """
    Удаляет врача.
    
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
            
            conn.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
            conn.commit()
            log_action("DELETE_DOCTOR", f"Deleted doctor ID:{doctor_id}")
            return {'success': True}
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error deleting doctor: {str(e)}")
        return {'success': False, 'error': str(e)}