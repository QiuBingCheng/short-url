# This file is used for hosting at PythonAnywhere.com
# 'app' must point to a Flask Application object.

from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(
        os.environ.get('PORT', 8080)), debug=False)
