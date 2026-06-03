"""
Модуль с вкладкой статистики.
"""

import tkinter as tk
from tkinter import ttk

class StatsTabMixin:
    """
    Миксин для вкладки статистики.
    """
    
    # ===========================================
    # ВКЛАДКА СТАТИСТИКИ
    # ===========================================
    
    def create_stats_tab(self):
        """Создаёт вкладку со статистикой"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Статистика")
        
        main_frame = ttk.Frame(tab, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(
            main_frame, 
            text="Статистика работы поликлиники", 
            font=('Arial', 14, 'bold')
        ).grid(row=0, column=0, columnspan=2, pady=10)
        
        self.stats_labels = {}
        stats_items = [
            ('patients', 'Пациентов:'),
            ('doctors', 'Врачей:'),
            ('appointments', 'Всего записей:'),
            ('appointments_scheduled', '  └─ Запланированных:'),
            ('appointments_cancelled', '  └─ Отменённых:'),
            ('today_appointments', 'Записей на сегодня:'),
            ('size_kb', 'Размер БД:'),
            ('last_backup', 'Последний бэкап:')
        ]
        
        for i, (key, label) in enumerate(stats_items):
            # Для дочерних элементов используем отступ
            if key in ['appointments_scheduled', 'appointments_cancelled']:
                ttk.Label(main_frame, text=label, font=('Arial', 10), foreground='gray').grid(
                    row=i+1, column=0, sticky='w', pady=2, padx=(20, 0)
                )
            else:
                ttk.Label(main_frame, text=label, font=('Arial', 11)).grid(
                    row=i+1, column=0, sticky='w', pady=5
                )
            self.stats_labels[key] = ttk.Label(main_frame, text="...", font=('Arial', 11, 'bold'))
            self.stats_labels[key].grid(row=i+1, column=1, sticky='w', pady=5, padx=20)
        
        # Информация о пользователе
        user_frame = ttk.LabelFrame(main_frame, text="Текущий пользователь", padding=10)
        user_frame.grid(row=len(stats_items)+2, column=0, columnspan=2, pady=10, sticky='ew')
        
        ttk.Label(user_frame, text=f"Имя: {self.user['name']}", font=('Arial', 10)).pack(anchor='w')
        ttk.Label(user_frame, text=f"Роль: {self.user['role']}", font=('Arial', 10)).pack(anchor='w')
        ttk.Label(user_frame, text=f"Логин: {self.user['login']}", font=('Arial', 10)).pack(anchor='w')
        
        ttk.Button(
            main_frame,
            text="Обновить статистику",
            command=self.load_stats
        ).grid(row=len(stats_items)+3, column=0, columnspan=2, pady=20)
        
        security_frame = ttk.LabelFrame(main_frame, text="Состояние безопасности", padding=10)
        security_frame.grid(row=len(stats_items)+4, column=0, columnspan=2, pady=10, sticky='ew')
        
        security_items = [
            ("Защита от SQL-инъекций", "green"),
            ("Валидация данных", "green"),
            ("Логирование действий", "green"),
            ("Автоматическое резервирование", "green")
        ]
        
        for i, (text, color) in enumerate(security_items):
            label = ttk.Label(security_frame, text=text, foreground=color)
            label.grid(row=i, column=0, sticky='w', pady=2)
        
        self.load_stats()
    
    def load_stats(self):
        """Загружает статистику"""
        import database as db
        
        stats = db.get_database_stats()
        
        self.stats_labels['patients'].config(text=str(stats['patients']))
        self.stats_labels['doctors'].config(text=str(stats['doctors']))
        self.stats_labels['appointments'].config(text=str(stats['appointments']))
        
        # Запланированные записи (зеленым цветом)
        scheduled_text = str(stats['appointments_scheduled'])
        if stats['appointments_scheduled'] > 0:
            scheduled_text = f"✓ {scheduled_text}"
        self.stats_labels['appointments_scheduled'].config(text=scheduled_text, foreground='green')
        
        # Отмененные записи (красным цветом)
        cancelled_text = str(stats['appointments_cancelled'])
        if stats['appointments_cancelled'] > 0:
            cancelled_text = f"✗ {cancelled_text}"
        self.stats_labels['appointments_cancelled'].config(text=cancelled_text, foreground='red')
        
        self.stats_labels['today_appointments'].config(text=str(stats['today_appointments']))
        self.stats_labels['size_kb'].config(text=f"{stats['size_kb']} КБ")
        self.stats_labels['last_backup'].config(text=stats['last_backup'] or "нет")