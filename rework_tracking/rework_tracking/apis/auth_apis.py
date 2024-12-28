# Create a Blueprint for the consumption API
from flask import Blueprint, request, render_template, session, redirect, url_for

from rework_tracking.models.users import User

auth_apis = Blueprint('auth_apis', __name__)


@auth_apis.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        if 'username' in session and 'user_type' in session and 'user_id' in session:
            return redirect(url_for('rendering_apis.home'))
        return render_template('login.html', error=None)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_details = User.query.filter_by(username=username).first()
        if user_details is None:
            error = 'Invalid username'
            return render_template('login.html', error=error)
        if user_details.password != password:
            error = 'Invalid password'
            return render_template('login.html', error=error)

        session['username'] = user_details.username
        session['user_id'] = user_details.user_id
        session['user_type'] = user_details.user_type.value

        print('Session:', session)

        if 'original_url' in session:
            return redirect(session.get('original_url'))

        return redirect(url_for('rendering_apis.home'))


@auth_apis.route('/logout', methods=['POST'])
def logout():
    session.clear()
    session['original_url'] = request.headers.get('Referer')
    return redirect(url_for('auth_apis.login'))
