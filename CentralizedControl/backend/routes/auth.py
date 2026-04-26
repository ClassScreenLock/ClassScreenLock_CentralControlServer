from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from utils.converters import format_account


def create_auth_routes(db, config, token_required):
    auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

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
            'createdAt': user['created_at'],
            'lastLoginAt': user['last_login_at']
        })

    return auth_bp
