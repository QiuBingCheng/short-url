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
    delete_one_record(User, {"email": "fake@gmail.com"})
    user = User(username="anonymous", password="123456",
                email="fake@gmail.com")
    user.save()

    # admin user data
    delete_one_record(User, {"email": app.config["MAIL"]})
    user = User(username=app.config["USERNAME"], password=app.config["PASSWORD"],
                email=app.config["MAIL"], role="admin")
    user.save()
