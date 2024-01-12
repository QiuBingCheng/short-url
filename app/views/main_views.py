from datetime import timedelta, timezone
from flask import request, render_template, jsonify, redirect, url_for, session
from app.database.models import UrlMapping, TracingRecord
from app import app
from app.util.util import get_client_information
import base62


@app.route('/', methods=('GET', 'POST'))
def home():
    print("home")
    if request.method == 'POST':

        url = request.form['url']
        max_id = UrlMapping.get_max_id()
        token = base62.encode(max_id)
        short_url = f'{app.config["HOST"]}/{token}'
        user = UrlMapping(short_url, url)
        user.save()
        print(short_url, url)
        return redirect(url_for("trace", tracing_code=token))

    return render_template('index.html')


@app.route('/trace/<tracing_code>')
def trace(tracing_code):
    short_url = f"{app.config['HOST']}/{tracing_code}"
    url_mapping = UrlMapping.query.filter_by(
        short_url=short_url).first_or_404()
    long_url = url_mapping.long_url
    tracing_url = '{}/trace/{}'.format(
        app.config["HOST"], tracing_code)

    # query the visit records of the trace
    records_of_the_url = TracingRecord.query.filter_by(
        tracing_code=tracing_code).all()
    for record in records_of_the_url:
        record.created_time = record.created_time.astimezone(
            timezone(timedelta(hours=8)))
        record.date = record.created_time.strftime('%Y-%m-%d %H:%M:%S')
        latitude, longitude = record.location.split(",")
        record.latitude = latitude
        record.longitude = longitude
        record.user_agent = "".join(
            [s+"#" if s == ")" else s.strip() for s in record.user_agent]).split("#")
    return render_template('track.html', records=records_of_the_url,
                           short_url=short_url,
                           long_url=long_url,
                           tracing_code=tracing_code,
                           tracing_url=tracing_url,
                           )


@app.route('/<tracing_code>')
def redirect_url(tracing_code):
    short_url = f"{app.config['HOST']}/{tracing_code}"

    url_mapping = UrlMapping.query.filter_by(
        short_url=short_url).first_or_404()

    info = get_client_information(request)

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
            tracing_code = url.short_url.replace(
                app.config["HOST"]+"/", "")
            url_mapping[i].tracing_url = '{}/trace/{}'.format(
                app.config["HOST"], tracing_code)
            url_mapping[i].created_time = url_mapping[i].created_time.strftime(
                '%Y-%m-%d %H:%M:%S')
        return render_template("admin.html", url_mapping=url_mapping)
    else:
        return redirect(url_for("login"), code=302)


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/validate", methods=["GET"])
def validate_user():
    username = request.args.get("username")
    password = request.args.get("password")

    if (app.config["USERNAME"] == username and app.config["PASSWORD"] == password):
        session.permanent = True
        session["logged_in"] = True
        return jsonify("success")
    else:
        return jsonify("fail!")


@app.route("/logout")
def logout():
    session["logged_in"] = False
    return redirect(url_for("login"), code=302)


@app.route("/delete_ajax", methods=["GET"])
def delete_ajax():
    if not session.get('logged_in'):
        return redirect(url_for("login"), code=302)

    try:
        Id = int(request.args.get("Id"))
        url = UrlMapping.query.get(Id)
        tracing_code = url.short_url.replace(
            app.config["DOMAIN_NAME"]+"/", "")
        records = TracingRecord.query.filter_by(
            tracing_code=tracing_code).all()

        # delete mapping
        url.delete()
        # delete records
        for record in records:
            record.delete()
        return jsonify("success")
    except Exception as e:
        print(str(e))
        return jsonify("fail!")


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404
