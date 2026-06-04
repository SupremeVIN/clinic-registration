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