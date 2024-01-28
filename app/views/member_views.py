

from flask import (Blueprint, request,
                   render_template, jsonify,
                   redirect, url_for, abort,
                   session
                   )
from app.database.models import User
from datetime import datetime
from app.lib.decorators import login_required
from app.lib.token import generate_token, confirm_token
from app.lib.mail import send_email
import pytz
from app import user_manager
from app.lib.user_manager import ClientType
member_blueprint = Blueprint('member', __name__, template_folder='templates')

TIME_ZONE = pytz.timezone('Asia/Taipei')
# %%


# %%


@member_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        """
        Handles the user login process.
        """
        username = request.form['username']
        password = request.form['password']

        # perform authentication logic
        user = User.query.filter_by(username=username).first()

        if user is None:
            abort(400, description=f"username {username} doesn't exist")

        if not user.is_authenticated:
            abort(400, description='account is not activated yet')

        result = user.check_password(password)
        if not result:
            abort(400, description='password is not correct.')

        # After successful login, check the 'next' parameter
        next_url = request.form.get('next', url_for('main.home'))

        # Attempt to log in the user
        user_manager.login(user.id)
        print(f'Successfully logged in. {user}')

        # [Todo] if user registered before
        # but not verified，send mail agail.

        return redirect(next_url, code=302)

    elif request.method == 'GET':

        if user_manager.user_type == ClientType.VISITOR:
            return render_template('member/login.html')
        elif user_manager.user_type == ClientType.UNVERIFIED_MEMBER:
            return redirect(url_for('member.inactive'), code=302)
        else:
            return redirect(url_for('main.home'), code=302)


@member_blueprint.route('/logout')
def logout():
    user_manager.logout()
    return redirect(url_for('member.login'), code=302)


@member_blueprint.route('/confirm_email/<token>')
def confirm_email(token):
    """
    Handles the email confirmation process using the provided token
    """
    error_msg = 'The confirmation link is invalid or has expired.'

    if user_manager.user_type == ClientType.VERIFIED_MEMBER:
        print(f'{user_manager.user} already confirmed.')
        return redirect(url_for('main.home'))

    email = confirm_token(token)
    user = User.query.filter_by(email=user_manager.user.email).first_or_404()

    if user.email == email:
        user.is_authenticated = True
        user.authenticated_time = datetime.now(TIME_ZONE)
        user.save()
        print(f'{user} confirmed the account')
        return redirect(url_for('main.home'))

    print(error_msg)
    return jsonify(error_msg)

# %%
# register function


def handle_registration():
    """
    Handles the user registration process, including checking for existing users,
    creating a new user, sending a verification email, and logging in the user.
    """
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    check_existing_user(username, email)

    user = create_user(email, password, username)

    send_verification_email(user)
    user_manager.login(user.id)


def check_existing_user(username, email):
    """
    Checks if a user with the given username or email already exists in the database.
    """
    if User.query.filter_by(email=email).first():
        abort(409, description='該信箱已經被註冊，請改用其他信箱~')
    if User.query.filter_by(username=username).first():
        abort(409, description='該使用者名稱已經被註冊，請改用其他名稱~')


def create_user(email, password, username):
    """
    Creates a new user with the provided email, password, and username.
    """

    user = User(email=email, password=password, username=username)
    flag, msg = user.save()
    if not flag:
        print(msg)
        abort(500, description='註冊失敗，請通知網站維護人員~')
    return User.query.filter_by(email=email).first()


def send_verification_email(user):
    """
    Sends a verification email to the provided user.
    """
    token = generate_token(user.email)
    confirm_url = url_for('member.confirm_email', token=token, _external=True)
    html = render_template('member/confirm_email.html',
                           confirm_url=confirm_url)
    subject = 'Please confirm your email'
    send_email(user.email, subject, html)


@member_blueprint.route('/register', methods=('GET', 'POST'))
def register():
    """
    Handles user registration
    """
    if request.method == 'POST':

        handle_registration()
        return redirect(url_for('member.inactive'))

    return render_template('member/register.html', code=302)

# %%


@member_blueprint.route('/inactive')
@login_required
def inactive():
    """
    Renders the 'inactive' page for unverified members.
    """
    if user_manager.user_type == ClientType.VERIFIED_MEMBER:
        return redirect(url_for('main.home'))

    return render_template('member/inactive.html',
                           username=user_manager.user.username)


@member_blueprint.route('/resend')
@login_required
def resend_confirmation():
    """
    Resends the email confirmation to the current user.
    """

    if user_manager.user_type == ClientType.VERIFIED_MEMBER:
        return redirect(url_for('main.home'))

    token = generate_token(user_manager.user.email)
    confirm_url = url_for('member.confirm_email',
                          token=token, _external=True)
    html = render_template('member/confirm_email.html',
                           confirm_url=confirm_url)
    subject = 'Please confirm your email'
    send_email(user_manager.user.email, subject, html)
    return redirect(url_for('member.inactive'))
