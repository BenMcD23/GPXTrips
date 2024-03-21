import pytest
from flask import url_for
from datetime import datetime
from dotenv import load_dotenv
import os
from unittest.mock import patch

# Load environment variables from test.env file
load_dotenv(dotenv_path='tests/test.env')

# Stripe keys configuration for testing
stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
    "price_id_1_week": os.environ["STRIPE_PRICE_ID_1_WEEK"],
    "price_id_1_month": os.environ["STRIPE_PRICE_ID_1_MONTH"],
    "price_id_1_year": os.environ["STRIPE_PRICE_ID_1_YEAR"],
}

# Import Flask app, database, bcrypt, and models for testing
from app import app, db, bcrypt, models


@pytest.fixture
def client():
    """
    Fixture for setting up Flask app configuration and database for testing.
    """
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
            hashed_password = bcrypt.generate_password_hash(
                "password").decode('utf-8')
            user = models.User(email='test@example.com', first_name='first_name', last_name='last_name',
                        password_hash=hashed_password, date_created=datetime.now(), account_active=True, manager=False)
            plan = models.Plan(name="Weekly", price=10.00, stripe_price_id = stripe_keys['price_id_1_week'])
            subscription = models.Subscription(user_id=user.id, plan_id=plan.id, date_start=datetime.now(), date_end=datetime(2025, 5, 17), active=True)
            db.session.add(user)
            db.session.add(plan)
            user.subscriptions.append(subscription)
            db.session.commit()
            yield client
            db.drop_all()


def test_user_upload_valid_gpx(client):
    """
    Test file upload with a valid GPX file.
    """
    # Simulate user login
    client.post(url_for('login'), data={'email': 'test@example.com', 'password': 'password', 'rememberMe': True})

    # Perform file upload
    with open('tests/gpxFiles/valid.gpx', 'rb') as f:
        data = {'file': (f, 'valid.gpx')}
        with patch('app.views.is_valid_gpx_structure', return_value=True):
            response = client.post('/upload', data=data, content_type='multipart/form-data')

            # Assert that the GPX file is uploaded successfully
            assert response.status_code == 200
            assert response.get_json() == {'message': 'File uploaded successfully'}


def test_user_upload_invalid_gpx(client):
    """
    Test file upload with an invalid GPX file.
    """
    # Simulate user login
    client.post(url_for('login'), data={'email': 'test@example.com', 'password': 'password', 'rememberMe': True})

    # Perform file upload
    with open('tests/gpxFiles/invalid.gpx', 'rb') as f:
        data = {'file': (f, 'invalid.gpx')}
        with patch('app.views.is_valid_gpx_structure', return_value=False):
            response = client.post('/upload', data=data, content_type='multipart/form-data')

            assert response.status_code == 400
            assert response.get_json() == {'error': 'Invalid GPX file structure'}


def test_user_upload_invalid_extension(client):
    """
    Test file upload with an invalid file extension.
    """
    # Simulate user login
    client.post(url_for('login'), data={'email': 'test@example.com', 'password': 'password', 'rememberMe': True})

    # Perform file upload with an invalid file extension
    with open('tests/gpxFiles/wrongExtension.txt', 'rb') as f:
        data = {'file': (f, 'wrongExtension.txt')}
        response = client.post('/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 400
    assert response.get_json() == {'error': 'File extension is not GPX'}


def test_download_file_success(client):
    """
    Test file download with an existing file route.
    """
    # Simulate user login
    client.post(url_for('login'), data={'email': 'test@example.com', 'password': 'password', 'rememberMe': True})

    # Create a mock route in the database
    route = models.Route(user_id=1, name='Test Route', upload_time=datetime.now(), gpx_data=b'<gpx>Test GPX Data</gpx>')
    db.session.add(route)
    db.session.commit()

    # Request to download the file
    response = client.get(f'/download/{route.id}')

    # Assert that the response is successful and contains the GPX data as an attachment
    assert response.status_code == 200
    assert response.headers['Content-Disposition'] == f'attachment; filename={route.name.replace(" ", "_")}'


def test_download_file_route_not_found(client):
    """
    Test file download with a non existing file route.
    """
    # Simulate user login
    client.post(url_for('login'), data={'email': 'test@example.com', 'password': 'password', 'rememberMe': True})

    # Request to download a non-existent route
    response = client.get('/download/999')

    # Assert that the response returns a 404 error
    assert response.status_code == 404
    assert response.get_json() == {'error': 'Route not found'}