"""
Главный модуль графического интерфейса.
Содержит основной класс приложения и общие методы.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import shutil
from pathlib import Path

# Импортируем все миксины
from gui.gui_validation import ValidationMixin
from gui.gui_dialogs import DialogsMixin
from gui.gui_patients import PatientsTabMixin
from gui.gui_doctors import DoctorsTabMixin
from gui.gui_appointments import AppointmentsTabMixin
from gui.gui_stats import StatsTabMixin
from gui.gui_datepicker import DatePicker
from database.config import DATA_DIR

class MainApplication(ValidationMixin, DialogsMixin, PatientsTabMixin, 
                      DoctorsTabMixin, AppointmentsTabMixin, StatsTabMixin):
    """
    Главный класс приложения.
    Содержит все методы для создания интерфейса и обработки событий.
    """
    
    def __init__(self, root, user_data):
        """
        Конструктор класса. Инициализирует главное окно и все компоненты.
        
        Args:
            root: главное окно tkinter
            user_data: данные пользователя (логин, роль, имя)
        """
        self.root = root
        self.user = user_data
        self.root.title(f"Регистратура поликлиники - {self.user['name']} ({self.user['role']})")
        self.root.geometry("1200x700")
        
        self.center_window()
        self.setup_styles()
        self.create_menu()
        self.create_status_bar()
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.create_patients_tab()
        self.create_doctors_tab()
        
        # Вкладка для управления врачами (только для админа)
        if self.user['role'] == 'admin':
            self.create_admin_doctors_tab()
        
        self.create_new_appointment_tab()
        self.create_appointments_tab()
        self.create_stats_tab()
        
        self.update_status(f"Программа готова к работе. Пользователь: {self.user['name']}")
        
        self.after_id = self.root.after(1000, self.show_startup_info)
    
    def center_window(self):
        """Центрирует окно на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_styles(self):
        """Настройка стилей для виджетов"""
        style = ttk.Style()
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Action.TButton', font=('Arial', 10), padding=5)
        style.configure('Warning.TButton', font=('Arial', 10), padding=5, foreground='red')
        style.configure('Admin.TButton', font=('Arial', 10), padding=5, foreground='blue')
    
    def create_menu(self):
        """Создаёт главное меню программы"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Обновить всё", command=self.refresh_all)
        file_menu.add_command(label="Очистить кэш БД", command=self.cleanup_database_cache)
        file_menu.add_command(label="Очистить кэш Python", command=self.cleanup_python_cache)
        file_menu.add_separator()
        file_menu.add_command(label="Создать резервную копию", command=self.create_backup)
        file_menu.add_separator()
        file_menu.add_command(label="Сменить пользователя", command=self.logout)
        file_menu.add_command(label="Выход", command=self.quit_application)
        
        security_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Безопасность", menu=security_menu)
        security_menu.add_command(label="Показать журнал аудита", command=self.show_audit_log)
        security_menu.add_command(label="Проверить целостность БД", command=self.check_integrity)
        security_menu.add_command(label="Статистика безопасности", command=self.show_security_stats)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
        help_menu.add_command(label="Руководство по безопасности", command=self.show_security_guide)
    
    def cleanup_python_cache(self):
        """
        Очищает кэш Python (__pycache__ и .pyc файлы) в GUI,
        защищая папку data от удаления.
        """
        if messagebox.askyesno("Подтверждение", 
                              "Очистить кэш Python?\n\n"
                              "Это удалит все папки __pycache__ и файлы .pyc\n"
                              "в папках проекта (кроме папки data).\n"
                              "Операция безопасна и может ускорить работу программы.\n\n"
                              "ВНИМАНИЕ: Программа будет перезапущена!"):
            
            try:
                current_dir = Path(__file__).parent.parent
                deleted_dirs = 0
                deleted_files = 0
                
                # Папки, которые нужно исключить из очистки
                excluded_dirs = {'data'}
                
                # Удаляем __pycache__ папки (кроме тех, что внутри data)
                for pycache_dir in current_dir.rglob("__pycache__"):
                    if pycache_dir.is_dir():
                        # Проверяем, не находится ли папка внутри data
                        should_skip = False
                        for parent in pycache_dir.parents:
                            if parent.name in excluded_dirs or parent == DATA_DIR:
                                should_skip = True
                                break
                        
                        # Также проверяем прямой путь
                        if DATA_DIR in pycache_dir.parents:
                            should_skip = True
                        
                        if not should_skip:
                            shutil.rmtree(pycache_dir)
                            deleted_dirs += 1
                
                # Удаляем .pyc файлы (кроме тех, что внутри data)
                for pyc_file in current_dir.rglob("*.pyc"):
                    should_skip = False
                    for parent in pyc_file.parents:
                        if parent.name in excluded_dirs or parent == DATA_DIR:
                            should_skip = True
                            break
                    
                    if not should_skip:
                        pyc_file.unlink()
                        deleted_files += 1
                
                messagebox.showinfo("Успех", 
                                   f"Очистка завершена!\n\n"
                                   f"Удалено папок __pycache__: {deleted_dirs}\n"
                                   f"Удалено файлов .pyc: {deleted_files}\n\n"
                                   "Папка data не была затронута.\n"
                                   "Программа будет перезапущена.")
                
                # Перезапускаем программу
                self.root.quit()
                self.root.destroy()
                
                # Запускаем заново
                import subprocess
                import sys
                subprocess.Popen([sys.executable, "main.py"])
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить кэш: {e}")
    
    def logout(self):
        """Выход из учетной записи"""
        if messagebox.askyesno("Подтверждение", "Выйти из системы?"):
            self.root.destroy()
            # Запускаем окно входа заново
            import auth
            login_dialog = auth.LoginDialog()
            user_data = login_dialog.show()
            
            if user_data:
                new_root = tk.Tk()
                new_app = MainApplication(new_root, user_data)
                new_root.mainloop()
    
    def quit_application(self):
        """Безопасное завершение приложения"""
        if messagebox.askyesno("Подтверждение", "Завершить работу программы?"):
            self.root.after(100, self.create_backup_silent)
            self.root.after(500, self.root.quit)
    
    def create_status_bar(self):
        """Создаёт строку состояния внизу окна"""
        self.status_bar = ttk.Label(
            self.root, 
            text=f" Пользователь: {self.user['name']} | Режим: безопасный", 
            relief='sunken', 
            anchor='w'
        )
        self.status_bar.pack(side='bottom', fill='x')
    
    def update_status(self, message):
        """
        Обновляет текст в строке состояния.
        
        Args:
            message (str): новое сообщение
        """
        if hasattr(self, 'status_bar'):
            current_time = datetime.now().strftime('%H:%M:%S')
            self.status_bar.config(
                text=f" [{current_time}] {message} | Пользователь: {self.user['name']} | Режим: безопасный"
            )
            self.root.update()
    
    def refresh_all(self):
        """Обновляет все данные во всех вкладках"""
        self.load_patients()
        self.load_doctors()
        self.load_appointments()
        self.load_stats()
        self.update_status("Все данные обновлены")
    
    def show_date_picker(self, parent, entry, min_date=None, max_date=None):
        """
        Показывает календарь для выбора даты.
        
        Args:
            parent: родительское окно
            entry: поле ввода, куда вставить дату
            min_date: минимальная дата
            max_date: максимальная дата
        """
        def on_date_selected(date_str):
            entry.delete(0, tk.END)
            entry.insert(0, date_str)
        
        # Создаем окно для календаря
        calendar_window = tk.Toplevel(parent)
        calendar_window.title("Выберите дату")
        calendar_window.geometry("300x300")
        calendar_window.transient(parent)
        calendar_window.grab_set()
        
        # Центрируем окно
        calendar_window.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - calendar_window.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - calendar_window.winfo_height()) // 2
        calendar_window.geometry(f"+{x}+{y}")
        
        # Создаем календарь
        date_picker = DatePicker(
            calendar_window,
            initial_date=entry.get() or datetime.now().strftime('%Y-%m-%d'),
            callback=on_date_selected,
            min_date=min_date,
            max_date=max_date
        )
        date_picker.frame.pack(fill='both', expand=True, padx=10, pady=10)


# ===========================================
# ТОЧКА ВХОДА (для тестирования)
# ===========================================

if __name__ == "__main__":
    # Этот код выполняется только при прямом запуске gui_main.py
    print("=" * 60)
    print("ЗАПУСК РЕГИСТРАТУРЫ ПОЛИКЛИНИКИ (РЕЖИМ ТЕСТИРОВАНИЯ)")
    print("=" * 60)
    
    # Для тестирования создаем тестового пользователя
    test_user = {
        'login': 'admin',
        'role': 'admin',
        'name': 'Администратор'
    }
    
    root = tk.Tk()
    app = MainApplication(root, test_user)
    root.mainloop()