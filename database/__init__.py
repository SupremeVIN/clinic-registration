"""
Модуль для работы с базой данных SQLite.
Экспортирует все основные функции.
"""

from database.connection import get_connection, init_db, verify_database_integrity, backup_database, vacuum_database
from database.security import log_action, hash_sensitive_data, sanitize_input
from database.patients import (
    get_all_patients, search_patients, add_patient, 
    get_patient_by_id, update_patient, delete_patient
)
from database.doctors import get_all_doctors, get_doctor_by_id, check_room_unique
from database.appointments import (
    get_free_time, add_appointment, get_all_appointments,
    get_appointments_by_date, cancel_appointment, delete_old_appointments
)
from database.stats import get_database_stats
from database.config import DATA_DIR, DB_PATH, AUDIT_LOG_PATH, BACKUP_DIR_PATH, ensure_data_dir

__all__ = [
    # Connection
    'get_connection', 'init_db', 'verify_database_integrity', 'backup_database', 'vacuum_database',
    # Security
    'log_action', 'hash_sensitive_data', 'sanitize_input',
    # Patients
    'get_all_patients', 'search_patients', 'add_patient',
    'get_patient_by_id', 'update_patient', 'delete_patient',
    # Doctors
    'get_all_doctors', 'get_doctor_by_id', 'check_room_unique',
    # Appointments
    'get_free_time', 'add_appointment', 'get_all_appointments',
    'get_appointments_by_date', 'cancel_appointment', 'delete_old_appointments',
    # Stats
    'get_database_stats',
    # Config
    'DATA_DIR', 'DB_PATH', 'AUDIT_LOG_PATH', 'BACKUP_DIR_PATH', 'ensure_data_dir'
]