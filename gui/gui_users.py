"""
Модуль с вкладкой управления пользователями (только для администратора).
"""

import tkinter as tk
from tkinter import ttk, messagebox

class UsersTabMixin:
    """
    Миксин для вкладки управления пользователями.
    """
    
    def create_users_tab(self):
        """Создаёт вкладку управления пользователями (только для админа)"""
        if self.user['role'] != 'admin':
            return
        
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Пользователи (админ)")
        
        top_frame = ttk.Frame(tab)
        top_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            top_frame,
            text="Добавить пользователя",
            command=self.open_add_user_dialog,
            style='Admin.TButton'
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame,
            text="Сбросить пароль",
            command=self.reset_user_password
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame,
            text="Удалить",
            command=self.delete_selected_user,
            style='Warning.TButton'
        ).pack(side='left', padx=2)
        
        ttk.Button(
            top_frame,
            text="Обновить",
            command=self.load_users
        ).pack(side='left', padx=2)
        
        # Таблица пользователей
        columns = ('id', 'Логин', 'ФИО', 'Роль', 'Дата создания')
        self.users_tree = ttk.Treeview(
            tab, 
            columns=columns, 
            show='headings', 
            height=20
        )
        
        for col in columns:
            self.users_tree.heading(col, text=col)
        
        widths = [50, 150, 250, 120, 150]
        for col, width in zip(columns, widths):
            self.users_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(
            tab, 
            orient='vertical', 
            command=self.users_tree.yview
        )
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        self.users_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        self.load_users()
    
    def load_users(self):
        """Загружает список пользователей"""
        import database as db
        
        try:
            for row in self.users_tree.get_children():
                self.users_tree.delete(row)
            
            users = db.get_all_users()
            role_names = {
                'admin': 'Администратор',
                'registrar': 'Регистратор',
                'doctor': 'Врач'
            }
            
            for user in users:
                self.users_tree.insert('', 'end', values=(
                    user['id'],
                    user['username'],
                    user['full_name'],
                    role_names.get(user['role'], user['role']),
                    user['created_at']
                ))
            
            self.update_status(f"Загружено {len(users)} пользователей")
        except Exception as e:
            self.update_status(f"Ошибка загрузки: {e}")
    
    def open_add_user_dialog(self):
        """Открывает диалог добавления пользователя"""
        import database as db
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление пользователя")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Используем grid для основной формы
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Форма
        ttk.Label(main_frame, text="Логин:", font=('Arial', 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky='w'
        )
        username_entry = ttk.Entry(main_frame, width=30)
        username_entry.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        
        ttk.Label(main_frame, text="ФИО:", font=('Arial', 10)).grid(
            row=1, column=0, padx=10, pady=10, sticky='w'
        )
        fullname_entry = ttk.Entry(main_frame, width=30)
        fullname_entry.grid(row=1, column=1, padx=10, pady=10, sticky='w')
        
        # Валидация для ФИО (только буквы, пробелы, дефис, точка)
        vcmd_name = (dialog.register(self.validate_doctor_name), '%P')
        fullname_entry.config(validate='key', validatecommand=vcmd_name)
        
        ttk.Label(main_frame, text="Роль:", font=('Arial', 10)).grid(
            row=2, column=0, padx=10, pady=10, sticky='w'
        )
        role_var = tk.StringVar(value='registrar')
        role_combo = ttk.Combobox(
            main_frame,
            textvariable=role_var,
            values=['registrar', 'doctor'],
            state='readonly',
            width=27
        )
        role_combo.grid(row=2, column=1, padx=10, pady=10, sticky='w')
        
        # Фрейм для дополнительных полей (будет показан только для врача)
        extra_frame = ttk.LabelFrame(main_frame, text="Данные врача", padding=10)
        extra_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='ew')
        extra_frame.grid_remove()  # Скрываем по умолчанию
        
        # Поля для врача
        ttk.Label(extra_frame, text="Специальность:", font=('Arial', 10)).grid(
            row=0, column=0, padx=10, pady=10, sticky='w'
        )
        specialty_entry = ttk.Entry(extra_frame, width=30)
        specialty_entry.grid(row=0, column=1, padx=10, pady=10, sticky='w')
        
        # Валидация для специальности (только буквы, пробелы, дефис)
        vcmd_specialty = (dialog.register(self.validate_specialty), '%P')
        specialty_entry.config(validate='key', validatecommand=vcmd_specialty)
        
        ttk.Label(extra_frame, text="Кабинет:", font=('Arial', 10)).grid(
            row=1, column=0, padx=10, pady=10, sticky='w'
        )
        room_entry = ttk.Entry(extra_frame, width=30)
        room_entry.grid(row=1, column=1, padx=10, pady=10, sticky='w')
        
        # Валидация для кабинета (цифры и буквы)
        vcmd_room = (dialog.register(self.validate_room_number), '%P')
        room_entry.config(validate='key', validatecommand=vcmd_room)
        
        # Метка для проверки уникальности кабинета
        room_status_label = ttk.Label(extra_frame, text="", foreground='gray', font=('Arial', 8))
        room_status_label.grid(row=2, column=1, padx=10, pady=2, sticky='w')
        
        # Функция проверки кабинета в реальном времени
        def check_room_status(*args):
            room = room_entry.get().strip()
            if room:
                is_unique, msg = db.check_room_unique(room)
                if is_unique:
                    room_status_label.config(text="✓ Кабинет свободен", foreground='green')
                else:
                    room_status_label.config(text=f"✗ {msg}", foreground='red')
            else:
                room_status_label.config(text="")
        
        room_entry.bind('<KeyRelease>', check_room_status)
        
        # Пароль
        ttk.Label(main_frame, text="Пароль:", font=('Arial', 10)).grid(
            row=4, column=0, padx=10, pady=10, sticky='w'
        )
        password_entry = ttk.Entry(main_frame, width=30, show='•')
        password_entry.grid(row=4, column=1, padx=10, pady=10, sticky='w')
        
        # Подтверждение пароля
        ttk.Label(main_frame, text="Подтверждение пароля:", font=('Arial', 10)).grid(
            row=5, column=0, padx=10, pady=10, sticky='w'
        )
        confirm_password_entry = ttk.Entry(main_frame, width=30, show='•')
        confirm_password_entry.grid(row=5, column=1, padx=10, pady=10, sticky='w')
        
        error_label = ttk.Label(main_frame, text="", foreground='red')
        error_label.grid(row=6, column=0, columnspan=2, pady=5)
        
        def on_role_change(*args):
            if role_var.get() == 'doctor':
                extra_frame.grid()  # Показываем
            else:
                extra_frame.grid_remove()  # Скрываем
        
        role_var.trace('w', on_role_change)
        
        def save_user():
            username = username_entry.get().strip()
            fullname = fullname_entry.get().strip()
            role = role_var.get()
            password = password_entry.get().strip()
            confirm_password = confirm_password_entry.get().strip()
            specialty = specialty_entry.get().strip()
            room = room_entry.get().strip()
            
            if not username or not fullname or not password:
                error_label.config(text="Все поля обязательны для заполнения")
                return
            
            if password != confirm_password:
                error_label.config(text="Пароли не совпадают")
                password_entry.delete(0, tk.END)
                confirm_password_entry.delete(0, tk.END)
                password_entry.focus()
                return
            
            if len(username) < 3:
                error_label.config(text="Логин должен содержать минимум 3 символа")
                return
            
            if len(password) < 4:
                error_label.config(text="Пароль должен содержать минимум 4 символа")
                return
            
            # Если роль врач, проверяем заполнение специальности и кабинета
            if role == 'doctor':
                if not specialty:
                    error_label.config(text="Для врача необходимо указать специальность")
                    return
                if not room:
                    error_label.config(text="Для врача необходимо указать номер кабинета")
                    return
                
                # Проверяем уникальность кабинета
                is_unique, msg = db.check_room_unique(room)
                if not is_unique:
                    error_label.config(text=msg)
                    return
            
            # Создаем пользователя
            user_id = db.add_user(username, password, role, fullname)
            
            if user_id:
                if role == 'doctor':
                    # Создаем врача и привязываем к пользователю
                    doctor_id = db.add_doctor(fullname, specialty, room, user_id)
                    if not doctor_id:
                        # Если не удалось создать врача, удаляем пользователя
                        db.delete_user(user_id)
                        error_label.config(text="Ошибка при создании врача (возможно, кабинет занят)")
                        return
                
                messagebox.showinfo("Успех", 
                                   f"Пользователь добавлен (ID: {user_id})\n\n"
                                   f"Логин: {username}\n"
                                   f"Пароль: {password}\n"
                                   f"Роль: {'Врач' if role == 'doctor' else 'Регистратор'}")
                self.load_users()
                # Обновляем списки врачей в других вкладках
                self.load_doctors()
                self.load_doctors_to_combobox()
                self.load_admin_doctors()
                dialog.destroy()
                self.update_status(f"Добавлен пользователь: {username}")
            else:
                error_label.config(text="Ошибка: возможно, такой логин уже существует")
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=save_user, width=15).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy, width=15).pack(side='left', padx=5)
    
    def reset_user_password(self):
        """Сброс пароля пользователя"""
        import database as db
        
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return
        
        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Сброс пароля")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Пользователь: {username}", font=('Arial', 10, 'bold')).pack(pady=10)
        
        ttk.Label(dialog, text="Новый пароль:").pack(pady=5)
        password_entry = ttk.Entry(dialog, width=30, show='•')
        password_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Подтверждение пароля:").pack(pady=5)
        confirm_entry = ttk.Entry(dialog, width=30, show='•')
        confirm_entry.pack(pady=5)
        
        error_label = ttk.Label(dialog, text="", foreground='red')
        error_label.pack(pady=5)
        
        def save_password():
            new_password = password_entry.get().strip()
            confirm_password = confirm_entry.get().strip()
            
            if not new_password:
                error_label.config(text="Введите пароль")
                return
            
            if new_password != confirm_password:
                error_label.config(text="Пароли не совпадают")
                password_entry.delete(0, tk.END)
                confirm_entry.delete(0, tk.END)
                password_entry.focus()
                return
            
            if len(new_password) < 4:
                error_label.config(text="Пароль должен содержать минимум 4 символа")
                return
            
            if db.update_user_password(user_id, new_password):
                messagebox.showinfo("Успех", f"Пароль для {username} изменён на: {new_password}")
                dialog.destroy()
                self.update_status(f"Пароль изменён для {username}")
            else:
                error_label.config(text="Не удалось изменить пароль")
        
        ttk.Button(dialog, text="Сохранить", command=save_password).pack(pady=10)
    
    def delete_selected_user(self):
        """Удаляет выбранного пользователя"""
        import database as db
        
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя")
            return
        
        item = self.users_tree.item(selection[0])
        user_id = item['values'][0]
        username = item['values'][1]
        
        if messagebox.askyesno("Подтверждение", f"Удалить пользователя {username}?\n\nЭто действие необратимо."):
            result = db.delete_user(user_id)
            
            if result['success']:
                self.load_users()
                self.load_doctors()
                self.load_doctors_to_combobox()
                self.load_admin_doctors()
                self.update_status(f"Пользователь {username} удалён")
                messagebox.showinfo("Успех", "Пользователь удалён")
            else:
                messagebox.showerror("Ошибка", result.get('error', 'Не удалось удалить пользователя'))