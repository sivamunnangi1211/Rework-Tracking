from datetime import datetime
from operator import and_, or_

import pytz
import requests
from flask import Blueprint, request, jsonify

from rework_tracking import db
from rework_tracking.apis.auth_decorador import login_required
from rework_tracking.models.batch_details import RunningBatch
from rework_tracking.models.machines import Machine, Cascade
from rework_tracking.models.tags import SubmittedTag, TagProcessingStatus, FailedProcessingTag, \
    TagProcessingFailureReason

tag_verifier_apis = Blueprint('tag_verifier_apis', __name__)


class LastScannedTag:
    def __init__(self, machine_id, tag_id, last_scanned_time):
        self.machine_id = machine_id
        self.tag_id = tag_id
        self.last_scanned_time = last_scanned_time


read_data = {}
machine_scan_status = {}
time_delta_for_each_scan_in_seconds = 30
last_scanned_tag_per_machine = {}


@tag_verifier_apis.route('/tag_verifier/verify/<string:verifier_machine_id>', methods=['POST'])
def verify_tag_data(verifier_machine_id):
    data = request.json
    db.session.commit()
    print('Data received from machine_id: ', verifier_machine_id, data)

    if data and isinstance(data.get('event_data'), list):
        tags_to_check = [event['ep'] for event in data['event_data'] if 'ep' in event]

        # Check if any tags were extracted
        if tags_to_check:
            current_time = datetime.now()
            current_time_millis = current_time.timestamp() * 1000
            machine_info = Machine.query.filter_by(machine_id=verifier_machine_id).first()
            cascade_info = Cascade.query.filter_by(cascade_id=machine_info.cascade_id).first()

            running_batch = (
                db.session.query(RunningBatch).where((RunningBatch.cascade_id == machine_info.cascade_id)
                                                     & (RunningBatch.from_date_millis < current_time_millis)
                                                     & (RunningBatch.to_date_millis >= current_time_millis))
                .order_by(RunningBatch.id.desc())
                .first())
            print('Running batch:', running_batch)

            if len(tags_to_check) > 1:
                print('Multiple tags to check found, rejecting all:', tags_to_check)
                post_data_to_endpoint(
                    {'tag': 'multiple_tags_found', 'status': 'not_ok', 'remarks': 'multiple_tags_found',
                     'submission_id': 'multiple_tags_found'},
                    machine_info.verifier_display_machine_ip)
                return jsonify({'status': 'error', 'status_code': 'multiple_tags_found',
                                'message': 'Multiple tags found. Rejecting all tags.'}), 400

            for tag in tags_to_check:
                print('Checking tag:', tag)
                submitted_tag = (db.session.query(SubmittedTag)
                                 .where((SubmittedTag.tag_id == tag)
                                        & or_(SubmittedTag.processing_status == TagProcessingStatus.SUBMITTED,
                                              SubmittedTag.processing_status == TagProcessingStatus.PROCESSED))
                                 .order_by(SubmittedTag.submission_id.desc())
                                 .first())

                print('Submitted tag:', submitted_tag)

                if verifier_machine_id in last_scanned_tag_per_machine:
                    last_scanned_tag = last_scanned_tag_per_machine[verifier_machine_id]
                    if ((tag != last_scanned_tag.tag_id)
                            and (current_time - last_scanned_tag.last_scanned_time)
                                    .seconds < time_delta_for_each_scan_in_seconds):
                        print('Scanned too soon. Last scanned tag:', last_scanned_tag.tag_id, 'last scanned time:',
                              last_scanned_tag.last_scanned_time, 'rejecting all:', tags_to_check)

                        post_data_to_endpoint(
                            {'tag': 'scanned_too_soon', 'status': 'not_ok', 'remarks': 'scanned_too_soon',
                             'submission_id': 'scanned_too_soon'},
                            machine_info.verifier_display_machine_ip)
                        return jsonify({'status': 'error', 'status_code': 'scanned_too_soon',
                                        'message': 'Scanned too soon. Rejecting all tags.'}), 400

                last_scanned_tag_per_machine[verifier_machine_id] = LastScannedTag(verifier_machine_id, tag,
                                                                                   current_time)

                if not running_batch:
                    handle_failed_processing(tag, TagProcessingFailureReason.NO_RUNNING_BATCH,
                                             'No running batch found',
                                             machine_info,
                                             cascade_info,
                                             submitted_tag=submitted_tag)
                    continue

                if submitted_tag:
                    if (submitted_tag.processing_status == TagProcessingStatus.PROCESSED
                            and submitted_tag.formulation_id == running_batch.formulation_id
                            and submitted_tag.scrap_type_id != 'metal'
                            and submitted_tag.processed_batch_id == running_batch.id):
                        post_data_to_endpoint({'tag': tag, 'status': 'ok', 'remarks': 'Tag verified successfully',
                                               'submission_id': submitted_tag.submission_id},
                                              machine_info.verifier_display_machine_ip)
                        continue
                    if (submitted_tag.processing_status == TagProcessingStatus.SUBMITTED
                            and submitted_tag.formulation_id == running_batch.formulation_id
                            and submitted_tag.scrap_type_id != 'metal'):
                        submitted_tag.processing_status = TagProcessingStatus.PROCESSED
                        submitted_tag.processed_machine_id = verifier_machine_id
                        submitted_tag.processed_machine_name = machine_info.machine_name
                        submitted_tag.processed_batch_id = running_batch.id
                        submitted_tag.processed_cascade_id = cascade_info.cascade_id
                        submitted_tag.processed_cascade_name = cascade_info.cascade_name
                        submitted_tag.processed_shift = get_shift()
                        submitted_tag.processed_at = current_time
                        db.session.commit()
                        post_data_to_endpoint({'tag': tag, 'status': 'ok', 'remarks': 'Tag verified successfully',
                                               'submission_id': submitted_tag.submission_id},
                                              machine_info.verifier_display_machine_ip)

                    elif submitted_tag.scrap_type_id == 'metal':
                        handle_failed_processing(tag, TagProcessingFailureReason.METAL_SCRAP_TYPE,
                                                 'Metal scrap type',
                                                 machine_info,
                                                 cascade_info,
                                                 running_batch=running_batch,
                                                 submitted_tag=submitted_tag)

                    else:
                        handle_failed_processing(tag, TagProcessingFailureReason.INCORRECT_FORMULATION,
                                                 'Incorrect formulation',
                                                 machine_info,
                                                 cascade_info,
                                                 running_batch=running_batch,
                                                 submitted_tag=submitted_tag)
                else:
                    handle_failed_processing(tag, TagProcessingFailureReason.NO_SUBMISSION,
                                             'No submission found',
                                             machine_info,
                                             cascade_info,
                                             running_batch=running_batch)
        else:
            print('No tags to check')
            return jsonify({'status': 'error', 'message': 'No tags to check'}), 400

    return jsonify({'status': 'success', 'message': 'Data received successfully'})


