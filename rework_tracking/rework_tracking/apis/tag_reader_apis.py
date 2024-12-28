import datetime
from operator import and_

import pytz
from flask import Blueprint, request, jsonify, render_template, session

from rework_tracking import db
from rework_tracking.apis.auth_decorador import login_required
from rework_tracking.apis.tag_verifier_apis import get_shift
from rework_tracking.models.batch_details import ScannerMachineFormulationMapping
from rework_tracking.models.machines import Machine, Cascade
from rework_tracking.models.tags import SubmittedTag, TagProcessingStatus

tag_reader_apis = Blueprint('tag_reader_apis', __name__)

read_data = {}
machine_scan_status = {}


@tag_reader_apis.route('/tag_reader/read/<string:reader_machine_id>', methods=['POST', 'GET'])
def read_tag_data(reader_machine_id):
    if request.method == 'GET':
        machine = Machine.query.filter_by(machine_id=reader_machine_id).first()
        if not machine:
            return jsonify({'status': 'error', 'message': 'Machine not found', 'status_code': 'not_found'})

        return jsonify({'status': 'success',
                        'tags': read_data.get(reader_machine_id, []),
                        'reader_machine_id': reader_machine_id,
                        'reader_machine_name': machine.machine_name})

    if request.method == 'POST':
        data = request.json
        print('Data received from machine_id: ', reader_machine_id, data)
        if (machine_scan_status.get(reader_machine_id, False)
                and data and isinstance(data.get('event_data'), list)):
            for event in data['event_data']:
                if 'ep' in event:
                    tag_name = event['ep']
                    if reader_machine_id not in read_data:
                        read_data[reader_machine_id] = []
                    if tag_name not in read_data[reader_machine_id]:
                        read_data[reader_machine_id].append(tag_name)

            return jsonify({'tags': read_data[reader_machine_id], 'reader_machine_id': reader_machine_id,
                            'reader_machine_name': data['reader_name']})

        return jsonify({'status': 'error', 'message': 'No valid data provided', 'status_code': 'invalid_input'})


@tag_reader_apis.route('/tag_reader/clear/<string:reader_machine_id>', methods=['POST'])
@login_required
def clear_tag_data(reader_machine_id):
    if reader_machine_id in read_data:
        read_data[reader_machine_id] = []
        return jsonify({'message': 'Data cleared successfully'})
    return jsonify({'error': 'No data to clear'})


@tag_reader_apis.route('/tag_reader/scan/<string:reader_machine_id>', methods=['GET'])
@login_required
def activate_reader(reader_machine_id):
    if reader_machine_id:
        machine = Machine.query.filter_by(machine_id=reader_machine_id).first()
        if machine:
            cascade = Cascade.query.filter_by(cascade_id=machine.cascade_id).first()
            formulation_association = (ScannerMachineFormulationMapping.query.filter_by(machine_id=reader_machine_id)
                                       .first())
            if formulation_association:
                machine_scan_status[reader_machine_id] = True
                read_data[reader_machine_id] = []
                return render_template('scan_tags_page.html',
                                       machine={'machine_id': machine.machine_id,
                                                'machine_name': machine.machine_name,
                                                'cascade_id': machine.cascade_id,
                                                'cascade_name': cascade.cascade_name, },
                                       formulation_mapping={
                                           'formulation_id': formulation_association.formulation_id,
                                           'formulation_name': formulation_association.formulation_name,
                                           'scrap_type_id': formulation_association.scrap_type_id,
                                           'scrap_type_name': formulation_association.scrap_type_name})
            else:
                return render_template('scan_tags_page.html', machine_id=reader_machine_id,
                                       error='Formulation association not found')

    return render_template('scan_tags_page.html', machine_id=reader_machine_id, error='Machine not found')


@tag_reader_apis.route('/tag_reader/deactivate/<string:reader_machine_id>', methods=['POST'])
@login_required
def deactivate_reader(reader_machine_id):
    machine_scan_status[reader_machine_id] = False
    return jsonify({'message': 'Reader activated successfully'})


@tag_reader_apis.route('/tag_reader/tag_status/<string:reader_machine_id>', methods=['POST'])
@login_required
def check_scanned_tag_status(reader_machine_id):
    data = request.json
    print('Checking scanned tag status from machine_id: ', reader_machine_id, data)
    if data and isinstance(data.get('tag_id'), str):
        tag_id = data['tag_id']
        existing_submissions = (db.session.query(SubmittedTag)
                                .filter(and_(SubmittedTag.tag_id == tag_id,
                                             SubmittedTag.processing_status == TagProcessingStatus.SUBMITTED))
                                .order_by(SubmittedTag.submitted_at.desc())
                                .first())
        if existing_submissions:
            return jsonify({'status': 'success', 'has_existing_submission': True,
                            'existing_formulation': existing_submissions.formulation_name,
                            'existing_scrap_type': existing_submissions.scrap_type_name,
                            'existing_cascade': existing_submissions.scanned_cascade_name,
                            'message': 'Tag already submitted'})

    return jsonify({'status': 'success', 'has_existing_submission': False, 'message': 'Tag not submitted yet'})


