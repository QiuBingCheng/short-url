

from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from app.database.models import User
from datetime import datetime
from app.lib.token import generate_token, confirm_token
from app.lib.mail import send_email
import pytz

FAIL = "fail"
SUCCESS = "success"

member_blueprint = Blueprint('member', __name__, template_folder='templates')

TIME_ZONE = pytz.timezone('Asia/Taipei')


@member_blueprint.route("/login", methods=["GET", "POST"])
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

    elif request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for("main.home"), code=302)

        return render_template("login.html")


@member_blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.login"), code=302)


@member_blueprint.route('/confirm_email/<token>')
@login_required
def confirm_email(token):

    error_msg = "The confirmation link is invalid or has expired."

    if current_user.is_confirmed:
        print(f"{current_user} already confirmed.")
        return redirect(url_for("main.home"))

    email = confirm_token(token)
    user = User.query.filter_by(email=current_user.email).first_or_404()

    if user.email == email:
        user.is_confirmed = True
        user.confirmed_time = datetime.now(TIME_ZONE)
        user.save()
        print(f"{user} confirmed the account")
        return redirect(url_for("main.home"))

    print(error_msg)
    return jsonify(error_msg)


@member_blueprint.route('/register', methods=('GET', 'POST'))
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
            confirm_url = url_for("main.confirm_email",
                                  token=token, _external=True)
            html = render_template("confirm_email.html",
                                   confirm_url=confirm_url)
            subject = "Please confirm your email"
            send_email(user.email, subject, html)
            login_user(user)
            return redirect(url_for("main.inactive"))

        except Exception as e:
            print(e)
            return jsonify(FAIL)

    return render_template("register.html", code=302)


@member_blueprint.route("/inactive")
@login_required
def inactive():
    if current_user.is_active:
        return redirect(url_for("main.home"))
    return render_template("inactive.html")
