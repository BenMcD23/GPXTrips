from config import stripe_keys
from app import app, db, admin, bcrypt, csrf
from flask_admin.contrib.sqla import ModelView
from .models import User, Plan, Subscription, Route, SubscriptionStats
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify, abort
from flask_login import login_user, login_required, logout_user, current_user
from .forms import FileUploadForm, RegistrationForm, LoginForm, UserSearch
from werkzeug.utils import secure_filename
from DAL import add_route, get_route
from datetime import datetime, timedelta
import stripe
import json
import gpxpy
from functools import wraps


class UserView(ModelView):
    # Custom view class for the User model
    column_list = ['email', 'first_name',
                   'last_name', 'date_created', 'manager', 'account_active', 'subscriptions', 'routes']


class RouteView(ModelView):
    # Custom view class for the Route model
    column_list = ['name', 'upload_time']


class PlanView(ModelView):
    # Custom view class for the Plan model
    column_list = ['name', 'cost', 'stripe_price_id']


class SubscriptionView(ModelView):
    # Custom view class for the Subscription model
    column_list = ['user', 'plan',
                   'subscription_id', 'date_start', 'date_end', 'active']

class SubscriptionStatsView(ModelView):
    # Custom view class for the Subscription model
    column_list = ['week_of_year', 'total_revenue', 'num_customers']



# Add views for each model using the custom view classes
admin.add_view(UserView(User, db.session))
admin.add_view(RouteView(Route, db.session))
admin.add_view(PlanView(Plan, db.session))
admin.add_view(SubscriptionView(Subscription, db.session))
admin.add_view(SubscriptionStatsView(SubscriptionStats, db.session))


# role for manager pages
# decorate manager pages with this role
def manger_required():
    def decorator(func):
        @wraps(func)
        def authorize(*args, **kwargs):
            # queries database to see if current user is manager
            if not current_user.is_manager():
                abort(401)  # not authorized
            return func(*args, **kwargs)
        return authorize
    return decorator


@app.route("/", methods=["GET", "POST"])
def login():
    # Login route
    # Create an instance of the LoginForm
    form = LoginForm()

    if request.method == 'POST':
        # Query the user by email
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            # if the account isnt active
            if user.account_active != True:
                flash("Account is deactivated, please contact support.",
                      category="error")
                return redirect(url_for("login"))

            # if the password is correct
            elif bcrypt.check_password_hash(user.password_hash, form.password.data):
                flash("Logged in!", category="success")
                remember_me = form.rememberMe.data
                login_user(user, remember=remember_me)
                if user.manager == True:
                    # if theyre a manager then redirect to manager page
                    return redirect(url_for("manager"))
                # if theyre just a normal user then redirect to user page
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


@app.route("/register", methods=["GET", "POST"])
def register():
    # Register route
    # Create an instance of the RegistrationForm
    form = RegistrationForm()

    if request.method == 'POST':
        # Request data from form
        email = request.form.get("email")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        tandc_confirm = request.form.get("TandCConfirm")

        # Check provided email has an account that exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash(
                "Email already in use. Please choose a different email.",
                category="error"
            )
            return redirect(url_for("register"))

        # Password validation
        if password != confirm_password:
            flash(
                "Passwords do not match. Please make sure your passwords match.",
                category="error",
            )
            return redirect(url_for("register"))

        if not tandc_confirm:
            flash(
                "Please accept the Terms and Conditions to proceed.",
                category="error"
            )
            return redirect(url_for("register"))

        # Hash password and add used to the database
        hashed_password = bcrypt.generate_password_hash(password)
        user = User(email=email, first_name=first_name, last_name=last_name,
                    password_hash=hashed_password, date_created=datetime.now(), account_active=True, manager=False)
        db.session.add(user)
        db.session.commit()

        flash("User added successfully!", category="success")

        # Redirect to login after successful registration
        return redirect(url_for("login"))

    return render_template("registration.html", title="Register", form=form)


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    # Logout user and redirect to login
    logout_user()
    return redirect(url_for("login"))


@app.route('/manager')
@manger_required()
def manager():
    return render_template("manager.html")


@app.route('/manage_users', methods=["GET", "POST"])
@manger_required()
def manage_users():
    UserSearchForm = UserSearch()

    if (UserSearchForm.submitSearch.data and
            UserSearchForm.validate_on_submit()):

        if UserSearchForm.userEmail.data == "":
            users = User.query.all()

        else:
            users = User.query.filter_by(
                email=UserSearchForm.userEmail.data).all()

    else:
        users = User.query.all()

    return render_template("manage_users.html", users=users, UserSearch=UserSearchForm)


