"""
Функции безопасности: валидация, хеширование, логирование, очистка данных.
"""

import re
import hashlib
import logging
from database.config import AUDIT_LOG, SALT

# Настройка логирования
logging.basicConfig(
    filename=AUDIT_LOG,
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_action(action, details, user="SYSTEM"):
    """
    Логирование важных действий для аудита.
    
    Args:
        action (str): действие (ADD, DELETE, UPDATE, etc.)
        details (str): детали действия
        user (str): пользователь (по умолчанию SYSTEM)
    """
    logging.info(f"{user} | {action} | {details}")

def hash_sensitive_data(data):
    """
    Хеширование чувствительных данных (для защиты).
    
    Args:
        data (str): данные для хеширования
    
    Returns:
        str: хеш данных (первые 16 символов)
    """
    if not data:
        return None
    salted = data + SALT
    return hashlib.sha256(salted.encode()).hexdigest()[:16]

def sanitize_input(text, max_length=1000):
    """
    Очистка входных данных от потенциально опасных символов.
    
    Args:
        text (str): входной текст
        max_length (int): максимальная длина
    
    Returns:
        str: очищенный текст
    """
    if not text:
        return ""
    
    text = str(text)[:max_length]
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    return text.strip()

# ============================================
# ФУНКЦИИ ВАЛИДАЦИИ
# ============================================

def validate_policy_number(policy):
    """
    Валидация номера полиса.
    
    Args:
        policy (str): номер полиса
    
    Returns:
        tuple: (bool, str) - (валиден ли, сообщение об ошибке)
    """
    if not policy or not policy.strip():
        return False, "Номер полиса обязателен"
    
    policy = policy.strip()
    
    if len(policy) != 16:
        return False, "Номер полиса должен содержать ровно 16 цифр"
    
    if not re.match(r'^\d+$', policy):
        return False, "Номер полиса может содержать только цифры"
    
    return True, "OK"

def validate_phone(phone):
    """
    Валидация номера телефона.
    
    Args:
        phone (str): номер телефона
    
    Returns:
        tuple: (bool, str) - (валиден ли, сообщение об ошибке)
    """
    if not phone:
        return True, "OK"
    
    phone = phone.strip()
    
    if len(phone) > 20:
        return False, "Номер телефона слишком длинный"
    
    if not re.match(r'^[\d\+\-\s\(\)]+$', phone):
        return False, "Телефон содержит недопустимые символы"
    
    return True, "OK"

def validate_name(name):
    """
    Валидация ФИО.
    
    Args:
        name (str): ФИО
    
    Returns:
        tuple: (bool, str) - (валиден ли, сообщение об ошибке)
    """
    if not name or not name.strip():
        return False, "ФИО обязательно для заполнения"
    
    name = name.strip()
    
    if len(name) > 200:
        return False, "ФИО слишком длинное"
    
    if len(name) < 2:
        return False, "ФИО слишком короткое"
    
    if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-\.]+$', name):
        return False, "ФИО может содержать только буквы, пробелы, дефисы и точки"
    
    return True, "OK"

def validate_date(date_str):
    """
    Валидация даты.
    
    Args:
        date_str (str): дата в формате ГГГГ-ММ-ДД
    
    Returns:
        tuple: (bool, str) - (валиден ли, сообщение об ошибке)
    """
    if not date_str:
        return True, "OK"
    
    date_str = date_str.strip()
    
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False, "Дата должна быть в формате ГГГГ-ММ-ДД"
    
    try:
        from datetime import datetime
        datetime.strptime(date_str, '%Y-%m-%d')
        return True, "OK"
    except ValueError:
        return False, "Некорректная дата"