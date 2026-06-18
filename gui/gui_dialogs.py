"""
Модуль с диалоговыми окнами.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
from database.config import AUDIT_LOG_PATH

class DialogsMixin:
    """
    Миксин с диалоговыми окнами.
    """
    
    def show_about(self):
        """Показывает информацию о программе"""
        about_text = f"""РЕГИСТРАТУРА ПОЛИКЛИНИКИ
Версия 2.7 (Безопасная)

ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ:
• Имя: {self.user['name']}
• Роль: {self.user['role']}
• Логин: {self.user['login']}

ЗАЩИТА ДАННЫХ:
• Параметризованные SQL-запросы
• Валидация всех входных данных
• Логирование действий (audit.log)
• Автоматическое резервирование
• Проверка целостности БД

Чухарев Сергей Михайлович
Разработано для курсовой работы
Февраль 2026 год"""
        
        messagebox.showinfo("О программе", about_text)
    
    def show_audit_log(self):
        """Показывает журнал аудита"""
        from database.config import AUDIT_LOG_PATH
        
        if not os.path.exists(AUDIT_LOG_PATH):
            messagebox.showinfo("Журнал аудита", "Журнал аудита пуст")
            return
        
        log_window = tk.Toplevel(self.root)
        log_window.title("Журнал аудита")
        log_window.geometry("800x500")
        
        text_frame = ttk.Frame(log_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        text_widget = tk.Text(text_frame, wrap='none', yscrollcommand=scrollbar.set)
        text_widget.pack(side='left', fill='both', expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        try:
            with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    text_widget.insert('1.0', content)
                else:
                    text_widget.insert('1.0', "Журнал аудита пуст")
            text_widget.config(state='disabled')
        except Exception as e:
            text_widget.insert('1.0', f"Ошибка чтения лога: {e}")
    
    def show_security_stats(self):
        """Показывает статистику безопасности"""
        import database as db
        
        stats = db.get_database_stats()
        
        log_size = 0
        from database.config import AUDIT_LOG_PATH
        if os.path.exists(AUDIT_LOG_PATH):
            log_size = os.path.getsize(AUDIT_LOG_PATH) // 1024
        
        security_info = f"""
╔════════════════════════════════════╗
║     СТАТИСТИКА БЕЗОПАСНОСТИ        ║
╚════════════════════════════════════╝

ПОЛЬЗОВАТЕЛЬ:
   • Имя: {self.user['name']}
   • Роль: {self.user['role']}
   • Логин: {self.user['login']}

ДАННЫЕ:
   • Пациентов: {stats['patients']}
   • Врачей: {stats['doctors']}
   • Записей всего: {stats['appointments']}
   • Записей на сегодня: {stats['today_appointments']}

РЕЗЕРВНОЕ КОПИРОВАНИЕ:
   • Размер БД: {stats['size_kb']} КБ
   • Последний бэкап: {stats['last_backup'] or 'нет'}

ЗАЩИТА:
   • SQL-инъекции: Заблокированы
   • Валидация данных: Активна
   • Логирование: Включено
   • Журнал аудита: {log_size} КБ
"""
        messagebox.showinfo("Статистика безопасности", security_info)
    
    def show_security_guide(self):
        """Показывает руководство по безопасности"""
        guide = """
РУКОВОДСТВО ПО БЕЗОПАСНОСТИ
===========================

ЗАЩИТА ДАННЫХ:
1. Все SQL-запросы параметризованы
2. Входные данные проходят валидацию
3. Номера полисов хешируются в логах

РЕЗЕРВНОЕ КОПИРОВАНИЕ:
• Автоматически при запуске
• Вручную через меню "Файл"
• Хранятся в папке data/backups
• Восстановление через меню "Файл"

АУДИТ:
• Все действия логируются
• Лог хранится в data/audit.log
• Не редактируйте лог вручную

