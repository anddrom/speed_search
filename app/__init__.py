import os
from flask import Flask
from authlib.integrations.flask_client import OAuth
from decouple import config

AUTH0_CALLBACK_URL = config('AUTH0_CALLBACK_URL')
AUTH0_CLIENT_ID = config('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = config('AUTH0_CLIENT_SECRET')
AUTH0_DOMAIN = config('AUTH0_DOMAIN')
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = config('AUTH0_AUDIENCE')

def create_app():
    config_name = os.environ.get('FLASK_CONFIG', 'development')

    app = Flask(__name__, static_url_path='/static')
    app.config.from_object('config_' + config_name)

    from .auth import auth as auth_blueprint
    from .home import home as home_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(home_blueprint)

    oauth = OAuth(app)

    auth0 = oauth.register(
        'auth0',
        client_id=AUTH0_CLIENT_ID,
        client_secret=AUTH0_CLIENT_SECRET,
        api_base_url=AUTH0_BASE_URL,
        access_token_url=AUTH0_BASE_URL + '/oauth/token',
        authorize_url=AUTH0_BASE_URL + '/authorize',
        client_kwargs={
            'scope': 'openid profile email',
        },
    )

    return app, auth0
