import json
import sqlite3
from typing import Dict, Any, Optional


class PermissionModel:
    def __init__(self, db):
        self.db = db

    def init_table(self) -> None:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT UNIQUE NOT NULL,
                    page_permissions TEXT,
                    action_permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
            self._migrate_system_logs_permission(conn)
    
    def _migrate_system_logs_permission(self, conn) -> None:
        import json
        cursor = conn.cursor()
        cursor.execute('SELECT role, page_permissions, action_permissions FROM role_permissions')
        rows = cursor.fetchall()
        
        for row in rows:
            role = row['role']
            page_perms = json.loads(row['page_permissions']) if row['page_permissions'] else self.get_default_page_permissions()
            action_perms = json.loads(row['action_permissions']) if row['action_permissions'] else self.get_default_action_permissions()
            
            needs_update = False
            
            if '/system-logs' not in page_perms:
                page_perms['/system-logs'] = ['super_admin', 'admin']
                needs_update = True
            
            if 'systemLogs' not in action_perms:
                action_perms['systemLogs'] = {
                    'view': True,
                    'search': True,
                    'deleteSingle': True,
                    'batchDelete': True,
                    'clearAll': True
                }
                needs_update = True
            
            if needs_update:
                page_json = json.dumps(page_perms, ensure_ascii=False)
                action_json = json.dumps(action_perms, ensure_ascii=False)
                cursor.execute('''
                    UPDATE role_permissions 
                    SET page_permissions = ?, action_permissions = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE role = ?
                ''', (page_json, action_json, role))
        
        conn.commit()

    def get_default_page_permissions(self) -> Dict[str, Any]:
        return {
            '/dashboard': ['super_admin', 'admin', 'user'],
            '/organizations': ['super_admin', 'admin'],
            '/devices': ['super_admin', 'admin'],
            '/accounts': ['super_admin', 'admin'],
            '/security-config': ['super_admin', 'admin'],
            '/network-intercept': ['super_admin', 'admin'],
            '/settings': ['super_admin', 'admin', 'user'],
            '/permissions': ['super_admin'],
            '/system-logs': ['super_admin', 'admin']
        }

    def get_default_action_permissions(self) -> Dict[str, Any]:
        return {
            'org': {
                'edit': True,
                'delete': True,
                'create': True
            },
            'device': {
                'viewDetail': True,
                'delete': True
            },
            'account': {
                'create': True,
                'changeRole': True,
                'delete': True
            },
            'security': {
                'manageAccounts': True,
                'jsonEdit': True,
                'enableTwoFactor': True,
                'changeLoginMode': True,
                'modifyPermissions': True
            },
            'network': {
                'enableGlobal': True,
                'manageDomains': True
            },
            'systemLogs': {
                'view': True,
                'search': True,
                'deleteSingle': True,
                'batchDelete': True,
                'clearAll': True
            },
            'permissionMgmt': {
                'modifyLowerOrSame': True
            }
        }

    def get_all(self) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM role_permissions')
            rows = cursor.fetchall()

            result = {}
            for row in rows:
                role = row['role']
                result[role] = {
                    'pagePermissions': json.loads(row['page_permissions']) if row['page_permissions'] else self.get_default_page_permissions(),
                    'actionPermissions': json.loads(row['action_permissions']) if row['action_permissions'] else self.get_default_action_permissions()
                }

            for role in ['super_admin', 'admin', 'user']:
                if role not in result:
                    result[role] = {
                        'pagePermissions': self.get_default_page_permissions(),
                        'actionPermissions': self.get_default_action_permissions()
                    }

            return result

    def get_by_role(self, role: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM role_permissions WHERE role = ?', (role,))
            row = cursor.fetchone()

            if not row:
                return {
                    'pagePermissions': self.get_default_page_permissions(),
                    'actionPermissions': self.get_default_action_permissions()
                }

            return {
                'pagePermissions': json.loads(row['page_permissions']) if row['page_permissions'] else self.get_default_page_permissions(),
                'actionPermissions': json.loads(row['action_permissions']) if row['action_permissions'] else self.get_default_action_permissions()
            }

    def update(self, role: str, page_permissions: Dict[str, Any], action_permissions: Dict[str, Any]) -> bool:
        page_json = json.dumps(page_permissions, ensure_ascii=False)
        action_json = json.dumps(action_permissions, ensure_ascii=False)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO role_permissions
                (role, page_permissions, action_permissions, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (role, page_json, action_json, 'now'))
            conn.commit()
            return True

    def check_action_permission(self, role: str, category: str, action: str) -> bool:
        if role == 'super_admin':
            return True

        permissions = self.get_by_role(role)
        if not permissions:
            return False

        action_perms = permissions.get('actionPermissions', {})
        category_perms = action_perms.get(category, {})
        return category_perms.get(action, False)
