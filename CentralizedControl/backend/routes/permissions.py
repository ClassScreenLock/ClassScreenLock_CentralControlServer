from flask import Blueprint, request, jsonify


def create_permissions_routes(db, token_required):
    permissions_bp = Blueprint('permissions', __name__, url_prefix='/api/permissions')

    ROLE_LEVEL = {
        'super_admin': 3,
        'admin': 2,
        'user': 1
    }

    @permissions_bp.route('', methods=['GET'])
    @token_required
    def get_permissions(user):
        if user['role'] not in ['super_admin', 'admin', 'user']:
            return jsonify({'error': '权限不足，无法访问'}), 403

        all_permissions = db.permissions.get_all()
        
        return jsonify(all_permissions)

    @permissions_bp.route('/<role>', methods=['GET'])
    @token_required
    def get_role_permissions(user, role):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法访问'}), 403

        if user['role'] == 'admin' and role not in ['admin', 'user']:
            return jsonify({'error': '权限不足，无法访问该角色权限'}), 403

        if role not in ['super_admin', 'admin', 'user']:
            return jsonify({'error': '无效的角色'}), 400

        permissions = db.permissions.get_by_role(role)
        return jsonify(permissions)

    def can_modify_role(current_role, target_role, user_permissions):
        if current_role == 'super_admin':
            return True
        
        current_level = ROLE_LEVEL.get(current_role, 0)
        target_level = ROLE_LEVEL.get(target_role, 0)
        
        action_permissions = user_permissions.get('actionPermissions', {})
        permission_mgmt = action_permissions.get('permissionMgmt', {})
        can_modify_lower = permission_mgmt.get('modifyLower', False)
        can_modify_same = permission_mgmt.get('modifySame', False)
        
        if target_level < current_level:
            return can_modify_lower
        
        if target_level == current_level:
            return can_modify_lower and can_modify_same
        
        return False

    @permissions_bp.route('/<role>', methods=['PUT'])
    @token_required
    def update_role_permissions(user, role):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法修改'}), 403

        if user['role'] == 'admin' and role not in ['admin', 'user']:
            return jsonify({'error': '权限不足，无法修改该角色权限'}), 403

        if role not in ['super_admin', 'admin', 'user']:
            return jsonify({'error': '无效的角色'}), 400

        if user['role'] == 'admin':
            user_permissions = db.permissions.get_by_role('admin')
            
            if not can_modify_role(user['role'], role, user_permissions):
                if ROLE_LEVEL.get(role, 0) < ROLE_LEVEL.get(user['role'], 0):
                    return jsonify({'error': '权限不足，您没有修改低等级权限的权限'}), 403
                else:
                    return jsonify({'error': '权限不足，您没有修改同等级权限的权限'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400

        page_permissions = data.get('pagePermissions')
        action_permissions = data.get('actionPermissions')

        if not page_permissions or not action_permissions:
            return jsonify({'error': '页面权限和操作权限不能为空'}), 400

        if role == 'super_admin':
            for path in page_permissions:
                if 'super_admin' not in page_permissions[path]:
                    page_permissions[path].append('super_admin')
            
            for category in action_permissions:
                for action in action_permissions[category]:
                    action_permissions[category][action] = True

        db.permissions.update(role, page_permissions, action_permissions)
        return jsonify({'message': '权限更新成功'})

    @permissions_bp.route('/check', methods=['POST'])
    @token_required
    def check_permission(user):
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400

        category = data.get('category')
        action = data.get('action')

        if not category or not action:
            return jsonify({'error': '类别和操作不能为空'}), 400

        has_permission = db.permissions.check_action_permission(user['role'], category, action)
        return jsonify({
            'hasPermission': has_permission,
            'role': user['role'],
            'category': category,
            'action': action
        })

    return permissions_bp
