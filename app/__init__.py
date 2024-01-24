# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.

from flask import Flask, render_template
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from google.cloud.sql.connector import Connector, IPTypes
from flask_login import LoginManager
import logging
logging.basicConfig(level=logging.INFO)
# %%

app = Flask(__name__)

# Instantiate Flask extensions
db = SQLAlchemy()
migrate = Migrate()
connector = Connector()
mail = Mail()
login_manager = LoginManager()

# Initialize Flask Application

# Setup Flask login


login_manager.init_app(app)
login_manager.login_view = "member.login"


@login_manager.user_loader
def load_user(user_id):
    from app.database.models import User
    return User.query.get(user_id)


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

    ########################
    #### error handlers ####
    ########################

    @app.errorhandler(401)
    def unauthorized_page(error):
        return render_template("errors/401.html"), 401

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("errors/500.html"), 500

    return app
