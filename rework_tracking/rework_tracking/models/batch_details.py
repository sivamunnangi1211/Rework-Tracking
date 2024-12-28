# Define a model for batch details
import datetime
from enum import Enum

import pytz

from rework_tracking import db


class RunningBatchStatus(Enum):
    RUNNING = 'running'
    ENDED = 'ended'
    STOPPED = 'stopped'
    NOT_STARTED = 'not_started'


class FormulationStatus(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'


class RunningBatch(db.Model):
    __tablename__ = 'running_batches'
    id = db.Column(db.Integer, primary_key=True)
    cascade_id = db.Column(db.String(80), db.ForeignKey('cascades.cascade_id'))
    cascade_name = db.Column(db.String(120), nullable=False)
    formulation_id = db.Column(db.Integer, db.ForeignKey('formulations.id'))
    formulation_name = db.Column(db.String(255), nullable=False)
    from_date_millis = db.Column(db.BigInteger, nullable=False)
    from_date = db.Column(db.DateTime, nullable=False)
    to_date_millis = db.Column(db.BigInteger, nullable=False)
    to_date = db.Column(db.DateTime, nullable=False)
    running_status = db.Column(db.Enum(RunningBatchStatus), nullable=False, default=RunningBatchStatus.NOT_STARTED)
    ended_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    created_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))


class Formulation(db.Model):
    __tablename__ = 'formulations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(FormulationStatus), nullable=False, default=FormulationStatus.ACTIVE)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    created_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))
    deleted_at = db.Column(db.DateTime)
    deleted_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))


class ScrapType(db.Model):
    __tablename__ = 'scrap_types'
    id = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    created_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))


class ScannerMachineFormulationMapping(db.Model):
    __tablename__ = 'scanner_machine_formulation_mapping'
    machine_id = db.Column(db.String(80), db.ForeignKey('machines.machine_id'), primary_key=True, nullable=False)
    formulation_id = db.Column(db.Integer, db.ForeignKey('formulations.id'))
    formulation_name = db.Column(db.String(255), nullable=False)
    scrap_type_id = db.Column(db.String(80), db.ForeignKey('scrap_types.id'), nullable=False)
    scrap_type_name = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    created_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))