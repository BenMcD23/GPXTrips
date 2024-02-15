# test_app.py
import pytest
from flask import url_for
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm
from app.models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = "Key"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_registration(client):
    response = client.get('/register')
    assert response.status_code == 200

    data = {
        'username': 'testuser',
        'password': 'password123',
        'confirm_password': 'password123',
    }
    response = client.post('/register', data=data, follow_redirects=True)
    assert b"User added successfully!" in response.data

def test_registration_password_mismatch(client):
    data = {
        'username': 'testuser',
        'password': 'password123',
        'confirm_password': 'password456',  # Mismatched password
    }
    response = client.post('/register', data=data, follow_redirects=True)
    assert b"Passwords do not match." in response.data


def test_registration_existing_user(client):
    # Create a user with the same username
    existing_user = User(username='testuser', password='hashed_password')
    db.session.add(existing_user)
    db.session.commit()

    data = {
        'username': 'testuser',
        'password': 'password123',
        'confirm_password': 'password123',
    }
    response = client.post('/register', data=data, follow_redirects=True)
    assert b"Username already taken." in response.data

def test_login(client):
    # Create a user for testing login
    hashed_password = bcrypt.generate_password_hash('password123')
    user = User(username='testuser', password=hashed_password)
    db.session.add(user)
    db.session.commit()

    data = {
        'username': 'testuser',
        'password': 'password123',
    }
    response = client.post('/login', data=data, follow_redirects=True)
    assert b"Logged in!" in response.data

def test_login_incorrect_password(client):
    # Create a user for testing
    hashed_password = bcrypt.generate_password_hash('password')
    user = User(username='testuser', password=hashed_password)
    db.session.add(user)
    db.session.commit()

    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    }, follow_redirects=True)

    assert b'Password is wrong!' in response.data

def test_login_nonexistent_user(client):
    data = {
        'username': 'nonexistentuser',
        'password': 'password123',
    }
    response = client.post('/login', data=data, follow_redirects=True)
    assert b"Username does not exist!" in response.data
