from app import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    password_hash = db.Column(db.String(128), nullable=False)
    subscription_id = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, nullable=False)

    subsciptions = db.relationship('Subscription', backref='user', lazy=True)
    routes = db.relationship('Route', backref='user', lazy=True)


class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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
