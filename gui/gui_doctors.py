"""
Модуль с вкладками врачей (просмотр и админ).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from gui.gui_base_dialog import BaseFormDialog

class DoctorDialog(BaseFormDialog):
    """Диалог добавления/редактирования врача"""
    
    def __init__(self, parent, mode="add", doctor=None):
        self.mode = mode
        self.doctor = doctor
        fields = [
            ('ФИО', 'full_name', 'entry', None),
            ('Специальность', 'specialty', 'entry', None),
            ('Кабинет', 'room', 'entry', None)
        ]
        super().__init__(parent, "Редактирование врача" if mode == "edit" else "Добавление врача", fields, 600, 450)
    
    def create_widgets(self):
        import database as db
        
        super().create_widgets()
        
        # Заголовок
        ttk.Label(
            self.dialog, 
            text="Данные врача", 
            font=('Arial', 12, 'bold')
        ).place(x=20, y=10)
        
        # Добавляем валидаторы
        if 'full_name' in self.entries:
            vcmd_name = (self.dialog.register(self.validate_doctor_name), '%P')
            self.entries['full_name'].config(validate='key', validatecommand=vcmd_name)
        
        if 'specialty' in self.entries:
            vcmd_specialty = (self.dialog.register(self.validate_specialty), '%P')
            self.entries['specialty'].config(validate='key', validatecommand=vcmd_specialty)
        
        if 'room' in self.entries:
            vcmd_room = (self.dialog.register(self.validate_room_number), '%P')
            self.entries['room'].config(validate='key', validatecommand=vcmd_room)
        
        # Счетчик символов для ФИО
        name_counter = ttk.Label(self.dialog, text="0/100", foreground='gray', font=('Arial', 8))
        name_counter.place(x=450, y=68)
        
        def update_name_counter(*args):
            length = len(self.get_value('full_name'))
            name_counter.config(text=f"{length}/100")
            if length > 100:
                name_counter.config(foreground='red')
            elif length >= 2:
                name_counter.config(foreground='green')
            else:
                name_counter.config(foreground='gray')
        
        self.entries['full_name'].bind('<KeyRelease>', update_name_counter)
        
        # Счетчик символов для специальности
        specialty_counter = ttk.Label(self.dialog, text="0/50", foreground='gray', font=('Arial', 8))
        specialty_counter.place(x=450, y=118)
        
        def update_specialty_counter(*args):
            length = len(self.get_value('specialty'))
            specialty_counter.config(text=f"{length}/50")
            if length > 50:
                specialty_counter.config(foreground='red')
            elif length >= 2:
                specialty_counter.config(foreground='green')
            else:
                specialty_counter.config(foreground='gray')
        
        self.entries['specialty'].bind('<KeyRelease>', update_specialty_counter)
        
        # Если редактирование - заполняем поля
        if self.mode == "edit" and self.doctor:
            self.set_value('full_name', self.doctor['full_name'])
            self.set_value('specialty', self.doctor['specialty'])
            self.set_value('room', self.doctor['room_number'])
            update_name_counter()
            update_specialty_counter()
        
        # Информация о безопасности
        security_label = ttk.Label(
            self.dialog, 
            text="✓ Данные проверяются: буквы в ФИО и специальности, буквы/цифры в кабинете",
            foreground='green',
            font=('Arial', 9)
        )
        security_label.place(x=20, y=380)
    
    @staticmethod
    def validate_doctor_name(text):
        """Проверяет, что ФИО содержит только буквы, пробелы, дефисы и точки"""
        if not text:
            return True
        return all(c.isalpha() or c.isspace() or c in '-.' for c in text)
    
    @staticmethod
    def validate_specialty(text):
        """Проверяет, что специальность содержит только буквы, пробелы, дефисы"""
        if not text:
            return True
        return all(c.isalpha() or c.isspace() or c == '-' for c in text)
    
    @staticmethod
    def validate_room_number(text):
        """Проверяет, что номер кабинета содержит только цифры и буквы"""
        if not text:
            return True
        return all(c.isdigit() or c.isalpha() for c in text)
    
    def validate(self):
        import database as db
        
        name = self.get_value('full_name')
        specialty = self.get_value('specialty')
        room = self.get_value('room')
        
        if not name:
            self.show_error("Ошибка: ФИО обязательно для заполнения")
            return False
        
        if not specialty:
            self.show_error("Ошибка: Специальность обязательна для заполнения")
            return False
        
        if len(name) < 2:
            self.show_error("Ошибка: ФИО должно содержать минимум 2 символа")
            return False
        
        if len(specialty) < 2:
            self.show_error("Ошибка: Специальность должна содержать минимум 2 символа")
            return False
        
        if len(name) > 100:
            self.show_error("Ошибка: ФИО слишком длинное (максимум 100 символов)")
            return False
        
        if len(specialty) > 50:
            self.show_error("Ошибка: Специальность слишком длинная (максимум 50 символов)")
            return False
        
        if room:
            if len(room) > 10:
                self.show_error("Ошибка: Номер кабинета слишком длинный (максимум 10 символов)")
                return False
            
            if self.mode == "add":
                is_unique, msg = db.check_room_unique(room)
            else:
                is_unique, msg = db.check_room_unique(room, self.doctor['id'])
            
            if not is_unique:
                self.show_error(msg)
                return False
        
        return True
    
    def get_data(self):
        return {
            'full_name': self.get_value('full_name'),
            'specialty': self.get_value('specialty'),
            'room_number': self.get_value('room') or None
        }


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
            text="Расписание врача",
            command=self.open_doctor_schedule_dialog,
            style='Admin.TButton'
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
        import database as db
        
        dialog = DoctorDialog(self.root, mode="add")
        result = dialog.show()
        
        if result:
            doctor_id = db.add_doctor(
                result['full_name'],
                result['specialty'],
                result['room_number']
            )
            if doctor_id:
                messagebox.showinfo("Успех", f"Врач добавлен (ID: {doctor_id})")
                self.load_admin_doctors()
                self.load_doctors()
                self.load_doctors_to_combobox()
                self.update_status(f"Добавлен врач: {result['full_name']}")
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить врача. Возможно, кабинет уже занят.")
    
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
            dialog = DoctorDialog(self.root, mode="edit", doctor=doctor)
            result = dialog.show()
            
            if result:
                if db.update_doctor(doctor_id, result['full_name'], result['specialty'], result['room_number']):
                    messagebox.showinfo("Успех", "Данные врача обновлены")
                    self.load_admin_doctors()
                    self.load_doctors()
                    self.load_doctors_to_combobox()
                    self.update_status(f"Обновлён врач: {result['full_name']}")
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить данные врача")
        else:
            messagebox.showerror("Ошибка", "Врач не найден")
    
    def open_doctor_schedule_dialog(self):
        """Открывает диалог редактирования индивидуального расписания врача"""
        from gui.gui_doctor_schedule import DoctorScheduleDialog
        
        selection = self.admin_doctors_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите врача для настройки расписания")
            return
        
        item = self.admin_doctors_tree.item(selection[0])
        doctor_id = item['values'][0]
        doctor_name = item['values'][1]
        
        dialog = DoctorScheduleDialog(self.root, doctor_id, doctor_name)
        dialog.show()
        self.update_status(f"Настройки расписания для врача {doctor_name} обновлены")
        # Обновляем также список врачей для выбора в записи
        self.load_doctors_to_combobox()
    
    def delete_selected_doctor(self):
        """Удаляет выбранного врача (с сохранением истории)"""
        import database as db
        
        selection = self.admin_doctors_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите врача для удаления")
            return
        
        item = self.admin_doctors_tree.item(selection[0])
        doctor_id = item['values'][0]
        doctor_name = item['values'][1]
        
        # Показываем диалог с выбором режима удаления
        dialog = tk.Toplevel(self.root)
        dialog.title("Удаление врача")
        dialog.geometry("500x320")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Центрируем диалог
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(dialog, text=f"Врач: {doctor_name}", font=('Arial', 12, 'bold')).pack(pady=10)
        
        ttk.Label(dialog, text="Выберите режим удаления:", font=('Arial', 10)).pack(pady=5)
        
        keep_history = tk.BooleanVar(value=True)
        
        ttk.Radiobutton(
            dialog, 
            text="Мягкое удаление (рекомендуется) - сохранить историю записей",
            variable=keep_history, 
            value=True
        ).pack(anchor='w', padx=20, pady=5)
        
        ttk.Label(
            dialog, 
            text="  • Врач будет скрыт из списков\n  • Все исторические записи сохранятся\n  • Будущие записи будут отменены",
            foreground='gray',
            font=('Arial', 8),
            justify='left'
        ).pack(anchor='w', padx=40, pady=2)
        
        ttk.Radiobutton(
            dialog,
            text="Полное удаление (не рекомендуется) - потеря истории",
            variable=keep_history,
            value=False
        ).pack(anchor='w', padx=20, pady=5)
        
        ttk.Label(
            dialog,
            text="  • ВНИМАНИЕ: Все записи врача будут удалены!\n  • Восстановление невозможно",
            foreground='red',
            font=('Arial', 8),
            justify='left'
        ).pack(anchor='w', padx=40, pady=2)
        
        def confirm_delete():
            if messagebox.askyesno("Подтверждение", 
                                  f"Удалить врача {doctor_name}?\n\n"
                                  f"Режим: {'Мягкое удаление (с сохранением истории)' if keep_history.get() else 'Полное удаление (безвозвратно)'}"):
                
                result = db.delete_doctor(doctor_id, keep_history=keep_history.get())
                
                if result.get('success'):
                    self.load_admin_doctors()
                    self.load_doctors()
                    self.load_doctors_to_combobox()
                    self.update_status(f"Врач {doctor_name} удалён")
                    
                    if result.get('history_preserved'):
                        messagebox.showinfo("Успех", 
                                           f"Врач {doctor_name} удалён\n\n"
                                           "История записей сохранена.\n"
                                           "Будущие записи были отменены.")
                    else:
                        messagebox.showinfo("Успех", f"Врач {doctor_name} полностью удалён")
                    
                    dialog.destroy()
                elif 'future_appointments' in result:
                    messagebox.showerror("Ошибка", 
                                        f"Нельзя удалить врача с будущими записями\n"
                                        f"Количество будущих записей: {result['future_appointments']}")
                    dialog.destroy()
                else:
                    messagebox.showerror("Ошибка", f"Не удалось удалить врача: {result.get('error', '')}")
                    dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Удалить", command=confirm_delete, style='Warning.TButton').pack(side='left', padx=5)
        ttk.Button(button_frame, text="Отмена", command=dialog.destroy).pack(side='left', padx=5)