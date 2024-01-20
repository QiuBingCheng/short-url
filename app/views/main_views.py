
from flask import request, render_template, jsonify, redirect, url_for, session
from app.database.models import UrlMapping, TracingRecord, User
from app import app
from app.lib.util import is_admin, date_str, make_short_url, make_tracing_url
from app.lib.request_parser import get_client_info
from app.lib.db_operation import (next_token, anonymous_user_id,
                                  delete_records,
                                  get_record_by_id)

FAIL = "fail"
SUCCESS = "success"


@app.route('/', methods=('GET', 'POST'))
def home():
    if request.method == 'POST':
        url = request.form['url']
        token = next_token()

        # If user not logged in, default anonymous user will be used to store the mapping record.
        id_ = anonymous_user_id()
        user = UrlMapping(tracing_code=token, long_url=url, user_id=id_)
        user.save()
        return redirect(url_for("trace", tracing_code=token))

    return render_template('index.html')


@app.route('/trace/<tracing_code>')
def trace(tracing_code):
    url_mapping = UrlMapping.query.filter_by(
        tracing_code=tracing_code).first_or_404()
    short_url = make_short_url(tracing_code)
    tracing_url = make_tracing_url(tracing_code)

    # query the visit records of the trace
    records_of_the_url = TracingRecord.query.filter_by(
        tracing_code=tracing_code).all()
    for record in records_of_the_url:
        record.date = date_str(record.created_time)
        latitude, longitude = record.location.split(",")
        record.latitude = latitude
        record.longitude = longitude
        record.user_agent = "".join(
            [s+"#" if s == ")" else s.strip() for s in record.user_agent]).split("#")
    return render_template('track.html', records=records_of_the_url,
                           short_url=short_url,
                           long_url=url_mapping.long_url,
                           tracing_code=tracing_code,
                           tracing_url=tracing_url,
                           )


@app.route('/<tracing_code>')
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


@app.route("/admin", methods=["GET"])
def admin():
    if session.get('logged_in'):
        url_mapping = UrlMapping.query.all()
        for i, url in enumerate(url_mapping):
            url_mapping[i].short_url = make_short_url(url.tracing_code)
            url_mapping[i].tracing_url = make_tracing_url(url.tracing_code)
            url_mapping[i].created_time = date_str(url_mapping[i].created_time)
        return render_template("admin.html", url_mapping=url_mapping)
    else:
        return redirect(url_for("login"), code=302)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        print(request.form)
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user is None:
            print(f"{username} doesn't exist in database")
            return jsonify(FAIL)

        result = user.check_password(password)
        if not result:
            print("password is not correct.")
            return jsonify(FAIL)

        return jsonify(SUCCESS)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session["logged_in"] = False
    return redirect(url_for("login"), code=302)


@app.route("/delete_record", methods=["GET"])
def delete_record():
    if not session.get('logged_in'):
        return redirect(url_for("login"), code=302)

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


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404
