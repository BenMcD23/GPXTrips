import pytest
from flask import url_for
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path='tests/test.env')

stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
    "price_id_1_week": os.environ["STRIPE_PRICE_ID_1_WEEK"],
    "price_id_1_month": os.environ["STRIPE_PRICE_ID_1_MONTH"],
    "price_id_1_year": os.environ["STRIPE_PRICE_ID_1_YEAR"],
}

from app import app, db, bcrypt, models

# Pytest fixture to create a test client for Flask
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

# Test cases for user registration functionality
def test_successful_registration(client):
    # Send a POST request with valid registration data
    response = client.post(
        url_for('register'),
        data={
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'password',
            'confirm_password': 'password',
            'TandCConfirm': True
        },
    )

    # Check if the user is redirected to the login page
    assert response.status_code == 302
    assert response.location == url_for('login', _external=True)


def test_duplicate_email_registration(client):
    test_user = models.User(email='test@example.com', password_hash=bcrypt.generate_password_hash('password').decode('utf-8'), date_created=datetime.now(), account_active=True, manager=False)
    db.session.add(test_user)
    db.session.commit()

    # Send a POST request with email that already has an account
    response = client.post(
        url_for('register'),
        data={
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'password',
            'confirm_password': 'password',
            'TandCConfirm': True
        },
    )
    
    # Check if the user is redirected to the registration page
    assert response.status_code == 302
    assert response.location == url_for('register', _external=True)


def test_password_mismatch_registration(client):
    # Send a POST request with mismatched passwords
    response = client.post(
        url_for('register'),
        data={
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'password',
            'confirm_password': 'mismatched_password',
            'TandCConfirm': True
        },
    )

    # Check if the user is redirected to the registration page
    assert response.status_code == 302
    assert response.location == url_for('register', _external=True)


def test_registration_with_false_TandCConfirm(client):
    # Send a POST request with TandCConfirm set to False
    response = client.post(
        url_for('register'),
        data={
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'password',
            'confirm_password': 'password',
            'TandCConfirm': None
        },
    )

    # Check if the user is redirected to the registration page
    assert response.status_code == 302
    assert response.location == url_for('register', _external=True)


def test_login_successful_user(client):
    # Create a test user
    test_user = models.User(email='test@example.com', password_hash=bcrypt.generate_password_hash('password').decode('utf-8'), date_created=datetime.now(), account_active=True, manager=False)
    db.session.add(test_user)
    db.session.commit()

    # Send a POST request with valid credentials
    response = client.post(url_for('login'), data={'email': 'test@example.com', 'password': 'password', 'rememberMe': False})

    # Check if the user is redirected to the user page
    assert response.status_code == 302
    assert response.location == url_for('user', _external=True)


def test_login_successful_manager(client):
    # Create a test user
    test_user = models.User(email='test@example.com', password_hash=bcrypt.generate_password_hash('password').decode('utf-8'), date_created=datetime.now(), account_active=True, manager=True)
    db.session.add(test_user)
    db.session.commit()

    # Send a POST request with valid credentials
    response = client.post(url_for('login'), data={'email': 'test@example.com', 'password': 'password', 'rememberMe': False})

    # Check if the user is redirected to the manager page
    assert response.status_code == 302
    assert response.location == url_for('manager', _external=True)


def test_invalid_password(client):
    # Create a test user
    test_user = models.User(email='test@example.com', password_hash=bcrypt.generate_password_hash('password').decode('utf-8'), date_created=datetime.now(), account_active=True, manager=False)
    db.session.add(test_user)
    db.session.commit()

    # Send a POST request with invalid password
    response = client.post(url_for('login'), data={'email': 'test@example.com', 'password': 'wrong_password', 'rememberMe': False})

    # Check if the user is redirected to the login page
    assert response.status_code == 302
    assert response.location == url_for('login', _external=True)


def test_deactivated_account(client):
    # Create a test user
    test_user = models.User(email='test@example.com', password_hash=bcrypt.generate_password_hash('password').decode('utf-8'), date_created=datetime.now(), account_active=False, manager=False)
    db.session.add(test_user)
    db.session.commit()

    # Send a POST request with credentials to a deactivated account
    response = client.post(url_for('login'), data={'email': 'test@example.com', 'password': 'password', 'rememberMe': False})

    # Check if the user is redirected to the login page
    assert response.status_code == 302
    assert response.location == url_for('login', _external=True)


def test_nonexistent_account(client):
    # Send a POST request with invalid credentials
    response = client.post(url_for('login'), data={'email': 'nonexistent@example.com', 'password': 'password', 'rememberMe': False})

    # Check if the user is redirected to the login page
    assert response.status_code == 302
    assert response.location == url_for('login', _external=True)