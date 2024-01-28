from flask_script import Command
from app.database.models import User, UrlMapping, TracingRecord
from app import app
from app.lib.db_operation import delete_all_records
import logging


class InitDataCommand(Command):
    """ Initialize the data."""

    def run(self):
        clear_data()
        init_data()


def clear_data():
    tables = [TracingRecord, UrlMapping, User]
    for table in tables:
        delete_all_records(table)


def init_data():
    # create admin data
    user = User(username=app.config["USERNAME"],
                password=app.config["PASSWORD"],
                email=app.config["MAIL"],
                is_authenticated=True, role="admin")
    user.save()
    logging.info(f"{user} has been added.")
