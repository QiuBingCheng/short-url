
from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from app.database.models import UrlMapping, TracingRecord
from app.lib.util import make_short_url, make_tracing_url
from app.lib.user_manager import ClientType
from app.lib.decorators import login_required
from app.lib.request_parser import get_client_info
from app.lib.db_operation import (generate_tracing_code, admin_id,
                                  delete_records,
                                  get_record_by_id)
import pytz
from app import user_manager

main_blueprint = Blueprint('main', __name__, template_folder='templates')

FAIL = 'fail'
SUCCESS = 'success'
TIME_ZONE = pytz.timezone('Asia/Taipei')


@main_blueprint.route('/', methods=('GET', 'POST'))
def home():
    """
    Handles requests to the home page.

    GET:
    - Renders the home page with information about the current user.

    POST:
    - Processes the submitted form data to create a short URL mapping for a long URL.
      If the user is a verified member, the mapping is associated with their account;
      otherwise, the admin account is used.

    """

    if request.method == 'GET':

        client_type = user_manager.user_type
        username = '訪客' if client_type == ClientType.VISITOR else user_manager.user.username

        print(f'Current user: {user_manager.user}')
        print(f'User type: {client_type}')

        return render_template('main/index.html',
                               client_type=client_type.value,
                               username=username)

    elif request.method == 'POST':
        print(request.form)
        long_url = request.form['long_url']
        code = generate_tracing_code()

        # If user not logged in, admin will be used to store mapping record.
        if user_manager.user_type == ClientType.VERIFIED_MEMBER:
            id_ = user_manager.user.id
        else:
            id_ = admin_id()

        url_map = UrlMapping(tracing_code=code,
                             long_url=long_url, user_id=id_)
        success, msg = url_map.save()

        if success:
            short_url = make_short_url(code)
            return jsonify({'short_url': short_url})
        else:
            print(f'Error saving URL mapping: {msg}')
            return jsonify({'error': 'Failed to save URL mapping'}), 500


@main_blueprint.route('/trace/<tracing_code>')
@login_required
def trace(tracing_code):
    '''
    Handles tracing of a short URL by displaying visit records.

    Parameters:
    - tracing_code (str): The unique tracing code associated with the short URL.

    Returns:
    - Renders the 'main/track.html' template with modified visit records and related information.
    '''

    url_mapping = UrlMapping.query.filter_by(
        tracing_code=tracing_code).first_or_404()
    print(url_mapping)

    # Query the visit records of the shorturl
    records_of_the_url = url_mapping.tracing_records
    print(records_of_the_url)

    modified_records = []
    for record in records_of_the_url:
        # Modify some attributes
        date = record.created_time.strftime('%Y-%m-%d %H:%M:%S')
        latitude, longitude = record.location.split(',')
        user_agent = ''.join(
            [s+'#' if s == ')' else s.strip() for s in record.user_agent]).split('#')

        # Store modified record
        modified_record = record.to_dict()
        modified_record['latitude'] = latitude
        modified_record['longitude'] = longitude
        modified_record['date'] = date
        modified_record['user_agent'] = user_agent

        modified_records.append(modified_record)

    return render_template('main/track.html', records=modified_records,
                           short_url=make_short_url(tracing_code),
                           long_url=url_mapping.long_url,
                           created_time=url_mapping.created_time
                           )


@main_blueprint.route('/<tracing_code>')
def redirect_url(tracing_code):
    """
    Redirects to the original long URL associated with the given tracing code.
    """
    url_mapping = UrlMapping.query.filter_by(
        tracing_code=tracing_code).first_or_404()
    client_info = get_client_info(request)

    # create record
    new_record = TracingRecord(tracing_code=tracing_code,
                               ip=client_info.ip,
                               port=client_info.port,
                               location=client_info.location,
                               user_agent=client_info.user_agent)

    success, msg = new_record.save()
    if success:
        return redirect(url_mapping.long_url, code=302)
    else:
        print(f'Error saving TracingRecord: {msg}')
        return render_template('error.html', error='Failed to save tracing record'), 500


@main_blueprint.route('/admin', methods=['GET'])
@login_required
def admin():
    """
    Renders the admin page with URL mappings for the logged-in verified member.
    """
    if user_manager.user_type != ClientType.VERIFIED_MEMBER:
        return redirect(url_for('member.inactive'))

    user = user_manager.user
    url_mappings = user.url_mappings

    modified_records = []
    for url_map in url_mappings:
        modified_record = {
            'id': url_map.id,
            'long_url': url_map.long_url,
            'short_url': make_short_url(url_map.tracing_code),
            'tracing_url': make_tracing_url(url_map.tracing_code),
            'created_time': url_map.created_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        modified_records.append(modified_record)

    return render_template('main/admin.html', url_mappings=modified_records)


@main_blueprint.route('/delete_record', methods=['GET'])
@login_required
def delete_record():
    """
    Deletes a URL mapping and its associated tracing records.

    Returns:
    - JSON response indicating success or failure.
    """

    if user_manager.user_type != ClientType.VERIFIED_MEMBER:
        return redirect(url_for('member.login'), code=302)

    try:
        id = int(request.args.get('id'))

        # Delete related tracing records first
        url_mapping_record = get_record_by_id(UrlMapping, id)
        if url_mapping_record is None:
            return jsonify(FAIL)

        result_tracing = delete_records(
            TracingRecord, {'tracing_code': url_mapping_record.tracing_code})
        result_mapping = delete_records(UrlMapping, {'id': id})

        if result_tracing and result_mapping:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'fail'})

    except ValueError:
        # Handle invalid ID parameter
        return jsonify({'status': 'fail'})
