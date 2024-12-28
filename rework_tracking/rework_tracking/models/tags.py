import datetime
from enum import Enum

import pytz

from rework_tracking import db


class TagProcessingStatus(Enum):
    SUBMITTED = 'SUBMITTED'
    PROCESSED = 'PROCESSED'
    OVERWRITTEN = 'OVERWRITTEN'


class TagProcessingFailureReason(Enum):
    INCORRECT_CASCADE = 'incorrect_cascade'
    INCORRECT_FORMULATION = 'incorrect_formulation'
    INCORRECT_SCRAP_TYPE = 'incorrect_scrap_type'
    METAL_SCRAP_TYPE = 'metal_scrap_type'
    NO_RUNNING_BATCH = 'no_running_batch'
    NO_SUBMISSION = 'no_submission'


class ScannedTag(db.Model):
    __tablename__ = 'scanned_tags'
    scan_id = db.Column(db.String(80), primary_key=True, nullable=False)
    tag_id = db.Column(db.String(80), nullable=False)
    machine_id = db.Column(db.String(80), db.ForeignKey('machines.machine_id'))
    cascade_id = db.Column(db.String(80), db.ForeignKey('cascades.cascade_id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))


class SubmittedTag(db.Model):
    __tablename__ = 'submitted_tags'
    submission_id = db.Column(db.Integer, primary_key=True, nullable=False)
    tag_id = db.Column(db.String(80), nullable=False, index=True)
    scanned_machine_id = db.Column(db.String(80), db.ForeignKey('machines.machine_id'))
    scanned_cascade_id = db.Column(db.String(80), db.ForeignKey('cascades.cascade_id'))
    scanned_cascade_name = db.Column(db.String(120), nullable=False)
    scanned_machine_name = db.Column(db.String(80), nullable=False)
    scanned_shift = db.Column(db.String(80), nullable=False)
    formulation_id = db.Column(db.Integer, db.ForeignKey('formulations.id'))
    formulation_name = db.Column(db.String(80), nullable=False)
    scrap_type_id = db.Column(db.String(80), db.ForeignKey('scrap_types.id'))
    scrap_type_name = db.Column(db.String(80), nullable=False)
    processing_status = db.Column(db.Enum(TagProcessingStatus), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    processed_batch_id = db.Column(db.Integer, db.ForeignKey('running_batches.id'))
    processed_machine_id = db.Column(db.String(80), db.ForeignKey('machines.machine_id'))
    processed_cascade_id = db.Column(db.String(80), db.ForeignKey('cascades.cascade_id'))
    processed_cascade_name = db.Column(db.String(120))
    processed_machine_name = db.Column(db.String(80))
    processed_shift = db.Column(db.String(80))
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    created_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_by = db.Column(db.String(80), db.ForeignKey('users.user_id'))


class FailedProcessingTag(db.Model):
    failure_id = db.Column(db.Integer, primary_key=True, nullable=False)
    tag_id = db.Column(db.String(50), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submitted_tags.submission_id'), nullable=True)
    failure_reason = db.Column(db.Enum(TagProcessingFailureReason), nullable=False)
    scanned_machine_id = db.Column(db.String(80), db.ForeignKey('machines.machine_id'))
    scanned_cascade_id = db.Column(db.String(80), db.ForeignKey('cascades.cascade_id'))
    scanned_cascade_name = db.Column(db.String(120), nullable=False)
    scanned_machine_name = db.Column(db.String(80), nullable=False)
    running_batch_id = db.Column(db.Integer, db.ForeignKey('running_batches.id'))
    running_formulation_id = db.Column(db.Integer, db.ForeignKey('formulations.id'))
    running_formulation_name = db.Column(db.String(80))
    scanned_shift = db.Column(db.String(80), nullable=False)
    scanned_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now(pytz.timezone('Asia/Kolkata')))
