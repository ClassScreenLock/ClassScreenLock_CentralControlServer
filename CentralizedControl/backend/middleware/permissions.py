from functools import wraps
from flask import request, jsonify


def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(user, *args, **kwargs):
            user_role = user.get('role')
            if not user_role or user_role not in roles:
                return jsonify({'error': '权限不足，无法执行此操作'}), 403
            return f(user, *args, **kwargs)
        return decorated
    return decorator


def require_action_permission(db, category, action):
    def decorator(f):
        @wraps(f)
        def decorated(user, *args, **kwargs):
            if user.get('role') == 'super_admin':
                return f(user, *args, **kwargs)

            has_permission = db.permissions.check_action_permission(user['role'], category, action)
            if not has_permission:
                return jsonify({'error': '权限不足，无法执行此操作'}), 403
            return f(user, *args, **kwargs)
        return decorated
    return decorator
