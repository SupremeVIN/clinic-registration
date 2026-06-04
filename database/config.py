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

# Файл для хранения соли
SALT_FILE = "salt.key"

# Директория для бэкапов
BACKUP_DIR = "backups"

# Пути к файлам (все внутри DATA_DIR)
DB_PATH = DATA_DIR / DB_NAME
AUDIT_LOG_PATH = DATA_DIR / AUDIT_LOG
BACKUP_DIR_PATH = DATA_DIR / BACKUP_DIR
SALT_PATH = DATA_DIR / SALT_FILE

def ensure_data_dir():
    """Создаёт директорию для данных, если её нет"""
    DATA_DIR.mkdir(exist_ok=True)
    BACKUP_DIR_PATH.mkdir(exist_ok=True)

def get_salt():
    """
    Получает или создаёт соль для хеширования.
    Соль хранится в файле data/salt.key.
    """
    ensure_data_dir()
    
    if SALT_PATH.exists():
        with open(SALT_PATH, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        import secrets
        salt = secrets.token_hex(32)  # 64 символа
        with open(SALT_PATH, 'w', encoding='utf-8') as f:
            f.write(salt)
        # Устанавливаем права только для чтения владельцем
        os.chmod(SALT_PATH, 0o400)
        return salt