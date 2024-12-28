from functools import wraps

from flask import session, redirect, url_for, request


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print('decorator called')
        if 'username' not in session or 'user_type' not in session or 'user_id' not in session:
            session['original_url'] = request.url
            print('Session:', session)
            print('user details not found in session, redirecting to login')
            return redirect(url_for('auth_apis.login'))
        return f(*args, **kwargs)

    return decorated_function
