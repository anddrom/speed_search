import os
from flask import Flask

def create_app():
    config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(__name__, static_url_path='/static')
    app.config.from_object('config_' + config_name)

    from .home import home as home_blueprint
    app.register_blueprint(home_blueprint)

    return app
