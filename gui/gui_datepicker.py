"""
Модуль с календарем для выбора даты.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
import calendar

class DatePicker:
    """
    Класс для выбора даты с календарем.
    """
    
    def __init__(self, parent, initial_date=None, callback=None, min_date=None, max_date=None):
        """
        Инициализация календаря.
        
        Args:
            parent: родительский виджет
            initial_date: начальная дата (datetime или None)
            callback: функция, вызываемая при выборе даты
            min_date: минимальная допустимая дата
            max_date: максимальная допустимая дата
        """
        self.parent = parent
        self.callback = callback
        self.min_date = min_date or datetime(1900, 1, 1).date()
        self.max_date = max_date or datetime(2100, 12, 31).date()
        
        if initial_date:
            if isinstance(initial_date, str):
                try:
                    self.current_date = datetime.strptime(initial_date, '%Y-%m-%d').date()
                except:
                    self.current_date = datetime.now().date()
            else:
                self.current_date = initial_date
        else:
            self.current_date = datetime.now().date()
        
        self.selected_date = None
        self.create_widgets()
        
        # Кнопка для закрытия окна
        self.close_button = None
    
    def create_widgets(self):
        """Создает виджеты календаря."""
        self.frame = ttk.Frame(self.parent)
        
        # Заголовок с месяцем и годом
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill='x', pady=5)
        
        self.month_year_label = ttk.Label(header_frame, text="", font=('Arial', 10, 'bold'))
        self.month_year_label.pack(side='left', padx=10)
        
        nav_frame = ttk.Frame(header_frame)
        nav_frame.pack(side='right')
        
        ttk.Button(nav_frame, text="◀", width=3, command=self.prev_month).pack(side='left', padx=2)
        ttk.Button(nav_frame, text="▶", width=3, command=self.next_month).pack(side='left', padx=2)
        ttk.Button(nav_frame, text="Сегодня", command=self.go_today).pack(side='left', padx=5)
        
        # Дни недели
        days_frame = ttk.Frame(self.frame)
        days_frame.pack(fill='x', pady=5)
        
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for i, day in enumerate(days):
            label = ttk.Label(days_frame, text=day, width=4, anchor='center', font=('Arial', 9, 'bold'))
            label.grid(row=0, column=i, padx=1, pady=1)
        
        # Календарь
        self.calendar_frame = ttk.Frame(self.frame)
        self.calendar_frame.pack(fill='both', expand=True)
        
        self.update_calendar()
        
        # Кнопка закрытия
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill='x', pady=10)
        
        self.close_button = ttk.Button(
            button_frame, 
            text="Закрыть", 
            command=self.close_calendar,
            width=15
        )
        self.close_button.pack()
    
    def close_calendar(self):
        """Закрывает окно календаря"""
        if hasattr(self.parent, 'destroy'):
            self.parent.destroy()
        else:
            self.frame.destroy()
    
    def update_calendar(self):
        """Обновляет отображение календаря."""
        # Очищаем старый календарь
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # Обновляем заголовок
        month_names = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                       'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        self.month_year_label.config(text=f"{month_names[self.current_date.month-1]} {self.current_date.year}")
        
        # Получаем календарь на месяц
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        # Создаем кнопки для дней
        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    # Пустой день
                    btn = ttk.Label(self.calendar_frame, text="", width=4)
                    btn.grid(row=week_num, column=day_num, padx=1, pady=1)
                else:
                    # День с числом
                    date = datetime(self.current_date.year, self.current_date.month, day).date()
                    
                    # Проверяем, доступна ли дата
                    is_valid = self.min_date <= date <= self.max_date
                    
                    btn = ttk.Button(
                        self.calendar_frame,
                        text=str(day),
                        width=4,
                        command=lambda d=date: self.select_date(d)
                    )
                    
                    # Применяем стили
                    if not is_valid:
                        btn.state(['disabled'])
                    
                    btn.grid(row=week_num, column=day_num, padx=1, pady=1)
    
    def select_date(self, date):
        """Выбирает дату и закрывает календарь."""
        self.selected_date = date
        if self.callback:
            self.callback(date.strftime('%Y-%m-%d'))
        # Закрываем окно после выбора даты
        self.close_calendar()
    
    def prev_month(self):
        """Переход к предыдущему месяцу."""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year-1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month-1)
        self.update_calendar()
    
    def next_month(self):
        """Переход к следующему месяцу."""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year+1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month+1)
        self.update_calendar()
    
    def go_today(self):
        """Переход к текущей дате."""
        self.current_date = datetime.now().date()
        self.update_calendar()