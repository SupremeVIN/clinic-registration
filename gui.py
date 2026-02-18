"""
Модуль с графическим интерфейсом программы.
Использует библиотеку tkinter.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import database as db
import os

class MainApplication:
    """
    Главный класс приложения.
    Содержит все методы для создания интерфейса и обработки событий.
    """
    
    def __init__(self, root):
        """
        Конструктор класса. Инициализирует главное окно и все компоненты.
        
        Args:
            root: главное окно tkinter
        """
        self.root = root
        self.root.title("Регистратура поликлиники")
        self.root.geometry("1200x700")
        
        self.center_window()
        self.setup_styles()
        self.create_menu()
        self.create_status_bar()
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.create_patients_tab()
        self.create_doctors_tab()
        self.create_new_appointment_tab()
        self.create_appointments_tab()
        self.create_stats_tab()
        
        self.update_status("Программа готова к работе. Режим: безопасный")
        
        self.after_id = self.root.after(1000, self.show_startup_info)
    
    def show_startup_info(self):
        """Показывает информацию о безопасности при запуске"""
        stats = db.get_database_stats()
        messagebox.showinfo(
            "Информация о безопасности",
            f"База данных защищена\n"
            f"Статистика:\n"
            f" - Пациентов: {stats['patients']}\n"
            f" - Врачей: {stats['doctors']}\n"
            f" - Записей: {stats['appointments']}\n"
            f" - Размер БД: {stats['size_kb']} КБ\n\n"
            f"Меры безопасности активны:\n"
            f" - Защита от SQL-инъекций\n"
            f" - Валидация всех данных\n"
            f" - Логирование действий\n"
            f" - Автоматическое резервирование"
        )
    
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
    
    def create_menu(self):
        """Создаёт главное меню программы"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Обновить всё", command=self.refresh_all)
        file_menu.add_command(label="Очистить кэш БД", command=self.cleanup_database_cache)
        file_menu.add_command(label="Создать резервную копию", command=self.create_backup)
        file_menu.add_separator()
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
    
    def quit_application(self):
        """Безопасное завершение приложения"""
        if messagebox.askyesno("Подтверждение", "Завершить работу программы?"):
            self.root.after(100, self.create_backup_silent)
            self.root.after(500, self.root.quit)
    
    def create_backup_silent(self):
        """Создаёт резервную копию без показа сообщения"""
        backup_file = db.backup_database()
        if backup_file:
            print(f"Автоматический бэкап создан: {backup_file}")
    
    def create_backup(self):
        """Создаёт резервную копию"""
        backup_file = db.backup_database()
        if backup_file:
            messagebox.showinfo("Успех", f"Резервная копия создана:\n{backup_file}")
            self.update_status("Резервная копия создана")
        else:
            messagebox.showerror("Ошибка", "Не удалось создать резервную копию")
    
    def check_integrity(self):
        """Проверяет целостность базы данных"""
        if db.verify_database_integrity():
            messagebox.showinfo("Проверка целостности", 
                              "База данных цела и не повреждена")
        else:
            if messagebox.askyesno("Повреждение БД", 
                                 "База данных повреждена!\n\n"
                                 "Создать резервную копию и восстановить?"):
                self.create_backup()
                self.refresh_all()
    
    def show_audit_log(self):
        """Показывает журнал аудита"""
        log_file = 'audit.log'
        if not os.path.exists(log_file):
            messagebox.showinfo("Журнал аудита", "Журнал аудита пуст")
            return
        
        log_window = tk.Toplevel(self.root)
        log_window.title("Журнал аудита")
        log_window.geometry("800x500")
        
        text_frame = ttk.Frame(log_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        text_widget = tk.Text(text_frame, wrap='none', yscrollcommand=scrollbar.set)
        text_widget.pack(side='left', fill='both', expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                text_widget.insert('1.0', content)
            text_widget.config(state='disabled')
        except Exception as e:
            text_widget.insert('1.0', f"Ошибка чтения лога: {e}")
    
    def show_security_stats(self):
        """Показывает статистику безопасности"""
        stats = db.get_database_stats()
        
        log_size = 0
        if os.path.exists('audit.log'):
            log_size = os.path.getsize('audit.log') // 1024
        
        security_info = f"""
╔════════════════════════════════════╗
║     СТАТИСТИКА БЕЗОПАСНОСТИ       ║
╚════════════════════════════════════╝

ДАННЫЕ:
   • Пациентов: {stats['patients']}
   • Врачей: {stats['doctors']}
   • Записей всего: {stats['appointments']}
   • Записей на сегодня: {stats['today_appointments']}

РЕЗЕРВНОЕ КОПИРОВАНИЕ:
   • Размер БД: {stats['size_kb']} КБ
   • Последний бэкап: {stats['last_backup'] or 'нет'}

ЗАЩИТА:
   • SQL-инъекции: ✅ Заблокированы
   • Валидация данных: ✅ Активна
   • Логирование: ✅ Включено
   • Журнал аудита: {log_size} КБ

ВНИМАНИЕ:
   • Все действия записываются в audit.log
   • Не удаляйте файлы .db и .log вручную
   • Используйте меню "Безопасность" для проверок
"""
        messagebox.showinfo("Статистика безопасности", security_info)
    
    def show_security_guide(self):
        """Показывает руководство по безопасности"""
        guide = """
РУКОВОДСТВО ПО БЕЗОПАСНОСТИ
===========================

ЗАЩИТА ДАННЫХ:
1. Все SQL-запросы параметризованы
2. Входные данные проходят валидацию
3. Номера полисов хешируются в логах

РЕЗЕРВНОЕ КОПИРОВАНИЕ:
• Автоматически при запуске
• Вручную через меню "Файл"
• Хранятся в папке /backups

АУДИТ:
• Все действия логируются
• Лог хранится в audit.log
• Не редактируйте лог вручную

ВАЖНО:
• Не удаляйте файл clinic.db вручную
• Используйте функцию "Очистить кэш"
• При ошибках создавайте бэкап

РЕКОМЕНДАЦИИ:
• Регулярно проверяйте целостность БД
• Храните бэкапы в надежном месте
• Ограничьте доступ к программе
"""
        messagebox.showinfo("Руководство по безопасности", guide)
    
    def create_status_bar(self):
        """Создаёт строку состояния внизу окна"""
        self.status_bar = ttk.Label(
            self.root, 
            text=" Готово | Режим: безопасный", 
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
            self.status_bar.config(text=f" [{current_time}] {message} | Режим: безопасный")
            self.root.update()
    
    def refresh_all(self):
        """Обновляет все данные во всех вкладках"""
        self.load_patients()
        self.load_doctors()
        self.load_appointments()
        self.load_stats()
        self.update_status("Все данные обновлены")
    
    def cleanup_database_cache(self):
        """Очищает кэш базы данных (VACUUM)"""
        if messagebox.askyesno("Подтверждение", 
                              "Очистить кэш базы данных?\n"
                              "Это безопасная операция, которая уменьшит размер файла."):
            try:
                db.backup_database()
                
                if db.vacuum_database():
                    self.update_status("Кэш базы данных успешно очищен")
                    messagebox.showinfo("Успех", 
                                      "Кэш очищен\n"
                                      "Размер файла уменьшен")
                else:
                    messagebox.showerror("Ошибка", "Не удалось очистить кэш")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить кэш: {e}")
    
    # ============================================
    # ВКЛАДКА СТАТИСТИКИ
    # ============================================
    
    def create_stats_tab(self):
        """Создаёт вкладку со статистикой"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Статистика")
        
        main_frame = ttk.Frame(tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(
            main_frame, 
            text="Статистика работы поликлиники", 
            font=('Arial', 14, 'bold')
        ).grid(row=0, column=0, columnspan=2, pady=10)
        
        self.stats_labels = {}
        stats_items = [
            ('patients', 'Пациентов:'),
            ('doctors', 'Врачей:'),
            ('appointments', 'Всего записей:'),
            ('today_appointments', 'Записей на сегодня:'),
            ('size_kb', 'Размер БД:'),
            ('last_backup', 'Последний бэкап:')
        ]
        
        for i, (key, label) in enumerate(stats_items):
            ttk.Label(main_frame, text=label, font=('Arial', 11)).grid(
                row=i+1, column=0, sticky='w', pady=5
            )
            self.stats_labels[key] = ttk.Label(main_frame, text="...", font=('Arial', 11, 'bold'))
            self.stats_labels[key].grid(row=i+1, column=1, sticky='w', pady=5, padx=20)
        
        ttk.Button(
            main_frame,
            text="Обновить статистику",
            command=self.load_stats
        ).grid(row=len(stats_items)+2, column=0, columnspan=2, pady=20)
        
        security_frame = ttk.LabelFrame(main_frame, text="Состояние безопасности", padding=10)
        security_frame.grid(row=len(stats_items)+3, column=0, columnspan=2, pady=10, sticky='ew')
        
        security_items = [
            ("Защита от SQL-инъекций", "green"),
            ("Валидация данных", "green"),
            ("Логирование действий", "green"),
            ("Автоматическое резервирование", "green")
        ]
        
        for i, (text, color) in enumerate(security_items):
            label = ttk.Label(security_frame, text=text, foreground=color)
            label.grid(row=i, column=0, sticky='w', pady=2)
        
        self.load_stats()
    
    def load_stats(self):
        """Загружает статистику"""
        stats = db.get_database_stats()
        
        self.stats_labels['patients'].config(text=str(stats['patients']))
        self.stats_labels['doctors'].config(text=str(stats['doctors']))
        self.stats_labels['appointments'].config(text=str(stats['appointments']))
        self.stats_labels['today_appointments'].config(text=str(stats['today_appointments']))
        self.stats_labels['size_kb'].config(text=f"{stats['size_kb']} КБ")
        self.stats_labels['last_backup'].config(text=stats['last_backup'] or "нет")
    
    # ============================================
    # ВКЛАДКА "ПАЦИЕНТЫ"
    # ============================================
    
    def create_patients_tab(self):
        """Создаёт вкладку управления пациентами"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Пациенты")
        
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            top_frame, 
            text="Добавить пациента", 
            command=self.open_add_patient_dialog,
            style='Action.TButton'
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame, 
            text="Редактировать", 
            command=self.open_edit_patient_dialog
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame, 
            text="Удалить", 
            command=self.delete_selected_patient,
            style='Warning.TButton'
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame, 
            text="Обновить", 
            command=self.load_patients
        ).pack(side='left', padx=2)
        
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side='right')
        
        ttk.Label(search_frame, text="Поиск:").pack(side='left', padx=2)
        
        self.patient_search_var = tk.StringVar()
        self.patient_search_var.trace('w', lambda *args: self.search_patients())
        
        vcmd = (self.root.register(self.validate_search), '%P')
        ttk.Entry(
            search_frame, 
            textvariable=self.patient_search_var, 
            width=30,
            validate='key',
            validatecommand=vcmd
        ).pack(side='left')
        
        columns = ('id', 'ФИО', 'Дата рождения', 'Телефон', 'Номер полиса')
        self.patients_tree = ttk.Treeview(
            tab, 
            columns=columns, 
            show='headings', 
            height=20
        )
        
        for col in columns:
            self.patients_tree.heading(col, text=col)
        
        widths = [50, 250, 100, 120, 150]
        for col, width in zip(columns, widths):
            self.patients_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(
            tab, 
            orient='vertical', 
            command=self.patients_tree.yview
        )
        self.patients_tree.configure(yscrollcommand=scrollbar.set)
        
        self.patients_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        self.load_patients()
    
    def validate_search(self, value):
        """Валидация поискового запроса"""
        if len(value) > 50:
            return False
        return True
    
    def load_patients(self):
        """Загружает список пациентов в таблицу"""
        try:
            for row in self.patients_tree.get_children():
                self.patients_tree.delete(row)
            
            patients = db.get_all_patients()
            for patient in patients:
                self.patients_tree.insert('', 'end', values=(
                    patient['id'],
                    patient['full_name'],
                    patient['birth_date'] or '',
                    patient['phone'] or '',
                    patient['policy_number'] or ''
                ))
            
            self.update_status(f"Загружено {len(patients)} пациентов")
        except Exception as e:
            self.update_status(f"Ошибка загрузки: {e}")
    
    def search_patients(self):
        """Поиск пациентов"""
        search_text = self.patient_search_var.get().strip()
        
        try:
            for row in self.patients_tree.get_children():
                self.patients_tree.delete(row)
            
            if search_text and len(search_text) >= 2:
                patients = db.search_patients(search_text)
            else:
                patients = db.get_all_patients()
            
            for patient in patients:
                self.patients_tree.insert('', 'end', values=(
                    patient['id'],
                    patient['full_name'],
                    patient['birth_date'] or '',
                    patient['phone'] or '',
                    patient['policy_number'] or ''
                ))
        except Exception as e:
            self.update_status(f"Ошибка поиска: {e}")
    
    def open_add_patient_dialog(self):
        """Открывает диалог добавления пациента"""
        self.open_patient_dialog(mode="add")
    
    def open_edit_patient_dialog(self):
        """Открывает диалог редактирования пациента"""
        selection = self.patients_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пациента для редактирования")
            return
        
        item = self.patients_tree.item(selection[0])
        patient_id = item['values'][0]
        
        patient = db.get_patient_by_id(patient_id)
        if patient:
            self.open_patient_dialog(mode="edit", patient=patient)
        else:
            messagebox.showerror("Ошибка", "Пациент не найден")
    
    def delete_selected_patient(self):
        """Удаляет выбранного пациента"""
        selection = self.patients_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пациента для удаления")
            return
        
        item = self.patients_tree.item(selection[0])
        patient_id = item['values'][0]
        patient_name = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", 
                              f"Удалить пациента {patient_name}?\n\n"
                              "ВНИМАНИЕ:\n"
                              "Если у пациента есть будущие записи, удаление будет запрещено.\n"
                              "Все прошлые записи будут удалены."):
            
            result = db.delete_patient(patient_id)
            
            if result.get('success'):
                self.load_patients()
                self.load_appointments()
                self.load_stats()
                self.update_status(f"Пациент {patient_name} удалён")
                messagebox.showinfo("Успех", "Пациент удалён")
            elif 'future_appointments' in result:
                messagebox.showerror("Ошибка", 
                                    f"Нельзя удалить пациента с будущими записями\n"
                                    f"Количество будущих записей: {result['future_appointments']}")
            else:
                messagebox.showerror("Ошибка", f"Не удалось удалить пациента: {result.get('error', '')}")
    
    def open_patient_dialog(self, mode="add", patient=None):
        """
        Универсальный диалог для добавления/редактирования пациента.
        
        Args:
            mode (str): "add" или "edit"
            patient: данные пациента (для edit)
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование пациента" if mode == "edit" else "Добавление пациента")
        dialog.geometry("550x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(dialog, text="ФИО *", font=('Arial', 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky='w'
        )
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.focus()
        
        ttk.Label(dialog, text="Дата рождения (ГГГГ-ММ-ДД)", font=('Arial', 10)).grid(
            row=1, column=0, padx=10, pady=10, sticky='w'
        )
        birth_entry = ttk.Entry(dialog, width=40)
        birth_entry.grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Телефон", font=('Arial', 10)).grid(
            row=2, column=0, padx=10, pady=10, sticky='w'
        )
        phone_entry = ttk.Entry(dialog, width=40)
        phone_entry.grid(row=2, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Номер полиса *", font=('Arial', 10)).grid(
            row=3, column=0, padx=10, pady=10, sticky='w'
        )
        policy_entry = ttk.Entry(dialog, width=40)
        policy_entry.grid(row=3, column=1, padx=10, pady=10)
        
        if mode == "edit" and patient:
            name_entry.insert(0, patient['full_name'] or '')
            birth_entry.insert(0, patient['birth_date'] or '')
            phone_entry.insert(0, patient['phone'] or '')
            policy_entry.insert(0, patient['policy_number'] or '')
            policy_entry.config(state='disabled')
        
        security_label = ttk.Label(
            dialog, 
            text="Данные будут проверены и очищены",
            foreground='green',
            font=('Arial', 9)
        )
        security_label.grid(row=4, column=0, columnspan=2, pady=5)
        
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        def save_patient():
            name = name_entry.get().strip()
            birth = birth_entry.get().strip() or None
            phone = phone_entry.get().strip() or None
            policy = policy_entry.get().strip()
            
            if mode == "add":
                patient_id = db.add_patient(name, birth, phone, policy)
                if patient_id:
                    messagebox.showinfo("Успех", f"Пациент добавлен (ID: {patient_id})")
                    self.load_patients()
                    self.load_stats()
                    dialog.destroy()
                    self.update_status(f"Добавлен пациент: {name}")
                else:
                    messagebox.showerror("Ошибка", 
                                       "Не удалось добавить пациента.\n"
                                       "Возможно, такой номер полиса уже существует.")
            else:
                if db.update_patient(patient['id'], name, birth, phone, policy):
                    messagebox.showinfo("Успех", "Данные пациента обновлены")
                    self.load_patients()
                    dialog.destroy()
                    self.update_status(f"Обновлён пациент: {name}")
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить данные")
        
        ttk.Button(
            button_frame, 
            text="Сохранить", 
            command=save_patient, 
            width=15
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, 
            text="Отмена", 
            command=dialog.destroy, 
            width=15
        ).pack(side='left', padx=5)
    
    # ============================================
    # ВКЛАДКА "ВРАЧИ"
    # ============================================
    
    def create_doctors_tab(self):
        """Создаёт вкладку со списком врачей"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Врачи")
        
        columns = ('id', 'ФИО', 'Специальность', 'Кабинет')
        self.doctors_tree = ttk.Treeview(
            tab, 
            columns=columns, 
            show='headings', 
            height=20
        )
        
        for col in columns:
            self.doctors_tree.heading(col, text=col)
        
        widths = [50, 250, 150, 80]
        for col, width in zip(columns, widths):
            self.doctors_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(
            tab, 
            orient='vertical', 
            command=self.doctors_tree.yview
        )
        self.doctors_tree.configure(yscrollcommand=scrollbar.set)
        
        self.doctors_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        self.load_doctors()
        
        info_label = ttk.Label(
            tab,
            text="Список врачей доступен только для просмотра. Изменения через администратора.",
            foreground='blue',
            font=('Arial', 9)
        )
        info_label.pack(side='bottom', pady=5)
    
    def load_doctors(self):
        """Загружает список врачей в таблицу"""
        try:
            for row in self.doctors_tree.get_children():
                self.doctors_tree.delete(row)
            
            doctors = db.get_all_doctors()
            for doctor in doctors:
                self.doctors_tree.insert('', 'end', values=(
                    doctor['id'],
                    doctor['full_name'],
                    doctor['specialty'] or '',
                    doctor['room_number'] or ''
                ))
        except Exception as e:
            self.update_status(f"Ошибка загрузки врачей: {e}")
    
    def load_doctors_to_combobox(self):
        """Загружает врачей в выпадающий список"""
        try:
            doctors = db.get_all_doctors()
            doctor_list = [f"{d['id']}: {d['full_name']} ({d['specialty']})" for d in doctors]
            self.doctor_combobox['values'] = doctor_list
            if doctor_list:
                self.doctor_combobox.current(0)
        except Exception as e:
            self.update_status(f"Ошибка загрузки врачей: {e}")
    
    # ============================================
    # ВКЛАДКА "НОВАЯ ЗАПИСЬ"
    # ============================================
    
    def create_new_appointment_tab(self):
        """Создаёт вкладку для создания новой записи"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Новая запись")
        
        main_frame = ttk.Frame(tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(
            main_frame, 
            text="Создание новой записи на приём", 
            font=('Arial', 14, 'bold')
        ).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Выбор пациента
        ttk.Label(main_frame, text="Пациент:", font=('Arial', 11)).grid(
            row=1, column=0, sticky='w', pady=5
        )
        
        patient_frame = ttk.Frame(main_frame)
        patient_frame.grid(row=1, column=1, sticky='ew', pady=5)
        
        vcmd = (self.root.register(lambda P: len(P) <= 50), '%P')
        self.patient_search_entry = ttk.Entry(patient_frame, width=40, validate='key', validatecommand=vcmd)
        self.patient_search_entry.pack(side='left', padx=2)
        self.patient_search_entry.bind('<KeyRelease>', self.search_patients_for_appointment)
        
        ttk.Button(
            patient_frame, 
            text="Поиск", 
            command=self.search_patients_for_appointment
        ).pack(side='left', padx=2)
        
        self.patients_listbox = tk.Listbox(main_frame, height=5, width=60)
        self.patients_listbox.grid(row=2, column=0, columnspan=2, pady=5, sticky='ew')
        
        self.selected_patient_id = None
        self.selected_patient_text = None
        self.patients_listbox.bind('<<ListboxSelect>>', self.on_patient_select)
        
        self.selected_patient_label = ttk.Label(
            main_frame, 
            text="Пациент не выбран", 
            foreground='gray'
        )
        self.selected_patient_label.grid(row=3, column=0, columnspan=2, pady=2, sticky='w')
        
        # Выбор врача
        ttk.Label(main_frame, text="Врач:", font=('Arial', 11)).grid(
            row=4, column=0, sticky='w', pady=5
        )
        
        self.doctor_combobox = ttk.Combobox(
            main_frame, 
            width=50, 
            state='readonly'
        )
        self.doctor_combobox.grid(row=4, column=1, sticky='w', pady=5)
        self.load_doctors_to_combobox()
        
        # Выбор даты
        ttk.Label(main_frame, text="Дата (ГГГГ-ММ-ДД):", font=('Arial', 11)).grid(
            row=5, column=0, sticky='w', pady=5
        )
        
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=5, column=1, sticky='w', pady=5)
        
        vcmd_date = (self.root.register(self.validate_date_input), '%P')
        self.date_entry = ttk.Entry(
            date_frame, 
            width=15,
            validate='key',
            validatecommand=vcmd_date
        )
        self.date_entry.pack(side='left', padx=2)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Button(
            date_frame, 
            text="Показать свободное время", 
            command=self.show_free_time
        ).pack(side='left', padx=2)
        
        # Выбор времени
        ttk.Label(main_frame, text="Доступное время:", font=('Arial', 11)).grid(
            row=6, column=0, sticky='w', pady=5
        )
        
        self.time_listbox = tk.Listbox(main_frame, height=8, width=30)
        self.time_listbox.grid(row=6, column=1, pady=5, sticky='w')
        
        self.selected_time = None
        self.time_listbox.bind('<<ListboxSelect>>', self.on_time_select)
        
        self.selected_time_label = ttk.Label(
            main_frame, 
            text="Время не выбрано", 
            foreground='gray'
        )
        self.selected_time_label.grid(row=7, column=1, pady=2, sticky='w')
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame, 
            text="Записать на приём", 
            command=self.create_appointment,
            style='Action.TButton'
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Очистить форму",
            command=self.clear_appointment_form
        ).pack(side='left', padx=5)
        
        self.appointment_info_label = ttk.Label(main_frame, text="", foreground='blue')
        self.appointment_info_label.grid(row=9, column=0, columnspan=2)
        
        security_label = ttk.Label(
            main_frame,
            text="Все данные проверяются. Запись в прошлое невозможна.",
            foreground='green',
            font=('Arial', 9)
        )
        security_label.grid(row=10, column=0, columnspan=2, pady=5)
    
    def validate_date_input(self, value):
        """Валидация ввода даты"""
        if not value:
            return True
        if len(value) > 10:
            return False
        for char in value:
            if not (char.isdigit() or char == '-'):
                return False
        return True
    
    def on_patient_select(self, event):
        """Обработчик выбора пациента"""
        selection = self.patients_listbox.curselection()
        if selection:
            self.selected_patient_text = self.patients_listbox.get(selection[0])
            try:
                self.selected_patient_id = int(self.selected_patient_text.split(':')[0])
                patient_name = self.selected_patient_text.split(':', 1)[1].split('(')[0].strip()
                self.selected_patient_label.config(
                    text=f"Выбран пациент: {patient_name}", 
                    foreground='green'
                )
                self.update_status(f"Выбран пациент: {patient_name}")
            except (ValueError, IndexError):
                self.selected_patient_id = None
                self.selected_patient_label.config(text="Ошибка выбора пациента", foreground='red')
    
    def on_time_select(self, event):
        """Обработчик выбора времени"""
        selection = self.time_listbox.curselection()
        if selection:
            self.selected_time = self.time_listbox.get(selection[0])
            if self.selected_time != "Нет свободного времени":
                self.selected_time_label.config(
                    text=f"Выбрано время: {self.selected_time}",
                    foreground='green'
                )
            else:
                self.selected_time = None
                self.selected_time_label.config(text="Время не выбрано", foreground='gray')
    
    def search_patients_for_appointment(self, event=None):
        """Поиск пациентов для записи"""
        search_text = self.patient_search_entry.get().strip()
        
        self.patients_listbox.delete(0, tk.END)
        self.selected_patient_id = None
        self.selected_patient_text = None
        self.selected_patient_label.config(text="Пациент не выбран", foreground='gray')
        
        if len(search_text) < 2:
            return
        
        try:
            patients = db.search_patients(search_text)
            for patient in patients:
                display_text = f"{patient['id']}: {patient['full_name']} (Полис: {patient['policy_number']})"
                self.patients_listbox.insert(tk.END, display_text)
        except Exception as e:
            self.update_status(f"Ошибка поиска: {e}")
    
    def show_free_time(self):
        """Показывает свободное время"""
        if not self.selected_patient_id:
            messagebox.showwarning("Предупреждение", 
                                 "Сначала выберите пациента")
            return
        
        if not self.doctor_combobox.get():
            messagebox.showwarning("Предупреждение", "Выберите врача")
            return
        
        date = self.date_entry.get().strip()
        if not date:
            messagebox.showwarning("Предупреждение", "Введите дату")
            return
        
        try:
            doctor_id = int(self.doctor_combobox.get().split(':')[0])
        except:
            messagebox.showerror("Ошибка", "Неверный формат данных врача")
            return
        
        try:
            free_times = db.get_free_time(doctor_id, date)
            
            self.time_listbox.delete(0, tk.END)
            self.selected_time = None
            self.selected_time_label.config(text="Время не выбрано", foreground='gray')
            
            for time in free_times:
                self.time_listbox.insert(tk.END, time)
            
            if not free_times:
                self.time_listbox.insert(tk.END, "Нет свободного времени")
                self.appointment_info_label.config(
                    text="На эту дату нет свободных слотов",
                    foreground='red'
                )
            else:
                self.appointment_info_label.config(
                    text=f"Доступно слотов: {len(free_times)}",
                    foreground='green'
                )
        except Exception as e:
            self.update_status(f"Ошибка: {e}")
    
    def create_appointment(self):
        """Создаёт новую запись"""
        if not self.selected_patient_id:
            messagebox.showwarning("Предупреждение", "Выберите пациента")
            return
        
        if not self.doctor_combobox.get():
            messagebox.showwarning("Предупреждение", "Выберите врача")
            return
        
        try:
            doctor_id = int(self.doctor_combobox.get().split(':')[0])
        except:
            messagebox.showerror("Ошибка", "Неверный формат данных врача")
            return
        
        if not self.selected_time or self.selected_time == "Нет свободного времени":
            messagebox.showwarning("Предупреждение", "Выберите время")
            return
        
        date = self.date_entry.get().strip()
        if not date:
            messagebox.showwarning("Предупреждение", "Введите дату")
            return
        
        appointment_id = db.add_appointment(self.selected_patient_id, doctor_id, date, self.selected_time)
        
        if appointment_id:
            messagebox.showinfo("Успех", "Пациент успешно записан на приём")
            self.clear_appointment_form()
            self.load_appointments()
            self.load_stats()
            self.notebook.select(3)
            self.update_status("Создана новая запись")
        else:
            messagebox.showerror("Ошибка", 
                               "Не удалось создать запись.\n"
                               "Возможно, это время уже занято.")
    
    def clear_appointment_form(self):
        """Очищает форму записи"""
        self.patient_search_entry.delete(0, tk.END)
        self.patients_listbox.delete(0, tk.END)
        self.selected_patient_id = None
        self.selected_patient_text = None
        self.selected_patient_label.config(text="Пациент не выбран", foreground='gray')
        
        self.time_listbox.delete(0, tk.END)
        self.selected_time = None
        self.selected_time_label.config(text="Время не выбрано", foreground='gray')
        self.appointment_info_label.config(text="")
        
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        self.update_status("Форма очищена")
    
    # ============================================
    # ВКЛАДКА "ВСЕ ЗАПИСИ"
    # ============================================
    
    def create_appointments_tab(self):
        """Создаёт вкладку со списком всех записей"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Все записи")
        
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            top_frame, 
            text="Обновить", 
            command=self.load_appointments
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame, 
            text="Отменить запись", 
            command=self.cancel_selected_appointment,
            style='Warning.TButton'
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame,
            text="Удалить старые записи",
            command=self.delete_old_appointments
        ).pack(side='left', padx=2)
        
        columns = ('id', 'Пациент', 'Полис', 'Врач', 'Специальность', 'Кабинет', 'Дата', 'Время', 'Статус')
        self.appointments_tree = ttk.Treeview(
            tab, 
            columns=columns, 
            show='headings', 
            height=20
        )
        
        for col in columns:
            self.appointments_tree.heading(col, text=col)
        
        widths = [50, 200, 100, 200, 120, 60, 80, 80, 100]
        for col, width in zip(columns, widths):
            self.appointments_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(
            tab, 
            orient='vertical', 
            command=self.appointments_tree.yview
        )
        self.appointments_tree.configure(yscrollcommand=scrollbar.set)
        
        self.appointments_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        self.load_appointments()
    
    def load_appointments(self):
        """Загружает список записей"""
        try:
            for row in self.appointments_tree.get_children():
                self.appointments_tree.delete(row)
            
            appointments = db.get_all_appointments()
            for apt in appointments:
                self.appointments_tree.insert('', 'end', values=(
                    apt['id'],
                    apt['patient_name'],
                    apt['policy_number'] or '',
                    apt['doctor_name'],
                    apt['specialty'] or '',
                    apt['room_number'] or '',
                    apt['date'],
                    apt['time'],
                    apt['status']
                ))
            
            self.update_status(f"Загружено {len(appointments)} записей")
        except Exception as e:
            self.update_status(f"Ошибка загрузки: {e}")
    
    def cancel_selected_appointment(self):
        """Отменяет выбранную запись"""
        selection = self.appointments_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите запись для отмены")
            return
        
        item = self.appointments_tree.item(selection[0])
        appointment_id = item['values'][0]
        patient_name = item['values'][1]
        date = item['values'][6]
        time = item['values'][7]
        
        if messagebox.askyesno("Подтверждение", 
                              f"Отменить запись?\n\n"
                              f"Пациент: {patient_name}\n"
                              f"Дата: {date}\n"
                              f"Время: {time}"):
            
            reason = None
            if messagebox.askyesno("Причина отмены", "Указать причину отмены?"):
                reason = self.ask_cancel_reason()
            
            if db.cancel_appointment(appointment_id, reason):
                self.load_appointments()
                self.update_status(f"Запись отменена")
                messagebox.showinfo("Успех", "Запись отменена")
            else:
                messagebox.showerror("Ошибка", "Не удалось отменить запись")
    
    def ask_cancel_reason(self):
        """Запрашивает причину отмены"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Причина отмены")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Укажите причину отмены:").pack(pady=10)
        
        reason_var = tk.StringVar()
        reason_entry = ttk.Entry(dialog, textvariable=reason_var, width=50)
        reason_entry.pack(pady=10)
        reason_entry.focus()
        
        result = None
        
        def on_ok():
            nonlocal result
            result = reason_var.get().strip()
            dialog.destroy()
        
        def on_skip():
            nonlocal result
            result = None
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="OK", command=on_ok, width=10).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Пропустить", command=on_skip, width=10).pack(side='left', padx=5)
        
        dialog.wait_window()
        return result
    
    def delete_old_appointments(self):
        """Удаляет старые записи"""
        if messagebox.askyesno("Подтверждение", 
                              "Удалить все записи старше 30 дней?\n\n"
                              "ВНИМАНИЕ:\n"
                              "Эта операция необратима.\n"
                              "Будет создана резервная копия."):
            try:
                db.backup_database()
                
                count = db.delete_old_appointments()
                self.load_appointments()
                self.load_stats()
                self.update_status(f"Удалено старых записей: {count}")
                messagebox.showinfo("Успех", f"Удалено записей: {count}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить старые записи: {e}")
    
    # ============================================
    # ДИАЛОГ "О ПРОГРАММЕ"
    # ============================================
    
    def show_about(self):
        """Показывает информацию о программе"""
        about_text = """РЕГИСТРАТУРА ПОЛИКЛИНИКИ
