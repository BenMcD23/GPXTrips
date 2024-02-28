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

# Fixture to create a new user and handle session cleanup
@pytest.fixture
def new_user():
    user = User(email='testuser@example.com', password_hash=bcrypt.generate_password_hash('password123'), date_created=datetime.now())
    return user  # Do not commit the user here

def test_registration(client):
    data = {
        'email': 'test@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'password123',
        'confirm_password': 'password123',
    }
    response = client.post('/register', data=data, follow_redirects=True)
    assert b"User added successfully!" in response.data

def test_registration_password_mismatch(client):
    data = {
        'email': 'testuser@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'password123',
        'confirm_password': 'password456',
    }
    response = client.post('/register', data=data, follow_redirects=True)
    assert b"Passwords do not match." in response.data

def test_registration_existing_user(client, new_user):
    with app.app_context():
        db.session.add(new_user)
        db.session.commit()
    data = {
        'email': 'testuser@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'password': 'password123',
        'confirm_password': 'password123',
    }
    response = client.post('/register', data=data, follow_redirects=True)
    assert b"Email already in use." in response.data

def test_login(client, new_user):
    with app.app_context():
        db.session.add(new_user)
        db.session.commit()
    data = {
        'email': 'testuser@example.com',
        'password': 'password123',
    }
    response = client.post('/', data=data, follow_redirects=True)
    assert b"Logged in!" in response.data

def test_login_incorrect_password(client, new_user):
    with app.app_context():
        db.session.add(new_user)
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