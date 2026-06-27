from flask import Blueprint, request, jsonify, send_from_directory
from datetime import datetime, timedelta
from utils.converters import format_account
import os
import uuid
import base64


def create_auth_routes(db, config, token_required):
    auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

    AVATAR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'avatars')

    @auth_bp.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        if not db.accounts.verify_password(username, password):
            return jsonify({'error': 'Invalid username or password'}), 401

        account = db.accounts.get_by_username(username)
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        db.accounts.update_last_login(account['id'])
        
        db.activity_logs.create(
            account_id=account['id'],
            account_username=username,
            action_type='login',
            action_category='auth',
            description=f'用户 {username} 登录系统',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        token = db.generate_token(account['id'], account['password'])

        return jsonify({
            'id': account['id'],
            'username': account['username'],
            'role': account['role'],
            'token': token,
            'expiresIn': config.token_expiry_hours * 3600,
            'expiresAt': (datetime.now() + timedelta(hours=config.token_expiry_hours)).isoformat()
        })

    @auth_bp.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        if role not in ['super_admin', 'admin', 'user']:
            return jsonify({'error': 'Invalid role'}), 400

        try:
            account_id = db.accounts.create(username, password, role)
            account = db.accounts.get_by_id(account_id)
            
            db.activity_logs.create(
                account_id=account_id,
                account_username=username,
                action_type='register',
                action_category='auth',
                description=f'用户 {username} 注册账号',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify({
                'id': account['id'],
                'username': account['username'],
                'role': account['role']
            }), 201
        except Exception:
            return jsonify({'error': 'Username already exists'}), 409

    @auth_bp.route('/logout', methods=['POST'])
    def logout():
        token = request.headers.get('Authorization')
        if token:
            if token.startswith('Bearer '):
                token = token[7:]
            user = db.verify_token(token)
            if user:
                db.activity_logs.create(
                    account_id=user['id'],
                    account_username=user['username'],
                    action_type='logout',
                    action_category='auth',
                    description=f'用户 {user["username"]} 退出登录',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
        
        return jsonify({'message': 'Logged out successfully'})

    @auth_bp.route('/me', methods=['GET'])
    def get_current_user():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        if token.startswith('Bearer '):
            token = token[7:]
        user = db.verify_token(token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'avatarUrl': user.get('avatar_url', ''),
            'nickname': user.get('nickname', ''),
            'createdAt': user['created_at'],
            'lastLoginAt': user['last_login_at']
        })

    @auth_bp.route('/password', methods=['PUT'])
    def change_password():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        if token.startswith('Bearer '):
            token = token[7:]
        user = db.verify_token(token)
        if not user:
            return jsonify({'error': 'Invalid or expired token'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        if not db.accounts.verify_password(user['username'], current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401

        import bcrypt
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        with db.get_connection() as conn:
            conn.cursor().execute('UPDATE accounts SET password = ? WHERE id = ?', (hashed.decode('utf-8'), user['id']))
            conn.commit()

        db.activity_logs.create(
            account_id=user['id'], account_username=user['username'],
            action_type='update', action_category='account',
            description=f'用户 {user["username"]} 修改了密码',
            ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent')
        )
        return jsonify({'message': 'Password changed successfully'})

    @auth_bp.route('/profile', methods=['PUT'])
    def update_profile():
        token = request.headers.get('Authorization')
        if not token: return jsonify({'error': 'Token is missing'}), 401
        if token.startswith('Bearer '): token = token[7:]
        user = db.verify_token(token)
        if not user: return jsonify({'error': 'Invalid or expired token'}), 401

        data = request.get_json()
        if not data: return jsonify({'error': 'Request body is required'}), 400
        nickname = data.get('nickname')
        if nickname is not None:
            with db.get_connection() as conn:
                conn.cursor().execute('UPDATE accounts SET nickname = ? WHERE id = ?', (nickname, user['id']))
                conn.commit()
            return jsonify({'message': 'Profile updated', 'nickname': nickname})
        return jsonify({'error': 'No fields to update'}), 400

    @auth_bp.route('/avatar', methods=['POST'])
    def upload_avatar():
        token = request.headers.get('Authorization')
        if not token: return jsonify({'error': 'Token is missing'}), 401
        if token.startswith('Bearer '): token = token[7:]
        user = db.verify_token(token)
        if not user: return jsonify({'error': 'Invalid or expired token'}), 401

        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'Image data is required'}), 400

        image_b64 = data['image']
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]
        try:
            image_bytes = base64.b64decode(image_b64)
        except Exception:
            return jsonify({'error': 'Invalid image data'}), 400
        if len(image_bytes) > 2 * 1024 * 1024:
            return jsonify({'error': 'Image size must be less than 2MB'}), 400

        os.makedirs(AVATAR_DIR, exist_ok=True)
        # 删旧头像
        old_avatar = user.get('avatar_url')
        if old_avatar:
            old_filename = old_avatar.split('/')[-1]
            old_path = os.path.join(AVATAR_DIR, old_filename)
            if os.path.exists(old_path): os.remove(old_path)

        ext = 'png'
        if image_bytes[:3] == b'\xff\xd8\xff': ext = 'jpg'
        elif image_bytes[:6] in (b'GIF87a', b'GIF89a'): ext = 'gif'
        elif len(image_bytes) > 12 and image_bytes[8:12] == b'WEBP': ext = 'webp'

        filename = f"{user['id']}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(AVATAR_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        avatar_url = f'/api/auth/avatar/{filename}'
        with db.get_connection() as conn:
            conn.cursor().execute('UPDATE accounts SET avatar_url = ? WHERE id = ?', (avatar_url, user['id']))
            conn.commit()
        return jsonify({'message': 'Avatar uploaded', 'avatarUrl': avatar_url})

    @auth_bp.route('/avatar/<filename>', methods=['GET'])
    def get_avatar(filename):
        return send_from_directory(AVATAR_DIR, filename)

    return auth_bp
