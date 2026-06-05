"""
Модуль с вкладкой управления пациентами.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from gui.gui_base_dialog import BaseFormDialog

class PatientDialog(BaseFormDialog):
    """Диалог добавления/редактирования пациента"""
    
    def __init__(self, parent, mode="add", patient=None):
        self.mode = mode
        self.patient = patient
        fields = [
            ('ФИО', 'full_name', 'entry', None),
            ('Дата рождения', 'birth_date', 'date', None),
            ('Телефон', 'phone', 'entry', None),
            ('Номер полиса', 'policy', 'entry', None)
        ]
        super().__init__(
            parent, 
            "Редактирование пациента" if mode == "edit" else "Добавление пациента",
            fields, 500, 420
        )
        
        # Добавляем счетчик для полиса
        if 'policy' in self.entries:
            # Уменьшаем ширину поля ввода полиса
            self.entries['policy'].config(width=20)
            
            policy_counter = ttk.Label(
                self.dialog, text="0/16", foreground='gray', font=('Arial', 8)
            )
            policy_counter.place(x=330, y=168)
            
            def update_counter(*args):
                length = len(self.get_value('policy'))
                policy_counter.config(text=f"{length}/16")
                if length == 16:
                    policy_counter.config(foreground='green')
                else:
                    policy_counter.config(foreground='gray')
            
            self.entries['policy'].bind('<KeyRelease>', update_counter)
    
    def create_widgets(self):
        super().create_widgets()
        
        # Если редактирование - заполняем поля
        if self.mode == "edit" and self.patient:
            self.set_value('full_name', self.patient['full_name'])
            self.set_value('birth_date', self.patient['birth_date'])
            self.set_value('phone', self.patient['phone'])
            self.set_value('policy', self.patient['policy_number'])
            self.disable_field('policy')
            
            # Обновляем счетчик
            length = len(self.patient['policy_number'] or '')
            for widget in self.dialog.winfo_children():
                if isinstance(widget, ttk.Label) and widget.cget('text') == f"{length}/16":
                    widget.config(text=f"{length}/16", foreground='green')
    
    def show_calendar(self, entry):
        """Показывает календарь с ограничением на будущие даты"""
        from gui.gui_datepicker import DatePicker
        from datetime import datetime
        
        calendar_window = tk.Toplevel(self.dialog)
        calendar_window.title("Выберите дату")
        calendar_window.geometry("300x350")
        calendar_window.transient(self.dialog)
        calendar_window.grab_set()
        
        def on_date_selected(date_str):
            entry.delete(0, tk.END)
            entry.insert(0, date_str)
        
        date_picker = DatePicker(
            calendar_window,
            initial_date=entry.get() or datetime.now().strftime('%Y-%m-%d'),
            callback=on_date_selected,
            max_date=datetime.now().date()
        )
        date_picker.frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    def validate(self):
        import re
        import database as db
        from datetime import datetime
        
        name = self.get_value('full_name')
        birth = self.get_value('birth_date')
        phone = self.get_value('phone')
        policy = self.get_value('policy')
        
        # Проверка ФИО
        if not name:
            self.show_error("Ошибка: ФИО обязательно для заполнения")
            return False
        
        if len(name) < 2:
            self.show_error("Ошибка: ФИО должно содержать минимум 2 символа")
            return False
        
        # Проверка даты рождения
        if not birth:
            self.show_error("Ошибка: Дата рождения обязательна для заполнения")
            return False
        
        try:
            birth_date = datetime.strptime(birth, '%Y-%m-%d').date()
            if birth_date > datetime.now().date():
                self.show_error("Ошибка: Дата рождения не может быть в будущем")
                return False
            if birth_date < datetime.now().replace(year=datetime.now().year - 150).date():
                self.show_error("Ошибка: Слишком старая дата рождения (максимум 150 лет)")
                return False
        except ValueError:
            self.show_error("Ошибка: Неверный формат даты рождения (ГГГГ-ММ-ДД)")
            return False
        
        # Проверка телефона
        if not phone:
            self.show_error("Ошибка: Номер телефона обязателен для заполнения")
            return False
        
        phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone)
        if len(phone_clean) < 10:
            self.show_error("Ошибка: Номер телефона слишком короткий (минимум 10 цифр)")
            return False
        if len(phone_clean) > 15:
            self.show_error("Ошибка: Номер телефона слишком длинный (максимум 15 цифр)")
            return False
        
        # Проверка полиса (только для добавления)
        if self.mode == "add":
            if not policy:
                self.show_error("Ошибка: Номер полиса обязателен для заполнения")
                return False
            if len(policy) != 16:
                self.show_error("Ошибка: Номер полиса должен содержать ровно 16 цифр")
                return False
        
        return True
    
    def get_data(self):
        return {
            'full_name': self.get_value('full_name'),
            'birth_date': self.get_value('birth_date') or None,
            'phone': self.get_value('phone') or None,
            'policy': self.get_value('policy')
        }


class PatientsTabMixin:
    """
    Миксин для вкладки пациентов.
    """
    
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
        import database as db
        
        dialog = PatientDialog(self.root, mode="add")
        result = dialog.show()
        
        if result:
            patient_id = db.add_patient(
                result['full_name'], 
                result['birth_date'], 
                result['phone'], 
                result['policy']
            )
            if patient_id:
                messagebox.showinfo("Успех", f"Пациент добавлен (ID: {patient_id})")
                self.load_patients()
                self.load_stats()
                self.update_status(f"Добавлен пациент: {result['full_name']}")
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить пациента. Возможно, такой номер полиса уже существует.")
    
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
            dialog = PatientDialog(self.root, mode="edit", patient=patient)
            result = dialog.show()
            
            if result:
                if db.update_patient(patient_id, result['full_name'], result['birth_date'], result['phone'], result['policy']):
                    messagebox.showinfo("Успех", "Данные пациента обновлены")
                    self.load_patients()
                    self.update_status(f"Обновлён пациент: {result['full_name']}")
                else:
                    messagebox.showerror("Ошибка", "Не удалось обновить данные пациента")
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