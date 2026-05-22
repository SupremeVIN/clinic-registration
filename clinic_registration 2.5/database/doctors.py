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