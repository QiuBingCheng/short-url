from app import db
import datetime


class ModelBase():

    Id = db.Column(db.Integer, primary_key=True,
                   autoincrement=True, unique=True, index=True)
    created_time = db.Column(db.DateTime, default=datetime.datetime.now)

    def toDict(self):
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


class UrlMapping(db.Model, ModelBase):
    __tablename__ = 'url_mapping'

    short_url = db.Column(db.String(64))
    long_url = db.Column(db.String(256))

    def __init__(self, short_url, long_url):
        self.short_url = short_url
        self.long_url = long_url

    @classmethod
    def get_max_id(cls):
        url = db.session.query(db.func.max(cls.Id)).first()
        return url[0]+1 if url[0] is not None else 1


class TracingRecord(db.Model, ModelBase):
    __tablename__ = 'tracing_record'

    tracing_code = db.Column(db.String(64))
    ip = db.Column(db.String(64))
    port = db.Column(db.String(8))
    location = db.Column(db.String(25))
    user_agent = db.Column(db.String(256))

    def __init__(self, tracing_code, ip, port, location, user_agent
                 ):
        self.tracing_code = tracing_code
        self.ip = ip
        self.port = port
        self.location = location
        self.user_agent = user_agent
