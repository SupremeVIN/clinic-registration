#!/usr/bin/env python3
"""
Главный файл для запуска программы регистратуры поликлиники.
Запускайте программу командой: python3 main.py
"""

import sys
import os
import sqlite3
from datetime import datetime

# Добавляем текущую папку в путь поиска модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем наши модули
from gui import MainApplication
import tkinter as tk
import database as db

def setup_environment():
    """
    Настройка безопасного окружения перед запуском.
    """
    print("🔧 Настройка безопасного окружения...")
    
    # Создаём необходимые папки
    os.makedirs("backups", exist_ok=True)
    
    # Проверяем права доступа к файлам
    for filename in ['clinic.db', 'audit.log']:
        if os.path.exists(filename):
            if not os.access(filename, os.W_OK):
                print(f"⚠️  Файл {filename} защищён от записи!")
                try:
                    os.chmod(filename, 0o666)
                    print(f"   Права восстановлены")
                except:
                    print(f"   ❌ Не удалось изменить права")
    
    print("✅ Окружение настроено")

def check_database():
    """
    Проверяет целостность базы данных.
    
    Returns:
        bool: True если БД в порядке
    """
    db_file = 'clinic.db'
    
    if not os.path.exists(db_file):
        print("📁 Файл базы данных будет создан")
        return True
    
    try:
        conn = sqlite3.connect(db_file)
        conn.execute("SELECT 1")
        conn.close()
        print("✅ Файл базы данных корректен")
        return True
    except sqlite3.DatabaseError as e:
        print(f"❌ Файл {db_file} повреждён: {e}")
        
        if os.path.exists(db_file):
            backup_name = f"clinic.db.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(db_file, backup_name)
            print(f"💾 Создан бэкап повреждённого файла: {backup_name}")
        
        return False

def print_banner():
    """Выводит красивый баннер при запуске"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║     РЕГИСТРАТУРА ПОЛИКЛИНИКИ v2.0 (БЕЗОПАСНЫЙ РЕЖИМ)    ║
╠══════════════════════════════════════════════════════════╣
║  🛡️  Защита:                                              ║
║     • Параметризованные SQL-запросы                      ║
║     • Валидация всех входных данных                       ║
║     • Логирование действий (audit.log)                    ║
║     • Автоматическое резервирование                        ║
║     • Проверка целостности БД                              ║
╚══════════════════════════════════════════════════════════╝
"""
    print(banner)

def main():
    """
    Главная функция программы.
    """
    print_banner()
    
    setup_environment()
    
    if not check_database():
        print("⚠️  База данных будет создана заново")
    
    print("\n🔄 Инициализация базы данных...")
    db.init_db()
    
    print("\n🚀 Запуск графического интерфейса...")
    print("-" * 60)
    
    root = tk.Tk()
    app = MainApplication(root)
    
    print("✅ Программа запущена в безопасном режиме")
    print("📝 Журнал аудита: audit.log")
    print("=" * 60)
    
    root.mainloop()
    
    print("Программа завершена")

if __name__ == "__main__":
    main()