"""
Главный модуль графического интерфейса.
Содержит основной класс приложения и общие методы.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import shutil
import threading
from pathlib import Path

# Импортируем все миксины
from gui.gui_validation import ValidationMixin
from gui.gui_dialogs import DialogsMixin
from gui.gui_patients import PatientsTabMixin
from gui.gui_doctors import DoctorsTabMixin
from gui.gui_appointments import AppointmentsTabMixin
from gui.gui_stats import StatsTabMixin
from gui.gui_users import UsersTabMixin
from gui.gui_datepicker import DatePicker
from database.config import DATA_DIR

class MainApplication(ValidationMixin, DialogsMixin, PatientsTabMixin, 
                      DoctorsTabMixin, AppointmentsTabMixin, StatsTabMixin, UsersTabMixin):
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
            self.create_users_tab()
        
        self.create_new_appointment_tab()
        self.create_appointments_tab()
        self.create_stats_tab()
        
        # Информация о безопасности в строке состояния
        self.update_status(f"Добро пожаловать, {self.user['name']}! База данных защищена, все меры безопасности активны.")
    
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
        style.configure('Doctor.TButton', font=('Arial', 10), padding=5, foreground='green')
    
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
        
        # Добавляем подменю "Настройки"
        settings_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="Расписание работы", command=self.edit_schedule)
        
        # Подменю импорта/экспорта
        import_export_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Импорт/Экспорт данных", menu=import_export_menu)
        
        # Экспорт
        export_menu = tk.Menu(import_export_menu, tearoff=0)
        import_export_menu.add_cascade(label="Экспорт", menu=export_menu)
        export_menu.add_command(label="Все данные", command=self.export_all_data)
        export_menu.add_command(label="Пациенты", command=lambda: self.export_data('patients'))
        export_menu.add_command(label="Врачи", command=lambda: self.export_data('doctors'))
        export_menu.add_command(label="Записи", command=lambda: self.export_data('appointments'))
        
        # Импорт
        import_menu = tk.Menu(import_export_menu, tearoff=0)
        import_export_menu.add_cascade(label="Импорт", menu=import_menu)
        import_menu.add_command(label="Пациенты (CSV)", command=self.import_patients)
        import_menu.add_command(label="Врачи (CSV)", command=self.import_doctors)
        import_menu.add_command(label="Записи (CSV)", command=self.import_appointments)
        
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
    
    def edit_schedule(self):
        """Открывает диалог редактирования расписания"""
        from gui.gui_schedule import ScheduleDialog
        
        if self.user['role'] != 'admin':
            messagebox.showerror("Доступ запрещён", "Только администратор может изменять расписание")
            return
        
        dialog = ScheduleDialog(self.root)
        dialog.show()
        self.update_status("Настройки расписания обновлены")
    
    def export_all_data(self):
        """Экспорт всех данных"""
        import database as db
        
        filepath = filedialog.asksaveasfilename(
            title="Сохранить экспорт данных",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            base_path = filepath.rsplit('.', 1)[0]
            
            if db.export_data(base_path, 'all'):
                messagebox.showinfo("Успех", f"Данные экспортированы в:\n{base_path}_patients.csv\n{base_path}_doctors.csv\n{base_path}_appointments.csv")
                self.update_status("Все данные экспортированы")
            else:
                messagebox.showerror("Ошибка", "Не удалось экспортировать данные")
    
    def export_data(self, data_type):
        """Экспорт конкретного типа данных"""
        import database as db
        
        types_map = {
            'patients': ('Пациенты', '_patients.csv'),
            'doctors': ('Врачи', '_doctors.csv'),
            'appointments': ('Записи', '_appointments.csv')
        }
        
        title, suffix = types_map.get(data_type, ('Данные', '.csv'))
        
        filepath = filedialog.asksaveasfilename(
            title=f"Экспорт {title}",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            base_path = filepath.rsplit('.', 1)[0]
            
            if db.export_data(base_path, data_type):
                messagebox.showinfo("Успех", f"Данные экспортированы в:\n{base_path}{suffix}")
                self.update_status(f"{title} экспортированы")
            else:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать {title}")
    
    def import_patients(self):
        """Импорт пациентов из CSV с прогресс-баром"""
        import database as db
        
        filepath = filedialog.askopenfilename(
            title="Выберите CSV файл для импорта пациентов",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        # Создаем окно прогресса
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Импорт пациентов")
        progress_window.geometry("450x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Центрируем окно
        progress_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - progress_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - progress_window.winfo_height()) // 2
        progress_window.geometry(f"+{x}+{y}")
        
        ttk.Label(progress_window, text="Импорт пациентов...", font=('Arial', 12)).pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate', length=350)
        progress_bar.pack(pady=10)
        progress_bar.start()
        
        status_label = ttk.Label(progress_window, text="Анализ файла...", foreground='gray')
        status_label.pack(pady=10)
        
        def do_import():
            try:
                status_label.config(text="Импорт данных...")
                success, count, errors = db.import_patients_from_csv(filepath)
                self.root.after(0, lambda: self._import_complete_patients(progress_window, success, count, errors))
            except Exception as e:
                self.root.after(0, lambda: self._import_complete_patients(progress_window, False, 0, [str(e)]))
        
        thread = threading.Thread(target=do_import)
        thread.daemon = True
        thread.start()
    
    def _import_complete_patients(self, progress_window, success, count, errors):
        """Обработка завершения импорта пациентов"""
        progress_window.destroy()
        
        if success:
            messagebox.showinfo("Успех", f"Импортировано пациентов: {count}\nОшибок: {len(errors)}")
            self.load_patients()
            self.load_stats()
            self.update_status(f"Импортировано {count} пациентов")
            if errors:
                error_file = "import_errors_patients.log"
                with open(error_file, "w", encoding='utf-8') as f:
                    f.write("\n".join(errors))
                messagebox.showwarning("Ошибки импорта", 
                    f"Были ошибки при импорте.\nПодробности сохранены в файле:\n{error_file}")
        else:
            messagebox.showerror("Ошибка", f"Не удалось импортировать файл:\n{errors[0] if errors else 'Неизвестная ошибка'}")
    
    def import_doctors(self):
        """Импорт врачей из CSV"""
        import database as db
        
        filepath = filedialog.askopenfilename(
            title="Выберите CSV файл для импорта врачей",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        if self.user['role'] != 'admin':
            messagebox.showerror("Доступ запрещён", "Только администратор может импортировать врачей")
            return
        
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Импорт врачей")
        progress_window.geometry("450x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        progress_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - progress_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - progress_window.winfo_height()) // 2
        progress_window.geometry(f"+{x}+{y}")
        
        ttk.Label(progress_window, text="Импорт врачей...", font=('Arial', 12)).pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate', length=350)
        progress_bar.pack(pady=10)
        progress_bar.start()
        
        status_label = ttk.Label(progress_window, text="Анализ файла...", foreground='gray')
        status_label.pack(pady=10)
        
        def do_import():
            try:
                status_label.config(text="Импорт данных...")
                success, count, errors = db.import_doctors_from_csv(filepath)
                self.root.after(0, lambda: self._import_complete_doctors(progress_window, success, count, errors))
            except Exception as e:
                self.root.after(0, lambda: self._import_complete_doctors(progress_window, False, 0, [str(e)]))
        
        thread = threading.Thread(target=do_import)
        thread.daemon = True
        thread.start()
    
    def _import_complete_doctors(self, progress_window, success, count, errors):
        """Обработка завершения импорта врачей"""
        progress_window.destroy()
        
        if success:
            messagebox.showinfo("Успех", f"Импортировано врачей: {count}\nОшибок: {len(errors)}")
            self.load_admin_doctors()
            self.load_doctors()
            self.load_doctors_to_combobox()
            self.load_stats()
            self.update_status(f"Импортировано {count} врачей")
            if errors:
                error_file = "import_errors_doctors.log"
                with open(error_file, "w", encoding='utf-8') as f:
                    f.write("\n".join(errors))
                messagebox.showwarning("Ошибки импорта", 
                    f"Были ошибки при импорте.\nПодробности сохранены в файле:\n{error_file}")
        else:
            messagebox.showerror("Ошибка", f"Не удалось импортировать файл:\n{errors[0] if errors else 'Неизвестная ошибка'}")
    
    def import_appointments(self):
        """Импорт записей из CSV"""
        import database as db
        
        filepath = filedialog.askopenfilename(
            title="Выберите CSV файл для импорта записей",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Импорт записей")
        progress_window.geometry("450x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        progress_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - progress_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - progress_window.winfo_height()) // 2
        progress_window.geometry(f"+{x}+{y}")
        
        ttk.Label(progress_window, text="Импорт записей...", font=('Arial', 12)).pack(pady=20)
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate', length=350)
        progress_bar.pack(pady=10)
        progress_bar.start()
        
        status_label = ttk.Label(progress_window, text="Анализ файла...", foreground='gray')
        status_label.pack(pady=10)
        
        def do_import():
            try:
                status_label.config(text="Импорт данных...")
                success, count, errors = db.import_appointments_from_csv(filepath)
                self.root.after(0, lambda: self._import_complete_appointments(progress_window, success, count, errors))
            except Exception as e:
                self.root.after(0, lambda: self._import_complete_appointments(progress_window, False, 0, [str(e)]))
        
        thread = threading.Thread(target=do_import)
        thread.daemon = True
        thread.start()
    
    def _import_complete_appointments(self, progress_window, success, count, errors):
        """Обработка завершения импорта записей"""
        progress_window.destroy()
        
        if success:
            messagebox.showinfo("Успех", f"Импортировано записей: {count}\nОшибок: {len(errors)}")
            self.load_appointments()
            self.load_stats()
            self.update_status(f"Импортировано {count} записей")
            if errors:
                error_file = "import_errors_appointments.log"
                with open(error_file, "w", encoding='utf-8') as f:
                    f.write("\n".join(errors))
                messagebox.showwarning("Ошибки импорта", 
                    f"Были ошибки при импорте.\nПодробности сохранены в файле:\n{error_file}")
        else:
            messagebox.showerror("Ошибка", f"Не удалось импортировать файл:\n{errors[0] if errors else 'Неизвестная ошибка'}")
    
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
                        should_skip = False
                        for parent in pycache_dir.parents:
                            if parent.name in excluded_dirs or parent == DATA_DIR:
                                should_skip = True
                                break
                        
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
                
                self.root.quit()
                self.root.destroy()
                
                import subprocess
                import sys
                subprocess.Popen([sys.executable, "main.py"])
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить кэш: {e}")
    
    def logout(self):
        """Выход из учетной записи"""
        if messagebox.askyesno("Подтверждение", "Выйти из системы?"):
            self.root.destroy()
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
        
        calendar_window = tk.Toplevel(parent)
        calendar_window.title("Выберите дату")
        calendar_window.geometry("300x350")
        calendar_window.transient(parent)
        calendar_window.grab_set()
        
        calendar_window.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - calendar_window.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - calendar_window.winfo_height()) // 2
        calendar_window.geometry(f"+{x}+{y}")
        
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
    print("=" * 60)
    print("ЗАПУСК РЕГИСТРАТУРЫ ПОЛИКЛИНИКИ (РЕЖИМ ТЕСТИРОВАНИЯ)")
    print("=" * 60)
    
    test_user = {
        'login': 'admin',
        'role': 'admin',
        'name': 'Администратор'
    }
    
    root = tk.Tk()
    app = MainApplication(root, test_user)
    root.mainloop()