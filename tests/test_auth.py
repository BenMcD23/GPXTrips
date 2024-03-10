import pytest
from flask import url_for
from flask_testing import TestCase
from app import app, db, bcrypt
from app.models import User
from datetime import datetime

class TestLogin(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SERVER_NAME'] = 'localhost'
        app.config['APPLICATION_ROOT'] = '/'
        app.config['PREFERRED_URL_SCHEME'] = 'https'

        app.app_context().push()
        return app

    def setUp(self):
        self.client = app.test_client()
        db.create_all()

        hashed_password = bcrypt.generate_password_hash('test_password').decode('utf-8')
        user = User(email='test@example.com', password_hash=hashed_password, date_created=datetime.now())
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.drop_all()

    def follow_redirect(self, response, expected_final_path):
        assert response.status_code == 302  # Check if it's a redirect

        # Manually follow the redirect
        response = self.client.get(response.location, follow_redirects=True)

        # Check the final destination URL after following the redirect
        assert response.status_code == 200  # Adjust this status code based on your expected final destination
        assert response.request.path == expected_final_path

    def test_successful_login(self):
        response = self.client.post(
            url_for('login'),
            data={'email': 'test@example.com', 'password': 'test_password'},
            follow_redirects=False
        )
        self.follow_redirect(response, url_for('user'))

    def test_invalid_password(self):
        response = self.client.post(
            url_for('login'),
            data={'email': 'test@example.com', 'password': 'wrong_password'},
            follow_redirects=False
        )
        self.follow_redirect(response, url_for('login'))

    def test_nonexistent_account(self):
        response = self.client.post(
            url_for('login'),
            data={'email': 'nonexistent@example.com', 'password': 'test_password'},
            follow_redirects=False
        )
        self.follow_redirect(response, url_for('login'))

    def test_successful_registration(self):
        response = self.client.post(
            url_for('register'),
            data={
                'email': 'test2@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'test_password',
                'confirm_password': 'test_password',
                'plan': 'option1'
            },
            follow_redirects=False
        )
        self.follow_redirect(response, url_for('login'))

    def test_duplicate_email_registration(self):
        response = self.client.post(
            url_for('register'),
            data={
                'email': 'test@example.com',
                'first_name': 'Another',
                'last_name': 'User',
                'password': 'another_password',
                'confirm_password': 'another_password',
                'plan': 'option2'
            },
            follow_redirects=False
        )
        self.follow_redirect(response, url_for('register'))

    def test_password_mismatch_registration(self):
        response = self.client.post(
            url_for('register'),
            data={
                'email': 'test@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'test_password',
                'confirm_password': 'mismatched_password',
                'plan': 'option3'
            },
            follow_redirects=False
        )
        self.follow_redirect(response, url_for('register'))