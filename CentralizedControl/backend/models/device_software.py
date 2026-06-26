from typing import List, Optional, Dict, Any
import json


class DeviceSoftwareModel:
    def __init__(self, db):
        self.db = db

    def init_table(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS device_software (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    publisher TEXT,
                    version TEXT,
                    install_date TEXT,
                    install_location TEXT,
                    estimated_size TEXT,
                    uninstall_string TEXT,
                    is_system_software BOOLEAN DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_device_software_device_id 
                ON device_software(device_id)
            ''')
            conn.commit()

    def upsert_software_list(self, device_id: str, software_list: List[Dict[str, Any]]) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM device_software WHERE device_id = ?', (device_id,))
            
            for software in software_list:
                cursor.execute('''
                    INSERT INTO device_software 
                    (device_id, name, publisher, version, install_date, install_location, 
                     estimated_size, uninstall_string, is_system_software)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device_id,
                    software.get('name', ''),
                    software.get('publisher'),
                    software.get('version'),
                    software.get('installDate') or software.get('install_date'),
                    software.get('installLocation') or software.get('install_location'),
                    software.get('estimatedSize') or software.get('estimated_size'),
                    software.get('uninstallString') or software.get('uninstall_string'),
                    software.get('isSystemSoftware', software.get('is_system_software', False))
                ))
            conn.commit()
            return True

    def get_software_by_device(self, device_id: str, include_system: bool = True) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if include_system:
                cursor.execute('''
                    SELECT id, device_id, name, publisher, version, install_date, 
                           install_location, estimated_size, uninstall_string, 
                           is_system_software, last_updated
                    FROM device_software 
                    WHERE device_id = ?
                    ORDER BY name COLLATE NOCASE
                ''', (device_id,))
            else:
                cursor.execute('''
                    SELECT id, device_id, name, publisher, version, install_date, 
                           install_location, estimated_size, uninstall_string, 
                           is_system_software, last_updated
                    FROM device_software 
                    WHERE device_id = ? AND is_system_software = 0
                    ORDER BY name COLLATE NOCASE
                ''', (device_id,))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_software_count(self, device_id: str) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM device_software WHERE device_id = ?', (device_id,))
            return cursor.fetchone()[0]

    def delete_device_software(self, device_id: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM device_software WHERE device_id = ?', (device_id,))
            conn.commit()
            return cursor.rowcount > 0

    def search_software(self, device_id: str, query: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, device_id, name, publisher, version, install_date, 
                       install_location, estimated_size, uninstall_string, 
                       is_system_software, last_updated
                FROM device_software 
                WHERE device_id = ? AND (name LIKE ? OR publisher LIKE ?)
                ORDER BY name COLLATE NOCASE
            ''', (device_id, f'%{query}%', f'%{query}%'))
            
            return [dict(row) for row in cursor.fetchall()]
