
from flask_migrate import MigrateCommand
from flask_script import Manager

from app import create_app
from app.commands import InitDbCommand, InitDataCommand

# Setup Flask-Script with command line commands
manager = Manager(create_app)
manager.add_command('db', MigrateCommand)
manager.add_command('init_db', InitDbCommand)
manager.add_command('init_data', InitDataCommand)

if __name__ == "__main__":
    # python manage.py                      # shows available commands
    # python manage.py runserver --help     # shows available runserver options
    manager.run()
