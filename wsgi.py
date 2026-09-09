# wsgi.py
from dash_app import app

# Gunicorn için server export et
server = app.server

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8051)
