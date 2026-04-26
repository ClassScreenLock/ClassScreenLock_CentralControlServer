from datetime import datetime
from typing import List, Optional, Dict, Any


class ActivityLogModel:
    def __init__(self, db):
        self.db = db

    def init_table(self) -> None:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER,
                    account_username TEXT,
                    action_type TEXT NOT NULL,
                    action_category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (account_id) REFERENCES accounts(id)
                )
            ''')
            conn.commit()

    def create(self, account_id: Optional[int], account_username: Optional[str],
               action_type: str, action_category: str, description: str,
               ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> int:
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activity_logs 
                (account_id, account_username, action_type, action_category, description, ip_address, user_agent, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (account_id, account_username, action_type, action_category, 
                  description, ip_address, user_agent, created_at))
            conn.commit()
            return cursor.lastrowid

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM activity_logs 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_with_total(self, limit: int = 50, offset: int = 0) -> tuple:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM activity_logs')
            total = cursor.fetchone()['count']
            
            cursor.execute('''
                SELECT * FROM activity_logs 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            logs = [dict(row) for row in cursor.fetchall()]
            return logs, total

    def get_filtered(self, category: Optional[str], action_type: Optional[str], 
                     limit: int = 50, offset: int = 0) -> tuple:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            where_clause = []
            params = []
            
            if category:
                where_clause.append('action_category = ?')
                params.append(category)
            
            if action_type:
                where_clause.append('action_type = ?')
                params.append(action_type)
            
            where_sql = ' AND '.join(where_clause) if where_clause else '1=1'
            
            cursor.execute(f'SELECT COUNT(*) as count FROM activity_logs WHERE {where_sql}', params)
            total = cursor.fetchone()['count']
            
            cursor.execute(f'''
                SELECT * FROM activity_logs 
                WHERE {where_sql}
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', params + [limit, offset])
            logs = [dict(row) for row in cursor.fetchall()]
            return logs, total

    def get_filtered_with_keyword(self, category: Optional[str], action_type: Optional[str],
                                   keyword: Optional[str], limit: int = 50, offset: int = 0) -> tuple:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            where_clause = []
            params = []
            
            if category:
                where_clause.append('action_category = ?')
                params.append(category)
            
            if action_type:
                where_clause.append('action_type = ?')
                params.append(action_type)
            
            if keyword:
                where_clause.append('(account_username LIKE ? OR description LIKE ?)')
                params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            where_sql = ' AND '.join(where_clause) if where_clause else '1=1'
            
            cursor.execute(f'SELECT COUNT(*) as count FROM activity_logs WHERE {where_sql}', params)
            total = cursor.fetchone()['count']
            
            cursor.execute(f'''
                SELECT * FROM activity_logs 
                WHERE {where_sql}
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', params + [limit, offset])
            logs = [dict(row) for row in cursor.fetchall()]
            return logs, total

    def get_by_category(self, category: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM activity_logs 
                WHERE action_category = ?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (category, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_by_account(self, account_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM activity_logs 
                WHERE account_id = ?
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (account_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def delete_old_logs(self, days: int = 30) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM activity_logs 
                WHERE created_at < datetime('now', '-' || ? || ' days')
            ''', (days,))
            conn.commit()
            return cursor.rowcount

    def delete(self, log_id: int) -> None:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM activity_logs WHERE id = ?', (log_id,))
            conn.commit()

    def batch_delete(self, log_ids: List[int]) -> None:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?' for _ in log_ids])
            cursor.execute(f'DELETE FROM activity_logs WHERE id IN ({placeholders})', log_ids)
            conn.commit()

    def clear_all(self) -> None:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM activity_logs')
            conn.commit()
