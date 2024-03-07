import pytest
from app import app, db, models, bcrypt
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    client = app.test_client()

    with app.app_context():
        db.create_all()
        # Add a user to the database
        user = models.User(email='test@example.com', password_hash=bcrypt.generate_password_hash('testpassword'), date_created=datetime.now())
        db.session.add(user)
        db.session.commit()

    yield client

    with app.app_context():
        db.session.remove()
        db.drop_all()

def test_user_page_render(client):
    # Login a user
    client.post('/', data={'email': 'test@example.com', 'password': 'testpassword'})

    # Access the user page
    response = client.get('/user')

    # Assert that the page renders successfully
    assert response.status_code == 200
    assert b"Map" in response.data

def test_user_upload_valid_gpx(client, mocker):
    # Mock is_valid_gpx_structure to return True for valid GPX structure
    mocker.patch('app.views.is_valid_gpx_structure', return_value=True)

    # Login a user
    client.post('/', data={'email': 'test@example.com', 'password': 'testpassword'})

    # Access the user page
    response = client.get('/user')

    # Submit a valid GPX file
    gpx_file_path = 'tests/gpxFiles/valid.gpx'
    with open(gpx_file_path, 'rb') as gpx_file:
        response = client.post('/user', data={'file_upload': (gpx_file, 'valid.gpx')}, follow_redirects=True)

    # Assert that the GPX file is uploaded successfully
    assert b"GPX file uploaded successfully!" in response.data

def test_user_upload_invalid_gpx(client, mocker):
    # Mock is_valid_gpx_structure to return False for invalid GPX structure
    mocker.patch('app.views.is_valid_gpx_structure', return_value=False)

    # Login a user
    client.post('/', data={'email': 'test@example.com', 'password': 'testpassword'})

    # Access the user page
    response = client.get('/user')

    # Submit an invalid GPX file
    gpx_file_path = 'tests/gpxFiles/invalid.gpx'
    with open(gpx_file_path, 'rb') as gpx_file:
        response = client.post('/user', data={'file_upload': (gpx_file, 'invalid.gpx')}, follow_redirects=True)

    # Assert that an error message is flashed
    assert b"Invalid GPX file structure. Please upload a valid GPX file." in response.data
