"""
Функции для работы с пользователями.
"""

import sqlite3
import hashlib
import time
from database.connection import get_connection
from database.security import log_action, sanitize_input
from database.config import get_salt

# Словарь для отслеживания неудачных попыток входа
# {username: {'count': int, 'last_attempt': timestamp, 'blocked_until': timestamp}}
failed_attempts = {}
MAX_ATTEMPTS = 5
BLOCK_TIME_SECONDS = 300  # 5 минут

def hash_password(password):
    """Хеширует пароль с использованием соли из файла"""
    SALT = get_salt()
    salted = password + SALT
    return hashlib.sha256(salted.encode()).hexdigest()

def get_failed_attempts_count(username):
    """
    Возвращает количество неудачных попыток для пользователя.
    
    Args:
        username (str): имя пользователя
    
    Returns:
        int: количество неудачных попыток
    """
    if username not in failed_attempts:
        return 0
    return failed_attempts[username]['count']

def is_user_blocked(username):
    """
    Проверяет, заблокирован ли пользователь из-за слишком многих неудачных попыток.
    
    Args:
        username (str): имя пользователя
    
    Returns:
        tuple: (bool, str) - (заблокирован ли, сообщение)
    """
    if username not in failed_attempts:
        return False, ""
    
    attempt_data = failed_attempts[username]
    current_time = time.time()
    
    # Проверяем, не истекло ли время блокировки
    if current_time < attempt_data['blocked_until']:
        remaining = int(attempt_data['blocked_until'] - current_time)
        minutes = remaining // 60
        seconds = remaining % 60
        return True, f"Слишком много неудачных попыток. Попробуйте через {minutes} мин {seconds} сек"
    
    # Если время блокировки истекло, очищаем данные
    if attempt_data['blocked_until'] > 0:
        del failed_attempts[username]
    return False, ""

def record_failed_attempt(username):
    """
    Записывает неудачную попытку входа.
    
    Args:
        username (str): имя пользователя
    """
    current_time = time.time()
    
    if username not in failed_attempts:
        failed_attempts[username] = {
            'count': 1,
            'last_attempt': current_time,
            'blocked_until': 0
        }
        log_action("AUTH_FAILED", f"Failed login attempt 1/5 for user {username}")
    else:
        attempt_data = failed_attempts[username]
        attempt_data['count'] += 1
        attempt_data['last_attempt'] = current_time
        log_action("AUTH_FAILED", f"Failed login attempt {attempt_data['count']}/5 for user {username}")
        
        # Если превышен лимит, блокируем
        if attempt_data['count'] >= MAX_ATTEMPTS:
            attempt_data['blocked_until'] = current_time + BLOCK_TIME_SECONDS
            log_action("AUTH_BLOCK", f"User {username} blocked for {BLOCK_TIME_SECONDS} seconds due to too many failed attempts")

def clear_failed_attempts(username):
    """
    Очищает неудачные попытки входа после успешной аутентификации.
    
    Args:
        username (str): имя пользователя
    """
    if username in failed_attempts:
        log_action("AUTH_SUCCESS", f"User {username} successfully logged in after {failed_attempts[username]['count']} failed attempts")
        del failed_attempts[username]

def authenticate(username, password):
    """
    Проверяет логин и пароль пользователя с защитой от брутфорса.
    
    Args:
        username (str): имя пользователя
        password (str): пароль
    
    Returns:
        dict: данные пользователя или None
    """
    username = sanitize_input(username, 50)
    
    # Проверяем, не заблокирован ли пользователь
    is_blocked, block_message = is_user_blocked(username)
    if is_blocked:
        log_action("AUTH_BLOCKED", f"Blocked login attempt for user {username}")
        return None
    
    try:
        with get_connection() as conn:
            hashed_password = hash_password(password)
            cursor = conn.execute(
                "SELECT id, username, role, full_name FROM users WHERE username = ? AND password = ?",
                (username, hashed_password)
            )
            user = cursor.fetchone()
            
            if user:
                # Успешный вход - очищаем неудачные попытки
                clear_failed_attempts(username)
                return {
                    'id': user['id'],
                    'login': user['username'],
                    'role': user['role'],
                    'name': user['full_name']
                }
            else:
                # Неудачный вход - записываем попытку
                record_failed_attempt(username)
                return None
    except sqlite3.DatabaseError as e:
        log_action("AUTH_ERROR", f"Authentication error: {str(e)}")
        return None

def get_all_users():
    """Возвращает список всех пользователей"""
    try:
        with get_connection() as conn:
            cursor = conn.execute("SELECT id, username, role, full_name, created_at FROM users ORDER BY full_name")
            return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting users: {str(e)}")
        return []

def get_doctor_by_user_id(user_id):
    """Получает врача по ID пользователя"""
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM doctors WHERE user_id = ?",
                (user_id,)
            )
            return cursor.fetchone()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting doctor by user_id: {str(e)}")
        return None

def get_doctor_by_full_name(full_name):
    """Получает врача по ФИО"""
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM doctors WHERE full_name = ?",
                (full_name,)
            )
            return cursor.fetchone()
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error getting doctor by name: {str(e)}")
        return None

def add_user(username, password, role, full_name):
    """
    Добавляет нового пользователя.
    
    Args:
        username (str): логин
        password (str): пароль
        role (str): роль (admin, registrar, doctor)
        full_name (str): полное имя
    
    Returns:
        int: ID пользователя или None
    """
    username = sanitize_input(username, 50)
    full_name = sanitize_input(full_name, 100)
    
    if not username or not password or not full_name:
        return None
    
    try:
        with get_connection() as conn:
            hashed_password = hash_password(password)
            cursor = conn.execute(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                (username, hashed_password, role, full_name)
            )
            conn.commit()
            user_id = cursor.lastrowid
            log_action("ADD_USER", f"Added user ID:{user_id}, username:{username}, role:{role}")
            return user_id
    except sqlite3.IntegrityError:
        log_action("DUPLICATE_USER", f"Attempt to add duplicate username: {username}")
        return None
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error adding user: {str(e)}")
        return None

def update_user_password(user_id, new_password):
    """Обновляет пароль пользователя"""
    try:
        with get_connection() as conn:
            hashed_password = hash_password(new_password)
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hashed_password, user_id)
            )
            conn.commit()
            log_action("UPDATE_PASSWORD", f"Updated password for user ID:{user_id}")
            return True
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error updating password: {str(e)}")
        return False

def delete_user(user_id):
    """Удаляет пользователя"""
    try:
        with get_connection() as conn:
            # Проверяем, что это не последний администратор
            admin_count = conn.execute(
                "SELECT COUNT(*) as count FROM users WHERE role = 'admin'"
            ).fetchone()['count']
            
            user = conn.execute(
                "SELECT role FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            
            if user and user['role'] == 'admin' and admin_count <= 1:
                return {'success': False, 'error': 'Нельзя удалить последнего администратора'}
            
            # Проверяем, есть ли связанный врач
            doctor = conn.execute(
                "SELECT id FROM doctors WHERE user_id = ?", (user_id,)
            ).fetchone()
            
            if doctor:
                # Отвязываем врача от пользователя
                conn.execute(
                    "UPDATE doctors SET user_id = NULL WHERE user_id = ?",
                    (user_id,)
                )
            
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            log_action("DELETE_USER", f"Deleted user ID:{user_id}")
            return {'success': True}
    except sqlite3.DatabaseError as e:
        log_action("DB_ERROR", f"Error deleting user: {str(e)}")
        return {'success': False, 'error': str(e)}