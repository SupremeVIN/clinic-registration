#!/usr/bin/env python3
"""
Главный файл для запуска программы регистратуры поликлиники.
Запускайте программу командой: python3 main.py
"""

import sys
import os
import sqlite3
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import database as db  # <-- ИСПРАВЛЕНО: импортируем как db
import auth

def setup_environment():
    """
    Настройка безопасного окружения перед запуском.
    """
    print("Настройка безопасного окружения...")
    
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
║       Новые функции:                                       ║
║     • Система входа (пользователь/администратор)           ║
║     • Управление врачами для администратора                ║
║     • Удобные календари для выбора дат                     ║
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
    db.init_db()  # <-- ТЕПЕРЬ РАБОТАЕТ, так как db импортирован
    
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