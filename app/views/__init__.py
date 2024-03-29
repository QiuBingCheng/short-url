# __init__.py is a special Python file that allows a directory to become
# a Python package so it can be accessed using the 'import' statement.

from .main_views import main_blueprint
from .member_views import member_blueprint


def register_blueprints(app):
    app.register_blueprint(main_blueprint)
    app.register_blueprint(member_blueprint)
