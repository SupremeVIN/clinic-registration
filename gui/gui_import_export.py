"""
Модуль с функциями импорта/экспорта данных.
"""

import os
import csv
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime

class ImportExportMixin:
    """
    Миксин для импорта/экспорта данных с проверкой типов файлов.
    """
    
    # Расширения файлов для разных типов данных
    FILE_TYPES = {
        'patients': {
            'name': 'Пациенты',
            'extension': '.csv',
            'filetypes': [("CSV файлы пациентов", "*.csv"), ("Все файлы", "*.*")],
            'expected_headers': ['ФИО', 'Дата рождения', 'Телефон', 'Номер полиса'],
            'required_headers': ['ФИО', 'Номер полиса'],
            'forbidden_headers': ['Специальность', 'Кабинет'],
            'forbidden_keywords': ['врач', 'доктор', 'специальность', 'кабинет'],
            'required_patterns': [r'\d{16}']
        },
        'doctors': {
            'name': 'Врачи',
            'extension': '.csv',
            'filetypes': [("CSV файлы врачей", "*.csv"), ("Все файлы", "*.*")],
            'expected_headers': ['ФИО', 'Специальность', 'Кабинет'],
            'required_headers': ['ФИО'],
            'forbidden_headers': ['Номер полиса', 'Полис', 'Дата рождения'],
            'forbidden_keywords': ['пациент', 'полис', 'рождения'],
            'required_patterns': []
        },
        'appointments': {
            'name': 'Записи',
            'extension': '.csv',
            'filetypes': [("CSV файлы записей", "*.csv"), ("Все файлы", "*.*")],
            'expected_headers': ['Пациент', 'Врач', 'Дата', 'Время'],
            'required_headers': ['Пациент', 'Врач', 'Дата', 'Время'],
            'forbidden_headers': ['Номер полиса', 'Специальность', 'Кабинет'],
            'forbidden_keywords': ['полис', 'специальность', 'кабинет'],
            'required_patterns': [r'\d{2}:\d{2}']
        },
        'all': {
            'name': 'Все данные',
            'extension': '.csv',
            'filetypes': [("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            'expected_headers': [],
            'required_headers': [],
            'forbidden_headers': [],
            'forbidden_keywords': [],
            'required_patterns': []
        }
    }
    
    def get_export_directory(self):
        """
        Предлагает выбрать директорию для экспорта данных.
        Возвращает путь к выбранной директории или None.
        """
        directory = filedialog.askdirectory(
            title="Выберите папку для сохранения экспортированных данных",
            initialdir=os.path.expanduser("~")
        )
        return directory if directory else None
    
    def get_import_filepath(self, data_type):
        """
        Открывает диалог выбора файла для импорта с проверкой типа.
        
        Args:
            data_type (str): тип данных ('patients', 'doctors', 'appointments')
        
        Returns:
            str: путь к файлу или None
        """
        file_info = self.FILE_TYPES.get(data_type)
        if not file_info:
            return None
        
        filepath = filedialog.askopenfilename(
            title=f"Выберите CSV файл для импорта {file_info['name']}",
            filetypes=file_info['filetypes']
        )
        
        if not filepath:
            return None
        
        # Проверяем расширение файла
        if not filepath.lower().endswith('.csv'):
            messagebox.showerror("Ошибка", "Файл должен иметь расширение .csv")
            return None
        
        # Проверяем содержимое файла
        validation_result, error_msg = self.validate_csv_file(filepath, data_type)
        if not validation_result:
            messagebox.showerror("Ошибка валидации", error_msg)
            return None
        
        return filepath
    
    def validate_csv_file(self, filepath, data_type):
        """
        Проверяет CSV файл на соответствие типу данных.
        
        Args:
            filepath (str): путь к файлу
            data_type (str): тип данных
        
        Returns:
            tuple: (bool, str) - (валиден ли, сообщение об ошибке)
        """
        file_info = self.FILE_TYPES.get(data_type)
        if not file_info:
            return False, "Неизвестный тип данных"
        
        try:
            # Определяем разделитель
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                sample = f.read(4096)
                delimiter = ';' if ';' in sample else ','
                
                # Проверяем, что файл не пустой
                if not sample.strip():
                    return False, "Файл пуст"
            
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=delimiter)
                rows = list(reader)
                
                if not rows:
                    return False, "Файл не содержит данных"
                
                # Проверяем первую строку (заголовки)
                headers = [h.strip() for h in rows[0] if h.strip()]
                headers_lower = [h.lower().strip() for h in headers]
                
                if not headers:
                    return False, "Файл не содержит заголовков"
                
                # 1. ПРОВЕРКА ЗАПРЕЩЕННЫХ ЗАГОЛОВКОВ
                forbidden_headers = [h.lower() for h in file_info.get('forbidden_headers', [])]
                for forbidden in forbidden_headers:
                    if any(forbidden in h for h in headers_lower):
                        return False, (
                            f"Файл НЕ является файлом {file_info['name'].lower()}.\n\n"
                            f"Обнаружен запрещенный заголовок: '{forbidden}'\n"
                            f"Этот заголовок характерен для другого типа данных.\n\n"
                            f"Найдены заголовки: {', '.join(headers)}\n\n"
                            f"Убедитесь, что вы выбрали правильный файл."
                        )
                
                # 2. ПРОВЕРКА ЗАПРЕЩЕННЫХ КЛЮЧЕВЫХ СЛОВ В ДАННЫХ
                forbidden_keywords = file_info.get('forbidden_keywords', [])
                if forbidden_keywords:
                    check_rows = min(5, len(rows) - 1)
                    for i in range(1, check_rows + 1):
                        row = rows[i]
                        if not any(cell.strip() for cell in row):
                            continue
                        
                        for cell in row:
                            cell_lower = cell.lower().strip()
                            for keyword in forbidden_keywords:
                                if keyword in cell_lower:
                                    words = re.findall(r'\b\w+\b', cell_lower)
                                    for word in words:
                                        if keyword in word:
                                            return False, (
                                                f"Файл НЕ является файлом {file_info['name'].lower()}.\n\n"
                                                f"В строке {i+1} обнаружено слово, характерное для другого типа данных: '{cell}'\n"
                                                f"Ключевое слово: '{keyword}'\n\n"
                                                f"Этот файл, вероятно, содержит данные другого типа.\n\n"
                                                f"Убедитесь, что вы выбрали правильный файл."
                                            )
                
                # 3. ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ ЗАГОЛОВКОВ
                required_headers = [h.lower() for h in file_info.get('required_headers', [])]
                missing_headers = []
                for req in required_headers:
                    if not any(req in h for h in headers_lower):
                        missing_headers.append(req)
                
                if missing_headers:
                    return False, (
                        f"Файл НЕ является файлом {file_info['name'].lower()}.\n\n"
                        f"Отсутствуют обязательные колонки: {', '.join(missing_headers)}\n"
                        f"Найдены колонки: {', '.join(headers)}\n\n"
                        f"Убедитесь, что вы выбрали правильный файл."
                    )
                
                # 4. ПРОВЕРКА ДАННЫХ НА СООТВЕТСТВИЕ ПАТТЕРНАМ
                required_patterns = file_info.get('required_patterns', [])
                if required_patterns and len(rows) > 1:
                    check_rows = min(10, len(rows) - 1)
                    found_match = False
                    
                    for i in range(1, check_rows + 1):
                        row = rows[i]
                        if not any(cell.strip() for cell in row):
                            continue
                        
                        row_text = ' '.join(row)
                        
                        for pattern in required_patterns:
                            if re.search(pattern, row_text):
                                found_match = True
                                break
                        
                        if found_match:
                            break
                    
                    if data_type == 'patients' and not found_match:
                        return False, (
                            f"Файл НЕ является файлом пациентов.\n\n"
                            f"В данных не найдено 16-значных номеров полисов.\n"
                            f"Файл пациентов должен содержать номера полисов (16 цифр).\n\n"
                            f"Убедитесь, что вы выбрали правильный файл."
                        )
                    
                    if data_type == 'appointments' and not found_match:
                        return False, (
                            f"Файл НЕ является файлом записей.\n\n"
                            f"В данных не найдено время в формате ЧЧ:ММ.\n"
                            f"Файл записей должен содержать время приёма.\n\n"
                            f"Убедитесь, что вы выбрали правильный файл."
                        )
                
                # 5. СПЕЦИАЛЬНАЯ ПРОВЕРКА ДЛЯ ВРАЧЕЙ
                if data_type == 'doctors' and len(rows) > 1:
                    found_policy = False
                    check_rows = min(10, len(rows) - 1)
                    for i in range(1, check_rows + 1):
                        row = rows[i]
                        if not any(cell.strip() for cell in row):
                            continue
                        row_text = ' '.join(row)
                        if re.search(r'\b\d{16}\b', row_text):
                            found_policy = True
                            break
                    
                    if found_policy:
                        return False, (
                            f"Файл НЕ является файлом врачей.\n\n"
                            f"В данных обнаружены 16-значные номера полисов.\n"
                            f"Это характерно для файла пациентов, а не врачей.\n\n"
                            f"Убедитесь, что вы выбрали правильный файл."
                        )
                
                return True, "OK"
                
        except Exception as e:
            return False, f"Не удалось прочитать файл:\n{str(e)}"
    
    def get_export_filepath(self, data_type):
        """
        Открывает диалог сохранения файла с правильным именем.
        
        Args:
            data_type (str): тип данных
        
        Returns:
            tuple: (base_path, full_path) или (None, None)
        """
        file_info = self.FILE_TYPES.get(data_type)
        if not file_info:
            return None, None
        
        # Сначала предлагаем выбрать папку
        directory = self.get_export_directory()
        if not directory:
            return None, None
        
        # Формируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{file_info['name'].lower()}_{timestamp}"
        
        # Предлагаем имя файла
        filepath = filedialog.asksaveasfilename(
            title=f"Сохранить {file_info['name']}",
            initialdir=directory,
            initialfile=f"{base_name}{file_info['extension']}",
            defaultextension=file_info['extension'],
            filetypes=file_info['filetypes']
        )
        
        if not filepath:
            return None, None
        
        # Возвращаем базовый путь (без расширения) и полный путь
        base_path = filepath.rsplit('.', 1)[0]
        return base_path, filepath