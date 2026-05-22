"""
Модуль с вкладками записей (новая запись и все записи).
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
            text="", 
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
        
        # Проверяем, что дата не в прошлом
        try:
            selected_date = datetime.strptime(date, '%Y-%m-%d').date()
            if selected_date < datetime.now().date():
                messagebox.showwarning("Предупреждение", "Нельзя выбрать дату в прошлом")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты")
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
        
        appointment_id = db.add_appointment(self.selected_patient_id, doctor_id, date, self.selected_time)
        
        if appointment_id:
            messagebox.showinfo("Успех", "Пациент успешно записан на приём")
            self.clear_appointment_form()
            self.load_appointments()
            self.load_stats()
            self.notebook.select(4)  # Переключаемся на вкладку "Все записи"
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
    
    # ===========================================
    # ВКЛАДКА "ВСЕ ЗАПИСИ"
    # ===========================================
    
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
        import database as db
        
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