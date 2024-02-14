from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), unique=True)
    password_hash = db.Column(db.String(128))
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'))
    date_created = db.Column(db.DateTime)

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    gpx_data = db.Column(db.LargeBinary)

class Plan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monthly_cost = db.Column(db.Decimal)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'))
    date_start = db.Column(db.DateTime)
    date_end = db.Column(db.DateTime)