@app.route('/view_revenue')
@manger_required()
def view_revenue():

    # get the first and last entry in database
    firstWeek = SubscriptionStats.query.first()
    latestWeek = SubscriptionStats.query.order_by(SubscriptionStats.id.desc()).first()

    labels = []
    revData = []
    customerData = []
    CWGR = 0
    noData = False
    if not firstWeek or not latestWeek:
        noData = True

    else:
        numberOfWeeks = latestWeek.week_of_year

        # Compound Weekly Growth Rate, based on from start of calendar year
        CWGR = ((latestWeek.total_revenue / firstWeek.total_revenue) ** (1 / numberOfWeeks))
        
        labels = ["Week " + str(i) for i in range(1, 53)]
        lastRevValue = latestWeek.total_revenue

        lastCusValue = latestWeek.num_customers
        for i in range(1, 53):
            lastRevValue = lastRevValue * CWGR
            lastCusValue = lastCusValue * CWGR
            revData.append(lastRevValue)
            customerData.append(lastCusValue)
        print(customerData)
    return render_template("view_revenue.html", noData=noData, labels=labels, revData=revData, customerData=customerData, CWGR=CWGR)


@app.route('/friends')
@login_required
def friends():
    # Query all friends of the current user + pending friends requests
    if current_user_current_subscription() == False:
        # If user doesn't have an active subscription, redirect to user page
        return redirect(url_for('user'))
    return render_template("friends.html", current_user=current_user)


@app.route('/profile')
@login_required
def profile():
    # Pass data to retrive user details
    # Variable to keep track of subscription auto renewal status for the user. By default, set to off
    autoRenewal = False

    if current_user_current_subscription() == False:
        # If user doesn't have an active subscription, redirect to user page
        return redirect(url_for('user'))

    if current_user_active_subscription() != False:
        # Auto-renewal is on
        autoRenewal = True

    # retrieve the users plan (year/month/week) and the expiry date of plan from db
    userPlan = Subscription.query.filter_by(
        user_id=current_user.id).first().plan.name
    expiryDate = (Subscription.query.filter_by(
        user_id=current_user.id).first().date_end).date()

    return render_template("profile.html", current_user=current_user, userPlan=userPlan, expiryDate=expiryDate, autoRenewal=autoRenewal)


@app.route('/settings')
@login_required
def settings():
    if current_user_current_subscription() == False:
        # If user doesn't have an active subscription, redirect to user page
        return redirect(url_for('user'))
    # Pass data and receive user changes (i.e email/name/payment changes)
    return render_template("settings.html", current_user=current_user)


@app.route('/user',  methods=['GET', 'POST'])
@login_required
def user():
    """Render map page from templates.

    Returns:
        render_template: render template, with map.html
    """
    # File upload form
    all_routes = Route.query.all()
    file_upload_form = FileUploadForm()
    routes = current_user.routes

    route = None
    # Disables the page unless set otherwise
    disabled = False

    # If User doesnt have an active subscription then display the subscribe card, and disable the rest of the poge
    if current_user_current_subscription() == False:
        disabled = True

    return render_template("user.html", title='Map', FileUploadForm=file_upload_form, route=route, routes=routes, all_routes=all_routes, disabled=disabled)


# for user search (manger view)
@app.route('/emails')
def tagsDic():
    allEmails = User.query.all()
    # turn all the emails into a dictionary
    dicEmails = [i.email_as_dict() for i in allEmails]
    # change dictionary into a json
    return jsonify(dicEmails)


@app.route('/getRoute', methods=['GET'])
def getRoute():
    # post all routes to JavaScript
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


@app.route('/accountState', methods=['POST'])
def accountState():
    # get data posted
    data = request.get_json()

    # change the user account state in database
    User.query.filter_by(id=data["id"]).first().account_active = data["state"]
    db.session.commit()

    return jsonify(data=data)


@app.route('/accountManger', methods=['POST'])
def accountManger():
    # get data posted
    data = request.get_json()

    # change the user account state in database
    User.query.filter_by(id=data["id"]).first().manager = data["state"]
    db.session.commit()

    return jsonify(data=data)


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
@csrf.exempt
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

            return redirect(url_for("profile"))
        except Exception as e:
            return jsonify(error=str(e)), 403
    else:
        return jsonify(error="No active subscription found."), 403


@app.route("/success")
def success():
    return redirect(url_for('user'))


@app.route("/cancel")
def cancelled():
    flash("Payment cancelled.")
    return redirect(url_for("manage_subscription"))


