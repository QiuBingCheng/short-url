
from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from flask_login import current_user, login_required
from app.database.models import UrlMapping, TracingRecord
from app.lib.util import date_str, make_short_url, make_tracing_url
from app.lib.request_parser import get_client_info
from app.lib.db_operation import (generate_tracing_code, admin_id,
                                  delete_records,
                                  get_record_by_id)
import pytz

main_blueprint = Blueprint('main', __name__, template_folder='templates')

FAIL = "fail"
SUCCESS = "success"
TIME_ZONE = pytz.timezone('Asia/Taipei')


@main_blueprint.route('/', methods=('GET', 'POST'))
def home():

    if request.method == 'GET':

        username = "訪客"
        logged = False
        is_confirmed = False

        if not current_user.is_anonymous:
            logged = True
            username = current_user.username
            is_confirmed = current_user.is_confirmed

        print(f"Current user: {current_user}")
        return render_template('main/index.html', logged=logged,
                               username=username,
                               is_confirmed=is_confirmed)

    elif request.method == 'POST':
        print(request.form)
        long_url = request.form["long_url"]
        token = generate_tracing_code()

        # If user not logged in, admin will be used to store mapping record.
        if current_user.is_authenticated:
            id_ = current_user.id
        else:
            id_ = admin_id()

        url_map = UrlMapping(tracing_code=token,
                             long_url=long_url, user_id=id_)
        url_map.save()
        print(f"{url_map} is saved.")

        short_url = make_short_url(token)
        return jsonify({"short_url": short_url})


@main_blueprint.route('/trace/<tracing_code>')
def trace(tracing_code):
    url_mapping = UrlMapping.query.filter_by(
        tracing_code=tracing_code).first_or_404()
    print(url_mapping)

    # query the visit records of the trace
    records_of_the_url = TracingRecord.query.filter_by(
        tracing_code=tracing_code).all()

    modified_records = []
    for record in records_of_the_url:
        # modify some attribure
        date = date_str(record.created_time)
        latitude, longitude = record.location.split(",")
        user_agent = "".join(
            [s+"#" if s == ")" else s.strip() for s in record.user_agent]).split("#")

        # store modified record
        modified_record = record.to_dict()
        modified_record["latitude"] = latitude
        modified_record["longitude"] = longitude
        modified_record["date"] = date
        modified_record["user_agent"] = user_agent

        modified_records.append(modified_record)

    return render_template('main/track.html', records=modified_records,
                           short_url=make_short_url(tracing_code),
                           long_url=url_mapping.long_url,
                           created_time=url_mapping.created_time
                           )


@main_blueprint.route('/<tracing_code>')
def redirect_url(tracing_code):

    url_mapping = UrlMapping.query.filter_by(
        tracing_code=tracing_code).first_or_404()
    info = get_client_info(request)

    # create record
    new_record = TracingRecord(tracing_code=tracing_code,
                               ip=info["ip"],
                               port=info["port"],
                               location=info["location"],
                               user_agent=info['user_agent'])

    new_record.save()
    return redirect(url_mapping.long_url, code=302)


@main_blueprint.route("/admin", methods=["GET"])
@login_required
def admin():

    print(current_user)
    print(current_user.url_mappings)

    url_mappings = current_user.url_mappings
    for i, url in enumerate(url_mappings):
        url_mappings[i].short_url = make_short_url(url.tracing_code)
        url_mappings[i].tracing_url = make_tracing_url(url.tracing_code)
        url_mappings[i].created_time = date_str(url_mappings[i].created_time)
    return render_template("main/admin.html", url_mappings=url_mappings)


@main_blueprint.route("/delete_record", methods=["GET"])
def delete_record():
    if current_user is None:
        return redirect(url_for("member.login"), code=302)

    id = int(request.args.get("id"))
    # Delete related tracing records at first
    url_mapping_record = get_record_by_id(UrlMapping, id)
    if url_mapping_record is None:
        return jsonify(FAIL)

    result = delete_records(
        TracingRecord, {"tracing_code": url_mapping_record.tracing_code})

    if not result:
        return jsonify(FAIL)

    result = delete_records(UrlMapping, {"id": id})
    if not result:
        return jsonify(FAIL)

    return jsonify(SUCCESS)
