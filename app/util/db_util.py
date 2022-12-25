import sqlite3
from flask import g


def get_url_max_id(db):
    url = db.session.query(db.func.max(UrlMapping.Id)).first()
    return url[0]+1 if url[0] is not None else 1
