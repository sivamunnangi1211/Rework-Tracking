import datetime
from enum import Enum

import pytz

from rework_tracking import db


class UserType(Enum):
    ADMIN = 'admin'
    OPERATOR = 'operator'
    SUPERVISOR = 'supervisor'

    @staticmethod
    def from_str(label):
        if label == 'admin':
            return UserType.ADMIN
        elif label == 'operator':
            return UserType.OPERATOR
        elif label == 'supervisor':
            return UserType.SUPERVISOR
        else:
            return None


class UserStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DELETED = 'deleted'


class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(80), primary_key=True)
    employee_id = db.Column(db.String(80), nullable=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False)
    user_status = db.Column(db.Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    created_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))
