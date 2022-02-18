import os

from functools import wraps
from flask import redirect, session
from authlib.integrations.flask_client import OAuth
from app import create_app

flask_app = create_app()

AUTH0_CALLBACK_URL = flask_app.config['AUTH0_CALLBACK_URL']
AUTH0_CLIENT_ID = flask_app.config['AUTH0_CLIENT_ID']
AUTH0_CLIENT_SECRET = flask_app.config['AUTH0_CLIENT_SECRET']
AUTH0_DOMAIN = flask_app.config['AUTH0_DOMAIN']
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = flask_app.config['AUTH0_AUDIENCE']

oauth = OAuth(flask_app)

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


if __name__ == '__main__':
    flask_app.run(debug = True, host = "0.0.0.0")
