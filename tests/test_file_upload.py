import pytest
from flask import url_for
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
    "price_id_1_week": os.environ["STRIPE_PRICE_ID_1_WEEK"],
    "price_id_1_month": os.environ["STRIPE_PRICE_ID_1_MONTH"],
    "price_id_1_year": os.environ["STRIPE_PRICE_ID_1_YEAR"],
}

from app import app, db, bcrypt, models

@pytest.fixture
def client():
    # Setting up Flask app configuration for testing
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SERVER_NAME'] = 'localhost'
    app.config['SESSION_COOKIE_DOMAIN'] = 'localhost.localdomain'
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    
    # Creating a test client with a context manager
    with app.test_client() as client:
        with app.app_context():
            # Creating and dropping the database for each test
            db.create_all()
            yield client
            db.drop_all()


'''def test_user_upload_valid_gpx(client):
    # Login a user
    client.post('/', data={'email': 'test@example.com', 'password': 'password'})

    # Access the user page
    response = client.get('/user')

    # Submit a valid GPX file
    gpx_file_path = 'tests/gpxFiles/valid.gpx'
    with open(gpx_file_path, 'rb') as gpx_file:
        response = client.post('/user', data={'file_upload': (gpx_file, 'valid.gpx')}, follow_redirects=True)

    # Assert that the GPX file is uploaded successfully
    assert b"GPX file uploaded successfully!" in response.data


def test_user_upload_invalid_gpx(client):
    # Login a user
    client.post('/', data={'email': 'test@example.com', 'password': 'testpassword'})

    # Access the user page
    response = client.get('/user')

    # Submit an invalid GPX file
    gpx_file_path = 'tests/gpxFiles/invalid.gpx'
    with open(gpx_file_path, 'rb') as gpx_file:
        response = client.post('/user', data={'file_upload': (gpx_file, 'invalid.gpx')}, follow_redirects=True)

    # Assert that an error message is flashed
    assert b"Invalid GPX file structure." in response.data'''