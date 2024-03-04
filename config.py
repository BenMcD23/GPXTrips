import os
import stripe
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = True
WTF_CSRF_ENABLED = True

# sets a random secret key each run
# logs out user after server re run so commented out for now until production
# SECRET_KEY = secrets.token_urlsafe(16)

SECRET_KEY = "Key"


stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
    "price_id": os.environ["STRIPE_PRICE_ID"],
}