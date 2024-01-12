# This file is used for hosting at PythonAnywhere.com
# 'app' must point to a Flask Application object.

from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run()
