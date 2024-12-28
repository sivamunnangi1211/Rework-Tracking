import datetime

import pytz
from flask import Blueprint, redirect, url_for, session, render_template, jsonify, request

from rework_tracking import db
from rework_tracking.apis.auth_decorador import login_required
from rework_tracking.models.users import User, UserStatus, UserType

manage_users_api = Blueprint('manage_users_api', __name__)


@manage_users_api.route('/users/manage', methods=['GET'])
def manage_users():
    if (not session.get('user_id')) or (not session.get('user_type') == 'admin'):
        return redirect(url_for('auth_apis.login'))
    user_details = User.query.filter_by(user_status=UserStatus.ACTIVE).all()
    if user_details:
        user_details = [{'user_id': user.user_id,
                         'name': user.name,
                         'username': user.username,
                         'password': user.password,
                         'user_type': user.user_type.value,
                         'user_status': user.user_status.value} for user in user_details]
    else:
        user_details = []

    return render_template('manage_users.html', users=user_details)


@manage_users_api.route('/users/<string:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.user_status = UserStatus.DELETED
        user.updated_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        user.updated_by = session.get('user_id')
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User not found'})


@manage_users_api.route('/users', methods=['POST'])
@login_required
def add_user():
    data = request.json
    user_name = data.get('username')
    existing_user = User.query.filter_by(username=user_name).first()
    print('Adding user for ', user_name, existing_user)
    if existing_user and existing_user.user_status != UserStatus.DELETED:
        return jsonify({'status': 'error', 'status_code': 'username_exists', 'message': 'Username already exists'})

    if existing_user and existing_user.user_status == UserStatus.DELETED:
        return jsonify({'status': 'error', 'status_code': 'username_exists_deleted',
                        'message': 'Username already exists, but deleted'})

    user = User(user_id=user_name,
                username=user_name,
                password=data.get('password'),
                name=data.get('name'),
                user_type=UserType.from_str(data.get('user_type')),
                user_status=UserStatus.ACTIVE,
                created_by=session.get('user_id'),
                updated_at=datetime.datetime.now(pytz.timezone('Asia/Kolkata')),
                updated_by=session.get('user_id'))


    db.session.add(user)
    db.session.commit()
    return jsonify({'status': 'success'})


@manage_users_api.route('/users/<string:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    data = request.json
    user = User.query.get(user_id)
    if user:
        if data.get('password') is not None and data.get('password') != '':
            user.password = data.get('password')
        user.name = data.get('name')
        user.updated_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        user.updated_by = session.get('user_id')
        db.session.commit()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'User not found'})
