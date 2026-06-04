"""
Модуль с вкладками врачей (просмотр и админ).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class DoctorsTabMixin:
    """
    Миксин для вкладок врачей.
    """
    
    # ===========================================
    # ВКЛАДКА "ВРАЧИ" (для всех)
    # ===========================================
    
    def create_doctors_tab(self):
        """Создаёт вкладку со списком врачей (только просмотр)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Врачи (просмотр)")
        
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
            text="Список врачей доступен только для просмотра.",
            foreground='blue',
            font=('Arial', 9)
        )
        info_label.pack(side='bottom', pady=5)
    
    def load_doctors(self):
        """Загружает список врачей в таблицу"""
        import database as db
        
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
        """Загружает врачей в выпадающий список (только для регистратора и админа)"""
        import database as db
        
        try:
            doctors = db.get_all_doctors()
            
            # Для врача - показываем только его, для остальных - всех
            if self.user['role'] == 'doctor':
                # Находим врача, привязанного к пользователю
                doctor = db.get_doctor_by_user_id(self.user['id'])
                if doctor:
                    doctor_list = [f"{doctor['id']}: {doctor['full_name']} ({doctor['specialty']})"]
                    self.doctor_combobox['values'] = doctor_list
                    if doctor_list:
                        self.doctor_combobox.current(0)
                    self.doctor_combobox.config(state='disabled')
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
    
    # ===========================================
    # ВКЛАДКА "УПРАВЛЕНИЕ ВРАЧАМИ" (только для админа)
    # ===========================================
    
    def create_admin_doctors_tab(self):
        """Создаёт вкладку управления врачами (только для админа)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Управление врачами (админ)")
        
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            top_frame,
            text="Добавить врача",
            command=self.open_add_doctor_dialog,
            style='Admin.TButton'
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame,
            text="Редактировать",
            command=self.open_edit_doctor_dialog
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame,
            text="Удалить",
            command=self.delete_selected_doctor,
            style='Warning.TButton'
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame,
            text="Обновить",
            command=self.load_admin_doctors
        ).pack(side='left', padx=2)
        
        # Таблица врачей для админа
        columns = ('id', 'ФИО', 'Специальность', 'Кабинет')
        self.admin_doctors_tree = ttk.Treeview(
            tab, 
            columns=columns, 
            show='headings', 
            height=20
        )
        
        for col in columns:
            self.admin_doctors_tree.heading(col, text=col)
        
        widths = [50, 250, 150, 80]
        for col, width in zip(columns, widths):
            self.admin_doctors_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(
            tab, 
            orient='vertical', 
            command=self.admin_doctors_tree.yview
        )
        self.admin_doctors_tree.configure(yscrollcommand=scrollbar.set)
        
        self.admin_doctors_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        self.load_admin_doctors()
    
    def load_admin_doctors(self):
        """Загружает список врачей для админ-таблицы"""
        import database as db
        
        try:
            for row in self.admin_doctors_tree.get_children():
                self.admin_doctors_tree.delete(row)
            
            doctors = db.get_all_doctors()
            for doctor in doctors:
                self.admin_doctors_tree.insert('', 'end', values=(
                    doctor['id'],
                    doctor['full_name'],
                    doctor['specialty'] or '',
                    doctor['room_number'] or ''
                ))
        except Exception as e:
            self.update_status(f"Ошибка загрузки врачей: {e}")
    
    def open_add_doctor_dialog(self):
        """Открывает диалог добавления врача"""
        self.open_doctor_dialog(mode="add")
    
    def open_edit_doctor_dialog(self):
        """Открывает диалог редактирования врача"""
        import database as db
        
        selection = self.admin_doctors_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите врача для редактирования")
            return
        
        item = self.admin_doctors_tree.item(selection[0])
        doctor_id = item['values'][0]
        
        doctor = db.get_doctor_by_id(doctor_id)
        if doctor:
            self.open_doctor_dialog(mode="edit", doctor=doctor)
        else:
            messagebox.showerror("Ошибка", "Врач не найден")
    
    def delete_selected_doctor(self):
        """Удаляет выбранного врача"""
        import database as db
        
        selection = self.admin_doctors_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите врача для удаления")
            return
        
        item = self.admin_doctors_tree.item(selection[0])
        doctor_id = item['values'][0]
        doctor_name = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", 
                              f"Удалить врача {doctor_name}?\n\n"
                              "ВНИМАНИЕ:\n"
                              "Будут удалены все записи к этому врачу!"):
            
            try:
                # Проверяем, есть ли будущие записи у врача
                with db.get_connection() as conn:
                    cursor = conn.execute('''
                        SELECT COUNT(*) as count FROM appointments 
                        WHERE doctor_id = ? AND date >= date('now') AND status = 'запланирован'
                    ''', (doctor_id,))
                    result = cursor.fetchone()
                    
                    if result and result['count'] > 0:
                        if not messagebox.askyesno("Подтверждение", 
                                                 f"У врача есть {result['count']} будущих записей.\n"
                                                 "Они также будут удалены.\n\n"
                                                 "Продолжить?"):
                            return
                
                # Удаляем врача
                conn.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
                conn.commit()
                
                self.load_admin_doctors()
                self.load_doctors()  # Обновляем обычную таблицу врачей
                self.load_doctors_to_combobox()  # Обновляем выпадающий список
                self.update_status(f"Врач {doctor_name} удалён")
                messagebox.showinfo("Успех", "Врач удалён")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить врача: {e}")
                db.log_action("DELETE_DOCTOR_ERROR", f"Error deleting doctor {doctor_id}: {str(e)}")
    
    def open_doctor_dialog(self, mode="add", doctor=None):
        """
        Диалог для добавления/редактирования врача.
        
        Args:
            mode (str): "add" или "edit"
            doctor: данные врача (для edit)
        """
        import database as db
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование врача" if mode == "edit" else "Добавление врача")
        dialog.geometry("600x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Заголовок
        ttk.Label(
            dialog, 
            text="Данные врача", 
            font=('Arial', 12, 'bold')
        ).grid(row=0, column=0, columnspan=3, pady=10)
        
        # ФИО
        ttk.Label(dialog, text="ФИО", font=('Arial', 10)).grid(
            row=1, column=0, padx=10, pady=10, sticky='w'
        )
        
        name_frame = ttk.Frame(dialog)
        name_frame.grid(row=1, column=1, padx=10, pady=10, sticky='w')
        
        # Валидация для ФИО (только буквы, пробелы, дефис, точка)
        vcmd_name = (dialog.register(self.validate_doctor_name), '%P')
        name_entry = ttk.Entry(
            name_frame, 
            width=40, 
            validate='key', 
            validatecommand=vcmd_name
        )
        name_entry.pack(side='left')
        name_entry.focus()
        
        ttk.Label(
            name_frame, 
            text="(только буквы, пробелы, дефис, точка)", 
            foreground='gray', 
            font=('Arial', 8)
        ).pack(side='left', padx=5)
        
        # Специальность
        ttk.Label(dialog, text="Специальность", font=('Arial', 10)).grid(
            row=2, column=0, padx=10, pady=10, sticky='w'
        )
        
        specialty_frame = ttk.Frame(dialog)
        specialty_frame.grid(row=2, column=1, padx=10, pady=10, sticky='w')
        
        # Валидация для специальности (только буквы, пробелы, дефис)
        vcmd_specialty = (dialog.register(self.validate_specialty), '%P')
        specialty_entry = ttk.Entry(
            specialty_frame, 
            width=40, 
            validate='key', 
            validatecommand=vcmd_specialty
        )
        specialty_entry.pack(side='left')
        
        ttk.Label(
            specialty_frame, 
            text="(только буквы, пробелы, дефис)", 
            foreground='gray', 
            font=('Arial', 8)
        ).pack(side='left', padx=5)
        
        # Кабинет
        ttk.Label(dialog, text="Кабинет", font=('Arial', 10)).grid(
            row=3, column=0, padx=10, pady=10, sticky='w'
        )
        
        room_frame = ttk.Frame(dialog)
        room_frame.grid(row=3, column=1, padx=10, pady=10, sticky='w')
        
        # Валидация для кабинета (цифры и буквы)
        vcmd_room = (dialog.register(self.validate_room_number), '%P')
        room_entry = ttk.Entry(
            room_frame, 
            width=20, 
            validate='key', 
            validatecommand=vcmd_room
        )
        room_entry.pack(side='left')
        
        ttk.Label(
            room_frame, 
            text="(цифры и буквы, например: 101, 12А)", 
            foreground='gray', 
            font=('Arial', 8)
        ).pack(side='left', padx=5)
        
        # Счетчик символов для ФИО
        name_counter = ttk.Label(
            dialog, 
            text="0/100", 
            foreground='gray', 
            font=('Arial', 8)
        )
        name_counter.grid(row=1, column=2, padx=5, sticky='w')
        
        def update_name_counter(*args):
            length = len(name_entry.get())
            name_counter.config(text=f"{length}/100")
            if length > 100:
                name_counter.config(foreground='red')
            elif length >= 2:
                name_counter.config(foreground='green')
            else:
                name_counter.config(foreground='gray')
        
        name_entry.bind('<KeyRelease>', update_name_counter)
        
        # Счетчик символов для специальности
        specialty_counter = ttk.Label(
            dialog, 
            text="0/50", 
            foreground='gray', 
            font=('Arial', 8)
        )
        specialty_counter.grid(row=2, column=2, padx=5, sticky='w')
        
        def update_specialty_counter(*args):
            length = len(specialty_entry.get())
            specialty_counter.config(text=f"{length}/50")
            if length > 50:
                specialty_counter.config(foreground='red')
            elif length >= 2:
                specialty_counter.config(foreground='green')
            else:
                specialty_counter.config(foreground='gray')
        
        specialty_entry.bind('<KeyRelease>', update_specialty_counter)
        
        # Метка для ошибок
        error_label = ttk.Label(
            dialog,
            text="",
            foreground='red',
            font=('Arial', 9)
        )
        error_label.grid(row=4, column=0, columnspan=3, pady=5)
        
        # Если режим редактирования - заполняем поля
        if mode == "edit" and doctor:
            name_entry.insert(0, doctor['full_name'] or '')
            specialty_entry.insert(0, doctor['specialty'] or '')
            room_entry.insert(0, doctor['room_number'] or '')
            update_name_counter()
            update_specialty_counter()
        
        # Информация о безопасности
        security_label = ttk.Label(
            dialog, 
            text="✓ Данные проверяются: буквы в ФИО и специальности, буквы/цифры в кабинете",
            foreground='green',
            font=('Arial', 9)
        )
        security_label.grid(row=5, column=0, columnspan=3, pady=10)
        
        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        def save_doctor():
            # Очищаем сообщение об ошибке
            error_label.config(text="")
            
            name = name_entry.get().strip()
            specialty = specialty_entry.get().strip()
            room = room_entry.get().strip()
            
            # Проверка обязательных полей
            if not name:
                error_label.config(text="Ошибка: ФИО обязательно для заполнения")
                name_entry.focus()
                return
            
            if not specialty:
                error_label.config(text="Ошибка: Специальность обязательна для заполнения")
                specialty_entry.focus()
                return
            
            # Проверка минимальной длины
            if len(name) < 2:
                error_label.config(text="Ошибка: ФИО должно содержать минимум 2 символа")
                name_entry.focus()
                return
            
            if len(specialty) < 2:
                error_label.config(text="Ошибка: Специальность должна содержать минимум 2 символа")
                specialty_entry.focus()
                return
            
            # Проверка максимальной длины
            if len(name) > 100:
                error_label.config(text="Ошибка: ФИО слишком длинное (максимум 100 символов)")
                name_entry.focus()
                return
            
            if len(specialty) > 50:
                error_label.config(text="Ошибка: Специальность слишком длинная (максимум 50 символов)")
                specialty_entry.focus()
                return
            
            # Проверка кабинета на уникальность
            if room:
                if len(room) > 10:
                    error_label.config(text="Ошибка: Номер кабинета слишком длинный (максимум 10 символов)")
                    room_entry.focus()
                    return
                
                # Проверяем, не занят ли кабинет
                if mode == "add":
                    is_unique, msg = db.check_room_unique(room)
                else:
                    is_unique, msg = db.check_room_unique(room, doctor['id'])
                
                if not is_unique:
                    error_label.config(text=msg)
                    room_entry.focus()
                    return
            
            try:
                if mode == "add":
                    with db.get_connection() as conn:
                        cursor = conn.execute('''
                            INSERT INTO doctors (full_name, specialty, room_number)
                            VALUES (?, ?, ?)
                        ''', (name, specialty, room if room else None))
                        conn.commit()
                        doctor_id = cursor.lastrowid
                    
                    messagebox.showinfo("Успех", f"Врач добавлен (ID: {doctor_id})")
                    db.log_action("ADD_DOCTOR", f"Added doctor ID:{doctor_id}, name:{name}")
                else:
                    with db.get_connection() as conn:
                        conn.execute('''
                            UPDATE doctors 
                            SET full_name = ?, specialty = ?, room_number = ?
                            WHERE id = ?
                        ''', (name, specialty, room if room else None, doctor['id']))
                        conn.commit()
                    
                    messagebox.showinfo("Успех", "Данные врача обновлены")
                    db.log_action("UPDATE_DOCTOR", f"Updated doctor ID:{doctor['id']}")
                
                # Обновляем все таблицы с врачами
                self.load_admin_doctors()
                self.load_doctors()
                self.load_doctors_to_combobox()
                dialog.destroy()
                self.update_status(f"Врач {name} сохранён")
            except Exception as e:
                error_label.config(text=f"Ошибка: {str(e)}")
                db.log_action("DOCTOR_ERROR", f"Error saving doctor: {str(e)}")
        
        ttk.Button(
            button_frame, 
            text="Сохранить", 
            command=save_doctor, 
            width=15
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, 
            text="Отмена", 
            command=dialog.destroy, 
            width=15
        ).pack(side='left', padx=5)