ВАЖНО:
• Не удаляйте файл data/clinic.db вручную
• Используйте функцию "Очистить кэш"
• При ошибках создавайте бэкап
"""
        messagebox.showinfo("Руководство по безопасности", guide)
    
    def show_startup_info(self):
        """Показывает информацию о безопасности при запуске"""
        import database as db
        
        stats = db.get_database_stats()
        messagebox.showinfo(
            "Информация о безопасности",
            f"База данных защищена\n"
            f"Статистика:\n"
            f" - Пациентов: {stats['patients']}\n"
            f" - Врачей: {stats['doctors']}\n"
            f" - Записей: {stats['appointments']}\n"
            f" - Размер БД: {stats['size_kb']} КБ\n\n"
            f"Пользователь: {self.user['name']} ({self.user['role']})\n"
            f"Меры безопасности активны:\n"
            f" - Защита от SQL-инъекций\n"
            f" - Валидация всех данных\n"
            f" - Логирование действий\n"
            f" - Автоматическое резервирование"
        )
    
    def check_integrity(self):
        """Проверяет целостность базы данных"""
        import database as db
        
        if db.verify_database_integrity():
            messagebox.showinfo("Проверка целостности", 
                              "База данных цела и не повреждена")
        else:
            if messagebox.askyesno("Повреждение БД", 
                                 "База данных повреждена!\n\n"
                                 "Создать резервную копию и восстановить?"):
                self.create_backup()
                self.refresh_all()
    
    def create_backup(self):
        """Создаёт резервную копию"""
        import database as db
        
        backup_file = db.backup_database()
        if backup_file:
            messagebox.showinfo("Успех", f"Резервная копия создана:\n{backup_file}")
            self.update_status("Резервная копия создана")
        else:
            messagebox.showerror("Ошибка", "Не удалось создать резервную копию")
    
    def create_backup_silent(self):
        """Создаёт резервную копию без показа сообщения"""
        import database as db
        
        backup_file = db.backup_database()
        if backup_file:
            print(f"Автоматический бэкап создан: {backup_file}")
    
    def restore_from_backup(self):
        """Восстанавливает базу данных из выбранной резервной копии"""
        import database as db
        
        # Получаем список бэкапов
        backups = db.get_backup_list()
        
        if not backups:
            messagebox.showinfo("Восстановление", "Нет доступных резервных копий для восстановления")
            return
        
        # Создаём диалог выбора бэкапа
        backup_window = tk.Toplevel(self.root)
        backup_window.title("Восстановление из резервной копии")
        backup_window.geometry("600x400")
        backup_window.transient(self.root)
        backup_window.grab_set()
        
        # Центрируем окно
        backup_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - backup_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - backup_window.winfo_height()) // 2
        backup_window.geometry(f"+{x}+{y}")
        
        # Заголовок
        ttk.Label(
            backup_window, 
            text="Выберите резервную копию для восстановления", 
            font=('Arial', 12, 'bold')
        ).pack(pady=10)
        
        ttk.Label(
            backup_window,
            text="ВНИМАНИЕ: Текущая база данных будет заменена!",
            foreground='red'
        ).pack(pady=5)
        
        # Список бэкапов
        frame = ttk.Frame(backup_window)
        frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('Дата', 'Размер', 'Имя файла')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column('Дата', width=150)
        tree.column('Размер', width=80)
        tree.column('Имя файла', width=300)
        
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Заполняем список
        for backup in backups:
            size_str = f"{backup['size_kb']} KB" if backup['size_kb'] < 1024 else f"{backup['size_kb'] // 1024} MB"
            tree.insert('', 'end', values=(
                backup['date'],
                size_str,
                backup['name']
            ), tags=(backup['path'],))
        
        # Кнопки
        button_frame = ttk.Frame(backup_window)
        button_frame.pack(pady=10)
        
        def do_restore():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите резервную копию")
                return
            
            item = tree.item(selection[0])
            backup_path = item['tags'][0]
            
            # Подтверждение восстановления
            if not messagebox.askyesno(
                "Подтверждение восстановления",
                f"Восстановить базу данных из бэкапа?\n\n"
                f"Файл: {item['values'][2]}\n"
                f"Дата: {item['values'][0]}\n\n"
                "Текущая база данных будет заменена!\n"
                "Перед восстановлением будет создана резервная копия текущей базы."
            ):
                return
            
            # Выполняем восстановление
            backup_window.destroy()
            
            result = db.restore_from_backup(backup_path)
            
            if result['success']:
                messagebox.showinfo(
                    "Успех",
                    f"{result['message']}\n\n"
                    f"Рекомендуется перезапустить программу для полного обновления."
                )
                self.update_status("База данных восстановлена из бэкапа")
                self.refresh_all()
                
                # Предлагаем перезапустить программу
                if messagebox.askyesno(
                    "Перезапуск",
                    "Для полного применения изменений рекомендуется перезапустить программу.\n"
                    "Перезапустить сейчас?"
                ):
                    self.root.quit()
                    self.root.destroy()
                    import subprocess
                    import sys
                    subprocess.Popen([sys.executable, "main.py"])
            else:
                messagebox.showerror("Ошибка", f"Не удалось восстановить базу данных:\n{result['message']}")
        
        ttk.Button(button_frame, text="Восстановить", command=do_restore, style='Action.TButton', width=15).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Отмена", command=backup_window.destroy, width=15).pack(side='left', padx=5)
    
    def cleanup_database_cache(self):
        """Очищает кэш базы данных (VACUUM)"""
        import database as db
        
        if messagebox.askyesno("Подтверждение", 
                              "Очистить кэш базы данных?\n"
                              "Это безопасная операция, которая уменьшит размер файла."):
            try:
                db.backup_database()
                
                if db.vacuum_database():
                    self.update_status("Кэш базы данных успешно очищен")
                    messagebox.showinfo("Успех", 
                                      "Кэш очищен\n"
                                      "Размер файла уменьшен")
                else:
                    messagebox.showerror("Ошибка", "Не удалось очистить кэш")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось очистить кэш: {e}")