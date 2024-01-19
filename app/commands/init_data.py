from flask_script import Command
from app.database.models import User
from app import app
from app.lib.db_operation import delete_one_record


class InitDataCommand(Command):
    """ Initialize the data."""

    def run(self):
        init_data()
        print('Some user data has been created.')


def init_data():
    # anonymous user data
    delete_one_record(User, {"email": app.config["ANONY_MAIL"]})
    user = User(username=app.config["ANONY_NAME"], password=app.config["ANONY_PASS"],
                email=app.config["ANONY_MAIL"])
    user.save()

    # admin user data
    delete_one_record(User, {"email": app.config["MAIL"]})
    user = User(username=app.config["USERNAME"], password=app.config["PASSWORD"],
                email=app.config["MAIL"], role="admin")
    user.save()
