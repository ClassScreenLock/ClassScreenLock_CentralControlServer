import sqlite3
import bcrypt
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from models.account import AccountModel
from models.organization import OrganizationModel
from models.device import DeviceModel
from models.permission import PermissionModel
from models.activity_log import ActivityLogModel


class Database:
    def __init__(self, db_path: str = 'classscreenlock.db'):
        self.db_path = db_path
        self.accounts = AccountModel(self)
        self.organizations = OrganizationModel(self)
        self.devices = DeviceModel(self)
        self.permissions = PermissionModel(self)
        self.activity_logs = ActivityLogModel(self)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _migrate_organizations_table(self, cursor) -> None:
        cursor.execute("PRAGMA table_info(organizations)")
        columns = [row[1] for row in cursor.fetchall()]

        if not columns:
            cursor.execute('''
                CREATE TABLE organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            return

        has_old_columns = any(col in columns for col in ['province_code', 'city_code', 'district_code', 'server_url'])

        if has_old_columns:
            cursor.execute('SELECT * FROM organizations')
            old_data = cursor.fetchall()

            cursor.execute('DROP TABLE organizations')

            cursor.execute('''
                CREATE TABLE organizations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            for row in old_data:
                cursor.execute('''
                    INSERT INTO organizations (id, name, description, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (row['id'], row['name'], row.get('description'), row.get('created_at')))

    def init_database(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')

            self._migrate_organizations_table(cursor)

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS organization_configs (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    security_config TEXT,
                    network_config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    mac_address TEXT,
                    organization_id TEXT,
                    status TEXT DEFAULT 'offline',
                    os_version TEXT,
                    app_version TEXT,
                    dotnet_version TEXT,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_heartbeat TIMESTAMP,
                    last_seen TIMESTAMP,
                    exit_time TIMESTAMP,
                    offline_reason TEXT,
                    contact_phone TEXT,
                    class_name TEXT,
                    person_in_charge TEXT,
                    cpu_usage REAL,
                    memory_usage REAL,
                    disk_usage REAL,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                )
            ''')

            self.permissions.init_table()
            self.activity_logs.init_table()

            conn.commit()

            if not cursor.execute('SELECT COUNT(*) FROM accounts').fetchone()[0]:
                self._create_default_admin(conn)

    def _create_default_admin(self, conn: sqlite3.Connection) -> None:
        hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO accounts (username, password, role)
            VALUES (?, ?, ?)
        ''', ('admin', hashed_password, 'super_admin'))
        conn.commit()

    def generate_token(self, account_id: int, password_hash: str) -> str:
        timestamp = datetime.now().timestamp()
        token_data = f"{account_id}:{timestamp}:{password_hash}"
        token_hash = hashlib.sha256(token_data.encode('utf-8')).hexdigest()
        return f"{account_id}:{timestamp}:{token_hash}"

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return None

            account_id = int(parts[0])
            timestamp = float(parts[1])
            token_hash = parts[2]

            from datetime import timedelta
            token_time = datetime.fromtimestamp(timestamp)
            if datetime.now() - token_time > timedelta(hours=48):
                return None

            user = self.get_account_by_id(account_id)
            if not user:
                return None

            expected_hash = hashlib.sha256(
                f"{account_id}:{timestamp}:{user['password']}".encode('utf-8')
            ).hexdigest()

            if token_hash != expected_hash:
                return None

            return user
        except Exception:
            return None

    def create_account(self, username: str, password: str, role: str) -> int:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (username, password, role)
                VALUES (?, ?, ?)
            ''', (username, hashed_password, role))
            conn.commit()
            return cursor.lastrowid

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE is_active = 1')
            return [dict(row) for row in cursor.fetchall()]

    def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE id = ? AND is_active = 1', (account_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_account_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE username = ? AND is_active = 1', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_account(self, account_id: int, username: Optional[str] = None,
                       password: Optional[str] = None, role: Optional[str] = None) -> bool:
        updates = []
        params = []

        if username:
            updates.append('username = ?')
            params.append(username)
        if password:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            updates.append('password = ?')
            params.append(hashed_password)
        if role:
            updates.append('role = ?')
            params.append(role)

        if not updates:
            return False

        params.append(account_id)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE accounts SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_account(self, account_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts SET is_active = 0 WHERE id = ?', (account_id,))
            conn.commit()
            return cursor.rowcount > 0

    def verify_password(self, username: str, password: str) -> bool:
        account = self.get_account_by_username(username)
        if not account:
            return False
        stored_hash = account['password']
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

    def update_last_login(self, account_id: int) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts SET last_login_at = ? WHERE id = ?',
                         (datetime.now().isoformat(), account_id))
            conn.commit()

    def create_organization(self, name: str, description: str = None) -> str:
        import uuid
        org_id = str(uuid.uuid4())

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO organizations (id, name, description)
                VALUES (?, ?, ?)
            ''', (org_id, name, description))
            conn.commit()
            return org_id

    def get_all_organizations(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM organizations')
            return [dict(row) for row in cursor.fetchall()]

    def get_organization_by_id(self, org_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM organizations WHERE id = ?', (org_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_organization(self, org_id: str, name: Optional[str] = None,
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

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE organizations SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_organization(self, org_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM organizations WHERE id = ?', (org_id,))
            org_deleted = cursor.rowcount > 0
            cursor.execute('DELETE FROM organization_configs WHERE organization_id = ?', (org_id,))
            conn.commit()
            return org_deleted

    def get_organization_config(self, org_id: str) -> Optional[Dict[str, Any]]:
        import json
        with self.get_connection() as conn:
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

    def save_organization_config(self, org_id: str, security_config: Dict = None,
                                network_config: Dict = None) -> bool:
        import json
        security_json = json.dumps(security_config, ensure_ascii=False) if security_config else None
        network_json = json.dumps(network_config, ensure_ascii=False) if network_config else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO organization_configs
                (id, organization_id, security_config, network_config, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (org_id, org_id, security_json, network_json, datetime.now().isoformat()))
            conn.commit()
            return True

    def create_device(self, name: str, ip_address: str, organization_id: str = None,
                     device_id: str = None, **kwargs) -> str:
        with self.get_connection() as conn:
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

    def get_all_devices(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM devices')
            return [dict(row) for row in cursor.fetchall()]

    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM devices WHERE id = ?', (device_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_device(self, device_id: str, **kwargs) -> bool:
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

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE devices SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_device(self, device_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM devices WHERE id = ?', (device_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_devices_by_organization(self, org_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM devices WHERE organization_id = ?', (org_id,))
            return [dict(row) for row in cursor.fetchall()]

    def migrate_from_json(self, json_dir: str) -> Dict[str, Any]:
        import json
        import os

        result = {
            'accounts': 0,
            'organizations': 0,
            'devices': 0,
            'errors': []
        }

        try:
            users_file = os.path.join(json_dir, 'users.json')
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                    for username, user_data in users.items():
                        try:
                            if not self.get_account_by_username(username):
                                self.create_account(
                                    username=username,
                                    password=user_data['password'],
                                    role=user_data['role']
                                )
                                result['accounts'] += 1
                        except Exception as e:
                            result['errors'].append(f"Failed to migrate user {username}: {str(e)}")

            orgs_file = os.path.join(json_dir, 'organizations.json')
            if os.path.exists(orgs_file):
                with open(orgs_file, 'r', encoding='utf-8') as f:
                    orgs = json.load(f)
                    for org_id, org_data in orgs.items():
                        try:
                            existing_org = self.get_organization_by_id(org_id)
                            if not existing_org:
                                self.create_organization(
                                    name=org_data['name'],
                                    description=org_data.get('description', ''),
                                    server_url=None
                                )
                                result['organizations'] += 1

                            if org_data.get('securityConfig'):
                                self.save_organization_config(
                                    org_id=org_id,
                                    security_config=org_data['securityConfig'],
                                    network_config=org_data.get('networkConfig')
                                )
                        except Exception as e:
                            result['errors'].append(f"Failed to migrate org {org_id}: {str(e)}")

            devices_file = os.path.join(json_dir, 'devices.json')
            if os.path.exists(devices_file):
                with open(devices_file, 'r', encoding='utf-8') as f:
                    devices = json.load(f)
                    for device_id, device_data in devices.items():
                        try:
                            self.create_device(
                                name=device_data['name'],
                                ip_address=device_data.get('ipAddress', ''),
                                organization_id=device_data.get('organizationId'),
                                device_id=device_id,
                                mac_address=device_data.get('macAddress'),
                                os_version=device_data.get('osVersion'),
                                app_version=device_data.get('appVersion'),
                                dotnet_version=device_data.get('dotnetVersion'),
                                contact_phone=device_data.get('contactPhone'),
                                class_name=device_data.get('className'),
                                person_in_charge=device_data.get('personInCharge')
                            )

                            update_data = {}
                            if device_data.get('status'):
                                update_data['status'] = device_data['status']
                            if device_data.get('lastHeartbeat'):
                                update_data['last_heartbeat'] = device_data['lastHeartbeat']
                            if device_data.get('lastSeen'):
                                update_data['last_seen'] = device_data['lastSeen']
                            if device_data.get('offlineReason'):
                                update_data['offline_reason'] = device_data['offlineReason']
                            if device_data.get('exitTime'):
                                update_data['exit_time'] = device_data['exitTime']
                            if device_data.get('cpuUsage') is not None:
                                update_data['cpu_usage'] = float(device_data['cpuUsage'])
                            if device_data.get('memoryUsage') is not None:
                                update_data['memory_usage'] = float(device_data['memoryUsage'])
                            if device_data.get('diskUsage') is not None:
                                update_data['disk_usage'] = float(device_data['diskUsage'])

                            if update_data:
                                self.update_device(device_id, **update_data)

                            result['devices'] += 1
                        except Exception as e:
                            result['errors'].append(f"Failed to migrate device {device_id}: {str(e)}")

        except Exception as e:
            result['errors'].append(f"Migration failed: {str(e)}")

        return result
