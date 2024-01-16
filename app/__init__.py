# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from google.cloud.sql.connector import Connector, IPTypes
from dotenv import load_dotenv
import os
import logging
logging.basicConfig(level=logging.INFO, filemode='w',
                    format='[%(asctime)s %(levelname)-8s] %(message)s',
                    datefmt='%Y%m%d %H:%M:%S',
                    )
# %%
app = Flask(__name__)
app.config.from_object('app.settings')

# Update config if it is in env
load_dotenv()
for key in app.config:
    value = os.getenv(key)
    if value is not None:
        app.config[key] = value

app.secret_key = app.config["SECRET_KEY"]

# init import object
db = SQLAlchemy()
migrate = Migrate()
connector = Connector()


def create_app():

    # Python Connector database connection function
    def getconn():
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

    # Setup Flask-SQLAlchemy
    db.init_app(app)
    # Setup Flask-Migrate
    migrate.init_app(app, db)

    from app.views import main_views
    return app
