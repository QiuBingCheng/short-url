from itsdangerous import URLSafeTimedSerializer

from app import app


def generate_token(email):
    """
    Generates a secure URL-safe token based on the provided email.
    """
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def confirm_token(token, expiration=3600):
    """
    Confirms and extracts the email from a token.
    """
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token, salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        return email
    except Exception:
        return False
