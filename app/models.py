from app import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    password_hash = db.Column(db.String(128), nullable=False)
    subscription_id = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, nullable=False)

    account_active = db.Column(db.Boolean, nullable=False)

    subsciptions = db.relationship('Subscription', backref='user', lazy=True)
    routes = db.relationship('Route', backref='user', lazy=True)

    # returns as dict so can be used for search bar
    def email_as_dict(self):
        return {'email': self.email}

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128))
    upload_time = db.Column(db.DateTime)
    gpx_data = db.Column(db.LargeBinary)


class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    monthly_cost = db.Column(db.Float)


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'))
    date_start = db.Column(db.DateTime, nullable=False)
    date_end = db.Column(db.DateTime)