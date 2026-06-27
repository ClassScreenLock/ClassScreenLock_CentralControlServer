from typing import List, Optional, Dict, Any
import json
from datetime import datetime


class DeviceModel:
    def __init__(self, db):
        self.db = db

    def create(self, name: str, ip_address: str, organization_id: str = None,
               device_id: str = None, **kwargs) -> str:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if device_id:
                cursor.execute('SELECT id FROM devices WHERE id = ?', (device_id,))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute('''
                        UPDATE devices SET
                            name = ?, ip_address = ?, organization_id = ?,
                            mac_address = ?, os_version = ?, app_version = ?,
                            dotnet_version = ?, contact_phone = ?, class_name = ?,
                            person_in_charge = ?
                        WHERE id = ?
                    ''', (name, ip_address, organization_id, kwargs.get('mac_address'),
                         kwargs.get('os_version'), kwargs.get('app_version'),
                         kwargs.get('dotnet_version'), kwargs.get('contact_phone'),
                         kwargs.get('class_name'), kwargs.get('person_in_charge'), device_id))
                    conn.commit()
                    return device_id

                cursor.execute('''
                    INSERT INTO devices (id, name, ip_address, organization_id, mac_address,
                                        os_version, app_version, dotnet_version,
                                        contact_phone, class_name, person_in_charge)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (device_id, name, ip_address, organization_id, kwargs.get('mac_address'),
                     kwargs.get('os_version'), kwargs.get('app_version'),
                     kwargs.get('dotnet_version'), kwargs.get('contact_phone'),
                     kwargs.get('class_name'), kwargs.get('person_in_charge')))
                conn.commit()
                return device_id
            else:
                cursor.execute('''
                    INSERT INTO devices (name, ip_address, organization_id, mac_address,
                                        os_version, app_version, dotnet_version,
                                        contact_phone, class_name, person_in_charge)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, ip_address, organization_id, kwargs.get('mac_address'),
                     kwargs.get('os_version'), kwargs.get('app_version'),
                     kwargs.get('dotnet_version'), kwargs.get('contact_phone'),
                     kwargs.get('class_name'), kwargs.get('person_in_charge')))
                conn.commit()
                return str(cursor.lastrowid)

    def get_all(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM devices')
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update(self, device_id: str, **kwargs) -> bool:
        updates = []
        params = []

        allowed_fields = ['name', 'ip_address', 'mac_address', 'organization_id',
                         'status', 'os_version', 'app_version', 'dotnet_version',
                         'last_heartbeat', 'last_seen', 'exit_time', 'offline_reason',
                         'contact_phone', 'class_name', 'person_in_charge',
                         'cpu_usage', 'memory_usage', 'disk_usage']

        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f'{field} = ?')
                params.append(value)

        if not updates:
            return False

        params.append(device_id)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE devices SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, device_id: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_by_organization(self, org_id: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM devices WHERE organization_id = ?', (org_id,))
            return [dict(row) for row in cursor.fetchall()]

    # ========== 设备级课表配置 ==========

    def get_schedule_config(self, device_id: str) -> Optional[Dict[str, Any]]:
        """获取设备的课表配置（可能为设备专属配置或组织默认配置）"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM device_schedule_configs WHERE device_id = ?', (device_id,))
            row = cursor.fetchone()
            if row and row['schedule_config']:
                result = json.loads(row['schedule_config'])
                result['_source'] = 'device'
                return result

            # 回退到组织配置
            device = self.get_by_id(device_id)
            if device and device.get('organization_id'):
                org_config = self.db.organizations.get_schedule_config(device['organization_id'])
                if org_config:
                    org_config['_source'] = 'organization'
                    return org_config

            return None

    def save_schedule_config(self, device_id: str, schedule_config: Dict) -> bool:
        """保存设备专属课表配置"""
        schedule_json = json.dumps(schedule_config, ensure_ascii=False)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO device_schedule_configs
                (id, device_id, schedule_config, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (device_id, device_id, schedule_json, datetime.now().isoformat()))
            conn.commit()
            return True

    def delete_schedule_config(self, device_id: str) -> bool:
        """删除设备专属课表配置（恢复使用组织配置）"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM device_schedule_configs WHERE device_id = ?', (device_id,))
            conn.commit()
            return cursor.rowcount > 0
