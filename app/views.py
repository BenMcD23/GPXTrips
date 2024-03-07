from config import stripe_keys
from app import app, db, models, admin, bcrypt
from flask_admin.contrib.sqla import ModelView
from .models import User, Plan, Subscription, Route, StripeCustomer
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .forms import FileUploadForm, RegistrationForm, LoginForm
from werkzeug.utils import secure_filename
from DAL import add_route, get_route
from datetime import datetime, timedelta

import stripe
# Custom view class for the User model


class UserView(ModelView):
    column_list = ['email', 'first_name', 'last_name', 'date_created']
    # Add other configurations as needed

# Custom view class for the Route model


class RouteView(ModelView):
    column_list = ['name', 'upload_time']
    # Add other configurations as needed

# Custom view class for the Plan model


class PlanView(ModelView):
    column_list = ['name', 'monthly_cost', 'stripe_price_id']
    # Add other configurations as needed

# Custom view class for the Subscription model


class SubscriptionView(ModelView):
    column_list = ['user', 'plan',
                   'subscription_id', 'date_start', 'date_end', 'active']
    # Add other configurations as needed

# Custom view class for the StripeCustomer model


class StripeCustomerView(ModelView):
    column_list = ['user', 'stripeCustomerId', 'stripeSubscriptionId']
    # Add other configurations as needed


# Add views for each model using the custom view classes
admin.add_view(UserView(User, db.session))
admin.add_view(RouteView(Route, db.session))
admin.add_view(PlanView(Plan, db.session))
admin.add_view(SubscriptionView(Subscription, db.session))
admin.add_view(StripeCustomerView(StripeCustomer, db.session))


@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if request.method == 'POST':
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password_hash, form.password.data):
                flash("Logged in!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("user"))
            else:
                flash("Password is wrong!", category="error")
                return redirect(url_for("login"))
        else:
            flash("Account does not exist!", category="error")
            return redirect(url_for("login"))

    return render_template("login.html", title="Login", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if request.method == 'POST':
        email = request.form.get("email")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash(
                "Email already in use. Please choose a different email.", "error"
            )
            return render_template("registration.html", title="Register", form=form)

        if password != confirm_password:
            flash(
                "Passwords do not match. Please make sure your passwords match.",
                "error",
            )
            return render_template("registration.html", title="Register", form=form)

        selected_plan = request.form.get("plan")
        if selected_plan == 'option1':
            answer = 'You selected Option 1'
        elif selected_plan == 'option2':
            answer = 'You selected Option 2'
        elif selected_plan == 'option3':
            answer = 'You selected Option 3'
        else:
            answer = 'Invalid option'

        hashed_password = bcrypt.generate_password_hash(password)
        user = User(email=email, first_name=first_name, last_name=last_name,
                    password_hash=hashed_password, date_created=datetime.now())
        db.session.add(user)
        db.session.commit()

        flash("User added successfully!", "success")

        return redirect(url_for("login"))

    return render_template("registration.html", title="Register", form=form)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route('/manager')
def manager():
    return render_template("manager.html")


@app.route('/user',  methods=['GET', 'POST'])
@login_required
def user():
    """render map page from templates

    Returns:
        render_template: render template, with map.html
    """
    # file upload form
    file_upload_form = FileUploadForm()

    route = None
    # if submit button is pressed and the file is valid
    if (file_upload_form.submit_file.data and
            file_upload_form.validate_on_submit()):

        #  get the file uploaded
        uploadedFile = request.files['file_upload']
        # read the data
        data = str(uploadedFile.read())

        # adds to database, waiting for login system to be implemented to test

        # Generate BLOB from GPX data
        gpx_blob = data.encode('ascii')
        # create database entry, currently RouteTest just for testing
        route = models.Route(
            gpx_data=gpx_blob
        )
        # add to database

        current_user.routes.append(route)
        db.session.add(current_user)
        db.session.add(route)
        db.session.commit()

        # this gets rid of all the \n in the string, cant be used with them
        # route = get_route()
        # splitData = route.split("\\n")
        # route = "".join(splitData)[2:][:-1]

    return render_template("user.html", title='Map', FileUploadForm=file_upload_form, route=route)


# Views for handling payments
@app.route("/manage_subscription")
def manage_subscription():
    # print(stripe_keys["price_id"])
    active_subscription = current_user_active_subscription()
    return render_template("subscription.html",
                           active_subscription=active_subscription)


@app.route("/stripe")
def get_publishable_key():
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)


@app.route("/checkout")
def checkout():
    domain_url = "http://localhost:5000/"
    stripe.api_key = stripe_keys["secret_key"]

    try:
        plan_duration = request.args.get("plan_duration", "1_year")
        # Get the corresponding price ID based on plan_duration
        if plan_duration == "1_year":
            price_id = stripe_keys["price_id_1_year"]
        elif plan_duration == "1_month":
            price_id = stripe_keys["price_id_1_month"]
        elif plan_duration == "1_week":
            price_id = stripe_keys["price_id_1_week"]
        else:
            return jsonify(error="Invalid plan duration"), 400

        checkout_session = stripe.checkout.Session.create(
            success_url=domain_url +
            "success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "cancel",
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ]
        )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return jsonify(error=str(e)), 403


@app.route("/cancel_subscription", methods=['POST'])
def cancel_subscription():
    stripe.api_key = stripe_keys["secret_key"]

    latest_subscription = Subscription.query.filter_by(
        user_id=current_user.id, active=True).order_by(Subscription.date_start.desc()).first()

    if latest_subscription:
        try:
            # Cancel the subscription (at the end of the billing period).
            stripe.Subscription.cancel(
                latest_subscription.subscription_id,
            )

            # Set the subscription as inactive.
            latest_subscription.active = False
            db.session.commit()

            return jsonify(success=True), 200
        except Exception as e:
            return jsonify(error=str(e)), 403
    else:
        return jsonify(error="No active subscription found."), 403


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/cancel")
def cancelled():
    flash("Payment cancelled.")
    return redirect(url_for("manage_subscription"))


@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    signature = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, stripe_keys["endpoint_secret"])
    except Exception as e:
        abort(400)

    if event['type'] == 'invoice.updated':

        # Grab data from invoice.
        invoice_data = event['data']['object']
        customer_email = invoice_data['customer_email']
        plan_id = invoice_data['lines']['data'][0]['plan']['id']
        subscription_id = invoice_data['subscription']

        user = User.query.filter_by(email=customer_email).first()

        # Query the plan based on the plan_id of the subscription.
        plan = Plan.query.filter_by(stripe_price_id=plan_id).first()

        # Debugging test.
        # print(user, plan, plan_id)
        # print(subscription_id)

        if user and plan:
            create_subscription(user, plan, subscription_id)
            print('Subscription created')
        else:
            print('User or plan not found')

    return jsonify({'success': True})

# Method to create a subscription in the database.


def create_subscription(user, plan, subscription_id):
    if plan.name == "Weekly":
        date_end = datetime.now()+timedelta(weeks=1)
    elif plan.name == "Monthly":
        date_end = datetime.now()+timedelta(weeks=4)
    else:
        date_end = datetime.now()+timedelta(weeks=52)

    subscription = Subscription(
        user=user,
        plan_id=plan.id,
        date_start=datetime.utcnow(),
        date_end=date_end,
        subscription_id=subscription_id,
    )

    db.session.add(subscription)
    db.session.commit()

    print(f"Subscription created for {user.email} with plan {plan.name}")


def current_user_active_subscription():
    return Subscription.query.filter_by(user_id=current_user.id, active=True).count() > 0