@app.route('/webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    print("webhook reached")

    payload = request.data
    signature = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, stripe_keys["endpoint_secret"])
    except Exception as e:
        print(e)
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
        print(user, plan, plan_id)
        print(subscription_id)

        if user and plan:
            create_subscription(user, plan, subscription_id)
            print('Subscription created')

            # add to stats
            subCost = plan.cost
            addToStats(subCost)

        else:
            print('User or plan not found')

    return jsonify({'success': True})


def create_subscription(user, plan, subscription_id):
    # Method to create a subscription in the database.
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

def addToStats(subCost):
    """adds the added amount of revenue a subscription gains us

    only want to save the current weeks revenue, after the week is over, 
    the week is removed 

    Args:
        subCost (int): a positive number for added revenue
                            
    """
    currentWeekNumber = datetime.now().isocalendar()[1]
    currentWeekdb = SubscriptionStats.query.filter_by(week_of_year=currentWeekNumber).first()
    # if the week of the year already exists in the database, then just add on the revenue
    if currentWeekdb:
        currentWeekdb.total_revenue = currentWeekdb.total_revenue + subCost
        currentWeekdb.num_customers = currentWeekdb.num_customers + 1
    # if the current week doesnt exist, write over the last week
    else:
        # get the lastest week that was entered
        # (not necessarily the last callendar week as may not have had any revenue)
        latestWeek = SubscriptionStats.query.order_by(SubscriptionStats.id.desc()).first()

        # dont want to write over week 0, this is our starting rev
        if latestWeek.week_of_year != 0:
            # change the week
            latestWeek.week_of_year = currentWeekNumber
            # revenue is just the sub that was purchased
            latestWeek.total_revenue = subCost
            latestWeek.num_customers = 1

        # if the only week is week 0, then create a new week, should only ever be done once, max
        else:
            newWeek = SubscriptionStats(week_of_year=currentWeekNumber, total_revenue=subCost, num_customers=1)
            db.session.add(newWeek)

    db.session.commit()


def current_user_active_subscription():
    # Active subscription - the user has a current subscription with auto renewals ON
    latest_subscription = Subscription.query.filter_by(
        user_id=current_user.id).order_by(Subscription.date_start.desc()).first()
    if latest_subscription:
        return latest_subscription.active
    return False


def current_user_current_subscription():
    # Current subscription - the user has a current subscription which expires some time in the future, irrespective of cancellation status
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
    for subscription in subscriptions:
        if subscription.date_end > datetime.now():
            return True

    return False


def is_valid_gpx_structure(gpx_data):
    try:
        # Parse GPX data
        gpx = gpxpy.parse(gpx_data)
        # No exception means the GPX data is structurally valid
        return True
    except gpxpy.gpx.GPXException as e:
        print(f"GPX parsing error: {e}")
        return False


@app.route('/upload', methods=['POST'])
def upload_file():
    form = FileUploadForm(request.form)

    if form.validate_on_submit():
        file = request.files['file']

        if file:
            print('File received:', file.filename)

            # Read the data from the file
            gpx_data = file.read()

            # Check GPX file structure validation
            if is_valid_gpx_structure(gpx_data):
                try:
                    # Generate BLOB from GPX data
                    gpx_blob = str(gpx_data).encode('ascii')

                    # Create a database entry
                    route = Route(
                        name=file.filename,
                        upload_time=datetime.now(),
                        gpx_data=gpx_blob
                    )

                    current_user.routes.append(route)

                    # Commit changes to the database
                    db.session.commit()

                    return jsonify({'message': 'File uploaded successfully'})
                except Exception as e:
                    db.session.rollback()  # Rollback changes if an exception occurs
                    print(f"Error: {e}")
                    return jsonify({'error': 'Internal server error'}), 500
            else:
                return jsonify({'error': 'Invalid GPX file structure'}), 400
        else:
            print('No file provided')
            return jsonify({'error': 'No file provided'}), 400
    else:
        print('Form validation failed')
        # Provide a more detailed error response for form validation failure
        return jsonify({'error': 'Form validation failed', 'errors': form.errors}), 400


@app.route('/getRouteForTable', methods=['GET'])
def getRouteForTable():
    # get the current logged in users routes
    routes = current_user.routes

    # list to store route information
    route_info_list = []

    # loop for all the routes
    for route in routes:
        route_info = {
            'id': route.id,
            'name': route.name,
            'user': {
                'first_name': route.user.first_name,
                'last_name': route.user.last_name
            },
            'length': 0,
            'duration': 0,
            'start': 0,
            'end': 0,
            'upload_time': route.upload_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        route_info_list.append(route_info)

    # return as JSON
    return jsonify(route_info_list)
