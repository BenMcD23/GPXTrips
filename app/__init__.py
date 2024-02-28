from flask import Flask, jsonify

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_talisman import Talisman

import os
import stripe

app = Flask(__name__)
app.config.from_object('config')
FLASK_DEBUG=1

# security stuff, conifgured below
talisman = Talisman(app)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

app.app_context().push()

migrate = Migrate(app, db)

from app import views, models

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

# configure talisman
csp = {
    # all the external links
    'default-src': [
        '\'self\'',
        'https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.6/umd/popper.min.js',
        'https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/js/bootstrap.min.js',
        'https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css',
        'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',
        'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
        'https://cdnjs.cloudflare.com/ajax/libs/leaflet-gpx/1.7.0/gpx.min.js',
        'https://unpkg.com/leaflet/dist/leaflet.css',
        'https://a.tile.openstreetmap.org/',
        'https://b.tile.openstreetmap.org/',
        'https://c.tile.openstreetmap.org/',
        'https://js.stripe.com/v3/',
    ],
    # external image links
    'img-src': [
        "'self' data:",
        'https://a.tile.openstreetmap.org/',
        'https://b.tile.openstreetmap.org/',
        'https://c.tile.openstreetmap.org/',
        'https://www.publicdomainpictures.net/pictures/170000/velka/jogging-at-sunset-1461853562JAu.jpg'
    ]
}

# this allows scripts to be used
nonce_list = ['default-src', 'img-src']
# HTTP Strict Transport Security (HSTS) Header
hsts = {
    'max-age': 31536000,
    'includeSubDomains': True
}
# Enforce HTTPS and other headersMou
talisman.force_https = True
talisman.force_file_save = True
talisman.frame_options_allow_from = 'https://www.google.com'
 
# add to Talisman
talisman.content_security_policy = csp
talisman.strict_transport_security = hsts
talisman.content_security_policy_nonce_in = nonce_list

# Stripe

app.stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"]
}

stripe.api_key = app.stripe_keys["secret_key"]