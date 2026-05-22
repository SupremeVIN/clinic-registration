"""
Статистика базы данных.
"""

import os
from pathlib import Path
from datetime import datetime

from database.connection import get_connection
from database.config import DB_NAME, BACKUP_DIR

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
            
            today = datetime.now().strftime('%Y-%m-%d')
            stats['today_appointments'] = conn.execute(
                "SELECT COUNT(*) as count FROM appointments WHERE date = ?",
                (today,)
            ).fetchone()['count']
        
        if os.path.exists(DB_NAME):
            stats['size_kb'] = os.path.getsize(DB_NAME) // 1024
        
        backup_dir = Path(BACKUP_DIR)
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("clinic_backup_*.db"))
            if backups:
                stats['last_backup'] = backups[-1].name
        
        return stats
    except Exception as e:
        from database.security import log_action
        log_action("STATS_ERROR", f"Error getting database stats: {str(e)}")
        return stats