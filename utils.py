from flask import abort
from flask_login import current_user
from functools import wraps

def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_view
    return wrapper
