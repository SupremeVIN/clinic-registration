"""
Модуль с вкладкой управления пациентами.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from gui.gui_datepicker import DatePicker

class PatientsTabMixin:
    """
    Миксин для вкладки пациентов.
    """
    
    # ===========================================
    # ВКЛАДКА "ПАЦИЕНТЫ"
    # ===========================================
    
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
    
    def load_patients(self):
        """Загружает список пациентов в таблицу"""
        import database as db
        
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
        import database as db
        
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
        import database as db
        
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
        import database as db
        
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
        import database as db
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование пациента" if mode == "edit" else "Добавление пациента")
        dialog.geometry("600x480")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Заголовок с информацией об обязательных полях
        header_label = ttk.Label(
            dialog,
            text="Все поля обязательны для заполнения",
            font=('Arial', 9, 'italic'),
            foreground='gray'
        )
        header_label.grid(row=0, column=0, columnspan=3, pady=(10, 0))
        
        # ФИО
        ttk.Label(dialog, text="ФИО", font=('Arial', 10)).grid(
            row=1, column=0, padx=10, pady=10, sticky='w'
        )
        
        name_frame = ttk.Frame(dialog)
        name_frame.grid(row=1, column=1, padx=10, pady=10, sticky='w')
        
        vcmd_name = (dialog.register(self.validate_letters_only), '%P')
        name_entry = ttk.Entry(name_frame, width=40, validate='key', validatecommand=vcmd_name)
        name_entry.pack(side='left')
        name_entry.focus()
        
        ttk.Label(name_frame, text="(только буквы)", foreground='gray', font=('Arial', 8)).pack(side='left', padx=5)
        
        # Дата рождения
        ttk.Label(dialog, text="Дата рождения", font=('Arial', 10)).grid(
            row=2, column=0, padx=10, pady=10, sticky='w'
        )
        
        birth_frame = ttk.Frame(dialog)
        birth_frame.grid(row=2, column=1, padx=10, pady=10, sticky='w')
        
        birth_entry = ttk.Entry(birth_frame, width=15)
        birth_entry.pack(side='left')
        
        ttk.Button(
            birth_frame,
            text="📅",
            width=3,
            command=lambda: self.show_date_picker(
                dialog, 
                birth_entry,
                max_date=datetime.now().date()
            )
        ).pack(side='left', padx=5)
        
        ttk.Label(birth_frame, text="ГГГГ-ММ-ДД", foreground='gray', font=('Arial', 8)).pack(side='left')
        
        # Телефон
        ttk.Label(dialog, text="Телефон", font=('Arial', 10)).grid(
            row=3, column=0, padx=10, pady=10, sticky='w'
        )
        
        phone_frame = ttk.Frame(dialog)
        phone_frame.grid(row=3, column=1, padx=10, pady=10, sticky='w')
        
        vcmd_phone = (dialog.register(self.validate_phone_chars), '%P')
        phone_entry = ttk.Entry(phone_frame, width=30, validate='key', validatecommand=vcmd_phone)
        phone_entry.pack(side='left')
        
        ttk.Label(phone_frame, text="+7 (999) 123-45-67", foreground='gray', font=('Arial', 8)).pack(side='left', padx=5)
        
        # Номер полиса
        ttk.Label(dialog, text="Номер полиса", font=('Arial', 10)).grid(
            row=4, column=0, padx=10, pady=10, sticky='w'
        )
        
        policy_frame = ttk.Frame(dialog)
        policy_frame.grid(row=4, column=1, padx=10, pady=10, sticky='w')
        
        vcmd_policy = (dialog.register(self.validate_digits_only), '%P')
        policy_entry = ttk.Entry(
            policy_frame, 
            width=20,
            validate='key', 
            validatecommand=vcmd_policy
        )
        policy_entry.pack(side='left')
        
        policy_counter = ttk.Label(policy_frame, text="0/16", foreground='gray', font=('Arial', 8))
        policy_counter.pack(side='left', padx=5)
        
        def update_policy_counter(*args):
            length = len(policy_entry.get())
            policy_counter.config(text=f"{length}/16")
            if length == 16:
                policy_counter.config(foreground='green')
            else:
                policy_counter.config(foreground='gray')
        
        policy_entry.bind('<KeyRelease>', update_policy_counter)
        
        if mode == "edit" and patient:
            name_entry.insert(0, patient['full_name'] or '')
            birth_entry.insert(0, patient['birth_date'] or '')
            phone_entry.insert(0, patient['phone'] or '')
            policy_entry.insert(0, patient['policy_number'] or '')
            policy_entry.config(state='disabled')
            update_policy_counter()
        
        # Метка для отображения ошибок валидации
        error_label = ttk.Label(
            dialog,
            text="",
            foreground='red',
            font=('Arial', 9)
        )
        error_label.grid(row=5, column=0, columnspan=2, pady=5)
        
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        def save_patient():
            # Очищаем сообщение об ошибке
            error_label.config(text="")
            
            name = name_entry.get().strip()
            birth = birth_entry.get().strip()
            phone = phone_entry.get().strip()
            policy = policy_entry.get().strip()
            
            # Проверка ФИО
            if not name:
                error_label.config(text="Ошибка: ФИО обязательно для заполнения")
                name_entry.focus()
                return
            
            if len(name) < 2:
                error_label.config(text="Ошибка: ФИО должно содержать минимум 2 символа")
                name_entry.focus()
                return
            
            # Проверка даты рождения
            if not birth:
                error_label.config(text="Ошибка: Дата рождения обязательна для заполнения")
                birth_entry.focus()
                return
            
            try:
                birth_date = datetime.strptime(birth, '%Y-%m-%d').date()
                # Проверка, что дата рождения не в будущем
                if birth_date > datetime.now().date():
                    error_label.config(text="Ошибка: Дата рождения не может быть в будущем")
                    birth_entry.focus()
                    return
                # Проверка, что пациенту не больше 150 лет
                if birth_date < datetime.now().replace(year=datetime.now().year - 150).date():
                    error_label.config(text="Ошибка: Слишком старая дата рождения (максимум 150 лет)")
                    birth_entry.focus()
                    return
            except ValueError:
                error_label.config(text="Ошибка: Неверный формат даты рождения (ГГГГ-ММ-ДД)")
                birth_entry.focus()
                return
            
            # Проверка телефона
            if not phone:
                error_label.config(text="Ошибка: Номер телефона обязателен для заполнения")
                phone_entry.focus()
                return
            
            # Очистка телефона от лишних символов для проверки длины
            import re
            phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone)
            if len(phone_clean) < 10:
                error_label.config(text="Ошибка: Номер телефона слишком короткий (минимум 10 цифр)")
                phone_entry.focus()
                return
            
            if len(phone_clean) > 15:
                error_label.config(text="Ошибка: Номер телефона слишком длинный (максимум 15 цифр)")
                phone_entry.focus()
                return
            
            # Проверка полиса (только для добавления нового пациента)
            if mode == "add":
                if not policy:
                    error_label.config(text="Ошибка: Номер полиса обязателен для заполнения")
                    policy_entry.focus()
                    return
                
                if len(policy) != 16:
                    error_label.config(text="Ошибка: Номер полиса должен содержать ровно 16 цифр")
                    policy_entry.focus()
                    return
            
            # Если все проверки пройдены, сохраняем
            if mode == "add":
                patient_id = db.add_patient(name, birth, phone, policy)
                if patient_id:
                    messagebox.showinfo("Успех", f"Пациент добавлен (ID: {patient_id})")
                    self.load_patients()
                    self.load_stats()
                    dialog.destroy()
                    self.update_status(f"Добавлен пациент: {name}")
                else:
                    error_label.config(text="Ошибка: Не удалось добавить пациента. Возможно, такой номер полиса уже существует.")
                    policy_entry.focus()
            else:
                if db.update_patient(patient['id'], name, birth, phone, policy):
                    messagebox.showinfo("Успех", "Данные пациента обновлены")
                    self.load_patients()
                    dialog.destroy()
                    self.update_status(f"Обновлён пациент: {name}")
                else:
                    error_label.config(text="Ошибка: Не удалось обновить данные пациента")
        
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