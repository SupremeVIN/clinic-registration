"""
Конфигурация и константы базы данных.
"""

import os
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).parent.parent

# Директория для данных (все создаваемые файлы будут здесь)
DATA_DIR = BASE_DIR / "data"

# Имя файла базы данных
DB_NAME = 'clinic.db'

# Файл для аудита
AUDIT_LOG = 'audit.log'

# Соль для хеширования
SALT = "clinic_salt_2026_change_this"

# Директория для бэкапов
BACKUP_DIR = "backups"

# Пути к файлам (все внутри DATA_DIR)
DB_PATH = DATA_DIR / DB_NAME
AUDIT_LOG_PATH = DATA_DIR / AUDIT_LOG
BACKUP_DIR_PATH = DATA_DIR / BACKUP_DIR

def ensure_data_dir():
    """Создаёт директорию для данных, если её нет"""
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR_PATH.mkdir(exist_ok=True)