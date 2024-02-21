from app import db
from flask_login import UserMixin

# many to many relationship
# many users can have many routes
UserRoutes = db.Table('UserRoutes',
    db.Column('route_id', db.Integer, db.ForeignKey('route.id'),
              primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'),
              primary_key=True)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    password_hash = db.Column(db.String(128), nullable=False)
    subscription_id = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, nullable=False)

    subsciptions = db.relationship('Subscription', backref='user', lazy=True)

    # relationship to Routes, many to many
    routes = db.relationship('Routes', secondary=UserRoutes,
                              back_populates="user", lazy='dynamic')


class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gpx_data = db.Column(db.LargeBinary)

    # relationship back to User, many to many
    user = db.relationship('User', secondary=UserRoutes,
                            back_populates="routes", lazy='dynamic')

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
