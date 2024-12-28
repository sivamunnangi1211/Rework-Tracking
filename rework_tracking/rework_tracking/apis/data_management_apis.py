from datetime import datetime

import pytz
from flask import Blueprint, request, session, jsonify
from rework_tracking import db
from rework_tracking.apis.auth_decorador import login_required
from rework_tracking.models.batch_details import RunningBatch, RunningBatchStatus

data_management_apis = Blueprint('data_management_apis', __name__)


@data_management_apis.route('/running_batch/submit', methods=['POST'])
@login_required
def submit_running_batch():
    data = request.json
    print('Data received from submitting running batch: ', data)
    cascade_id = data.get('cascade_id')
    cascade_name = data.get('cascade_name')
    formulation_id = data.get('formulation_id')
    formulation_name = data.get('formulation_name')
    from_date = data.get('from_date')
    to_date = data.get('to_date')

    # Convert date string to datetime object
    from_date = datetime.strptime(from_date, '%Y-%m-%dT%H:%M')
    to_date = datetime.strptime(to_date, '%Y-%m-%dT%H:%M')

    running_batch = RunningBatch(cascade_id=cascade_id,
                                 cascade_name=cascade_name,
                                 formulation_id=formulation_id,
                                 formulation_name=formulation_name,
                                 running_status=RunningBatchStatus.RUNNING,
                                 from_date_millis=from_date.timestamp() * 1000,
                                 from_date=from_date,
                                 to_date_millis=to_date.timestamp() * 1000,
                                 to_date=to_date,
                                 created_by=session.get('user_id'), )

    db.session.add(running_batch)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Running batch submitted successfully'})


@data_management_apis.route('/running_batch/stop', methods=['POST'])
@login_required
def stop_running_batch():
    data = request.json
    print('Data received from updating running batch: ', data)
    batch_id = data.get('batch_id')

    running_batch = RunningBatch.query.filter_by(id=batch_id).first()

    if running_batch is None:
        return jsonify({'error': 'Invalid batch ID'})

    running_batch.running_status = RunningBatchStatus.STOPPED
    running_batch.ended_at = datetime.now(pytz.timezone('Asia/Kolkata'))
    running_batch.updated_by = session.get('user_id')
    running_batch.updated_at = datetime.now(pytz.timezone('Asia/Kolkata'))

    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Running batch stopped successfully'})


@data_management_apis.route('/running_batch', methods=['GET'])
def get_running_batch():
    cascade_id = request.args.get('cascade_id')
    if cascade_id:
        running_batch = (RunningBatch.query.filter(cascade_id=cascade_id)
                         .filter(status=RunningBatchStatus.RUNNING)
                         .order_by(RunningBatch.id.desc())
                         .first())
        if running_batch is None:
            return jsonify({'status': 'error',
                            'message': 'No running batch found for the cascade ID',
                            'status_code': 'no_running_batch'})
        if running_batch.to_date_millis < datetime.now(pytz.timezone('Asia/Kolkata')).timestamp() * 1000:
            running_batch.running_status = RunningBatchStatus.ENDED
            db.session.commit()
            return jsonify({'status': 'error',
                            'message': 'Running batch has ended',
                            'status_code': 'running_batch_ended'})
        return jsonify(running_batch=running_batch.serialize())
    else:
        return jsonify({'error': 'Cascade ID not provided', 'status_code': 'invalid_cascade_id'})
