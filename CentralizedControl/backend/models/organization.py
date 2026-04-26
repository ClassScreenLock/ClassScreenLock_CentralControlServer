import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any


class OrganizationModel:
    def __init__(self, db):
        self.db = db

    def create(self, name: str, description: str = None) -> str:
        org_id = str(uuid.uuid4())
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO organizations (id, name, description)
                VALUES (?, ?, ?)
            ''', (org_id, name, description))
            conn.commit()
            return org_id

    def get_all(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM organizations')
            return [dict(row) for row in cursor.fetchall()]

    def get_all_with_device_counts(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.*, COUNT(d.id) as deviceCount
                FROM organizations o
                LEFT JOIN devices d ON o.id = d.organization_id
                GROUP BY o.id
                ORDER BY o.created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, org_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM organizations WHERE id = ?', (org_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update(self, org_id: str, name: Optional[str] = None,
               description: Optional[str] = None) -> bool:
        updates = []
        params = []

        if name:
            updates.append('name = ?')
            params.append(name)
        if description is not None:
            updates.append('description = ?')
            params.append(description)

        if not updates:
            return False

        params.append(org_id)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE organizations SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, org_id: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM organizations WHERE id = ?', (org_id,))
            org_deleted = cursor.rowcount > 0
            cursor.execute('DELETE FROM organization_configs WHERE organization_id = ?', (org_id,))
            conn.commit()
            return org_deleted

    def get_config(self, org_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM organization_configs WHERE organization_id = ?', (org_id,))
            row = cursor.fetchone()
            if not row:
                return None

            result = {'id': row['id'], 'organization_id': row['organization_id']}
            if row['security_config']:
                result['security_config'] = json.loads(row['security_config'])
            if row['network_config']:
                result['network_config'] = json.loads(row['network_config'])
            return result

    def save_config(self, org_id: str, security_config: Dict = None,
                    network_config: Dict = None) -> bool:
        security_json = json.dumps(security_config, ensure_ascii=False) if security_config else None
        network_json = json.dumps(network_config, ensure_ascii=False) if network_config else None

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO organization_configs
                (id, organization_id, security_config, network_config, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (org_id, org_id, security_json, network_json, datetime.now().isoformat()))
            conn.commit()
            return True
