import os
from app import create_app
from app.extensions import socketio

app = create_app(os.environ.get('FLASK_ENV', 'development'))


def create_gunicorn_app():

    return app


if __name__ == '__main__':

    socketio.run(
        app,
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=5000,
        use_reloader=True,
        log_output=True
    )