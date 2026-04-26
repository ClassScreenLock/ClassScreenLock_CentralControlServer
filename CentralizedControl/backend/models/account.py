import sqlite3
import bcrypt
from datetime import datetime
from typing import List, Optional, Dict, Any


class AccountModel:
    def __init__(self, db):
        self.db = db

    def create(self, username: str, password: str, role: str) -> int:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (username, password, role)
                VALUES (?, ?, ?)
            ''', (username, hashed_password, role))
            conn.commit()
            return cursor.lastrowid

    def get_all(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE is_active = 1')
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE id = ? AND is_active = 1', (account_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE username = ? AND is_active = 1', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update(self, account_id: int, username: Optional[str] = None,
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

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE accounts SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, account_id: int) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts SET is_active = 0 WHERE id = ?', (account_id,))
            conn.commit()
            return cursor.rowcount > 0

    def verify_password(self, username: str, password: str) -> bool:
        account = self.get_by_username(username)
        if not account:
            return False
        stored_hash = account['password']
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)

    def update_last_login(self, account_id: int) -> None:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts SET last_login_at = ? WHERE id = ?',
                         (datetime.now().isoformat(), account_id))
            conn.commit()
