from functools import wraps
from flask import request, jsonify


def token_required(db):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Token is missing'}), 401

            if token.startswith('Bearer '):
                token = token[7:]

            user = db.verify_token(token)
            if not user:
                return jsonify({'error': 'Invalid or expired token'}), 401

            return f(user, *args, **kwargs)
        return decorated
    return decorator
