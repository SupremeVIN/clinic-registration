"""
Базовые классы для диалоговых окон.
"""

import tkinter as tk
from tkinter import ttk

class BaseDialog:
    """
    Базовый класс для диалоговых окон.
    """
    
    def __init__(self, parent, title, width=500, height=400):
        """
        Инициализация базового диалога.
        
        Args:
            parent: родительское окно
            title (str): заголовок окна
            width (int): ширина окна
            height (int): высота окна
        """
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Центрируем окно
        self.center_window()
        
        self.result = None
        self.create_widgets()
        
        # Привязка клавиши Enter
        self.dialog.bind('<Return>', lambda event: self.on_ok())
        self.dialog.bind('<Escape>', lambda event: self.on_cancel())
        
        # Обработка закрытия окна
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def center_window(self):
        """Центрирует окно на экране"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Создает виджеты диалога (переопределяется в наследниках)"""
        pass
    
    def on_ok(self):
        """Обработчик кнопки OK"""
        pass
    
    def on_cancel(self):
        """Обработчик кнопки Отмена"""
        self.dialog.destroy()
    
    def show(self):
        """Показывает диалог и возвращает результат"""
        self.dialog.wait_window()
        return self.result


class BaseFormDialog(BaseDialog):
    """
    Базовый класс для диалогов с формой.
    """
    
    def __init__(self, parent, title, fields, width=500, height=400):
        """
        Инициализация формы.
        
        Args:
            parent: родительское окно
            title (str): заголовок окна
            fields (list): список полей [('label', 'name', 'type', 'validator'), ...]
            width (int): ширина окна
            height (int): высота окна
        """
        self.fields = fields
        self.entries = {}
        self.validators = {}
        super().__init__(parent, title, width, height)
    
    def create_widgets(self):
        """Создает поля формы"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        row = 0
        for label, name, field_type, validator in self.fields:
            ttk.Label(main_frame, text=label, font=('Arial', 10)).grid(
                row=row, column=0, padx=10, pady=10, sticky='w'
            )
            
            if field_type == 'entry':
                entry = ttk.Entry(main_frame, width=40)
                entry.grid(row=row, column=1, padx=10, pady=10, sticky='w')
                self.entries[name] = entry
                if validator:
                    vcmd = (self.dialog.register(validator), '%P')
                    entry.config(validate='key', validatecommand=vcmd)
                    self.validators[name] = validator
            elif field_type == 'combobox':
                combo = ttk.Combobox(main_frame, width=37, state='readonly')
                combo.grid(row=row, column=1, padx=10, pady=10, sticky='w')
                self.entries[name] = combo
            elif field_type == 'password':
                entry = ttk.Entry(main_frame, width=40, show='•')
                entry.grid(row=row, column=1, padx=10, pady=10, sticky='w')
                self.entries[name] = entry
            elif field_type == 'date':
                frame = ttk.Frame(main_frame)
                frame.grid(row=row, column=1, padx=10, pady=10, sticky='w')
                entry = ttk.Entry(frame, width=15)
                entry.pack(side='left')
                ttk.Button(
                    frame, text="📅", width=3,
                    command=lambda e=entry: self.show_calendar(e)
                ).pack(side='left', padx=5)
                ttk.Label(frame, text="ГГГГ-ММ-ДД", foreground='gray', font=('Arial', 8)).pack(side='left')
                self.entries[name] = entry
            
            row += 1
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=self.on_ok, width=15).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.on_cancel, width=15).pack(side='left', padx=5)
        
        # Метка для ошибок
        self.error_label = ttk.Label(main_frame, text="", foreground='red')
        self.error_label.grid(row=row+1, column=0, columnspan=2, pady=5)
    
    def show_calendar(self, entry, max_date=None):
        """Показывает календарь для выбора даты с ограничением"""
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
        
        # Если max_date не передан, используем переданный при создании календаря
        date_picker = DatePicker(
            calendar_window,
            initial_date=entry.get() or datetime.now().strftime('%Y-%m-%d'),
            callback=on_date_selected,
            max_date=max_date
        )
        date_picker.frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    def get_value(self, name):
        """Получает значение поля"""
        return self.entries[name].get().strip()
    
    def set_value(self, name, value):
        """Устанавливает значение поля"""
        self.entries[name].delete(0, tk.END)
        self.entries[name].insert(0, value or '')
    
    def set_values(self, values):
        """Устанавливает значения нескольких полей"""
        for name, value in values.items():
            if name in self.entries:
                self.set_value(name, value)
    
    def set_combobox_values(self, name, values):
        """Устанавливает значения для комбобокса"""
        self.entries[name]['values'] = values
        if values:
            self.entries[name].current(0)
    
    def disable_field(self, name):
        """Отключает поле"""
        self.entries[name].config(state='disabled')
    
    def show_error(self, message):
        """Показывает сообщение об ошибке"""
        self.error_label.config(text=message)
    
    def clear_error(self):
        """Очищает сообщение об ошибке"""
        self.error_label.config(text="")
    
    def validate(self):
        """Валидация формы (переопределяется в наследниках)"""
        return True
    
    def on_ok(self):
        """Обработчик OK"""
        self.clear_error()
        if self.validate():
            self.result = self.get_data()
            self.dialog.destroy()
    
    def get_data(self):
        """Получает данные из формы (переопределяется в наследниках)"""
        return {name: self.get_value(name) for name in self.entries}