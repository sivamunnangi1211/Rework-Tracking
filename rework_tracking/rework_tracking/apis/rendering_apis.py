import datetime
from operator import or_

import pytz
import requests
from flask import Blueprint, render_template, request

from rework_tracking import db
from rework_tracking.apis.auth_decorador import login_required
from rework_tracking.models.batch_details import Formulation, FormulationStatus, ScannerMachineFormulationMapping, \
    RunningBatch, RunningBatchStatus
from rework_tracking.models.machines import Machine, Cascade, MachineReaderType

rendering_apis = Blueprint('rendering_apis', __name__)


@rendering_apis.route('/running_batch')
@login_required
def running_batch():
    formulations = Formulation.query.filter_by(status=FormulationStatus.ACTIVE).all()
    formulations = [{'id': formulation.id, 'name': formulation.name} for formulation in formulations]
    cascades = Cascade.query.all()
    cascades = [{'id': cascade.cascade_id, 'name': cascade.cascade_name} for cascade in cascades]
    running_batches_from_db = (db.session.query(RunningBatch, Cascade)
                               .join(Cascade, RunningBatch.cascade_id == Cascade.cascade_id)
                               .filter(or_(RunningBatch.running_status == RunningBatchStatus.RUNNING,
                                           RunningBatch.running_status == RunningBatchStatus.NOT_STARTED))
                               .order_by(RunningBatch.created_at.desc()).all())
    running_batches = []

    for batch in running_batches_from_db:
        if batch[0].to_date_millis > datetime.datetime.now(pytz.timezone('Asia/Kolkata')).timestamp() * 1000:
            running_batches.append(batch)

    if running_batches:
        running_batches = [{'id': batch[0].id,
                            'cascade_id': batch[0].cascade_id,
                            'cascade_name': batch[0].cascade_name,
                            'formulation_id': batch[0].formulation_id,
                            'formulation_name': batch[0].formulation_name,
                            'from_date': batch[0].from_date.strftime("%Y-%m-%dT%H:%M"),
                            'to_date': batch[0].to_date.strftime("%Y-%m-%dT%H:%M")} for batch in running_batches]
    else:
        running_batches = []

    return render_template('running_batch.html',
                           formulations=formulations,
                           cascades=cascades,

                           min_from_date=datetime.datetime.now().strftime("%Y-%m-%dT00:00"),
                           running_batches=running_batches)


@rendering_apis.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')


@rendering_apis.route('/generation')
@login_required
def generation():
    return render_template('reports/age_report.html')


@rendering_apis.route('/consumption')
@login_required
def consumption():
    return render_template('reports/consumption_report.html')


@rendering_apis.route('/')
@login_required
def home():
    machine_ids = request.args.get('machine_ids')
    print('Getting details for remote address:', request.remote_addr)
    machine_ids = machine_ids if machine_ids else get_default_machine_ids(request.remote_addr)
    if machine_ids:
        machine_ids = machine_ids.split(',')
        results = (db.session.query(Machine, Cascade)
                   .join(Cascade, Machine.cascade_id == Cascade.cascade_id)
                   .filter(Machine.machine_id.in_(machine_ids))
                   .filter(Machine.machine_reader_type == MachineReaderType.SCANNER)
                   .all())
        if not results:
            results = (db.session.query(Machine, Cascade)
                       .join(Cascade, Machine.cascade_id == Cascade.cascade_id)
                       .filter(Machine.machine_reader_type == MachineReaderType.SCANNER)
                       .all())
    else:
        results = (db.session.query(Machine, Cascade)
                   .join(Cascade, Machine.cascade_id == Cascade.cascade_id)
                   .filter(Machine.machine_reader_type == MachineReaderType.SCANNER)
                   .all())

    formulations = Formulation.query.filter_by(status=FormulationStatus.ACTIVE).all()
    formulations = [{'id': formulation.id, 'name': formulation.name} for formulation in formulations]
    scrap_types = [{
        'id': 'metal',
        'name': 'Metal'
    },
        {
            'id': 'non_metal',
            'name': 'Non Metal'
        }]

    details = []
    for result in results:
        existing_association = ScannerMachineFormulationMapping.query.filter_by(machine_id=result[0].machine_id).first()
        details.append({'machine_id': result[0].machine_id,
                        'machine_name': result[0].machine_name,
                        'machine_type': result[0].machine_type,
                        'cascade_id': result[0].cascade_id,
                        'cascade_name': result[1].cascade_name,
                        'formulation_id': existing_association.formulation_id if existing_association else None,
                        'formulation_name': existing_association.formulation_name if existing_association else None,
                        'scrap_type_id': existing_association.scrap_type_id if existing_association else None,
                        'scrap_type_name': existing_association.scrap_type_name if existing_association else None})

    return render_template('home.html', machines=details,
                           formulations=formulations,
                           scrap_types=scrap_types)


def get_default_machine_ids(client_ip):
    if client_ip == '192.168.1.160':
        return 'plodder_1_a'
    elif client_ip == '192.168.1.161':
        return 'plodder_2_b'
    elif client_ip == '192.168.1.162':
        return 'chill_drum_a,chill_drum_b'
    else:
        return None
