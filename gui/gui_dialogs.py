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
                text_widget.insert('1.0', content)
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