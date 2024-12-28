import datetime
import json
from collections import defaultdict
from operator import or_

import pytz
from flask import Blueprint, session, redirect, url_for, render_template

from rework_tracking import db
from rework_tracking.apis.auth_decorador import login_required
from rework_tracking.apis.tag_verifier_apis import get_shift
from rework_tracking.models.batch_details import RunningBatch, RunningBatchStatus
from rework_tracking.models.tags import SubmittedTag, TagProcessingStatus, FailedProcessingTag

reporting_apis = Blueprint('reporting_apis', __name__)
allowed_user_types = ['admin', 'operator', 'supervisor']


@reporting_apis.route('/reports', methods=['GET'])
@login_required
def get_reports_home():
    if (not session.get('user_id')) or session.get('user_type') not in allowed_user_types:
        return redirect(url_for('auth_apis.login'))

    return render_template('reports_home.html')


@reporting_apis.route('/reports/age_report', methods=['GET'])
@login_required
def get_age_report():
    if (not session.get('user_id')) or session.get('user_type') not in allowed_user_types:
        return redirect(url_for('auth_apis.login'))

    submitted_data = (db.session.query(SubmittedTag)
                      .filter(or_(SubmittedTag.processing_status == TagProcessingStatus.PROCESSED,
                                  SubmittedTag.processing_status == TagProcessingStatus.OVERWRITTEN))
                      .order_by(SubmittedTag.submitted_at.desc())
                      .all())
    print(tag.processed_at for tag in submitted_data)
    print(tag.submitted_at for tag in submitted_data)

    report_data = [{'submission_id': tag.submission_id,
                    'tag_id': tag.tag_id,
                    'scanned_cascade_name': tag.scanned_cascade_name,
                    'scanned_machine_name': tag.scanned_machine_name,
                    'scanned_shift': tag.scanned_shift,
                    'formulation_name': tag.formulation_name,
                    'scrap_type_name': tag.scrap_type_name,
                    'processing_status': tag.processing_status.value,
                    'submitted_at': tag.submitted_at,
                    'submitted_datetime': tag.submitted_at.strftime('%d-%m-%Y %H:%M:%S'),
                    'processed_cascade_name': tag.processed_cascade_name,
                    'processing_machine_name': tag.processed_machine_name,
                    'processed_at': tag.processed_at,
                    'processed_datetime': tag.processed_at.strftime(
                        '%d-%m-%Y %H:%M:%S') if tag.processed_at else 'Not Processed',
                    'processed_shift': tag.processed_shift,
                    'age': format_timedelta((tag.processed_at if tag.processed_at else datetime.datetime.now())
                                            - tag.submitted_at)

                    } for tag in submitted_data]

    return render_template('reports/age_report.html', report_data=report_data)


@reporting_apis.route('/reports/consumption_report', methods=['GET'])
@login_required
def get_consumption_report():
    if (not session.get('user_id')) or session.get('user_type') not in allowed_user_types:
        return redirect(url_for('auth_apis.login'))

    one_week_ago = datetime.datetime.now(pytz.timezone('Asia/Kolkata')) - datetime.timedelta(weeks=1)
    submitted_data = (SubmittedTag.query.filter(SubmittedTag.submitted_at >= one_week_ago)
                      .order_by(SubmittedTag.submitted_at.desc())
                      .all())

    results = {}

    current_day = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).date()
    current_shift = get_shift()
    current_week = get_iso_week_number(current_day)
    # Process the data
    for entry in submitted_data:
        if (entry.processed_at is None) or (entry.processing_status != TagProcessingStatus.PROCESSED):
            continue
        machine_id = entry.processed_machine_id
        if results.get(machine_id) is None:
            results[machine_id] = {}
            results[machine_id]['machine_id'] = entry.processed_machine_id
            results[machine_id]['machine_name'] = entry.processed_machine_name
            results[machine_id]['current_day'] = current_day
            results[machine_id]['current_shift'] = current_shift
            results[machine_id]['current_week'] = current_week
            results[machine_id]['metal'] = {}
            results[machine_id]['non_metal'] = {}
            results[machine_id]['total'] = {}
            results[machine_id]['metal']['day_count'] = 0
            results[machine_id]['metal']['shift_count'] = 0
            results[machine_id]['metal']['weekly_count'] = 0
            results[machine_id]['non_metal']['day_count'] = 0
            results[machine_id]['non_metal']['shift_count'] = 0
            results[machine_id]['non_metal']['weekly_count'] = 0
            results[machine_id]['total']['day_count'] = 0
            results[machine_id]['total']['shift_count'] = 0
            results[machine_id]['total']['weekly_count'] = 0

        day_key = entry.submitted_at.date()
        shift = entry.scanned_shift
        week_key = get_iso_week_number(entry.submitted_at)

        if current_day == day_key:
            results[machine_id][entry.scrap_type_id]['day_count'] += 1
            if current_shift == shift:
                results[machine_id][entry.scrap_type_id]['shift_count'] += 1

        if current_week == week_key:
            results[machine_id][entry.scrap_type_id]['weekly_count'] += 1

    for machine_id, machine_info in results.items():
        results[machine_id]['total']['day_count'] = 0
        for category, data in machine_info.items():
            print('Category:', category)
            print('Data:', data)
            print(machine_info)
            if isinstance(data, dict) and 'day_count' in data and category != 'total':
                results[machine_id]['total']['day_count'] += data['day_count']
            if isinstance(data, dict) and 'shift_count' in data and category != 'total':
                results[machine_id]['total']['shift_count'] += data['shift_count']
            if isinstance(data, dict) and 'weekly_count' in data and category != 'total':
                results[machine_id]['total']['weekly_count'] += data['weekly_count']

    print(results)
    return render_template('reports/consumption_report.html', report_data=results)


