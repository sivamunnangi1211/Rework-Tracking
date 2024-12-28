import datetime

import pytz
from flask import Blueprint, jsonify, request, session, render_template

from rework_tracking.apis.auth_decorador import login_required
from rework_tracking.models.batch_details import FormulationStatus, Formulation
from rework_tracking import db

formulations_apis = Blueprint('formulations_apis', __name__)


@formulations_apis.route('/formulations/manage', methods=['GET'])
@login_required
def manage_formulations():
    formulations = Formulation.query.filter_by(status=FormulationStatus.ACTIVE).all()
    if formulations:
        formulations = [{'id': formulation.id, 'name': formulation.name} for formulation in formulations]
    else:
        formulations = []
    return render_template('manage_formulations.html', formulations=formulations)


@formulations_apis.route('/formulations', methods=['GET'])
@login_required
def get_formulations():
    formulations = Formulation.query.filter_by(status=FormulationStatus.ACTIVE).all()
    return jsonify(formulations=[formulation.name for formulation in formulations])


@formulations_apis.route('/formulations', methods=['PUT'])
@login_required
def add_formulation():
    data = request.json
    formulation_name = data.get('name')
    if formulation_name:
        new_formulation = Formulation(name=formulation_name,
                                      status=FormulationStatus.ACTIVE,
                                      created_by=session.get('user_id'))

        db.session.add(new_formulation)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Formulation name not provided'})


@formulations_apis.route('/formulations/<int:formulation_id>', methods=['DELETE'])
@login_required
def delete_formulation(formulation_id):
    formulation = Formulation.query.get(formulation_id)
    if formulation:
        formulation.status = FormulationStatus.INACTIVE
        formulation.deleted_at = datetime.datetime.now(pytz.timezone('Asia/Kolkata'))
        formulation.deleted_by = session.get('user_id')
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Formulation not found'})



