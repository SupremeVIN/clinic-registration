"""
Модуль с графическим интерфейсом программы.
Использует библиотеку tkinter.
"""

# Импортируем необходимые модули
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import database as db

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
        self.root.title("🏥 Регистратура поликлиники")
        self.root.geometry("1200x700")
        
        # Центрируем окно на экране
        self.center_window()
        
        # Настраиваем стили
        self.setup_styles()
        
        # Создаём меню
        self.create_menu()
        
        # Создаём строку состояния (статус бар)
        self.create_status_bar()
        
        # Создаём блокнот с вкладками
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Создаём все вкладки
        self.create_patients_tab()      # Вкладка "Пациенты"
        self.create_doctors_tab()        # Вкладка "Врачи"
        self.create_new_appointment_tab() # Вкладка "Новая запись"
        self.create_appointments_tab()    # Вкладка "Все записи"
        
        # Обновляем статус
        self.update_status("Программа готова к работе")
    
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
    
    def create_menu(self):
        """Создаёт главное меню программы"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Обновить всё", command=self.refresh_all)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def create_status_bar(self):
        """Создаёт строку состояния внизу окна"""
        self.status_bar = ttk.Label(
            self.root, 
            text=" Готово", 
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
            self.status_bar.config(text=f" {message}")
            self.root.update()
    
    def refresh_all(self):
        """Обновляет все данные во всех вкладках"""
        self.load_patients()
        self.load_doctors()
        self.load_appointments()
        self.update_status("Все данные обновлены")
    
    # ============================================
    # ВКЛАДКА "ПАЦИЕНТЫ"
    # ============================================
    
    def create_patients_tab(self):
        """Создаёт вкладку управления пациентами"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="👥 Пациенты")
        
        # Верхняя панель с кнопками
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        # Кнопка добавления пациента
        ttk.Button(
            top_frame, 
            text="➕ Добавить пациента", 
            command=self.open_add_patient_dialog
        ).pack(side='left', padx=2)
        
        # Кнопка обновления списка
        ttk.Button(
            top_frame, 
            text="🔄 Обновить список", 
            command=self.load_patients
        ).pack(side='left', padx=2)
        
        # Панель поиска
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side='right')
        
        ttk.Label(search_frame, text="Поиск:").pack(side='left', padx=2)
        
        # Переменная для хранения текста поиска
        self.patient_search_var = tk.StringVar()
        # При каждом изменении текста вызываем search_patients
        self.patient_search_var.trace('w', lambda *args: self.search_patients())
        
        ttk.Entry(
            search_frame, 
            textvariable=self.patient_search_var, 
            width=30
        ).pack(side='left')
        
        # Таблица пациентов
        columns = ('id', 'ФИО', 'Дата рождения', 'Телефон', 'Номер полиса')
        self.patients_tree = ttk.Treeview(
            tab, 
            columns=columns, 
            show='headings', 
            height=20
        )
        
        # Настройка заголовков
        self.patients_tree.heading('id', text='ID')
        self.patients_tree.heading('ФИО', text='ФИО')
        self.patients_tree.heading('Дата рождения', text='Дата рождения')
        self.patients_tree.heading('Телефон', text='Телефон')
        self.patients_tree.heading('Номер полиса', text='Номер полиса')
        
        # Настройка ширины колонок
        self.patients_tree.column('id', width=50)
        self.patients_tree.column('ФИО', width=250)
        self.patients_tree.column('Дата рождения', width=100)
        self.patients_tree.column('Телефон', width=120)
        self.patients_tree.column('Номер полиса', width=150)
        
        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(
            tab, 
            orient='vertical', 
            command=self.patients_tree.yview
        )
        self.patients_tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещаем таблицу и скроллбар
        self.patients_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # Загружаем данные
        self.load_patients()
    
    def load_patients(self):
        """Загружает список пациентов в таблицу"""
        # Очищаем таблицу
        for row in self.patients_tree.get_children():
            self.patients_tree.delete(row)
        
        # Загружаем пациентов из БД
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
    
    def search_patients(self):
        """Поиск пациентов по введённому тексту"""
        search_text = self.patient_search_var.get().strip()
        
        # Очищаем таблицу
        for row in self.patients_tree.get_children():
            self.patients_tree.delete(row)
        
        # Ищем пациентов
        if search_text:
            patients = db.search_patients(search_text)
        else:
            patients = db.get_all_patients()
        
        # Заполняем таблицу результатами
        for patient in patients:
            self.patients_tree.insert('', 'end', values=(
                patient['id'],
                patient['full_name'],
                patient['birth_date'] or '',
                patient['phone'] or '',
                patient['policy_number'] or ''
            ))
    
    def open_add_patient_dialog(self):
        """Открывает диалог добавления нового пациента"""
        # Создаём новое окно поверх главного
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление нового пациента")
        dialog.geometry("500x300")
        dialog.transient(self.root)  # Окно всегда поверх родителя
        dialog.grab_set()  # Захватываем фокус
        
        # Центрируем окно относительно родителя
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Поля ввода
        # ФИО (обязательное поле)
        ttk.Label(dialog, text="ФИО *", font=('Arial', 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky='w'
        )
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.focus()  # Устанавливаем курсор в это поле
        
        # Дата рождения
        ttk.Label(dialog, text="Дата рождения (ГГГГ-ММ-ДД)", font=('Arial', 10)).grid(
            row=1, column=0, padx=10, pady=10, sticky='w'
        )
        birth_entry = ttk.Entry(dialog, width=40)
        birth_entry.grid(row=1, column=1, padx=10, pady=10)
        # Подставляем сегодняшнюю дату как пример
        birth_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Телефон
        ttk.Label(dialog, text="Телефон", font=('Arial', 10)).grid(
            row=2, column=0, padx=10, pady=10, sticky='w'
        )
        phone_entry = ttk.Entry(dialog, width=40)
        phone_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # Номер полиса (обязательное поле, должно быть уникальным)
        ttk.Label(dialog, text="Номер полиса *", font=('Arial', 10)).grid(
            row=3, column=0, padx=10, pady=10, sticky='w'
        )
        policy_entry = ttk.Entry(dialog, width=40)
        policy_entry.grid(row=3, column=1, padx=10, pady=10)
        
        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        def save_patient():
            """Внутренняя функция для сохранения пациента"""
            # Получаем данные из полей ввода
            name = name_entry.get().strip()
            policy = policy_entry.get().strip()
            
            # Проверка обязательных полей
            if not name:
                messagebox.showerror("Ошибка", "Поле ФИО обязательно для заполнения")
                return
            
            if not policy:
                messagebox.showerror("Ошибка", "Поле 'Номер полиса' обязательно для заполнения")
                return
            
            # Сохраняем в БД
            patient_id = db.add_patient(
                name,
                birth_entry.get().strip() or None,
                phone_entry.get().strip() or None,
                policy
            )
            
            if patient_id:
                messagebox.showinfo("Успех", f"Пациент успешно добавлен (ID: {patient_id})")
                self.load_patients()  # обновляем список
                dialog.destroy()
                self.update_status(f"Добавлен новый пациент: {name}")
            else:
                messagebox.showerror("Ошибка", "Пациент с таким номером полиса уже существует")
        
        # Кнопки Сохранить и Отмена
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
        self.notebook.add(tab, text="👨‍⚕️ Врачи")
        
        # Таблица врачей
        columns = ('id', 'ФИО', 'Специальность', 'Кабинет')
        self.doctors_tree = ttk.Treeview(
            tab, 
            columns=columns, 
            show='headings', 
            height=20
        )
        
        # Настройка заголовков
        self.doctors_tree.heading('id', text='ID')
        self.doctors_tree.heading('ФИО', text='ФИО')
        self.doctors_tree.heading('Специальность', text='Специальность')
        self.doctors_tree.heading('Кабинет', text='Кабинет')
        
        # Настройка ширины
        self.doctors_tree.column('id', width=50)
        self.doctors_tree.column('ФИО', width=250)
        self.doctors_tree.column('Специальность', width=150)
        self.doctors_tree.column('Кабинет', width=80)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(
            tab, 
            orient='vertical', 
            command=self.doctors_tree.yview
        )
        self.doctors_tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещаем
        self.doctors_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # Загружаем врачей
        self.load_doctors()
    
    def load_doctors(self):
        """Загружает список врачей в таблицу"""
        # Очищаем таблицу
        for row in self.doctors_tree.get_children():
            self.doctors_tree.delete(row)
        
        # Загружаем врачей из БД
        doctors = db.get_all_doctors()
        for doctor in doctors:
            self.doctors_tree.insert('', 'end', values=(
                doctor['id'],
                doctor['full_name'],
                doctor['specialty'] or '',
                doctor['room_number'] or ''
            ))
    
    def load_doctors_to_combobox(self):
        """
        Загружает врачей в выпадающий список.
        Используется во вкладке "Новая запись"
        """
        doctors = db.get_all_doctors()
        # Форматируем строку: "ID: ФИО (специальность)"
        doctor_list = [f"{d['id']}: {d['full_name']} ({d['specialty']})" for d in doctors]
        self.doctor_combobox['values'] = doctor_list
        if doctor_list:
            self.doctor_combobox.current(0)  # Выбираем первого врача по умолчанию
    
    # ============================================
    # ВКЛАДКА "НОВАЯ ЗАПИСЬ"
    # ============================================
    
    def create_new_appointment_tab(self):
        """Создаёт вкладку для создания новой записи"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="➕ Новая запись")
        
        # Основной контейнер с отступами
        main_frame = ttk.Frame(tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Заголовок
        ttk.Label(
            main_frame, 
            text="Создание новой записи на приём", 
            font=('Arial', 14, 'bold')
        ).grid(row=0, column=0, columnspan=2, pady=10)
        
        # ========================================
        # ВЫБОР ПАЦИЕНТА
        # ========================================
        ttk.Label(main_frame, text="Пациент:", font=('Arial', 11)).grid(
            row=1, column=0, sticky='w', pady=5
        )
        
        # Панель с полем поиска и кнопкой
        patient_frame = ttk.Frame(main_frame)
        patient_frame.grid(row=1, column=1, sticky='ew', pady=5)
        
        self.patient_search_entry = ttk.Entry(patient_frame, width=40)
        self.patient_search_entry.pack(side='left', padx=2)
        # При каждом нажатии клавиши вызываем поиск
        self.patient_search_entry.bind('<KeyRelease>', self.search_patients_for_appointment)
        
        ttk.Button(
            patient_frame, 
            text="Поиск", 
            command=self.search_patients_for_appointment
        ).pack(side='left', padx=2)
        
        # Список найденных пациентов
        self.patients_listbox = tk.Listbox(main_frame, height=5, width=60)
        self.patients_listbox.grid(row=2, column=0, columnspan=2, pady=5, sticky='ew')
        
        # ========================================
        # ВЫБОР ВРАЧА
        # ========================================
        ttk.Label(main_frame, text="Врач:", font=('Arial', 11)).grid(
            row=3, column=0, sticky='w', pady=5
        )
        
        self.doctor_combobox = ttk.Combobox(
            main_frame, 
            width=50, 
            state='readonly'  # Только для чтения, нельзя вводить своё
        )
        self.doctor_combobox.grid(row=3, column=1, sticky='w', pady=5)
        self.load_doctors_to_combobox()  # Загружаем врачей в список
        
        # ========================================
        # ВЫБОР ДАТЫ
        # ========================================
        ttk.Label(main_frame, text="Дата (ГГГГ-ММ-ДД):", font=('Arial', 11)).grid(
            row=4, column=0, sticky='w', pady=5
        )
        
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=4, column=1, sticky='w', pady=5)
        
        self.date_entry = ttk.Entry(date_frame, width=15)
        self.date_entry.pack(side='left', padx=2)
        # Подставляем сегодняшнюю дату
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Button(
            date_frame, 
            text="Показать свободное время", 
            command=self.show_free_time
        ).pack(side='left', padx=2)
        
        # ========================================
        # ВЫБОР ВРЕМЕНИ
        # ========================================
        self.time_listbox = tk.Listbox(main_frame, height=8, width=30)
        self.time_listbox.grid(row=5, column=1, pady=5, sticky='w')
        
        # ========================================
        # КНОПКА ЗАПИСИ
        # ========================================
        ttk.Button(
            main_frame, 
            text="✅ Записать на приём", 
            command=self.create_appointment,
            style='Action.TButton'
        ).grid(row=6, column=1, pady=20)
        
        # Метка для вывода информации
        self.appointment_info_label = ttk.Label(main_frame, text="", foreground='blue')
        self.appointment_info_label.grid(row=7, column=0, columnspan=2)
    
    def search_patients_for_appointment(self, event=None):
        """Поиск пациентов для записи на приём"""
        search_text = self.patient_search_entry.get().strip()
        
        # Очищаем список
        self.patients_listbox.delete(0, tk.END)
        
        # Ищем только если введено хотя бы 2 символа
        if len(search_text) < 2:
            return
        
        # Ищем пациентов
        patients = db.search_patients(search_text)
        for patient in patients:
            display_text = f"{patient['id']}: {patient['full_name']} (Полис: {patient['policy_number']})"
            self.patients_listbox.insert(tk.END, display_text)
    
    def show_free_time(self):
        """Показывает свободное время для выбранного врача и даты"""
        # Проверяем, выбран ли пациент
        if not self.patients_listbox.curselection():
            messagebox.showwarning("Предупреждение", "Сначала выберите пациента из списка")
            return
        
        # Проверяем, выбран ли врач
        if not self.doctor_combobox.get():
            messagebox.showwarning("Предупреждение", "Выберите врача")
            return
        
        # Получаем дату
        date = self.date_entry.get().strip()
        if not date:
            messagebox.showwarning("Предупреждение", "Введите дату")
            return
        
        # Получаем ID врача из строки (формат "ID: ФИО (специальность)")
        doctor_text = self.doctor_combobox.get()
        try:
            doctor_id = int(doctor_text.split(':')[0])
        except:
            messagebox.showerror("Ошибка", "Неверный формат данных врача")
            return
        
        # Получаем свободное время из БД
        free_times = db.get_free_time(doctor_id, date)
        
        # Очищаем и заполняем список времени
        self.time_listbox.delete(0, tk.END)
        for time in free_times:
            self.time_listbox.insert(tk.END, time)
        
        # Обновляем информационную метку
        if not free_times:
            self.time_listbox.insert(tk.END, "Нет свободного времени")
            self.appointment_info_label.config(text="На эту дату нет свободных слотов")
        else:
            self.appointment_info_label.config(text=f"Доступно слотов: {len(free_times)}")
    
    def create_appointment(self):
        """Создаёт новую запись на приём"""
        # Проверяем выбор пациента
        if not self.patients_listbox.curselection():
            messagebox.showwarning("Предупреждение", "Выберите пациента из списка")
            return
        
        # Получаем ID пациента из выбранной строки
        patient_selection = self.patients_listbox.get(self.patients_listbox.curselection())
        try:
            patient_id = int(patient_selection.split(':')[0])
        except:
            messagebox.showerror("Ошибка", "Неверный формат данных пациента")
            return
        
        # Проверяем выбор врача
        if not self.doctor_combobox.get():
            messagebox.showwarning("Предупреждение", "Выберите врача")
            return
        
        # Получаем ID врача
        doctor_text = self.doctor_combobox.get()
        try:
            doctor_id = int(doctor_text.split(':')[0])
        except:
            messagebox.showerror("Ошибка", "Неверный формат данных врача")
            return
        
        # Проверяем выбор времени
        if not self.time_listbox.curselection():
            messagebox.showwarning("Предупреждение", "Выберите время из списка")
            return
        
        selected_time = self.time_listbox.get(self.time_listbox.curselection())
        if selected_time == "Нет свободного времени":
            messagebox.showwarning("Предупреждение", "Выберите другое время или дату")
            return
        
        # Получаем дату
        date = self.date_entry.get().strip()
        if not date:
            messagebox.showwarning("Предупреждение", "Введите дату")
            return
        
        # Создаём запись в БД
        appointment_id = db.add_appointment(patient_id, doctor_id, date, selected_time)
        
        if appointment_id:
            messagebox.showinfo("Успех", "Пациент успешно записан на приём")
            
            # Очищаем форму
            self.patient_search_entry.delete(0, tk.END)
            self.patients_listbox.delete(0, tk.END)
            self.time_listbox.delete(0, tk.END)
            
            # Обновляем список записей
            self.load_appointments()
            
            # Переключаемся на вкладку со списком записей
            # Индекс 3, потому что вкладки: 0-Пациенты, 1-Врачи, 2-Новая запись, 3-Все записи
            self.notebook.select(3)
            
            self.update_status("Создана новая запись на приём")
        else:
            messagebox.showerror("Ошибка", "Не удалось создать запись. Возможно, это время уже занято.")
    
    # ============================================
    # ВКЛАДКА "ВСЕ ЗАПИСИ"
    # ============================================
    
    def create_appointments_tab(self):
        """Создаёт вкладку со списком всех записей"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Все записи")
        
        # Верхняя панель с кнопками
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        # Кнопка обновления
        ttk.Button(
            top_frame, 
            text="🔄 Обновить", 
            command=self.load_appointments
        ).pack(side='left', padx=2)
        
        # Кнопка отмены записи
        ttk.Button(
            top_frame, 
            text="❌ Отменить выбранную запись", 
            command=self.cancel_selected_appointment
        ).pack(side='left', padx=2)
        
        # Таблица записей
        columns = ('id', 'Пациент', 'Полис', 'Врач', 'Специальность', 'Кабинет', 'Дата', 'Время', 'Статус')
        self.appointments_tree = ttk.Treeview(
            tab, 
            columns=columns, 
            show='headings', 
            height=20
        )
        
        # Настройка заголовков
        for col in columns:
            self.appointments_tree.heading(col, text=col)
        
        # Настройка ширины колонок
        widths = [50, 200, 100, 200, 120, 60, 80, 80, 100]
        for col, width in zip(columns, widths):
            self.appointments_tree.column(col, width=width)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(
            tab, 
            orient='vertical', 
            command=self.appointments_tree.yview
        )
        self.appointments_tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещаем
        self.appointments_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # Загружаем записи
        self.load_appointments()
    
    def load_appointments(self):
        """Загружает список всех записей в таблицу"""
        # Очищаем таблицу
        for row in self.appointments_tree.get_children():
            self.appointments_tree.delete(row)
        
        # Загружаем записи из БД
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
    
    def cancel_selected_appointment(self):
        """Отменяет выбранную запись"""
        # Получаем выбранную запись
        selection = self.appointments_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите запись для отмены")
            return
        
        # Получаем ID и имя пациента из выбранной строки
        item = self.appointments_tree.item(selection[0])
        appointment_id = item['values'][0]
        patient_name = item['values'][1]
        
        # Запрашиваем подтверждение
        if messagebox.askyesno("Подтверждение", f"Отменить запись пациента {patient_name}?"):
            db.cancel_appointment(appointment_id)
            self.load_appointments()  # Обновляем список
            self.update_status(f"Запись отменена")
    
    # ============================================
    # ДИАЛОГ "О ПРОГРАММЕ"
    # ============================================
    
    def show_about(self):
        """Показывает информацию о программе"""
        about_text = """🏥 Регистратура поликлиники
Версия 1.0

Программа для автоматизации работы регистратуры:
• Ведение базы пациентов
• Запись на приём к врачам
• Просмотр расписания

Разработано для курсовой работы
2026 год"""
        
        messagebox.showinfo("О программе", about_text)


# ============================================
# ТОЧКА ВХОДА (для самостоятельного запуска)
# ============================================

if __name__ == "__main__":
    print("Запуск программы регистратуры поликлиники...")
    
    # Инициализируем базу данных
    db.init_db()
    
    # Создаём главное окно
    root = tk.Tk()
    app = MainApplication(root)
    
    # Запускаем главный цикл обработки событий
    root.mainloop()