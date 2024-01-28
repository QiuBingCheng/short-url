# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.

from app.lib.user_manager import CurrentUserManager
from flask import Flask, render_template, jsonify
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from google.cloud.sql.connector import Connector, IPTypes
import logging
logging.basicConfig(level=logging.INFO)
# %%

app = Flask(__name__)

# Instantiate Flask extensions
db = SQLAlchemy()
migrate = Migrate()
connector = Connector()
mail = Mail()
user_manager = CurrentUserManager()
# Initialize Flask Application


def create_app():

    env = "production"
    settings = "app.local_settings" if env == "development" else "app.settings"
    app.config.from_object(settings)

    # Setup Flask-SQLAlchemy
    def getconn():
        # Python Connector database connection function
        conn = connector.connect(
            # Cloud SQL Instance Connection Name
            app.config["CLOUD_SQL_INSTANCE"],
            "pymysql",
            user=app.config["DB_USER"],
            password=app.config["DB_PASSWORD"],
            db=app.config["DB_NAME"],
            ip_type=IPTypes.PUBLIC
        )
        return conn

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "creator": getconn
    }
    db.init_app(app)

    # Setup Flask-Migrate
    migrate.init_app(app, db)

    # Setup Flask-Mail
    mail.init_app(app)

    # Register blueprints
    from .views import register_blueprints
    register_blueprints(app)

    #
    from .database.models import User
    user_manager.set_user_model(User)
    ########################
    #### error handlers ####
    ########################

    @app.errorhandler(400)
    def bad_request(error):
        print(error)
        return jsonify(error='Bad Request', message=str(error.description)), 400

    @app.errorhandler(404)
    def page_not_found(error):
        print(error)
        return render_template("errors/404.html"), 404

    @app.errorhandler(409)
    def conflict_error(error):
        print(error)
        return jsonify(error='Conflict', message=str(error.description)), 409

    @app.errorhandler(500)
    def server_error(error):
        print(error)
        return jsonify(error='Error', message=str(error.description)), 500

    return app
