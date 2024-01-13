# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.

from flask import Flask
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from dotenv import load_dotenv

# Instantiate Flask extensions
# Instantiate Flask
app = Flask(__name__)
db = SQLAlchemy()
migrate = Migrate()
load_dotenv()
# Initialize Flask Application


def create_app():
    """Create a Flask application.
    """
    # Load common settings
    app.config.from_object('app.settings')

    # Setup Flask-SQLAlchemy
    db.init_app(app)

    # Setup Flask-Migrate
    migrate.init_app(app, db)

    from app.views import main_views
    return app