@reporting_apis.route('/reports/submitted_report', methods=['GET'])
@login_required
def get_tagged_report():
    if (not session.get('user_id')) or session.get('user_type') not in allowed_user_types:
        return redirect(url_for('auth_apis.login'))

    submitted_data = (SubmittedTag.query.order_by(SubmittedTag.submitted_at.desc())
                      .limit(100).all())
    submitted_data = [{'submission_id': tag.submission_id,
                       'tag_id': tag.tag_id,
                       'scanned_cascade_name': tag.scanned_cascade_name,
                       'scanned_machine_name': tag.scanned_machine_name,
                       'scanned_shift': tag.scanned_shift,
                       'formulation_name': tag.formulation_name,
                       'scrap_type_name': tag.scrap_type_name,
                       'processing_status': tag.processing_status.value,
                       'submitted_at': tag.submitted_at,
                       'submitted_datetime': tag.submitted_at.strftime('%d-%m-%Y %H:%M:%S'),
                       'processed_cascade_name': tag.processed_cascade_name,
                       'processed_machine_name': tag.processed_machine_name if tag.processed_machine_name else '',
                       'processed_at': tag.processed_at if tag.processed_at is not None else '',
                       'processed_datetime': tag.processed_at.strftime('%d-%m-%Y %H:%M:%S') if tag.processed_at else '',
                       'processed_shift': tag.processed_shift,
                       } for tag in submitted_data]

    return render_template('reports/submitted_report.html', report_data=submitted_data)


@reporting_apis.route('/reports/rework_generation_report', methods=['GET'])
@login_required
def get_rework_generation_report():
    if (not session.get('user_id')) or session.get('user_type') not in allowed_user_types:
        return redirect(url_for('auth_apis.login'))

    one_week_ago = datetime.datetime.now(pytz.timezone('Asia/Kolkata')) - datetime.timedelta(weeks=1)
    submitted_data = (SubmittedTag.query.filter(SubmittedTag.submitted_at >= one_week_ago)
                      .order_by(SubmittedTag.submitted_at.desc())
                      .all())

    results = {}

    current_day = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).date()
    current_shift = get_shift()
    current_week = get_iso_week_number(current_day)

    # Process the data
    for entry in submitted_data:
        scrap_type_id = entry.scrap_type_id
        if results.get(scrap_type_id) is None:
            results[scrap_type_id] = {}
            results[scrap_type_id]['scrap_type_id'] = entry.scrap_type_id
            results[scrap_type_id]['scrap_type_name'] = entry.scrap_type_name
            results[scrap_type_id]['current_day'] = current_day
            results[scrap_type_id]['current_shift'] = current_shift
            results[scrap_type_id]['current_week'] = current_week
            results[scrap_type_id]['day_count'] = 0
            results[scrap_type_id]['shift_count'] = 0
            results[scrap_type_id]['weekly_count'] = 0

        day_key = entry.submitted_at.date()
        shift = entry.scanned_shift
        week_key = get_iso_week_number(entry.submitted_at)

        print('Week key:', week_key)
        print('Current day:', current_day)
        print('Day key:', day_key)
        print('Shift:', shift)
        print('Current shift:', current_shift)

        # current_day - datetime.timedelta(days=1)
        if current_day == day_key:
            results[scrap_type_id]['day_count'] += 1
            if current_shift == shift:
                results[scrap_type_id]['shift_count'] += 1

        if current_week == week_key:
            results[scrap_type_id]['weekly_count'] += 1

    results['total'] = {}
    results['total']['day_count'] = sum([results[key]['day_count']
                                         for key in results if 'day_count' in results[key]])
    results['total']['shift_count'] = sum([results[key]['shift_count']
                                           for key in results if 'shift_count' in results[key]])
    results['total']['weekly_count'] = sum([results[key]['weekly_count']
                                            for key in results if 'weekly_count' in results[key]])

    print(results)
    return render_template('reports/rework_generation_report.html', report_data=results)


