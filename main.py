#!/usr/bin/env python3
"""
Главный файл для запуска программы регистратуры поликлиники.
Запускайте программу командой: python3 main.py
"""

import sys
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import database as db
import auth
from database.config import DATA_DIR, DB_PATH, AUDIT_LOG_PATH, BACKUP_DIR_PATH, ensure_data_dir

def cleanup_pycache():
    """
    Удаляет все директории __pycache__ во всех подпапках проекта,
    кроме папки data (чтобы не нарушать работу базы данных).
    """
    print("Очистка кэша Python (__pycache__)...")
    
    deleted_count = 0
    deleted_size = 0
    
    current_dir = Path(__file__).parent
    
    # Папки, которые нужно исключить из очистки
    excluded_dirs = {'data', '__pycache__'}
    
    for pycache_dir in current_dir.rglob("__pycache__"):
        if pycache_dir.is_dir():
            # Проверяем, не находится ли папка внутри data или другой защищённой директории
            should_skip = False
            for parent in pycache_dir.parents:
                if parent.name in excluded_dirs:
                    should_skip = True
                    break
            
            # Также проверяем, не является ли папка частью data
            if DATA_DIR in pycache_dir.parents or pycache_dir == DATA_DIR / "__pycache__":
                should_skip = True
            
            if should_skip:
                print(f"  Пропущено (защищённая папка): {pycache_dir}")
                continue
            
            try:
                dir_size = sum(f.stat().st_size for f in pycache_dir.rglob('*') if f.is_file())
                deleted_size += dir_size
                shutil.rmtree(pycache_dir)
                deleted_count += 1
                print(f"  Удалено: {pycache_dir} ({dir_size // 1024} КБ)")
            except Exception as e:
                print(f"  Ошибка при удалении {pycache_dir}: {e}")
    
    if deleted_count > 0:
        print(f"  Очистка завершена: удалено {deleted_count} пап(ок/ки), освобождено {deleted_size // 1024} КБ")
    else:
        print("  Папки __pycache__ не найдены вне защищённых директорий")
    
    print()

def cleanup_pyc_files():
    """
    Удаляет все файлы .pyc в проекте, кроме папки data.
    """
    print("Очистка файлов .pyc...")
    
    deleted_count = 0
    deleted_size = 0
    
    current_dir = Path(__file__).parent
    
    # Папки, которые нужно исключить из очистки
    excluded_dirs = {'data'}
    
    for pyc_file in current_dir.rglob("*.pyc"):
        # Проверяем, не находится ли файл внутри data
        should_skip = False
        for parent in pyc_file.parents:
            if parent.name in excluded_dirs or parent == DATA_DIR:
                should_skip = True
                break
        
        if should_skip:
            continue
        
        try:
            file_size = pyc_file.stat().st_size
            deleted_size += file_size
            pyc_file.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"  Ошибка при удалении {pyc_file}: {e}")
    
    if deleted_count > 0:
        print(f"  Очистка завершена: удалено {deleted_count} файлов, освобождено {deleted_size // 1024} КБ")
    else:
        print("  Файлы .pyc не найдены вне защищённых директорий")
    
    print()

def setup_environment():
    """
    Настройка безопасного окружения перед запуском.
    """
    print("Настройка безопасного окружения...")
    
    ensure_data_dir()
    
    cleanup_pycache()
    cleanup_pyc_files()
    
    for filepath in [DB_PATH, AUDIT_LOG_PATH]:
        if os.path.exists(filepath):
            if not os.access(filepath, os.W_OK):
                print(f"Файл {filepath} защищён от записи!")
                try:
                    os.chmod(filepath, 0o666)
                    print(f"   Права восстановлены")
                except:
                    print(f"   Не удалось изменить права")
    
    print("Окружение настроено")
    print()

def check_database():
    """
    Проверяет целостность базы данных.
    
    Returns:
        bool: True если БД в порядке
    """
    if not os.path.exists(DB_PATH):
        print("Файл базы данных будет создан")
        return True
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        print("Файл базы данных корректен")
        return True
    except sqlite3.DatabaseError as e:
        print(f"Файл {DB_PATH} повреждён: {e}")
        
        if os.path.exists(DB_PATH):
            backup_name = DATA_DIR / f"clinic.db.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(DB_PATH, backup_name)
            print(f"Создан бэкап повреждённого файла: {backup_name}")
        
        return False

def print_banner():
    """Выводит красивый баннер при запуске"""
    banner = f"""
╔════════════════════════════════════════════════════════════╗
║     РЕГИСТРАТУРА ПОЛИКЛИНИКИ v2.7.6 (БЕЗОПАСНЫЙ РЕЖИМ)     ║
╠════════════════════════════════════════════════════════════╣
║       Защита:                                              ║
║     • Параметризованные SQL-запросы                        ║
║     • Валидация всех входных данных                        ║
║     • Логирование действий (audit.log)                     ║
║     • Автоматическое резервирование                        ║
║                                                            ║
║       Дополнительно:                                       ║
║     • Все данные хранятся в папке: data/                   ║
╚════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print(f"\nДиректория данных: {DATA_DIR}")
    print("=" * 60)

def main():
    """
    Главная функция программы.
    """
    print_banner()
    
    setup_environment()
    
    if not check_database():
        print("База данных будет создана заново")
    
    print("\nИнициализация базы данных...")
    db.init_db()
    
    print("\nЗапуск окна входа в систему...")
    login_dialog = auth.LoginDialog()
    user_data = login_dialog.show()
    
    if user_data:
        print(f"Вход выполнен: {user_data['name']} ({user_data['role']})")
        print("\nЗапуск графического интерфейса...")
        print("-" * 60)
        
        root = tk.Tk()
        from gui.gui_main import MainApplication
        app = MainApplication(root, user_data)
        
        print(f"Программа запущена в безопасном режиме")
        print(f"Журнал аудита: {AUDIT_LOG_PATH}")
        print("=" * 60)
        
        root.mainloop()
    else:
        print("Вход не выполнен. Программа завершена.")
    
    print("Программа завершена")

if __name__ == "__main__":
    main()