@tag_reader_apis.route('/tag_reader/submit_tag/<string:reader_machine_id>', methods=['POST'])
@login_required
def submit_tag_data(reader_machine_id):
    data = request.json
    print('Data received from submitting tag: ', reader_machine_id, data)
    tag_id = data.get('tag_id')
    machine_id = data.get('machine_id')
    cascade_id = data.get('cascade_id')
    cascade_name = data.get('cascade_name')
    formulation_id = data.get('formulation_id')
    formulation_name = data.get('formulation_name')
    scrap_type_id = data.get('scrap_type_id')
    scrap_type_name = data.get('scrap_type_name')
    shift = get_shift()
    has_existing_submission = data.get('has_existing_submission')

    if (not tag_id or not machine_id or not cascade_id or not cascade_name or not formulation_id
            or not formulation_name or not scrap_type_id or not scrap_type_name or not shift):
        return jsonify({'status': 'error', 'message': 'Invalid input provided', 'status_code': 'invalid_input'})

    if has_existing_submission:
        existing_submissions = (db.session.query(SubmittedTag)
                                .filter(and_(SubmittedTag.tag_id == tag_id,
                                             SubmittedTag.processing_status == TagProcessingStatus.SUBMITTED))
                                .order_by(SubmittedTag.submitted_at.desc())
                                .first())
        existing_submissions.processing_status = TagProcessingStatus.OVERWRITTEN
        existing_submissions.updated_by = session.get('user_id')
        existing_submissions.processed_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        db.session.commit()

    new_submission = SubmittedTag(tag_id=tag_id,
                                  scanned_machine_id=machine_id,
                                  scanned_machine_name=(Machine.query.filter_by(machine_id=machine_id)
                                                        .first().machine_name),
                                  scanned_cascade_id=cascade_id,
                                  scanned_cascade_name=cascade_name,
                                  formulation_id=formulation_id,
                                  formulation_name=formulation_name,
                                  scrap_type_id=scrap_type_id,
                                  scrap_type_name=scrap_type_name,
                                  submitted_at=datetime.datetime.now(pytz.timezone('Asia/Kolkata')),
                                  processing_status=TagProcessingStatus.SUBMITTED,
                                  scanned_shift=shift,
                                  created_by=session.get('user_id'),
                                  updated_by=session.get('user_id'))
    db.session.add(new_submission)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Tag submitted successfully'})


@tag_reader_apis.route('/tag_reader/formulation_association', methods=['GET'])
@login_required
def get_formulation_association():
    machine_id = request.args.get('machine_id')
    if not machine_id:
        return jsonify({'status': 'error', 'message': 'No machine_id provided', 'status_code': 'invalid_input'})

    formulation_association = (ScannerMachineFormulationMapping.query.filter_by(machine_id=machine_id).first())

    if not formulation_association:
        return jsonify({'status': 'error', 'message': 'No formulation association found', 'status_code': 'not_found'})

    return jsonify({'status': 'success',
                    'formulation_association': {'formulation_id': formulation_association.formulation_id,
                                                'formulation_name': formulation_association.formulation_name,
                                                'scrap_type_id': formulation_association.scrap_type_id,
                                                'scrap_type_name': formulation_association.scrap_type_name}})


@tag_reader_apis.route('/tag_reader/formulation_association', methods=['POST'])
@login_required
def create_formulation_association():
    data = request.json
    machine_id = data.get('machine_id')
    formulation_id = data.get('formulation_id')
    formulation_name = data.get('formulation_name')
    scrap_type_id = data.get('scrap_type_id')
    scrap_type_name = data.get('scrap_type_name')

    if not machine_id or not formulation_id or not formulation_name or not scrap_type_id or not scrap_type_name:
        return jsonify({'status': 'error', 'message': 'Invalid input provided', 'status_code': 'invalid_input'})

    mapping = (ScannerMachineFormulationMapping.query.filter_by(machine_id=machine_id).first())
    if mapping:
        mapping.formulation_id = formulation_id
        mapping.formulation_name = formulation_name
        mapping.scrap_type_id = scrap_type_id
        mapping.scrap_type_name = scrap_type_name
        mapping.updated_by = session.get('user_id')
    else:
        mapping = ScannerMachineFormulationMapping(machine_id=machine_id,
                                                   formulation_id=formulation_id,
                                                   formulation_name=formulation_name,
                                                   scrap_type_id=scrap_type_id,
                                                   scrap_type_name=scrap_type_name,
                                                   created_by=session.get('user_id'),
                                                   updated_by=session.get('user_id'))

        db.session.add(mapping)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Formulation association added successfully'})
