"""
Модуль для аутентификации пользователей.
Содержит систему входа по логину и паролю с проверкой в БД.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from database.users import authenticate, is_user_blocked, get_failed_attempts_count

class LoginDialog:
    """
    Диалог входа в систему.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Вход в систему - Регистратура поликлиники")
        self.root.geometry("450x400")  # Увеличено с 400x320 до 450x400
        self.root.resizable(False, False)
        
        # Центрируем окно
        self.center_window()
        
        # Переменные
        self.login_var = tk.StringVar()
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
        # Основной фрейм с отступами
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Заголовок
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=(0, 20))
        
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
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill='both', expand=True)
        
        # Логин
        ttk.Label(form_frame, text="Логин:", font=('Arial', 10)).pack(anchor='w', pady=(0, 2))
        
        self.login_entry = ttk.Entry(form_frame, font=('Arial', 10), width=35)
        self.login_entry.pack(fill='x', pady=(0, 15))
        self.login_entry.focus()
        
        # Пароль
        ttk.Label(form_frame, text="Пароль:", font=('Arial', 10)).pack(anchor='w', pady=(0, 2))
        
        self.password_entry = ttk.Entry(
            form_frame,
            textvariable=self.password_var,
            show='•',
            font=('Arial', 10),
            width=35
        )
        self.password_entry.pack(fill='x', pady=(0, 20))
        
        # Кнопки
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(pady=10)
        
        # Стиль для кнопок
        style = ttk.Style()
        style.configure('Login.TButton', font=('Arial', 10), padding=8)
        
        login_btn = ttk.Button(
            button_frame,
            text="Войти",
            command=self.login,
            width=15,
            style='Login.TButton'
        )
        login_btn.pack(side='left', padx=5)
        
        exit_btn = ttk.Button(
            button_frame,
            text="Выход",
            command=self.on_closing,
            width=15,
            style='Login.TButton'
        )
        exit_btn.pack(side='left', padx=5)
        
        # Статус (для сообщений об ошибках)
        self.status_label = ttk.Label(
            main_frame,
            text="",
            foreground='red',
            font=('Arial', 9),
            wraplength=380,  # Перенос текста
            justify='center'
        )
        self.status_label.pack(pady=(10, 5))
    
    def login(self):
        """Обработка входа с проверкой блокировки"""
        login = self.login_entry.get().strip()
        password = self.password_var.get()
        
        if not login or not password:
            self.status_label.config(text="Введите логин и пароль")
            return
        
        # Сначала проверяем, не заблокирован ли пользователь
        is_blocked, block_message = is_user_blocked(login)
        
        if is_blocked:
            self.status_label.config(text=block_message, foreground='red')
            self.login_entry.focus()
            return
        
        user = authenticate(login, password)
        
        if user:
            self.user_data = user
            self.root.destroy()
        else:
            # Показываем количество оставшихся попыток
            attempts = get_failed_attempts_count(login)
            remaining = 5 - attempts
            if remaining > 0:
                self.status_label.config(
                    text=f"Неверный логин или пароль. Осталось попыток: {remaining}",
                    foreground='red'
                )
            else:
                # Если попытки закончились, показываем сообщение о блокировке
                self.status_label.config(
                    text=f"Слишком много неудачных попыток. Попробуйте через 5 минут.",
                    foreground='red'
                )
            self.password_var.set('')
            self.password_entry.delete(0, tk.END)
            self.login_entry.focus()
    
    def on_closing(self):
        """Закрытие окна"""
        self.user_data = None
        self.root.destroy()
    
    def show(self):
        """Показывает диалог и возвращает данные пользователя"""
        self.root.mainloop()
        return self.user_data