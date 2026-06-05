"""
Модуль с диалогом редактирования расписания.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from database.appointments import get_work_schedule, save_schedule_config, generate_time_slots

class ScheduleDialog:
    """Диалог редактирования расписания работы"""
    
    def __init__(self, parent):
        self.parent = parent
        self.schedule = get_work_schedule()
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Настройка расписания работы")
        self.dialog.geometry("600x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.center_window()
        self.create_widgets()
        
        self.dialog.bind('<Return>', lambda event: self.save())
        self.dialog.bind('<Escape>', lambda event: self.dialog.destroy())
    
    def center_window(self):
        """Центрирует окно на экране"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Создаёт виджеты диалога"""
        # Основной фрейм с прокруткой
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(
            main_frame, 
            text="Настройка расписания работы поликлиники", 
            font=('Arial', 14, 'bold')
        ).pack(pady=(0, 15))
        
        # Рамка с настройками
        settings_frame = ttk.LabelFrame(main_frame, text="Рабочее время", padding=10)
        settings_frame.pack(fill='x', pady=5)
        
        # Время начала работы
        start_frame = ttk.Frame(settings_frame)
        start_frame.pack(fill='x', pady=5)
        ttk.Label(start_frame, text="Начало работы:", width=18).pack(side='left')
        self.start_hour_var = tk.StringVar(value=str(self.schedule.get('work_start_hour', 9)))
        start_spinbox = ttk.Spinbox(
            start_frame, 
            from_=0, to=22, 
            textvariable=self.start_hour_var,
            width=10,
            state='readonly'
        )
        start_spinbox.pack(side='left', padx=5)
        ttk.Label(start_frame, text=":00").pack(side='left')
        
        # Время окончания работы
        end_frame = ttk.Frame(settings_frame)
        end_frame.pack(fill='x', pady=5)
        ttk.Label(end_frame, text="Окончание работы:", width=18).pack(side='left')
        self.end_hour_var = tk.StringVar(value=str(self.schedule.get('work_end_hour', 18)))
        end_spinbox = ttk.Spinbox(
            end_frame, 
            from_=1, to=23, 
            textvariable=self.end_hour_var,
            width=10,
            state='readonly'
        )
        end_spinbox.pack(side='left', padx=5)
        ttk.Label(end_frame, text=":00").pack(side='left')
        
        # Длительность слота
        slot_frame = ttk.Frame(settings_frame)
        slot_frame.pack(fill='x', pady=5)
        ttk.Label(slot_frame, text="Длительность приёма:", width=18).pack(side='left')
        self.slot_var = tk.StringVar(value=str(self.schedule.get('slot_duration_minutes', 30)))
        slot_combo = ttk.Combobox(
            slot_frame,
            textvariable=self.slot_var,
            values=['15', '20', '30', '45', '60'],
            state='readonly',
            width=8
        )
        slot_combo.pack(side='left', padx=5)
        ttk.Label(slot_frame, text="минут").pack(side='left')
        
        # Обеденный перерыв
        ttk.Separator(settings_frame, orient='horizontal').pack(fill='x', pady=10)
        
        self.lunch_enabled = tk.BooleanVar(
            value=self.schedule.get('lunch_start_hour') is not None
        )
        lunch_check = ttk.Checkbutton(
            settings_frame, 
            text="Обеденный перерыв", 
            variable=self.lunch_enabled,
            command=self.toggle_lunch
        )
        lunch_check.pack(anchor='w', pady=5)
        
        lunch_frame = ttk.Frame(settings_frame)
        lunch_frame.pack(fill='x', pady=5)
        
        ttk.Label(lunch_frame, text="Начало обеда:", width=18).pack(side='left')
        self.lunch_start_var = tk.StringVar(
            value=str(self.schedule.get('lunch_start_hour', 13))
        )
        self.lunch_start_spinbox = ttk.Spinbox(
            lunch_frame, 
            from_=0, to=22, 
            textvariable=self.lunch_start_var,
            width=10,
            state='readonly'
        )
        self.lunch_start_spinbox.pack(side='left', padx=5)
        
        ttk.Label(lunch_frame, text="Конец обеда:", width=15).pack(side='left', padx=(10, 0))
        self.lunch_end_var = tk.StringVar(
            value=str(self.schedule.get('lunch_end_hour', 14))
        )
        self.lunch_end_spinbox = ttk.Spinbox(
            lunch_frame, 
            from_=1, to=23, 
            textvariable=self.lunch_end_var,
            width=10,
            state='readonly'
        )
        self.lunch_end_spinbox.pack(side='left', padx=5)
        
        # Рабочие дни
        days_frame = ttk.LabelFrame(main_frame, text="Рабочие дни", padding=10)
        days_frame.pack(fill='x', pady=10)
        
        working_days = self.schedule.get('working_days', [1, 2, 3, 4, 5])
        self.day_vars = {}
        
        days = [
            ('Понедельник', 1),
            ('Вторник', 2),
            ('Среда', 3),
            ('Четверг', 4),
            ('Пятница', 5),
            ('Суббота', 6),
            ('Воскресенье', 7)
        ]
        
        for i, (day_name, day_num) in enumerate(days):
            var = tk.BooleanVar(value=day_num in working_days)
            self.day_vars[day_num] = var
            cb = ttk.Checkbutton(days_frame, text=day_name, variable=var)
            cb.grid(row=i // 2, column=i % 2, sticky='w', padx=10, pady=5)
        
        # Предпросмотр расписания
        preview_frame = ttk.LabelFrame(main_frame, text="Предпросмотр", padding=10)
        preview_frame.pack(fill='x', pady=10)
        
        self.preview_label = ttk.Label(
            preview_frame, 
            text="", 
            foreground='black', 
            justify='left',
            font=('Courier', 9)
        )
        self.preview_label.pack(pady=5)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(
            button_frame, 
            text="Сохранить", 
            command=self.save,
            style='Action.TButton',
            width=15
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, 
            text="Отмена", 
            command=self.dialog.destroy,
            width=15
        ).pack(side='left', padx=5)
        
        # Инициализация состояния обеденного перерыва
        self.toggle_lunch()
        
        # Привязываем обновление предпросмотра
        self.start_hour_var.trace('w', lambda *args: self.update_preview())
        self.end_hour_var.trace('w', lambda *args: self.update_preview())
        self.slot_var.trace('w', lambda *args: self.update_preview())
        self.lunch_start_var.trace('w', lambda *args: self.update_preview())
        self.lunch_end_var.trace('w', lambda *args: self.update_preview())
        for var in self.day_vars.values():
            var.trace('w', lambda *args: self.update_preview())
        
        # Первоначальный предпросмотр
        self.update_preview()
    
    def toggle_lunch(self):
        """Включает/отключает обеденный перерыв"""
        if self.lunch_enabled.get():
            self.lunch_start_spinbox.config(state='readonly')
            self.lunch_end_spinbox.config(state='readonly')
        else:
            self.lunch_start_spinbox.config(state='disabled')
            self.lunch_end_spinbox.config(state='disabled')
        self.update_preview()
    
    def update_preview(self):
        """Обновляет предпросмотр расписания"""
        try:
            start = int(self.start_hour_var.get())
            end = int(self.end_hour_var.get())
            slot = int(self.slot_var.get())
            
            working_days = [day for day, var in self.day_vars.items() if var.get()]
            
            preview_text = f"Рабочие часы: {start:02d}:00 - {end:02d}:00\n"
            preview_text += f"Длительность приёма: {slot} минут\n"
            
            if self.lunch_enabled.get():
                lunch_start = int(self.lunch_start_var.get())
                lunch_end = int(self.lunch_end_var.get())
                preview_text += f"Обеденный перерыв: {lunch_start:02d}:00 - {lunch_end:02d}:00\n"
            else:
                preview_text += "Обеденный перерыв: отключён\n"
            
            day_names = {1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 5: 'Пт', 6: 'Сб', 7: 'Вс'}
            days_str = ', '.join([day_names[d] for d in sorted(working_days)])
            preview_text += f"Рабочие дни: {days_str}\n\n"
            
            # Показываем примерное расписание
            sample_schedule = {
                'work_start_hour': start,
                'work_end_hour': end,
                'slot_duration_minutes': slot,
                'lunch_start_hour': self.lunch_enabled.get() and int(self.lunch_start_var.get()) or None,
                'lunch_end_hour': self.lunch_enabled.get() and int(self.lunch_end_var.get()) or None
            }
            slots = generate_time_slots(sample_schedule)
            if slots:
                preview_text += f"Примерное расписание (первые 12 слотов):\n"
                # Группируем по часам для наглядности
                current_hour = None
                hour_slots = []
                for s in slots[:12]:
                    hour = s.split(':')[0]
                    if hour != current_hour:
                        if hour_slots:
                            preview_text += f"{current_hour}:00 - {', '.join(hour_slots)}\n"
                        current_hour = hour
                        hour_slots = [s.split(':')[1]]
                    else:
                        hour_slots.append(s.split(':')[1])
                if hour_slots:
                    preview_text += f"{current_hour}:00 - {', '.join(hour_slots)}"
                
                if len(slots) > 12:
                    preview_text += f"\n... и ещё {len(slots)-12} слотов"
            else:
                preview_text += "⚠ Нет доступных временных слотов при текущих настройках!"
            
            self.preview_label.config(text=preview_text)
        except Exception as e:
            self.preview_label.config(text=f"Ошибка предпросмотра: {e}")
    
    def save(self):
        """Сохраняет настройки расписания"""
        try:
            start = int(self.start_hour_var.get())
            end = int(self.end_hour_var.get())
            slot = int(self.slot_var.get())
            
            # Валидация
            if start >= end:
                messagebox.showerror("Ошибка", "Время начала работы должно быть меньше времени окончания")
                return
            
            if slot <= 0:
                messagebox.showerror("Ошибка", "Длительность приёма должна быть положительной")
                return
            
            if self.lunch_enabled.get():
                lunch_start = int(self.lunch_start_var.get())
                lunch_end = int(self.lunch_end_var.get())
                if lunch_start >= lunch_end:
                    messagebox.showerror("Ошибка", "Начало обеда должно быть раньше окончания")
                    return
                if not (start <= lunch_start < lunch_end <= end):
                    messagebox.showerror("Ошибка", "Обеденный перерыв должен быть в рабочее время")
                    return
            else:
                lunch_start = None
                lunch_end = None
            
            working_days = [day for day, var in self.day_vars.items() if var.get()]
            if not working_days:
                messagebox.showerror("Ошибка", "Должен быть выбран хотя бы один рабочий день")
                return
            
            # Сохраняем настройки
            new_schedule = {
                'work_start_hour': start,
                'work_end_hour': end,
                'slot_duration_minutes': slot,
                'lunch_start_hour': lunch_start,
                'lunch_end_hour': lunch_end,
                'break_between_slots': 0,
                'working_days': working_days
            }
            
            if save_schedule_config(new_schedule):
                messagebox.showinfo(
                    "Успех", 
                    "Настройки расписания сохранены!\n\n"
                    "Изменения вступят в силу при следующем поиске свободного времени."
                )
                self.dialog.destroy()
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить настройки")
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверное значение: {e}")
    
    def show(self):
        """Показывает диалог"""
        self.dialog.wait_window()
        return self.result