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

def cleanup_pycache():
    """
    Удаляет все директории __pycache__ во всех подпапках проекта.
    """
    print("Очистка кэша Python (__pycache__)...")
    
    deleted_count = 0
    deleted_size = 0
    
    # Текущая директория (корень проекта)
    current_dir = Path(__file__).parent
    
    # Рекурсивно ищем все папки __pycache__
    for pycache_dir in current_dir.rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                # Подсчитываем размер директории перед удалением
                dir_size = sum(f.stat().st_size for f in pycache_dir.rglob('*') if f.is_file())
                deleted_size += dir_size
                
                # Удаляем директорию
                shutil.rmtree(pycache_dir)
                deleted_count += 1
                print(f"  Удалено: {pycache_dir} ({dir_size // 1024} КБ)")
            except Exception as e:
                print(f"  Ошибка при удалении {pycache_dir}: {e}")
    
    if deleted_count > 0:
        print(f"  Очистка завершена: удалено {deleted_count} пап(ок/ки), освобождено {deleted_size // 1024} КБ")
    else:
        print("  Папки __pycache__ не найдены")
    
    print()

def cleanup_pyc_files():
    """
    Удаляет все файлы .pyc в проекте.
    """
    print("Очистка файлов .pyc...")
    
    deleted_count = 0
    deleted_size = 0
    
    current_dir = Path(__file__).parent
    
    # Рекурсивно ищем все файлы .pyc
    for pyc_file in current_dir.rglob("*.pyc"):
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
        print("  Файлы .pyc не найдены")
    
    print()

def setup_environment():
    """
    Настройка безопасного окружения перед запуском.
    """
    print("Настройка безопасного окружения...")
    
    # Очищаем кэш Python
    cleanup_pycache()
    cleanup_pyc_files()
    
    # Создаём необходимые папки
    os.makedirs("backups", exist_ok=True)
    
    # Проверяем права доступа к файлам
    for filename in ['clinic.db', 'audit.log']:
        if os.path.exists(filename):
            if not os.access(filename, os.W_OK):
                print(f"Файл {filename} защищён от записи!")
                try:
                    os.chmod(filename, 0o666)
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
    db_file = 'clinic.db'
    
    if not os.path.exists(db_file):
        print("Файл базы данных будет создан")
        return True
    
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("SELECT 1")
        conn.close()
        print("Файл базы данных корректен")
        return True
    except sqlite3.DatabaseError as e:
        print(f"Файл {db_file} повреждён: {e}")
        
        if os.path.exists(db_file):
            backup_name = f"clinic.db.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(db_file, backup_name)
            print(f"Создан бэкап повреждённого файла: {backup_name}")
        
        return False

def print_banner():
    """Выводит красивый баннер при запуске"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║     РЕГИСТРАТУРА ПОЛИКЛИНИКИ v2.3 (БЕЗОПАСНЫЙ РЕЖИМ)       ║
╠════════════════════════════════════════════════════════════╣
║       Защита:                                              ║
║     • Параметризованные SQL-запросы                        ║
║     • Валидация всех входных данных                        ║
║     • Логирование действий (audit.log)                     ║
║     • Автоматическое резервирование                        ║
║                                                            ║
║       Дополнительно:                                       ║
║     • Автоматическая очистка __pycache__ при запуске       ║
║     • Оптимизация производительности                       ║
╚════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print("\nТЕСТОВЫЕ УЧЕТНЫЕ ЗАПИСИ:")
    print("  • Регистратор: логин: user, пароль: user123")
    print("  • Администратор: логин: admin, пароль: admin123")
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
    
    # Показываем окно входа
    print("\nЗапуск окна входа в систему...")
    login_dialog = auth.LoginDialog()
    user_data = login_dialog.show()
    
    if user_data:
        print(f"Вход выполнен: {user_data['name']} ({user_data['role']})")
        print("\nЗапуск графического интерфейса...")
        print("-" * 60)
        
        root = tk.Tk()
        
        # Импортируем основной класс приложения из нового модуля
        from gui.gui_main import MainApplication
        
        app = MainApplication(root, user_data)
        
        print(f"Программа запущена в безопасном режиме")
        print(f"Пользователь: {user_data['name']}")
        print("Журнал аудита: audit.log")
        print("=" * 60)
        
        root.mainloop()
    else:
        print("Вход не выполнен. Программа завершена.")
    
    print("Программа завершена")

if __name__ == "__main__":
    main()