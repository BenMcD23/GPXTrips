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

    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    account_active = db.Column(db.Boolean, nullable=False)

    manager = db.Column(db.Boolean, nullable=False)

    routes = db.relationship('Route', backref='user', lazy=True)

    # returns as dict so can be used for search bar
    def email_as_dict(self):
        return {'email': self.email}

    # returns if current user is manager or not
    def is_manager(self):
        if self.manager == True:
            return True

        else:
            return False

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
    stripe_price_id = db.Column(db.String(255), nullable=False)


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'))
    subscription_id = db.Column(db.String(255))
    date_start = db.Column(db.DateTime, nullable=False)
    date_end = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)

    plan = db.relationship('Plan', backref='subscriptions')

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))