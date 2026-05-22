"""
Модуль для аутентификации пользователей.
Содержит простую систему входа по логину и паролю.
"""

import hashlib
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Простая база пользователей (в реальном проекте хранилась бы в БД с хешированием)
# Пароли хранятся в открытом виде для простоты (в учебном проекте)
USERS = {
    'user': {
        'password': 'user123',
        'role': 'user',
        'name': 'Регистратор'
    },
    'admin': {
        'password': 'admin123',
        'role': 'admin',
        'name': 'Администратор'
    }
}

def authenticate(login, password):
    """
    Проверяет логин и пароль.
    
    Args:
        login (str): логин
        password (str): пароль
    
    Returns:
        dict: данные пользователя или None
    """
    login = login.strip().lower()
    
    if login in USERS and USERS[login]['password'] == password:
        return {
            'login': login,
            'role': USERS[login]['role'],
            'name': USERS[login]['name']
        }
    
    return None

class LoginDialog:
    """
    Диалог входа в систему.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Вход в систему - Регистратура поликлиники")
        self.root.geometry("400x350")
        self.root.resizable(False, False)
        
        # Центрируем окно
        self.center_window()
        
        # Переменные
        self.login_var = tk.StringVar(value='user')
        self.password_var = tk.StringVar()
        self.user_data = None
        
        self.create_widgets()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Привязка клавиши Enter
        self.root.bind('<Return>', lambda event: self.login())
    
    def center_window(self):
        """Центрирует окно на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Создает виджеты окна входа"""
        # Заголовок
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=20, pady=(30, 10))
        
        ttk.Label(
            title_frame,
            text="Регистратура поликлиники",
            font=('Arial', 16, 'bold')
        ).pack()
        
        ttk.Label(
            title_frame,
            text="Вход в систему",
            font=('Arial', 12)
        ).pack(pady=(5, 0))
        
        # Форма входа
        form_frame = ttk.Frame(self.root)
        form_frame.pack(padx=40, pady=20, fill='both')
        
        # Логин
        ttk.Label(form_frame, text="Логин:", font=('Arial', 10)).pack(anchor='w', pady=(10, 2))
        
        login_combo = ttk.Combobox(
            form_frame,
            textvariable=self.login_var,
            values=['user', 'admin'],
            state='readonly',
            font=('Arial', 10),
            width=30
        )
        login_combo.pack(fill='x', pady=(0, 10))
        
        # Пароль
        ttk.Label(form_frame, text="Пароль:", font=('Arial', 10)).pack(anchor='w', pady=(10, 2))
        
        password_entry = ttk.Entry(
            form_frame,
            textvariable=self.password_var,
            show='•',
            font=('Arial', 10),
            width=30
        )
        password_entry.pack(fill='x', pady=(0, 10))
        password_entry.focus()
        
        # # Подсказка
        # hint_frame = ttk.LabelFrame(form_frame, text="Тестовые учетные записи", padding=10)
        # hint_frame.pack(fill='x', pady=10)
        
        # ttk.Label(
        #     hint_frame,
        #     text="Регистратор:",
        #     font=('Arial', 9, 'bold')
        # ).pack(anchor='w')
        
        # ttk.Label(
        #     hint_frame,
        #     text="   логин: user   пароль: user123",
        #     font=('Arial', 9)
        # ).pack(anchor='w')
        
        # ttk.Label(
        #     hint_frame,
        #     text="Администратор:",
        #     font=('Arial', 9, 'bold')
        # ).pack(anchor='w', pady=(5, 0))
        
        # ttk.Label(
        #     hint_frame,
        #     text="   логин: admin   пароль: admin123",
        #     font=('Arial', 9)
        # ).pack(anchor='w')
        
        # Кнопки
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame,
            text="Войти",
            command=self.login,
            width=15
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Выход",
            command=self.on_closing,
            width=15
        ).pack(side='left', padx=5)
        
        # Статус
        self.status_label = ttk.Label(
            self.root,
            text="",
            foreground='red',
            font=('Arial', 9)
        )
        self.status_label.pack(pady=(0, 20))
    
    def login(self):
        """Обработка входа"""
        login = self.login_var.get()
        password = self.password_var.get()
        
        if not login or not password:
            self.status_label.config(text="Введите логин и пароль")
            return
        
        user = authenticate(login, password)
        
        if user:
            self.user_data = user
            self.root.destroy()
        else:
            self.status_label.config(text="Неверный логин или пароль")
            self.password_var.set('')
    
    def on_closing(self):
        """Закрытие окна"""
        self.user_data = None
        self.root.destroy()
    
    def show(self):
        """Показывает диалог и возвращает данные пользователя"""
        self.root.mainloop()
        return self.user_data