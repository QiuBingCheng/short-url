import os
import json
import requests
from datetime import datetime, timedelta, timezone
from app.util.converter import base62_encode
from flask import request, render_template, jsonify, redirect, url_for, session
from app.database.models import UrlMapping, TracingRecord
from app import app
# import pytz
# %%


def get_client_information(request):
    # ip
    if 'HTTP_X_REAL_IP' in request.environ:
        ip = request.environ.get('HTTP_X_REAL_IP')
    elif 'CF-Connecting-IP' in request.headers:
        ip = request.headers['CF-Connecting-IP']
    elif request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.environ.get('REMOTE_ADDR')

    # port
    port = request.environ.get('REMOTE_PORT')

    # user_agent
    user_agent = request.environ.get('HTTP_USER_AGENT')

    # get location
    try:
        url = "http://api.ipstack.com/{}?access_key={}".format(
            ip, app.config["IPSTACK_API_KEY"])
        response = requests.get(url)
        identity = json.loads(response.text)
        longitude = identity["longitude"]
        latitude = identity["latitude"]
        location = f"{round(latitude,6)},{round(longitude,6)}"
    except:
        location = "NA,NA"

    info = {"ip": ip, "port": port, "user_agent": user_agent,
            "location": location
            }
    return info


def get_url_max_id():
    url = db.session.query(db.func.max(UrlMapping.Id)).first()
    return url[0]+1 if url[0] is not None else 1


@app.route('/', methods=('GET', 'POST'))
def home():
    print("home")
    if request.method == 'POST':

        url = request.form['url']
        max_id = get_url_max_id()
        token = base62_encode(max_id)
        short_url = f'{app.config["HOST"]}/{token}'
        user = UrlMapping(short_url, url)
        user.save()
        return redirect(url_for("trace", tracing_code=token))

    return render_template('index.html')


@app.route('/trace/<tracing_code>')
def trace(tracing_code):
    short_url = '{}/{}'.format(app.config["HOST"], tracing_code)
    url_mapping = UrlMapping.query.filter_by(
        short_url=short_url).first_or_404()
    long_url = url_mapping.long_url
    tracing_url = '{}/trace/{}'.format(
        app.config["HOST"], tracing_code)

    # 檢查有無紀錄
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
        print(record.user_agent)
    return render_template('track.html', records=records_of_the_url,
                           short_url=short_url,
                           long_url=long_url,
                           tracing_code=tracing_code,
                           tracing_url=tracing_url,
                           )


@app.route('/<tracing_code>')
def redirect_url(tracing_code):
    print(tracing_code)
    short_url = '{}/{}'.format(app.config["DOMAIN_NAME"], tracing_code)

    url_mapping = UrlMapping.query.filter_by(
        short_url=short_url).first_or_404()
    print(url_mapping.long_url)

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
