"""
Модуль с валидацией ввода.
"""

class ValidationMixin:
    """
    Миксин для валидации ввода.
    """
    
    @staticmethod
    def validate_letters_only(text):
        """
        Проверяет, что текст содержит только буквы, пробелы, дефисы и точки.
        
        Args:
            text (str): текст для проверки
        
        Returns:
            bool: True если валидно
        """
        if not text:
            return True
        return all(c.isalpha() or c.isspace() or c in '-.' for c in text)
    
    @staticmethod
    def validate_digits_only(text):
        """
        Проверяет, что текст содержит только цифры.
        
        Args:
            text (str): текст для проверки
        
        Returns:
            bool: True если валидно
        """
        if not text:
            return True
        return all(c.isdigit() for c in text)
    
    @staticmethod
    def validate_phone_chars(text):
        """
        Проверяет, что текст содержит допустимые символы для телефона.
        
        Args:
            text (str): текст для проверки
        
        Returns:
            bool: True если валидно
        """
        if not text:
            return True
        return all(c.isdigit() or c in '+ -()' for c in text)
    
    @staticmethod
    def validate_doctor_name(text):
        """
        Проверяет, что ФИО врача содержит только буквы, пробелы, дефисы и точки.
        
        Args:
            text (str): текст для проверки
        
        Returns:
            bool: True если валидно
        """
        if not text:
            return True
        # Разрешены: буквы, пробелы, дефис, точка
        return all(c.isalpha() or c.isspace() or c in '-.' for c in text)
    
    @staticmethod
    def validate_specialty(text):
        """
        Проверяет, что специальность содержит только буквы, пробелы, дефисы.
        (Цифры не разрешены)
        
        Args:
            text (str): текст для проверки
        
        Returns:
            bool: True если валидно
        """
        if not text:
            return True
        # Разрешены: буквы, пробелы, дефис
        return all(c.isalpha() or c.isspace() or c == '-' for c in text)
    
    @staticmethod
    def validate_room_number(text):
        """
        Проверяет, что номер кабинета содержит только цифры и буквы (для номеров типа 101А).
        
        Args:
            text (str): текст для проверки
        
        Returns:
            bool: True если валидно
        """
        if not text:
            return True
        # Разрешены: цифры и буквы (для номеров типа 101А, 12Б)
        return all(c.isdigit() or c.isalpha() for c in text)
    
    @staticmethod
    def validate_search(value):
        """Валидация поискового запроса"""
        if len(value) > 50:
            return False
        return True