"""
Модуль для работы с базой данных SQLite.
Экспортирует все основные функции.
"""

from database.connection import get_connection, init_db, verify_database_integrity, backup_database, vacuum_database, get_backup_list, restore_from_backup
from database.security import log_action, hash_sensitive_data, sanitize_input
from database.patients import (
    get_all_patients, search_patients, add_patient, 
    get_patient_by_id, update_patient, delete_patient
)
from database.doctors import (
    get_all_doctors, get_doctor_by_id, check_room_unique, add_doctor, 
    update_doctor, delete_doctor, get_doctor_appointments_history,
    get_doctor_schedule, save_doctor_schedule, delete_doctor_schedule
)
from database.appointments import (
    get_free_time, add_appointment, get_all_appointments,
    search_appointments, cancel_appointment, delete_old_appointments,
    export_data, import_patients_from_csv, import_doctors_from_csv, import_appointments_from_csv,
    generate_time_slots, get_work_schedule, save_schedule_config, is_working_day
)
from database.users import (
    authenticate, get_all_users, add_user, update_user_password, delete_user,
    get_doctor_by_user_id, get_doctor_by_full_name
)
from database.stats import get_database_stats
from database.config import DATA_DIR, DB_PATH, AUDIT_LOG_PATH, BACKUP_DIR_PATH, ensure_data_dir

__all__ = [
    # Connection
    'get_connection', 'init_db', 'verify_database_integrity', 'backup_database', 'vacuum_database',
    'get_backup_list', 'restore_from_backup',
    
    # Security
    'log_action', 'hash_sensitive_data', 'sanitize_input',
    
    # Patients
    'get_all_patients', 'search_patients', 'add_patient',
    'get_patient_by_id', 'update_patient', 'delete_patient',
    
    # Doctors
    'get_all_doctors', 'get_doctor_by_id', 'check_room_unique', 'add_doctor', 
    'update_doctor', 'delete_doctor', 'get_doctor_appointments_history',
    'get_doctor_schedule', 'save_doctor_schedule', 'delete_doctor_schedule',
    
    # Appointments
    'get_free_time', 'add_appointment', 'get_all_appointments',
    'search_appointments', 'cancel_appointment', 'delete_old_appointments',
    'export_data', 'import_patients_from_csv', 'import_doctors_from_csv', 'import_appointments_from_csv',
    'generate_time_slots', 'get_work_schedule', 'save_schedule_config', 'is_working_day',
    
    # Users
    'authenticate', 'get_all_users', 'add_user', 'update_user_password', 'delete_user',
    'get_doctor_by_user_id', 'get_doctor_by_full_name',
    
    # Stats
    'get_database_stats',
    
    # Config
    'DATA_DIR', 'DB_PATH', 'AUDIT_LOG_PATH', 'BACKUP_DIR_PATH', 'ensure_data_dir'
]