import datetime
from enum import Enum

import pytz

from rework_tracking import db


class MachineReaderType(Enum):
    SCANNER = 'scanner'
    VERIFIER = 'verifier'


class Cascade(db.Model):
    __tablename__ = 'cascades'
    cascade_id = db.Column(db.String(80), primary_key=True)
    cascade_name = db.Column(db.String(120), nullable=False)
    cascade_description = db.Column(db.String(200), nullable=False)
    created_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))


class Machine(db.Model):
    __tablename__ = 'machines'
    machine_id = db.Column(db.String(80), primary_key=True)
    machine_name = db.Column(db.String(80), nullable=False)
    machine_reader_type = db.Column(db.Enum(MachineReaderType), nullable=False)
    machine_type = db.Column(db.String(80), nullable=True)
    verifier_display_machine_ip = db.Column(db.String(80), nullable=True)
    cascade_id = db.Column(db.String(80), db.ForeignKey('cascades.cascade_id'))
    created_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))



