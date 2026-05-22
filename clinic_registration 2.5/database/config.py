"""
Конфигурация и константы базы данных.
"""

import os
from pathlib import Path

# Имя файла базы данных
DB_NAME = 'clinic.db'

# Файл для аудита
AUDIT_LOG = 'audit.log'

# Соль для хеширования
SALT = "clinic_salt_2026_change_this"

# Директория для бэкапов
BACKUP_DIR = "backups"

# Пути к файлам
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / DB_NAME
AUDIT_LOG_PATH = BASE_DIR / AUDIT_LOG
BACKUP_DIR_PATH = BASE_DIR / BACKUP_DIR