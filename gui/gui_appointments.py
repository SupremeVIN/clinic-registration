"""
Модуль с вкладками записей (новая запись и все записи).
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from gui.gui_datepicker import DatePicker

class AppointmentsTabMixin:
    """
    Миксин для вкладок записей на прием.
    """
    
    # ===========================================
    # ВКЛАДКА "НОВАЯ ЗАПИСЬ"
    # ===========================================
    
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
        ttk.Label(main_frame, text="Дата приёма:", font=('Arial', 11)).grid(
            row=5, column=0, sticky='w', pady=5
        )
        
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=5, column=1, sticky='w', pady=5)
        
        self.date_entry = ttk.Entry(date_frame, width=15)
        self.date_entry.pack(side='left', padx=2)
        
        # Устанавливаем сегодняшнюю дату
        today = datetime.now().strftime('%Y-%m-%d')
        self.date_entry.insert(0, today)
        
        ttk.Button(
            date_frame, 
            text="📅", 
            width=3,
            command=lambda: self.show_date_picker(
                tab,
                self.date_entry,
                min_date=datetime.now().date()
            )
        ).pack(side='left', padx=2)
        
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
        import database as db
        
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
    
    def load_doctors_to_combobox(self):
        """Загружает врачей в выпадающий список"""
        import database as db
        
        try:
            doctors = db.get_all_doctors()
            
            # Если пользователь врач - показываем только его
            if self.user['role'] == 'doctor':
                # Находим врача, привязанного к пользователю
                doctor = db.get_doctor_by_user_id(self.user['id'])
                if doctor:
                    doctor_list = [f"{doctor['id']}: {doctor['full_name']} ({doctor['specialty']})"]
                    self.doctor_combobox['values'] = doctor_list
                    if doctor_list:
                        self.doctor_combobox.current(0)
                    self.doctor_combobox.config(state='readonly')
                    self.doctor_combobox.config(state='disabled')  # Делаем недоступным для выбора (только один вариант)
                else:
                    self.doctor_combobox['values'] = []
                    self.doctor_combobox.config(state='disabled')
                    messagebox.showwarning("Предупреждение", "Ваша учетная запись не привязана к врачу. Обратитесь к администратору.")
            else:
                # Для админа и регистратора - все врачи
                doctor_list = [f"{d['id']}: {d['full_name']} ({d['specialty']})" for d in doctors]
                self.doctor_combobox['values'] = doctor_list
                if doctor_list:
                    self.doctor_combobox.current(0)
                self.doctor_combobox.config(state='readonly')
        except Exception as e:
            self.update_status(f"Ошибка загрузки врачей: {e}")
    
    def show_free_time(self):
        """Показывает свободное время"""
        import database as db
        
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
        
        # Проверяем формат даты
        try:
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Ошибка", 
                               f"Неверный формат даты!\n\n"
                               f"Введено: {date}\n"
                               f"Ожидается формат: ГГГГ-ММ-ДД\n"
                               f"Например: 2026-06-03")
            return
        
        # Проверяем, что дата не в прошлом
        if selected_date < datetime.now().date():
            messagebox.showwarning("Предупреждение", "Нельзя выбрать дату в прошлом")
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
        import database as db
        
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
        
        # Проверяем формат даты перед отправкой в БД
        try:
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Ошибка", 
                               f"Неверный формат даты!\n\n"
                               f"Введено: {date}\n"
                               f"Ожидается формат: ГГГГ-ММ-ДД\n"
                               f"Например: 2026-06-03")
            return
        
        # Проверяем, что дата не в прошлом
        if selected_date < datetime.now().date():
            messagebox.showwarning("Предупреждение", "Нельзя записаться на прошедшую дату")
            return
        
        created_by = f"{self.user['name']} ({self.user['role']})"
        appointment_id = db.add_appointment(self.selected_patient_id, doctor_id, date, self.selected_time, created_by)
        
        if appointment_id:
            messagebox.showinfo("Успех", "Пациент успешно записан на приём")
            self.clear_appointment_form()
            self.load_appointments()
            self.load_stats()
            self.notebook.select(4)  # Переключаемся на вкладку "Все записи"
            self.update_status("Создана новая запись")
        else:
            messagebox.showerror("Ошибка", 
                               "Не удалось создать запись.\n\n"
                               "Возможные причины:\n"
                               "• Это время уже занято\n"
                               "• Неверный формат даты\n"
                               "• Дата уже прошла\n\n"
                               "Проверьте правильность введенных данных.")
    
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
    
    # ===========================================
    # ВКЛАДКА "ВСЕ ЗАПИСИ"
    # ===========================================
    
    def create_appointments_tab(self):
        """Создаёт вкладку со списком всех записей"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Все записи")
        
        # Верхняя панель с кнопками
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        # Кнопки управления
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
        
        # Панель фильтрации
        filter_frame = ttk.LabelFrame(tab, text="Фильтр", padding=5)
        filter_frame.pack(fill='x', padx=5, pady=5)
        
        # Поиск по ФИО/полису
        ttk.Label(filter_frame, text="Поиск:").pack(side='left', padx=2)
        self.appointment_search_var = tk.StringVar()
        self.appointment_search_var.trace('w', lambda *args: self.search_appointments())
        ttk.Entry(
            filter_frame, 
            textvariable=self.appointment_search_var, 
            width=30
        ).pack(side='left', padx=2)
        
        # Фильтр по статусу
        ttk.Label(filter_frame, text="Статус:").pack(side='left', padx=(10,2))
        self.status_filter_var = tk.StringVar(value='все')
        status_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.status_filter_var,
            values=['все', 'запланирован', 'отменён'],
            state='readonly',
            width=12
        )
        status_combo.pack(side='left', padx=2)
        status_combo.bind('<<ComboboxSelected>>', lambda e: self.load_appointments())
        
        # Фильтр по дате
        ttk.Label(filter_frame, text="Дата от:").pack(side='left', padx=(10,2))
        self.date_from_entry = ttk.Entry(filter_frame, width=12)
        self.date_from_entry.pack(side='left', padx=2)
        ttk.Button(
            filter_frame,
            text="📅",
            width=3,
            command=lambda: self.show_date_picker(tab, self.date_from_entry)
        ).pack(side='left', padx=2)
        
        ttk.Label(filter_frame, text="до:").pack(side='left', padx=2)
        self.date_to_entry = ttk.Entry(filter_frame, width=12)
        self.date_to_entry.pack(side='left', padx=2)
        ttk.Button(
            filter_frame,
            text="📅",
            width=3,
            command=lambda: self.show_date_picker(tab, self.date_to_entry)
        ).pack(side='left', padx=2)
        
        ttk.Button(
            filter_frame,
            text="Применить фильтр",
            command=self.load_appointments
        ).pack(side='left', padx=10)
        
        ttk.Button(
            filter_frame,
            text="Сбросить",
            command=self.reset_filters
        ).pack(side='left', padx=2)
        
        # Кнопка для быстрого просмотра записей на сегодня
        ttk.Button(
            filter_frame,
            text="📅 Сегодня",
            command=self.show_today_appointments
        ).pack(side='right', padx=2)
        
        # Таблица записей - увеличиваем ширину колонки "Причина отмены"
        columns = ('id', 'Пациент', 'Полис', 'Врач', 'Специальность', 'Кабинет', 'Дата', 'Время', 'Статус', 'Кто создал', 'Причина отмены')
        self.appointments_tree = ttk.Treeview(
            tab, 
            columns=columns, 
            show='headings', 
            height=15
        )
        
        for col in columns:
            self.appointments_tree.heading(col, text=col)
        
        # Увеличиваем ширину для причины отмены
        widths = [50, 200, 100, 200, 120, 60, 80, 80, 100, 150, 300]
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
    
    def reset_filters(self):
        """Сбрасывает все фильтры"""
        self.appointment_search_var.set('')
        self.status_filter_var.set('все')
        self.date_from_entry.delete(0, tk.END)
        self.date_to_entry.delete(0, tk.END)
        self.load_appointments()
    
    def show_today_appointments(self):
        """Показывает записи на сегодня"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.date_from_entry.delete(0, tk.END)
        self.date_from_entry.insert(0, today)
        self.date_to_entry.delete(0, tk.END)
        self.date_to_entry.insert(0, today)
        self.load_appointments()
    
    def search_appointments(self):
        """Поиск записей по ФИО или полису"""
        import database as db
        
        search_text = self.appointment_search_var.get().strip()
        
        if len(search_text) < 2:
            self.load_appointments()
            return
        
        try:
            # Если пользователь врач - фильтруем по его ID
            doctor_id = None
            if self.user['role'] == 'doctor':
                doctor = db.get_doctor_by_user_id(self.user['id'])
                if doctor:
                    doctor_id = doctor['id']
            
            appointments = db.search_appointments(search_text, doctor_id)
            
            for row in self.appointments_tree.get_children():
                self.appointments_tree.delete(row)
            
            for apt in appointments:
                cancel_reason = apt['cancel_reason'] or ''
                created_by = apt['created_by'] or ''
                
                tag = 'cancelled' if apt['status'] == 'отменён' else ''
                
                self.appointments_tree.insert('', 'end', values=(
                    apt['id'],
                    apt['patient_name'],
                    apt['policy_number'] or '',
                    apt['doctor_name'],
                    apt['specialty'] or '',
                    apt['room_number'] or '',
                    apt['date'],
                    apt['time'],
                    apt['status'],
                    created_by,
                    cancel_reason
                ), tags=(tag,))
            
            self.appointments_tree.tag_configure('cancelled', foreground='red')
            self.update_status(f"Найдено {len(appointments)} записей")
        except Exception as e:
            self.update_status(f"Ошибка поиска: {e}")
    
    def load_appointments(self):
        """Загружает список записей с применением фильтров"""
        import database as db
        
        try:
            for row in self.appointments_tree.get_children():
                self.appointments_tree.delete(row)
            
            # Применяем фильтры
            status = None
            if self.status_filter_var.get() != 'все':
                status = self.status_filter_var.get()
            
            date_from = self.date_from_entry.get().strip() or None
            date_to = self.date_to_entry.get().strip() or None
            
            # Если пользователь врач - показываем только его записи
            doctor_id = None
            if self.user['role'] == 'doctor':
                doctor = db.get_doctor_by_user_id(self.user['id'])
                if doctor:
                    doctor_id = doctor['id']
            
            appointments = db.get_all_appointments(doctor_id=doctor_id, status=status, date_from=date_from, date_to=date_to)
            
            for apt in appointments:
                cancel_reason = apt['cancel_reason'] or ''
                created_by = apt['created_by'] or ''
                
                # Для отмененных записей выделяем красным
                tag = 'cancelled' if apt['status'] == 'отменён' else ''
                
                self.appointments_tree.insert('', 'end', values=(
                    apt['id'],
                    apt['patient_name'],
                    apt['policy_number'] or '',
                    apt['doctor_name'],
                    apt['specialty'] or '',
                    apt['room_number'] or '',
                    apt['date'],
                    apt['time'],
                    apt['status'],
                    created_by,
                    cancel_reason
                ), tags=(tag,))
            
            # Настройка цветов
            self.appointments_tree.tag_configure('cancelled', foreground='red')
            
            self.update_status(f"Загружено {len(appointments)} записей")
        except Exception as e:
            self.update_status(f"Ошибка загрузки: {e}")
    
    def cancel_selected_appointment(self):
        """Отменяет выбранную запись"""
        import database as db
        
        selection = self.appointments_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите запись для отмены")
            return
        
        item = self.appointments_tree.item(selection[0])
        appointment_id = item['values'][0]
        patient_name = item['values'][1]
        date = item['values'][6]
        time = item['values'][7]
        status = item['values'][8]
        
        if status == 'отменён':
            messagebox.showinfo("Информация", "Эта запись уже отменена")
            return
        
        if messagebox.askyesno("Подтверждение", 
                              f"Отменить запись?\n\n"
                              f"Пациент: {patient_name}\n"
                              f"Дата: {date}\n"
                              f"Время: {time}"):
            
            reason = None
            if messagebox.askyesno("Причина отмены", "Указать причину отмены?"):
                reason = self.ask_cancel_reason()
            
            cancelled_by = f"{self.user['name']} ({self.user['role']})"
            
            if db.cancel_appointment(appointment_id, reason, cancelled_by):
                self.load_appointments()
                self.update_status(f"Запись отменена пользователем {cancelled_by}")
                messagebox.showinfo("Успех", "Запись отменена")
            else:
                messagebox.showerror("Ошибка", "Не удалось отменить запись")
    
    def ask_cancel_reason(self):
        """Запрашивает причину отмены"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Причина отмены")
        dialog.geometry("450x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Укажите причину отмены:", font=('Arial', 10)).pack(pady=10)
        
        reason_var = tk.StringVar()
        reason_entry = ttk.Entry(dialog, textvariable=reason_var, width=50)
        reason_entry.pack(pady=10, padx=20, fill='x')
        reason_entry.focus()
        
        ttk.Label(dialog, text="(максимум 200 символов)", foreground='gray', font=('Arial', 8)).pack()
        
        result = None
        
        def on_ok():
            nonlocal result
            result = reason_var.get().strip()
            if len(result) > 200:
                messagebox.showwarning("Предупреждение", "Причина отмены не должна превышать 200 символов")
                return
            dialog.destroy()
        
        def on_skip():
            nonlocal result
            result = None
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=15)
        
        ttk.Button(button_frame, text="OK", command=on_ok, width=12).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Пропустить", command=on_skip, width=12).pack(side='left', padx=5)
        
        dialog.wait_window()
        return result
    
    def delete_old_appointments(self):
        """Удаляет старые записи"""
        import database as db
        
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