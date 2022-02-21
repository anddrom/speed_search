import os

from functools import wraps
from flask import redirect, render_template, session, url_for
from urllib.parse import urlencode
from authlib.integrations.flask_client import OAuth
from decouple import config
from manage import auth0

from . import auth

AUTH0_CALLBACK_URL = config('AUTH0_CALLBACK_URL')
AUTH0_CLIENT_ID = config('AUTH0_CLIENT_ID')
AUTH0_CLIENT_SECRET = config('AUTH0_CLIENT_SECRET')
AUTH0_DOMAIN = config('AUTH0_DOMAIN')
AUTH0_BASE_URL = 'https://' + AUTH0_DOMAIN
AUTH0_AUDIENCE = config('AUTH0_AUDIENCE')


# Controllers API
@auth.route('/')
def home():
    return render_template('auth/index.html')


@auth.route('/callback')
def callback_handling():
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session[config('JWT_PAYLOAD')] = userinfo
    session[config('PROFILE_KEY')] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture']
    }

    return redirect('/dashboard')


@auth.route('/login')
def login():
    return auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL, audience=AUTH0_AUDIENCE)


@auth.route('/logout')
def logout():
    session.clear()
    params = {'returnTo': url_for('home', _external=True), 'client_id': AUTH0_CLIENT_ID}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))
