from flask import Blueprint, request, jsonify
from utils.converters import format_account
from middleware.permissions import require_action_permission


def create_accounts_routes(db, token_required):
    accounts_bp = Blueprint('accounts', __name__, url_prefix='/api/accounts')

    @accounts_bp.route('', methods=['GET'])
    @token_required
    def get_accounts(user):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法访问'}), 403

        accounts = db.accounts.get_all()
        formatted_accounts = [format_account(account) for account in accounts]
        return jsonify(formatted_accounts)

    @accounts_bp.route('/<int:account_id>', methods=['GET'])
    @token_required
    def get_account(user, account_id):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法访问'}), 403

        account = db.accounts.get_by_id(account_id)
        if not account:
            return jsonify({'error': 'Account not found'}), 404

        return jsonify(format_account(account))

    @accounts_bp.route('', methods=['POST'])
    @token_required
    @require_action_permission(db, 'account', 'create')
    def create_account(user):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法创建账户'}), 403

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

        if user['role'] == 'admin' and role in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法创建高级别账户'}), 403

        try:
            account_id = db.accounts.create(username, password, role)
            account = db.accounts.get_by_id(account_id)
            
            db.activity_logs.create(
                account_id=user['id'],
                account_username=user['username'],
                action_type='create',
                action_category='account',
                description=f'用户 {user["username"]} 创建账号 {username}',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            return jsonify(format_account(account)), 201
        except Exception:
            return jsonify({'error': 'Username already exists'}), 409

    @accounts_bp.route('/<int:account_id>', methods=['PUT'])
    @token_required
    @require_action_permission(db, 'account', 'changeRole')
    def update_account(user, account_id):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法更新账户'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        username = data.get('username')
        password = data.get('password')
        role = data.get('role')

        if role and role not in ['super_admin', 'admin', 'user']:
            return jsonify({'error': 'Invalid role'}), 400

        if user['role'] == 'admin':
            target_account = db.accounts.get_by_id(account_id)
            if target_account and target_account['role'] == 'super_admin':
                return jsonify({'error': '权限不足，无法修改超级管理员账户'}), 403
            if role == 'super_admin':
                return jsonify({'error': '权限不足，无法提升为超级管理员'}), 403

        if not db.accounts.update(account_id, username=username, password=password, role=role):
            return jsonify({'error': 'Account not found or no changes made'}), 404

        account = db.accounts.get_by_id(account_id)
        
        db.activity_logs.create(
            account_id=user['id'],
            account_username=user['username'],
            action_type='update',
            action_category='account',
            description=f'用户 {user["username"]} 更新账号 {account["username"]}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify(format_account(account))

    @accounts_bp.route('/<int:account_id>', methods=['DELETE'])
    @token_required
    @require_action_permission(db, 'account', 'delete')
    def delete_account(user, account_id):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法删除账户'}), 403

        if account_id == user['id']:
            return jsonify({'error': 'Cannot delete your own account'}), 400

        target_account = db.accounts.get_by_id(account_id)
        if not target_account:
            return jsonify({'error': 'Account not found'}), 404

        if user['role'] == 'admin' and target_account['role'] == 'super_admin':
            return jsonify({'error': '权限不足，无法删除超级管理员账户'}), 403

        account_username = target_account['username']
        
        db.accounts.delete(account_id)
        
        db.activity_logs.create(
            account_id=user['id'],
            account_username=user['username'],
            action_type='delete',
            action_category='account',
            description=f'用户 {user["username"]} 删除账号 {account_username}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        return jsonify({'message': 'Account deleted successfully'})

    return accounts_bp
