from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import pytz

TIME_ZONE = pytz.timezone('Asia/Taipei')


class ModelBase():

    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, unique=True, index=True)
    created_time = db.Column(db.DateTime, default=datetime.now(TIME_ZONE))

    def to_dict(self):
        return {key: getattr(self, key) for key in self.__table__.columns.keys()}

    def save(self):
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as erorr_msg:
            db.session.rollback()
            return False, erorr_msg
        else:
            return True, f"{self} is saved!"

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as error_msg:
            db.session.rollback()
            return False, error_msg
        else:
            return True, 0


class User(db.Model, ModelBase):
    __tablename__ = 'user'

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_authenticated = db.Column(db.Boolean, default=False)
    authenticated_time = db.Column(db.DateTime, default=None)
    role = db.Column(db.String(20), default='user', nullable=False)

    # Define the one-to-many relationship
    url_mappings = db.relationship('UrlMapping', backref='user', lazy=True)

    def __init__(self, username, email, password, role=None, is_authenticated=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
        self.is_authenticated = is_authenticated

    def __repr__(self):
        return f"<User id={self.id}, email={self.email}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UrlMapping(db.Model, ModelBase):
    __tablename__ = 'url_mapping'

    tracing_code = db.Column(db.String(64), unique=True, nullable=False)
    long_url = db.Column(db.String(512), nullable=False)

    # Define the foreign key relationship
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Define the one-to-many relationship
    tracing_records = db.relationship(
        'TracingRecord', backref='url_mapping', lazy=True)

    def __init__(self, tracing_code, long_url, user_id):
        self.user_id = user_id
        self.tracing_code = tracing_code
        self.long_url = long_url

    def __repr__(self):
        return f"<UrlMapping id={self.id}, tracing_code={self.tracing_code}, user_id={self.user_id}>"


class TracingRecord(db.Model, ModelBase):
    __tablename__ = 'tracing_record'

    ip = db.Column(db.String(64), nullable=False)
    port = db.Column(db.String(8), nullable=False)
    location = db.Column(db.String(25))
    user_agent = db.Column(db.String(256))

    # Define the foreign key relationship
    tracing_code = db.Column(db.String(64), db.ForeignKey(
        'url_mapping.tracing_code'), nullable=False)

    def __init__(self, tracing_code, ip, port, location, user_agent
                 ):
        self.tracing_code = tracing_code
        self.ip = ip
        self.port = port
        self.location = location
        self.user_agent = user_agent

    def __repr__(self):
        return f"<TracingRecord id={self.id}, tracing_code={self.tracing_code}, created_time={self.created_time}>"
