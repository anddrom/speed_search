import os

from app import create_app

flask_app, auth0 = create_app()


if __name__ == '__main__':
    flask_app.run(debug = True, host = "0.0.0.0")
