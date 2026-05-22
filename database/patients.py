"""
Функции для работы с пациентами.
"""

import sqlite3
from database.connection import get_connection
from database.security import (
    log_action, hash_sensitive_data, sanitize_input,
    validate_name, validate_policy_number, validate_phone, validate_date
)

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
    if not valid and birth_date:
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
    if not valid and birth_date:
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