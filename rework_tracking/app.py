from flask import render_template
from sqlalchemy import inspect
from rework_tracking import db, create_app
from rework_tracking.apis.forumlations_api import formulations_apis
from rework_tracking.apis.manage_user_api import manage_users_api
from rework_tracking.apis.report_apis import reporting_apis
from rework_tracking.models.batch_details import RunningBatch, Formulation, FormulationStatus, ScrapType
from rework_tracking.models.machines import Cascade, Machine, MachineReaderType
from rework_tracking.models.tags import ScannedTag, SubmittedTag, FailedProcessingTag
from rework_tracking.models.users import User, UserType, UserStatus
from rework_tracking.apis.rendering_apis import rendering_apis
from rework_tracking.apis.data_management_apis import data_management_apis
from rework_tracking.apis.auth_apis import auth_apis
from rework_tracking.apis.tag_reader_apis import tag_reader_apis
from rework_tracking.apis.tag_verifier_apis import tag_verifier_apis

app = create_app()


def setup_database():
    with app.app_context():
        # db.metadata.create_all(db.engine, tables=[User.__table__, Cascade.__table__, Machine.__table__,
        #                                           ScannedTag.__table__,
        #                                           SubmittedTag.__table__,
        #                                           FailedProcessingTag.__table__,
        #                                           RunningBatch.__table__,
        #                                           Formulation.__table__, ])

        db.create_all()
        if not User.query.filter_by(user_type=UserType.ADMIN).first():
            admin = User(user_id='admin',
                         employee_id='admin',
                         name='Default Admin',
                         username='admin',
                         password='admin',
                         user_type=UserType.ADMIN,
                         user_status=UserStatus.ACTIVE)
            db.session.add(admin)

        if not User.query.filter_by(user_type=UserType.OPERATOR).first():
            operator = User(user_id='operator',
                            employee_id='operator',
                            name='Default Operator',
                            username='operator',
                            password='operator_password',
                            user_type=UserType.OPERATOR,
                            user_status=UserStatus.ACTIVE)
            db.session.add(operator)

        if not User.query.filter_by(user_type=UserType.SUPERVISOR).first():
            supervisor = User(user_id='supervisor',
                              employee_id='supervisor',
                              name='Default Supervisor',
                              username='supervisor',
                              password='supervisor_password',
                              user_type=UserType.SUPERVISOR,
                              user_status=UserStatus.ACTIVE)
            db.session.add(supervisor)

        add_machines()
        add_formulations()
        add_scrap_types()


