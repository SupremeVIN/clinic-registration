#!/usr/bin/env python3
"""
Главный файл для запуска программы регистратуры поликлиники.
Запускайте программу командой: python3 main.py
"""

import sys
import os
import sqlite3

# Добавляем текущую папку в путь поиска модулей
# Это нужно, чтобы Python нашёл наши файлы database.py и gui.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем наши модули
from gui import MainApplication
import tkinter as tk
import database as db

def check_database():
    """
    Проверяет целостность базы данных.
    Если файл повреждён - удаляет его.
    
    Returns:
        bool: True если БД в порядке или создана заново
    """
    db_file = 'clinic.db'
    
    # Если файла нет - всё хорошо, он создастся при инициализации
    if not os.path.exists(db_file):
        print("📁 Файл базы данных будет создан")
        return True
    
    # Проверяем, можно ли открыть базу
    try:
        # Пробуем подключиться и выполнить простой запрос
        conn = sqlite3.connect(db_file)
        conn.execute("SELECT 1")
        conn.close()
        print("📁 Файл базы данных найден и корректен")
        return True
    except sqlite3.DatabaseError:
        # Если файл повреждён, удаляем его
        print(f"⚠️ Файл {db_file} повреждён. Удаляем...")
        os.remove(db_file)
        return False

def main():
    """
    Главная функция программы.
    Запускает всё приложение.
    """
    # Печатаем красивый заголовок
    print("=" * 60)
    print("🏥 РЕГИСТРАТУРА ПОЛИКЛИНИКИ")
    print("=" * 60)
    print("Версия 1.0")
    print("Разработано для курсовой работы")
    print("-" * 60)
    
    # Проверяем базу данных
    check_database()
    
    print("🔄 Инициализация базы данных...")
    
    # Создаём базу данных, если её нет, или подключаемся к существующей
    db.init_db()
    
    print("🖥️  Запуск графического интерфейса...")
    print("-" * 60)
    
    # Создаём главное окно tkinter
    root = tk.Tk()
    
    # Создаём экземпляр нашего приложения
    app = MainApplication(root)
    
    print("✅ Программа запущена. Готово к работе.")
    print("=" * 60)
    
    # Запускаем главный цикл обработки событий
    # Программа будет работать, пока пользователь не закроет окно
    root.mainloop()
    
    print("👋 Программа завершена.")

# Это условие проверяет, запущен ли файл напрямую
# (а не импортирован как модуль)
if __name__ == "__main__":
    main()