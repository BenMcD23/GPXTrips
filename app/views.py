from config import stripe_keys
from app import app, db, models, admin, bcrypt
from flask_admin.contrib.sqla import ModelView
from .models import User, Plan, Subscription, Route
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

# Custom view class for the Route model


class RouteView(ModelView):
    column_list = ['name', 'upload_time']

# Custom view class for the Plan model


class PlanView(ModelView):
    column_list = ['name', 'monthly_cost', 'stripe_price_id']

# Custom view class for the Subscription model


class SubscriptionView(ModelView):
    column_list = ['user', 'plan',
                   'subscription_id', 'date_start', 'date_end', 'active']


# Add views for each model using the custom view classes
admin.add_view(UserView(User, db.session))
admin.add_view(RouteView(Route, db.session))
admin.add_view(PlanView(Plan, db.session))
admin.add_view(SubscriptionView(Subscription, db.session))


# Login route
@app.route("/", methods=["GET", "POST"])
def login():
    # Create an instance of the LoginForm
    form = LoginForm()

    if request.method == 'POST':
        # Query the user by email
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            if bcrypt.check_password_hash(user.password_hash, form.password.data):
                # Login user and redirect to user route after successful login
                flash("Logged in!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("user"))
            else:
                # Redirect to back login if password is incorrect
                flash("Password is wrong!", category="error")
                return redirect(url_for("login"))
        else:
            # Redirect to back login if account does not exist
            flash("Account does not exist!", category="error")
            return redirect(url_for("login"))

    return render_template("login.html", title="Login", form=form)
  
# Register route
@app.route("/register", methods=["GET", "POST"])
def register():
    # Create an instance of the RegistrationForm
    form = RegistrationForm()

    if request.method == 'POST':
        # Request data from form
        email = request.form.get("email")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Check provided email has an account that exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash(
                "Email already in use. Please choose a different email.", category="error"
            )
            return redirect(url_for("register"))

        # Password validation
        if password != confirm_password:
            flash(
                "Passwords do not match. Please make sure your passwords match.",
                category="error",
            )
            return redirect(url_for("register"))

        # Stubs for plan selection
        selected_plan = request.form.get("plan")
        if selected_plan == 'option1':
            answer = 'You selected Option 1'
        elif selected_plan == 'option2':
            answer = 'You selected Option 2'
        elif selected_plan == 'option3':
            answer = 'You selected Option 3'
        else:
            answer = 'Invalid option'

        # Hash password and add used to the database
        hashed_password = bcrypt.generate_password_hash(password)
        user = User(email=email, first_name=first_name, last_name=last_name,
                    password_hash=hashed_password, date_created=datetime.now())
        db.session.add(user)
        db.session.commit()

        flash("User added successfully!", category="success")

        # Redirect to login after successful registration
        return redirect(url_for("login")) 

    return render_template("registration.html", title="Register", form=form)


# Logout route
@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    # Logout user and redirect to login
    logout_user()
    return redirect(url_for("login"))


@app.route('/manager')
def manager():
    return render_template("manager.html")

@app.route('/manage_users')
@login_required
def manage_users():
    all_users = models.User.query.all()
    return render_template("manage_users.html",all_users=all_users)

@app.route('/view_revenue')
def view_revenue():
    return render_template("view_revenue.html")

@app.route('/friends')
@login_required
def friends():
    #Query all friends of the current user + pending friends requests
    return render_template("friends.html",current_user=current_user)

@app.route('/profile')
@login_required
def profile():
    #Pass data to retrive user details
    return render_template("profile.html",current_user=current_user)

@app.route('/settings')
@login_required
def settings():
    #Pass data and receive user changes (i.e email/name/payment changes)
    return render_template("settings.html",current_user=current_user)

@app.route('/user',  methods=['GET', 'POST'])
@login_required
def user():
    """Render map page from templates.

    Returns:
        render_template: render template, with map.html
    """
    # File upload form
    # file upload form
    all_routes = models.Route.query.all()
    file_upload_form = FileUploadForm()
    routes = current_user.routes

    route = None

    # If the form is submitted and is valid
    if request.method == 'POST' and file_upload_form.validate_on_submit():
        # Get the uploaded file
        uploaded_file = request.files['file_upload']
        
        # Read the data from the file
        gpx_data = uploaded_file.read()

        # Check GPX file structure validation
        if is_valid_gpx_structure(gpx_data):
            try:
                # Generate BLOB from GPX data
                gpx_blob = gpx_data

                # Create a database entry
                route = models.Route(
                    name=uploaded_file.filename,
                    upload_time=datetime.now(),
                    gpx_data=gpx_blob
                )

                # Add to the current user's routes
                current_user.routes.append(route)

                # Commit changes to the database
                db.session.commit()

                flash("GPX file uploaded successfully!", "success")
            except Exception as e:
                db.session.rollback()  # Rollback changes if an exception occurs
                print(f"Error: {e}")
                flash("An error occurred while processing the GPX file.", "error")
        else:
            flash("Invalid GPX file structure. Please upload a valid GPX file.", "error")

    return render_template("user.html", title='Map', FileUploadForm=file_upload_form, route=route, routes=routes, all_routes=all_routes, disabled=False)


# AJAX stuff 

# post all routes to JavaScript
@app.route('/getRoute', methods=['GET'])
def getRoute():
    # get the current logged in users routes
    routes = current_user.routes

    # dic for all data go in, goes into json
    data = {}
    # loop for all the routes
    for i in routes:
        # decode each route and get rid of \n
        route = i.gpx_data.decode('ascii')
        splitData = route.split("\\n")
        route = "".join(splitData)[2:][:-1]
        data[i.id] = route

    # return as a json
    return json.dumps(data)


def is_valid_gpx_structure(gpx_data):
    try:
        # Parse GPX data
        gpx = gpxpy.parse(gpx_data)

        # No exception means the GPX data is structurally valid
        return True

    except gpxpy.gpx.GPXException as e:
        print(f"GPX parsing error: {e}")
        return False


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
        active=True
    )

    db.session.add(subscription)
    db.session.commit()

    print(f"Subscription created for {user.email} with plan {plan.name}")

# Active subscription - the user has a current subscription with auto renewals ON
def current_user_active_subscription():
    latest_subscription = Subscription.query.filter_by(
            user_id=current_user.id).order_by(Subscription.date_start.desc()).first()
    if latest_subscription:
        return latest_subscription.active
    return False

# Current subscription - the user has a current subscription which expires some time in the future, irrespective of cancellation status
def current_user_current_subscription():
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
    for subscription in subscriptions:
        if subscription.date_end > datetime.now():
            return True

    return False