Версия 2.0 (Безопасная)

ЗАЩИТА ДАННЫХ:
• Параметризованные SQL-запросы
• Валидация всех входных данных
• Логирование действий (audit.log)
• Автоматическое резервирование
• Проверка целостности БД

ФУНКЦИОНАЛ:
• Ведение базы пациентов
• Запись на приём к врачам
• Просмотр и отмена записей
• Статистика и мониторинг
• Журнал аудита

БЕЗОПАСНОСТЬ:
• Защита от SQL-инъекций: 
• Валидация данных: 
• Аудит действий: 
• Резервное копирование: 

Чухарев Сергей Михайлович
Разработано для курсовой работы
Февраль 2026 год"""
        
        messagebox.showinfo("О программе", about_text)


# ============================================
# ТОЧКА ВХОДА
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("ЗАПУСК РЕГИСТРАТУРЫ ПОЛИКЛИНИКИ (БЕЗОПАСНЫЙ РЕЖИМ)")
    print("=" * 60)
    
    if not db.verify_database_integrity():
        print("База данных повреждена! Будет создана новая.")
        if os.path.exists('clinic.db'):
            backup_name = f"clinic.db.corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename('clinic.db', backup_name)
    
    db.init_db()
    
    backup = db.backup_database()
    if backup:
        print(f"✅ Создана резервная копия: {backup}")
    
    root = tk.Tk()
    app = MainApplication(root)
    
    print("Программа запущена в безопасном режиме")
    print("Журнал аудита: audit.log")
    print("=" * 60)
    
    root.mainloop()
    
    print("Программа завершена")