@reporting_apis.route('/reports/running_batch_report', methods=['GET'])
@login_required
def get_running_batch_report():
    if (not session.get('user_id')) or session.get('user_type') not in allowed_user_types:
        return redirect(url_for('auth_apis.login'))

    running_batch = (RunningBatch.query.order_by(RunningBatch.created_at.desc())
                     .limit(100).all())
    current_millis = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).timestamp() * 1000
    if running_batch:
        running_batch_data = [{'running_batch_id': batch.id,
                               'cascade_id': batch.cascade_id,
                               'cascade_name': batch.cascade_name,
                               'formulation_id': batch.formulation_id,
                               'formulation_name': batch.formulation_name,
                               'start_datetime': batch.from_date.strftime('%d-%m-%Y %H:%M:%S'),
                               'end_datetime': batch.to_date.strftime('%d-%m-%Y %H:%M:%S'),
                               'batch_status': get_batch_status(batch)} for batch in running_batch]
    else:
        running_batch_data = []

    return render_template('reports/running_batch_report.html', report_data=running_batch_data)


@reporting_apis.route('/reports/rejected_tags_report', methods=['GET'])
@login_required
def get_rejected_tags_report():
    if (not session.get('user_id')) or session.get('user_type') not in allowed_user_types:
        return redirect(url_for('auth_apis.login'))
    failed_processing_tags = (db.session.query(FailedProcessingTag, SubmittedTag)
                              .join(SubmittedTag, SubmittedTag.submission_id == FailedProcessingTag.submission_id)
                              .order_by(FailedProcessingTag.created_at.desc())
                              .limit(100).all())

    # print(type(failed_processing_tags))
    #
    # for failed_tag, submitted_tag in failed_processing_tags:
    #     print('\n\n\nTag details:')
    #     for key, value in failed_tag.__dict__.items():
    #         if not key.startswith('_'):
    #             print(f"{key}: {value}")
    #     print('\nSubmitted tag details:')
    #     for key, value in failed_tag.__dict__.items():
    #         if not key.startswith('_'):
    #             print(f"{key}: {value}")

    report_data = [{'tag_id': failed_tag.tag_id,
                    'formulation_name': submitted_tag.formulation_name,
                    'scrap_type_name': submitted_tag.scrap_type_name,
                    'submitted_datetime': submitted_tag.submitted_at.strftime('%d-%m-%Y %H:%M:%S'),
                    'rejected_datetime': failed_tag.created_at.strftime('%d-%m-%Y %H:%M:%S'),
                    'rejected_machine_name': failed_tag.scanned_machine_name,
                    'rejected_cascade_name': failed_tag.scanned_cascade_name,
                    'rejection_reason': failed_tag.failure_reason.value,
                    } for failed_tag, submitted_tag in failed_processing_tags]

    return render_template('reports/rejected_tags_report.html', report_data=report_data)


# Helper function to get the ISO week date
def get_iso_week_number(date):
    iso_year, iso_week_number, iso_weekday = date.isocalendar()
    return iso_week_number


def get_batch_status(batch):
    current_millis = datetime.datetime.now(pytz.timezone('Asia/Kolkata')).timestamp() * 1000
    if (batch.running_status != RunningBatchStatus.STOPPED) and (
            batch.from_date_millis < current_millis <= batch.to_date_millis):
        return RunningBatchStatus.RUNNING.name
    elif batch.running_status == RunningBatchStatus.STOPPED:
        return RunningBatchStatus.STOPPED.name
    elif batch.from_date_millis > current_millis:
        return RunningBatchStatus.NOT_STARTED.name
    else:
        return RunningBatchStatus.ENDED.name


def format_timedelta(td):
    # Get the total days from timedelta
    days = td.days
    # Convert remaining seconds to hours (ignoring minutes and seconds)
    hours = td.seconds // 3600  # There are 3600 seconds in one hour

    # Create a formatted string
    if days > 0 and hours > 0:
        return f"{days} days, {hours} hours"
    elif days > 0:
        return f"{days} days"
    elif hours > 0:
        return f"{hours} hours"
    else:
        return "0 hours"
