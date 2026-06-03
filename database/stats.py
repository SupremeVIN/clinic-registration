"""
Статистика базы данных.
"""

import os
from pathlib import Path
from datetime import datetime

from database.connection import get_connection
from database.config import DB_PATH, BACKUP_DIR_PATH

def get_database_stats():
    """
    Возвращает статистику базы данных.
    
    Returns:
        dict: статистика
    """
    stats = {
        'patients': 0,
        'doctors': 0,
        'appointments': 0,
        'appointments_scheduled': 0,
        'appointments_cancelled': 0,
        'today_appointments': 0,
        'size_kb': 0,
        'last_backup': None
    }
    
    try:
        with get_connection() as conn:
            stats['patients'] = conn.execute(
                "SELECT COUNT(*) as count FROM patients"
            ).fetchone()['count']
            
            stats['doctors'] = conn.execute(
                "SELECT COUNT(*) as count FROM doctors"
            ).fetchone()['count']
            
            stats['appointments'] = conn.execute(
                "SELECT COUNT(*) as count FROM appointments"
            ).fetchone()['count']
            
            # Запланированные записи
            stats['appointments_scheduled'] = conn.execute(
                "SELECT COUNT(*) as count FROM appointments WHERE status = 'запланирован'"
            ).fetchone()['count']
            
            # Отмененные записи
            stats['appointments_cancelled'] = conn.execute(
                "SELECT COUNT(*) as count FROM appointments WHERE status = 'отменён'"
            ).fetchone()['count']
            
            today = datetime.now().strftime('%Y-%m-%d')
            stats['today_appointments'] = conn.execute(
                "SELECT COUNT(*) as count FROM appointments WHERE date = ? AND status = 'запланирован'",
                (today,)
            ).fetchone()['count']
        
        if os.path.exists(DB_PATH):
            stats['size_kb'] = os.path.getsize(DB_PATH) // 1024
        
        if BACKUP_DIR_PATH.exists():
            backups = sorted(BACKUP_DIR_PATH.glob("clinic_backup_*.db"))
            if backups:
                stats['last_backup'] = backups[-1].name
        
        return stats
    except Exception as e:
        from database.security import log_action
        log_action("STATS_ERROR", f"Error getting database stats: {str(e)}")
        return stats