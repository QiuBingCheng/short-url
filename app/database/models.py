from app import db
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class ModelBase():

    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, unique=True, index=True)
    created_time = db.Column(db.DateTime, default=datetime.datetime.now)

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
            return True, 'Success'

    def delete(self):
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as error_msg:
            db.session.rollback()
            return False, error_msg
        else:
            return True, 0


class User(UserMixin, db.Model, ModelBase):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, unique=True, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_time = db.Column(db.DateTime, default=datetime.datetime.now)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    activated_time = db.Column(db.DateTime, default=None)
    role = db.Column(db.String(20), default='user', nullable=False)

    # Define the one-to-many relationship
    url_mappings = db.relationship('UrlMapping', backref='user', lazy=True)

    def __init__(self, username, email, password, role=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role

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
    tracing_record = db.relationship(
        'TracingRecord', backref='url_mapping', lazy=True)

    def __init__(self, tracing_code, long_url, user_id):
        self.user_id = user_id
        self.tracing_code = tracing_code
        self.long_url = long_url

    def __repr__(self):
        return f"<UrlMapping id={self.id}, tracing_code={self.tracing_code}>"


class TracingRecord(db.Model, ModelBase):
    __tablename__ = 'tracing_record'

    ip = db.Column(db.String(64), nullable=False)
    port = db.Column(db.String(8), nullable=False)
    location = db.Column(db.String(25))
    user_agent = db.Column(db.String(256))

    # Define the foreign key relationship
    tracing_code = db.Column(db.String(64), db.ForeignKey(
        'url_mapping.tracing_code'), unique=True, nullable=False)

    def __init__(self, tracing_code, ip, port, location, user_agent
                 ):
        self.tracing_code = tracing_code
        self.ip = ip
        self.port = port
        self.location = location
        self.user_agent = user_agent

    def __repr__(self):
        return f"<TracingRecord tracing_code={self.tracing_code}, created_time={self.created_time}>"