def add_machines():
    cascade_a = Cascade(cascade_id='cascade_a',
                        cascade_name='Cascade B',
                        cascade_description='Cascade B',
                        created_by='admin',
                        updated_by='admin')
    cascade_b = Cascade(cascade_id='cascade_b',
                        cascade_name='Cascade C',
                        cascade_description='Cascade C',
                        created_by='admin',
                        updated_by='admin')

    plodder_1_a = Machine(machine_id='plodder_1_a',
                          machine_name='Cascade B Plodder',
                          machine_reader_type=MachineReaderType.SCANNER,
                          machine_type='plodder',
                          cascade_id='cascade_a',
                          created_by='admin',
                          updated_by='admin')

    chill_drum_a = Machine(machine_id='chill_drum_a',
                           machine_name='Cascade B ChilledDrum',
                           machine_reader_type=MachineReaderType.SCANNER,
                           machine_type='chill_drum',
                           cascade_id='cascade_a',
                           created_by='admin',
                           updated_by='admin')

    plodder_2_b = Machine(machine_id='plodder_2_b',
                          machine_name='Cascade C Plodder',
                          machine_reader_type=MachineReaderType.SCANNER,
                          machine_type='plodder',
                          cascade_id='cascade_b',
                          created_by='admin',
                          updated_by='admin')

    chill_drum_b = Machine(machine_id='chill_drum_b',
                           machine_name='Cascade C ChilledDrum',
                           machine_reader_type=MachineReaderType.SCANNER,
                           machine_type='chill_drum',
                           cascade_id='cascade_b',
                           created_by='admin',
                           updated_by='admin')

    mixer_a = Machine(machine_id='mixer_a',
                      machine_name='Cascade B Mixer',
                      machine_reader_type=MachineReaderType.VERIFIER,
                      verifier_display_machine_ip='192.168.1.143',
                      machine_type='mixer',
                      cascade_id='cascade_a',
                      created_by='admin',
                      updated_by='admin')

    mixer_b = Machine(machine_id='mixer_b',
                      machine_name='Cascade C Mixer',
                      machine_reader_type=MachineReaderType.VERIFIER,
                      verifier_display_machine_ip='192.168.1.144',
                      machine_type='mixer',
                      cascade_id='cascade_b',
                      created_by='admin',
                      updated_by='admin')

    if not Cascade.query.filter_by(cascade_id='cascade_a').first():
        db.session.add(cascade_a)
    if not Cascade.query.filter_by(cascade_id='cascade_b').first():
        db.session.add(cascade_b)
    if not Machine.query.filter_by(machine_id='plodder_1_a').first():
        db.session.add(plodder_1_a)
    if not Machine.query.filter_by(machine_id='chill_drum_a').first():
        db.session.add(chill_drum_a)
    if not Machine.query.filter_by(machine_id='plodder_2_b').first():
        db.session.add(plodder_2_b)
    if not Machine.query.filter_by(machine_id='chill_drum_b').first():
        db.session.add(chill_drum_b)
    if not Machine.query.filter_by(machine_id='mixer_a').first():
        db.session.add(mixer_a)
    if not Machine.query.filter_by(machine_id='mixer_b').first():
        db.session.add(mixer_b)

    db.session.commit()


def add_formulations():
    formulation_1 = Formulation(name='Formulation 1',
                                status=FormulationStatus.ACTIVE,
                                created_by='admin',
                                deleted_by=None)
    formulation_2 = Formulation(name='Formulation 2',
                                status=FormulationStatus.ACTIVE,
                                created_by='admin',
                                deleted_by=None)
    formulation_3 = Formulation(name='Formulation 3',
                                status=FormulationStatus.ACTIVE,
                                created_by='admin',
                                deleted_by=None)

    if not Formulation.query.filter_by(name='Formulation 1').first():
        db.session.add(formulation_1)
    if not Formulation.query.filter_by(name='Formulation 2').first():
        db.session.add(formulation_2)
    if not Formulation.query.filter_by(name='Formulation 3').first():
        db.session.add(formulation_3)

    db.session.commit()


def add_scrap_types():
    metal_scrap = ScrapType(id='metal',
                            name='Metal',
                            created_by='admin',
                            updated_by='admin')
    non_metal_scrap = ScrapType(id='non_metal',
                                name='Non Metal',
                                created_by='admin',
                                updated_by='admin')
    if not ScrapType.query.filter_by(id='metal').first():
        db.session.add(metal_scrap)
    if not ScrapType.query.filter_by(id='non_metal').first():
        db.session.add(non_metal_scrap)

    db.session.commit()


def serialize_model(obj):
    serialized = {}
    for column in inspect(obj.__class__).attrs:
        serialized[column.key] = getattr(obj, column.key)
    return serialized


def register_endpoints():
    app.register_blueprint(rendering_apis)
    app.register_blueprint(data_management_apis)
    app.register_blueprint(auth_apis)
    app.register_blueprint(tag_reader_apis)
    app.register_blueprint(tag_verifier_apis)
    app.register_blueprint(formulations_apis)
    app.register_blueprint(reporting_apis)
    app.register_blueprint(manage_users_api)


if __name__ == '__main__':
    register_endpoints()
    setup_database()
    app.run(debug=True, host='192.168.1.11', port=5005)
