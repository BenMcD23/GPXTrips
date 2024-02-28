import pytest
from app import app, db, bcrypt
from app.models import User
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    with app.app_context():
        db.drop_all()

def test_registration(client):
    data = {
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'password123',
        'confirm_password': 'password123',
        'plan': 'plan1',
    }
    response = client.post('/register', data=data, follow_redirects=True)
    assert b"User added successfully!" in response.data

def test_registration_password_mismatch(client):
    data = {
        'email': 'testuser@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'password123',
        'confirm_password': 'password456',  # Mismatched password
        'plan': 'plan1',
    }
    response = client.post('/register', data=data, follow_redirects=True)
    assert b"Passwords do not match." in response.data


def test_registration_existing_user(client):
    existing_user = User(email='testuser@example.com', password_hash=bcrypt.generate_password_hash('password123'), date_created=datetime.now())
    db.session.add(existing_user)
    db.session.commit()

    data = {
        'email': 'testuser@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'password123',
        'confirm_password': 'password123',
        'plan': 'plan1',
    }
    response = client.post('/register', data=data, follow_redirects=True)
    assert b"Email already in use." in response.data

def test_login(client):
    # Create a user for testing login
    user = User(email='testuser@example.com', password_hash=bcrypt.generate_password_hash('password123'), date_created=datetime.now())
    db.session.add(user)
    db.session.commit()

    data = {
        'email': 'testuser@example.com',
        'password': 'password123',
    }
    response = client.post('/', data=data, follow_redirects=True)
    assert b"Logged in!" in response.data

def test_login_incorrect_password(client):
    # Create a user for testing
    user = User(email='testuser@example.com', password_hash=bcrypt.generate_password_hash('password123'), date_created=datetime.now())
    db.session.add(user)
    db.session.commit()

    response = client.post('/', data={
        'email': 'testuser@example.com',
        'password': 'password456',
    }, follow_redirects=True)

    assert b'Password is wrong!' in response.data

def test_login_nonexistent_user(client):
    data = {
        'email': 'testuser@example.com',
        'password': 'password123',
    }
    response = client.post('/', data=data, follow_redirects=True)
    assert b"Account does not exist!" in response.data
