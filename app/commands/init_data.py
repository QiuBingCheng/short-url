from flask_script import Command
from app.database.models import User
from app import app
from app.lib.db_operation import delete_all_records
import logging


class InitDataCommand(Command):
    """ Initialize the data."""

    def run(self):
        init_data()


def init_data():
    # create admin data
    delete_all_records(User)
    user = User(username=app.config["USERNAME"],
                password=app.config["PASSWORD"],
                email=app.config["MAIL"], role="admin")
    user.save()
    logging.info(f"{user} has been added.")
