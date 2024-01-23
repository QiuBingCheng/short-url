
from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from app.database.models import UrlMapping, TracingRecord, User
from datetime import datetime
from app.lib.util import date_str, make_short_url, make_tracing_url
from app.lib.request_parser import get_client_info
from app.lib.db_operation import (generate_tracing_code, admin_id,
                                  delete_records,
                                  get_record_by_id)
from app.lib.token import generate_token, confirm_token
from app.lib.mail import send_email
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

        if not current_user.is_anonymous:
            logged = True
            username = current_user.username

        print(current_user)
        print(logged, username, current_user.is_active)
        return render_template('index.html', logged=logged,
                               username=username,
                               is_active=current_user.is_active)

    elif request.method == 'POST':
        long_url = request.form['long_url']
        token = generate_tracing_code()

        # If user not logged in, admin will be used to store mapping record.
        id_ = current_user.user_id if current_user else admin_id()
        user = UrlMapping(tracing_code=token, long_url=long_url, user_id=id_)
        user.save()
        short_url = make_short_url(token)
        return jsonify({"short_url": short_url})


@main_blueprint.route('/trace/<tracing_code>')
def trace(tracing_code):
    url_mapping = UrlMapping.query.filter_by(
        tracing_code=tracing_code).first_or_404()

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
                           short_url=make_short_url(tracing_code),
                           long_url=url_mapping.long_url,
                           tracing_code=tracing_code,
                           tracing_url=make_tracing_url(tracing_code),
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


@main_blueprint.route('/confirm_email/<token>')
@login_required
def confirm_email(token):

    error_msg = "The confirmation link is invalid or has expired."

    if current_user.is_active:
        print(f"{current_user} already confirmed.")
        return redirect(url_for("main.home"))

    email = confirm_token(token)
    user = User.query.filter_by(email=current_user.email).first_or_404()

    if user.email == email:
        user.is_active = True
        user.activated_time = datetime.now(TIME_ZONE)
        user.save()
        print(f"{user} confirmed the account")
        return redirect(url_for("main.home"))

    print(error_msg)
    return jsonify(error_msg)


@main_blueprint.route('/register', methods=('GET', 'POST'))
def register():

    if request.method == 'POST':
        print(request.form)
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        try:
            # save user data
            user = User(email=email, password=password, username=username)
            user.save()
            user = User.query.filter_by(email=email).first()

            # send mail verification
            token = generate_token(user.email)
            confirm_url = url_for("confirm_email",
                                  token=token, _external=True)
            html = render_template("confirm_email.html",
                                   confirm_url=confirm_url)
            subject = "Please confirm your email"
            send_email(user.email, subject, html)
            login_user(user, force=True)

            return jsonify(SUCCESS)

        except Exception as e:
            print(e)
            return jsonify(FAIL)

    return render_template("register.html", code=302)


@main_blueprint.route("/admin", methods=["GET"])
@login_required
def admin():
    if current_user.is_active:
        url_mapping = UrlMapping.query.filter_by(
            user_id=current_user.user_id).all()
        for i, url in enumerate(url_mapping):
            url_mapping[i].short_url = make_short_url(url.tracing_code)
            url_mapping[i].tracing_url = make_tracing_url(url.tracing_code)
            url_mapping[i].created_time = date_str(url_mapping[i].created_time)
        return render_template("admin.html", url_mapping=url_mapping)

    return redirect(url_for("main.login"), code=302)


@main_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user is None:
            msg = f"username {username} doesn't exist"
            print(msg)
            return jsonify({"flag": FAIL, "msg": msg})

        result = user.check_password(password)
        if not result:
            msg = "password is not correct."
            print(msg)
            return jsonify({"flag": FAIL, "msg": msg})

        if not user.is_active:
            msg = "account is not activated yet"
            print(msg)
            return jsonify({"flag": FAIL, "msg": msg})

        login_user(user)
        print(f"Successfully logged in.{user}")
        return redirect(url_for("main.home"), code=302)

    return render_template("login.html")


@main_blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.login"), code=302)


@main_blueprint.route("/delete_record", methods=["GET"])
def delete_record():
    if current_user is None:
        return redirect(url_for("main.login"), code=302)

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