def handle_failed_processing(tag,
                             failure_reason,
                             remarks,
                             machine_info,
                             cascade_info,
                             running_batch=None,
                             submitted_tag=None):
    submission_id = submitted_tag.submission_id if submitted_tag else None
    running_formulation_id = running_batch.formulation_id if running_batch else None
    running_formulation_name = running_batch.formulation_name if running_batch else None
    running_batch_id = running_batch.id if running_batch else None
    failed_processing = FailedProcessingTag(tag_id=tag,
                                            submission_id=submission_id,
                                            failure_reason=failure_reason,
                                            scanned_machine_id=machine_info.machine_id,
                                            scanned_machine_name=machine_info.machine_name,
                                            scanned_cascade_id=machine_info.cascade_id,
                                            scanned_cascade_name=cascade_info.cascade_name,
                                            scanned_shift=get_shift(),
                                            running_batch_id=running_batch_id,
                                            running_formulation_id=running_formulation_id,
                                            running_formulation_name=running_formulation_name, )
    db.session.add(failed_processing)
    db.session.commit()
    post_data_to_endpoint({'tag': tag, 'status': 'not_ok', 'remarks': remarks},
                          machine_info.verifier_display_machine_ip)


def post_data_to_endpoint(data_to_post, ip_address):
    endpoint_url = 'http://' + ip_address + '/result'
    print('Posting data to endpoint:', endpoint_url, 'Data:', data_to_post)
    #return
    response = requests.post(endpoint_url, json=data_to_post)

    if response.status_code == 200:
        print("Data posted successfully.")
    else:
        print("Failed to post data. Status code:", response.status_code)
        print("Response content:", response.content.decode('utf-8'))


def get_shift():
    date = datetime.now(pytz.timezone('Asia/Kolkata'))
    hours = date.hour

    if 6 <= hours < 14:
        return 'shift_a'
    elif 14 <= hours < 22:
        return 'shift_b'
    else:
        return 'shift_c'
