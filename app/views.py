from flask import request
from config import stripe_keys
from sqlalchemy import func
from app import app, db, admin, bcrypt, csrf
from flask_admin.contrib.sqla import ModelView
from .models import User, Plan, Subscription, Route, SubscriptionStats, Friendship, FriendRequest
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify, abort, send_file
from flask_login import login_user, login_required, logout_user, current_user
from .forms import *
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import stripe
import json
import gpxpy
from functools import wraps
from .funcs import getCurrentBuisnessWeek
import time
from io import BytesIO
from xml.etree import ElementTree as ET
from geopy.distance import geodesic
from dateutil import parser


class UserView(ModelView):
    # Custom view class for the User model
    column_list = ['email', 'first_name',
                   'last_name', 'date_created', 'manager', 'account_active', 'subscriptions', 'routes']


class RouteView(ModelView):
    # Custom view class for the Route model
    column_list = ['name', 'upload_time']


class PlanView(ModelView):
    # Custom view class for the Plan model
    column_list = ['name', 'price', 'stripe_price_id']


class SubscriptionView(ModelView):
    # Custom view class for the Subscription model
    column_list = ['user', 'plan',
                   'subscription_id', 'customer_id', 'date_start', 'date_end', 'active']

class SubscriptionStatsView(ModelView):
    # Custom view class for the Subscription model
    column_list = ['week_of_business', 'total_revenue', 'num_customers']


class FriendshipView(ModelView):
    # Custom view class for the Friendship model
    column_list = ['user1_id', 'user2_id']

class FriendRequestView(ModelView):
    # Custom view class for the Friend Request model
    column_list=['sender_user_id','receiver_user_id']

# Add views for each model using the custom view classes
admin.add_view(UserView(User, db.session))
admin.add_view(RouteView(Route, db.session))
admin.add_view(PlanView(Plan, db.session))
admin.add_view(SubscriptionView(Subscription, db.session))
admin.add_view(SubscriptionStatsView(SubscriptionStats, db.session))
admin.add_view(FriendshipView(Friendship, db.session))
admin.add_view(FriendRequestView(FriendRequest, db.session))


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
    # get all prices and turn them into an array
    allPlans = Plan.query.all()
    priceArray = [i.price_as_pound() for i in allPlans]

    # Login route
    # Create an instance of the LoginForm
    form = LoginForm()

    if request.method == 'POST':
        # Query the user by email
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            if user.account_active:
                if user.check_password(form.password.data):
                    remember_me = form.rememberMe.data
                    login_user(user, remember=remember_me)
                    if user.manager:
                        # if theyre a manager then redirect to manager page
                        return redirect(url_for("manager"))
                    # if theyre just a normal user then redirect to user page
                    return redirect(url_for("user"))
                else:
                    # Redirect to back login if password is incorrect
                    flash("Password is wrong!", category="error")
            else:
                # if the account isnt active
                flash("Account is deactivated, please contact support.",
                      category="error")
        else:
            # Redirect to back login if account does not exist
            flash("Account does not exist!", category="error")

        return redirect(url_for("login"))

    return render_template("login.html", title="Login", priceArray=priceArray, form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    # Register route
    # Create an instance of the RegistrationForm
    form = RegistrationForm()

    if request.method == 'POST':
        # Request data from form
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        password = form.password.data
        confirm_password = form.confirm_password.data
        tandc_confirm = form.TandCConfirm.data

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            # Check provided email has an account that exists
            flash("Email already in use. Please choose a different email.",
                  category="error")
            return redirect(url_for("register"))

        if password != confirm_password:
            # Password validation
            flash(
                "Passwords do not match. Please make sure your passwords match.", category="error")
            return redirect(url_for("register"))

        if not tandc_confirm:
            flash("Please accept the Terms and Conditions to proceed.",
                  category="error")
            return redirect(url_for("register"))

        # Hash password and add used to the database
        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf-8')
        user = User(email=email, first_name=first_name, last_name=last_name,
                    password_hash=hashed_password, date_created=datetime.now(), account_active=True, manager=False)
        db.session.add(user)
        db.session.commit()

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

@app.route('/edit_prices', methods=["GET", "POST"])
@manger_required()
def edit_prices():
    # get all prices and turn them into an array
    allPlans = Plan.query.all()

    priceArray = [i.price_as_pound() for i in allPlans]

    # all forms
    WeeklyPriceForm = ChangeWeeklyPrice()
    MonthlyPriceForm = ChangeMonthlyPrice()
    YearlyPriceForm = ChangeYearlyPrice()

    # check if any of the forms have been submitted
    if (WeeklyPriceForm.weekly_submit_price.data and
        WeeklyPriceForm.validate_on_submit()):
        allPlans[0].price = WeeklyPriceForm.weekly_new_price.data
        db.session.commit()
        priceArray[0] = '£{:.2f}'.format(round(WeeklyPriceForm.weekly_new_price.data, 2))
        
    if (MonthlyPriceForm.monthly_submit_price.data and
        MonthlyPriceForm.validate_on_submit()):
        allPlans[1].price = MonthlyPriceForm.monthly_new_price.data
        db.session.commit()
        priceArray[1] = '£{:.2f}'.format(round(MonthlyPriceForm.monthly_new_price.data, 2))

    if (YearlyPriceForm.yearly_submit_price.data and
        YearlyPriceForm.validate_on_submit()):
        allPlans[2].price = YearlyPriceForm.yearly_new_price.data
        db.session.commit()
        priceArray[2] = '£{:.2f}'.format(round(YearlyPriceForm.yearly_new_price.data, 2))


    return render_template("edit_prices.html", priceArray=priceArray, WeeklyPriceForm=WeeklyPriceForm, MonthlyPriceForm=MonthlyPriceForm, YearlyPriceForm=YearlyPriceForm)

@app.route('/faq')
@manger_required()
def faq():
    return render_template("faq.html")

@app.route('/manage_users', methods=["GET", "POST"])
@manger_required()
def manage_users():
    allEmails = User.query.all()
    # turn all the emails into an array
    emailsArray = [i.email_return() for i in allEmails]

    UserSearchForm = UserSearch()

    # if the user has inputted a search
    if (UserSearchForm.submitSearch.data and
            UserSearchForm.validate_on_submit()):

        # if the input is nothing, then just display all users
        if UserSearchForm.userEmail.data == "":
            users = User.query.all()

        # otherwise display every email that matches
        # (should just be 1)
        else:
            users = User.query.filter_by(
                email=UserSearchForm.userEmail.data).all()

    # if nothing inputted, show all
    else:
        users = User.query.all()

    return render_template("manage_users.html", users=users, UserSearch=UserSearchForm, emails=emailsArray)


@app.route('/view_revenue', methods=["GET", "POST"])
@manger_required()
def view_revenue():
    """generates the data needed to plot the graphs
    theres a wiki on how the estimated stats work, but briefly explained here

    """
    # this is the diff between the start week and current week
    # so number of weeks since first week
    currentWeek = getCurrentBuisnessWeek()

    # gets all the stats saved, in descending order of week (high to low)
    # apart from the current week, if its there, as we dont know if theres going to be more sales
    allWeekStats = SubscriptionStats.query.filter(SubscriptionStats.week_of_business != currentWeek).order_by(SubscriptionStats.week_of_business.desc()).all()
    
    # create needed variables and arrays, so dont get error if theres not enough stats
    weeks_future = []
    revData_future = []
    customerData_future = []
    CWGR_rev = 0
    CWGR_cus = 0
    noEstimate = False

    # if we dont get anything from the stats, then we cant do anything
    # if theres only 1 week, we cant figure out an esitmate
    if not allWeekStats or len(allWeekStats) == 1:
        noEstimate = True
        for i in range(1, 53):
            revData_future.append(0)
            customerData_future.append(0)

    # if there is at least 2 weeks in stats (not including current week)
    else:
        # if theres less than 4 weeks of stats, just the lastest week and earliest week
        if len(allWeekStats) < 4:
            # Compound Weekly Growth Rate, based on earilest week in database
            CWGR_rev = ((allWeekStats[0].total_revenue / allWeekStats[-1].total_revenue) ** (1 / ((allWeekStats[0].week_of_business - allWeekStats[-1].week_of_business) + 1)))
            CWGR_cus = ((allWeekStats[0].num_customers / allWeekStats[-1].num_customers) ** (1 / ((allWeekStats[0].week_of_business - allWeekStats[-1].week_of_business) + 1)))

        # otherwise can use the lastest week and 4 entries before that
        # not necessarily 4 weeks, as can have weeks with 0, this is taken into account in the formula
        else :
            # Compound Weekly Growth Rate, based on lastest datapoint 4 datapoints ago in database
            CWGR_rev = ((allWeekStats[0].total_revenue / allWeekStats[3].total_revenue) ** (1 / ((allWeekStats[0].week_of_business - allWeekStats[3].week_of_business) + 1)))
            CWGR_cus = ((allWeekStats[0].num_customers / allWeekStats[3].num_customers) ** (1 / ((allWeekStats[0].week_of_business - allWeekStats[3].week_of_business) + 1)))

        # set to last completed weeks value
        lastRevValue = allWeekStats[0].total_revenue
        lastCusValue = allWeekStats[0].num_customers

        # loop for a year (52 week) and calcualte each data point
        # compounding, builds on the last weeks value
        for i in range(1, 53):
            lastRevValue = lastRevValue * CWGR_rev
            lastCusValue = lastCusValue * CWGR_cus
            revData_future.append(lastRevValue)
            customerData_future.append(lastCusValue)
            weeks_future.append("Week " + str(i))

    # set so doesnt error if not enough data
    revData_past = []
    weeks_past = []
    numOfWeeks = 4

    ChangeRevWeeksForm = ChangeRevWeeks()
    # if the input is valid
    if (ChangeRevWeeksForm.submitWeeks.data and
        ChangeRevWeeksForm.validate_on_submit()):

        # get how many weeks they want
        numOfWeeks = ChangeRevWeeksForm.weeks.data

    # if there isnt any input then just display the past 4 weeks
    else:
        numOfWeeks = 4

    # loop over all the weeks we want
    for i in range(0, numOfWeeks):
        # get the week with the corresponding week
        week = SubscriptionStats.query.filter_by(week_of_business=currentWeek).first()

        # always adding to start of list, index 0, want to go from low to high

        # if there isnt that week in the database, then that week must have no rev
        # just add 0
        if not week:
            revData_past.insert(0, 0)
        
        # otherwise, insert the rev in the datapoint
        else:
            revData_past.insert(0, week.total_revenue)

        # create weeks array for x axis
        if len(weeks_past) == 0:
            weeks_past.insert(0, "Week " + str(currentWeek) + " (Current Week)")

        else:
            weeks_past.insert(0, "Week " + str(currentWeek))

        # index the current week down
        currentWeek -= 1

    # get total revenue - all time
    total_rev = 0
    # re done as last time the current week was removed
    allWeekStats = SubscriptionStats.query.all()
    for i in allWeekStats:
        total_rev += i.total_revenue

    # round to 2dp with trailing 0's
    CWGR_rev = '{:.2f}'.format(round(CWGR_rev, 2))
    CWGR_cus = '{:.2f}'.format(round(CWGR_cus, 2))

    return render_template("view_revenue.html", ChangeRevWeeksForm=ChangeRevWeeksForm, noEstimate=noEstimate, weeks_future=weeks_future, revData_future=revData_future, customerData_future=customerData_future, CWGR_cus=CWGR_cus, CWGR_rev=CWGR_rev, revData_past=revData_past, weeks_past=weeks_past, total_rev=total_rev)


@app.route('/friends')
@login_required
def friends():
    # Query all friends of the current user + pending friends requests
    if current_user_current_subscription() == False:
        # If user doesn't have an active subscription, redirect to user page
        return redirect(url_for('user'))
    return render_template("friends.html", current_user=current_user, friends=getFriends())


@app.route('/profile')
@login_required
def profile():
    # get all prices and turn them into an array
    allPlans = Plan.query.all()
    priceArray = [i.price_as_pound() for i in allPlans]

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

    subscription_form = SubscriptionForm()
    account_form = AccountForm()

    return render_template("profile.html", priceArray=priceArray, current_user=current_user, userPlan=userPlan, expiryDate=expiryDate, autoRenewal=autoRenewal, subscription_form=subscription_form, account_form=account_form)


@app.route('/user',  methods=['GET', 'POST'])
@login_required
def user():
    # get all prices and turn them into an array
    allPlans = Plan.query.all()
    priceArray = [i.price_as_pound() for i in allPlans]

    # File upload form
    all_routes = Route.query.filter_by(user_id=current_user.id).all()
    friends = getFriends()
    friend_routes = []
    friend_names = []
    friend_emails = []
    
    for f in friends:
        for r in f.routes:
            friend_routes.append(r)
            friend_names.append(f.first_name + ' ' + f.last_name)
            friend_emails.append(f.email)

    file_upload_form = FileUploadForm()
    routes = current_user.routes

    # Build route info lists for both the user and their friends
    route_info_list = []
    friend_route_info = []
    getRouteInfoList(routes,route_info_list)
    getRouteInfoList(friend_routes, friend_route_info)
    
    
    # Disables the page unless set otherwise
    disabled = False

    # If User doesnt have an active subscription then display the subscribe card, and disable the rest of the poge
    if current_user_current_subscription() == False:
        disabled = True

    return render_template("user.html", title='Map', priceArray=priceArray, friend_names=friend_names, friend_emails=friend_emails, friend_routes=friend_route_info,  FileUploadForm=file_upload_form, routes=all_routes, route_info_list=route_info_list, disabled=disabled)


def getRouteInfoList(inputList,outputList):
    for route in inputList:
        gpx_data_decoded = route.gpx_data.decode('ascii')
        gpx_data = gpx_data_decoded.replace('\\r', '\r').replace('\\n', '\n')
        gpx_data = "".join(gpx_data)[2:][:-1]  # Trim excess characters
        # Calculate route information
        length, duration, start_point, end_point = calculate_route_info(gpx_data)
        route_info = {
            'id': route.id,
            'name': route.name,
            'user': {
                'first_name': route.user.first_name,
                'last_name': route.user.last_name
            },
            'length': length,
            'duration': duration,
            'start': start_point,
            'end': end_point,
            'upload_time': route.upload_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        outputList.append(route_info)



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
        data[str(i.id)+"_name"] = i.name

    # return as a json
    return json.dumps(data)


@app.route('/getFriendRoute', methods=['GET'])
def getFriendRoute():
    # post all routes to JavaScript
    # get the friends of the currently logged in users
    friends = getFriends()
    routes = []
    
    # get the routes of the users friends
    for f in friends:
        for r in f.routes:
            routes.append(r)

    # dic for all data go in, goes into json
    data = {}
    # loop for all the routes
    for i in routes:
        # decode each route and get rid of \n
        route = i.gpx_data.decode('ascii')
        splitData = route.split("\\n")
        route = "".join(splitData)[2:][:-1]
        data[i.id] = route
        data[str(i.id)+"_name"] = i.name
        
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
            customer_email=current_user.email,
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
        customer_id = invoice_data['customer']
        customer_email = invoice_data['customer_email']
        plan_id = invoice_data['lines']['data'][0]['plan']['id']
        subscription_id = invoice_data['id']

        user = User.query.filter_by(email=customer_email).first()

        # Query the plan based on the plan_id of the subscription.
        plan = Plan.query.filter_by(stripe_price_id=plan_id).first()

        # Debugging test.
        print(user, plan, plan_id)
        print(subscription_id)

        if user and plan:
            create_subscription(user, plan, subscription_id, customer_id)
            print('Subscription created')

            # add to stats
            subCost = plan.cost
            addToStats(subCost)

        else:
            print('User or plan not found')

    return jsonify({'success': True})


def create_subscription(user, plan, subscription_id, customer_id):
    # Method to create a subscription in the database.
    if plan.name == "Weekly":
        date_end = datetime.now() + timedelta(weeks=1)
    elif plan.name == "Monthly":
        date_end = datetime.now() + timedelta(weeks=4)
    else:
        date_end = datetime.now() + timedelta(weeks=52)

    subscription = Subscription(
        user=user,
        plan_id=plan.id,
        date_start=datetime.utcnow(),
        date_end=date_end,
        subscription_id=subscription_id,
        customer_id=customer_id,
        active=True
    )

    db.session.add(subscription)
    db.session.commit()

    print(f"Subscription created for {user.email} with plan {plan.name}")
    
    
def addToStats(subCost):
    # this is the diff between the start week and current week
    # so number of weeks since first week
    currentWeek = getCurrentBuisnessWeek()

    currentWeekdb = SubscriptionStats.query.filter_by(week_of_business=currentWeek).first()

    # if the week of the year already exists in the database, then just add on the revenue
    if currentWeekdb:
        currentWeekdb.total_revenue = currentWeekdb.total_revenue + subCost
        currentWeekdb.num_customers = currentWeekdb.num_customers + 1

    else:
        newWeek = SubscriptionStats(week_of_business=currentWeek, total_revenue=subCost, num_customers=1)
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
        return True, None
    except gpxpy.gpx.GPXException as e:
        error_message = f"GPX parsing error: {e}"
        return False, error_message


@app.route('/upload', methods=['POST'])
def upload_file():
    form = FileUploadForm(request.form)

    if form.validate_on_submit():
        file = request.files['file']

        if file:
            # Check file extension
            if file.filename.endswith('.gpx'):
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

                        return jsonify({'message': 'File uploaded successfully'}), 200
                    except Exception as e:
                        db.session.rollback()  # Rollback changes if an exception occurs
                        print(f"Error: {e}")
                        return jsonify({'error': 'Internal server error'}), 500
                else:
                    return jsonify({'error': 'Invalid GPX file structure'}), 400
            else:
                return jsonify({'error': 'File extension is not GPX'}), 400
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
            'start': (0, 0),
            'end': (0, 0),
            'upload_time': route.upload_time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Parse GPX data and calculate route information
        gpx_data_decoded = route.gpx_data.decode('ascii')
        gpx_data = gpx_data_decoded.replace('\\r', '\r').replace('\\n', '\n')
        gpx_data = "".join(gpx_data)[2:][:-1]  # Trim excess characters
        length, duration, start_point, end_point = calculate_route_info(gpx_data)
        route_info['length'] = length
        route_info['duration'] = duration
        route_info['start'] = start_point
        route_info['end'] = end_point

        route_info_list.append(route_info)

    # return as JSON
    return jsonify(route_info_list)

@app.route('/getFriendsList', methods=['GET'])
def getFriendsList():
    friends = getFriends()
    friend_infos = []

    for friend in friends:
        friend_info = {
            'id': friend.id,
            'first_name': friend.first_name,
            'last_name': friend.last_name,
            'email': friend.email
        }

        friend_infos.append(friend_info)

    # return as JSON
    return jsonify(friend_infos)

@app.route('/removeFriend', methods=['POST'])
def removeFriend():
    # get data posted
    data = request.get_json()
    friend_id = data["id"]

    # Attempt to retrieve the friendship one way
    friendship = Friendship.query.filter_by(user1_id=current_user.id, user2_id=friend_id).first()
    # Otherwise get it the other way
    if not friendship:
        friendship = Friendship.query.filter_by(user1_id=friend_id, user2_id=current_user.id).first()

    # Return error if friendship cannot be found in database
    if not friendship:
        return json.dumps({
            'error': 'Could not find friendship'
        })

    db.session.delete(friendship)
    db.session.commit()

    return json.dumps({
        'status':'OK'
    })

@app.route('/userSearch', methods=['POST'])
def userSearch():
    # get data posted
    data = request.get_json()
    searchTerm = data["searchTerm"]

    # Query users against search term
    users = User.query.filter(User.email.contains(searchTerm)).all()

    # Get all outgoing friend requests to mark them as pending
    out_frequests = FriendRequest.query.filter_by(sender_user_id=current_user.id).all()
    pending_ids = []
    for frequest in out_frequests:
        pending_ids.append(frequest.receiver_user_id)

    # Get all friends to exclude them from results
    friend_ids = []
    for friend in getFriends():
        friend_ids.append(friend.id)

    # Build list of user infos and return
    user_infos = []

    for user in users:
        # Ignore self
        if user.id == current_user.id:
            continue

        # Ignore friends
        if user.id in friend_ids:
            continue
        
        # Mark pending requests as pending
        pending = user.id in pending_ids

        # Mark incoming friend requests
        frequest = FriendRequest.query.filter_by(sender_user_id=user.id).first()
        frequest_id=-1
        if frequest:
            frequest_id=frequest.id

        user_info = {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'pending': pending,
            'frequest_id': frequest_id
        }

        user_infos.append(user_info)

    # return as JSON
    return jsonify(user_infos)

@app.route('/sendFriendRequest', methods=['POST'])
def sendFriendRequest():
    # get data posted
    data = request.get_json()
    user_id = data["id"]

    # Create and save friend request
    friendRequest = FriendRequest(
        sender_user_id=current_user.id,
        receiver_user_id=user_id
    )

    db.session.add(friendRequest)
    db.session.commit()

    return json.dumps({
        'status':'OK'
    })

@app.route('/getFriendRequestList', methods=['GET'])
def getFriendRequestList():
    frequests = FriendRequest.query.filter_by(receiver_user_id=current_user.id).all()
    frequest_infos = []

    for frequest in frequests:
        user = User.query.get(frequest.sender_user_id)

        frequest_info = {
            'id': frequest.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        }

        frequest_infos.append(frequest_info)

    # return as JSON
    return jsonify(frequest_infos)

def friendUser(user):
    friendship = Friendship(
        user1_id=current_user.id,
        user2_id=user.id
    )

    db.session.add(friendship)
    db.session.commit()


def getFriends():
    outgoingfriendships = Friendship.query.filter_by(user1_id=current_user.id).all()
    incomingfriendships = Friendship.query.filter_by(user2_id=current_user.id).all()

    friends = []

    for friendship in outgoingfriendships:
        friends.append(User.query.get(friendship.user2_id))

    for friendship in incomingfriendships:
        friends.append(User.query.get(friendship.user1_id))

    return friends


@app.route('/acceptFriendRequest', methods=['POST'])
def acceptFriendRequest():
    # get data posted
    data = request.get_json()
    id = data["id"]

    # find the friend request
    frequest = FriendRequest.query.get(id)

    # friend the sending user
    friendUser(User.query.get(frequest.sender_user_id))

    # delete the friend request
    db.session.delete(frequest)
    db.session.commit()

    return json.dumps({
        'status':'OK'
    })

@app.route('/declineFriendRequest', methods=['POST'])
def declineFriendRequest():
    # get data posted
    data = request.get_json()
    id = data["id"]

    # find the friend request
    frequest = FriendRequest.query.get(id)

    # delete the friend request without friending sending user
    db.session.delete(frequest)
    db.session.commit()

    return json.dumps({
        'status':'OK'
    })


# Routes for user profile.
@app.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    change_email_form = ChangeEmailForm()

    if change_email_form.validate_on_submit():

        new_email = change_email_form.new_email.data

        # Find the user's subscription
        subscription = Subscription.query.filter_by(
            user_id=current_user.id).first()

        if subscription:
            try:
                stripe.api_key = stripe_keys["secret_key"]
                # Retrieve the Stripe customer ID associated with the subscription
                customer_id = subscription.customer_id

                print(customer_id)
                # Update user's email address on Stripe
                stripe.Customer.modify(
                    customer_id,
                    email=new_email
                )
                flash('Email address has been updated successfully!', 'success')
            except Exception as e:
                flash(
                    'Failed to update email address on Stripe. Please try again later.', 'error')
                app.logger.error(f"Stripe error: {e}")
        else:
            flash('User subscription not found.', 'error')

        # Update user's email address in your database
        current_user.email = new_email
        db.session.commit()

        # Redirect to profile page after email change
        return redirect(url_for('profile'))

    return render_template("change_email.html", change_email_form=change_email_form)


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        # Check if old password matches
        if current_user.check_password(form.old_password.data):
            # Update password
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated successfully.', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid old password. Please try again.', 'error')

    return render_template('change_password.html', form=form)


@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        # Perform any additional validation or checks if needed
        # Delete the user's account from the database
        db.session.delete(current_user)
        db.session.commit()
        flash('Your account has been deleted.', 'success')
        # Redirect to logout or any other appropriate route
        return redirect(url_for('logout'))
    else:
        # Handle GET request for the route if needed
        pass

@app.route('/download/<int:route_id>', methods=['GET'])
def download_file(route_id):
    # Retrieve the route information from the database based on the provided route_id
    route = Route.query.get(route_id)

    if route:
        # Decode the GPX data from ASCII encoding and replace escape characters
        gpx_data_decoded = route.gpx_data.decode('ascii')
        gpx_data = gpx_data_decoded.replace('\\r', '\r').replace('\\n', '\n')
        gpx_data = "".join(gpx_data)[2:][:-1]  # Trim excess characters
        
        # Generate a filename for the GPX file by replacing spaces with underscores
        filename = route.name.replace(' ', '_')
        
        # Return the GPX file as an attachment for download
        return send_file(BytesIO(gpx_data.encode()), attachment_filename=filename, as_attachment=True)
    else:
        # Return an error response if the route with the given ID is not found
        return jsonify({'error': 'Route not found'}), 404


@app.route('/deleteRoute/<int:route_id>', methods=['GET'])
def delete_route(route_id):
    if request.method == 'GET':
        if not route_id:
            return jsonify({'error': 'Route ID is missing'}), 400

        # Find the route by ID
        route = Route.query.get(route_id)

        if not route:
            return jsonify({'error': 'Route not found'}), 404

        try:
            # Remove the route from the database
            db.session.delete(route)
            db.session.commit()
            return redirect(url_for('user'))
            # return jsonify({'message': 'Route deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            db.session.close()
    else:
        return jsonify({'error': 'Method not allowed'}), 405
    

def calculate_route_info(gpx_data, unit='km'):
    # Parse GPX data
    tree = ET.fromstring(gpx_data)

    # Extract track points
    track_points = [(float(trkpt.attrib['lat']), float(trkpt.attrib['lon']))
                    for trkpt in tree.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')]

    # Calculate route length
    length = sum(geodesic(track_points[i], track_points[i + 1]).meters
                 for i in range(len(track_points) - 1))

    # Convert length to kilometers or miles based on unit preference
    if unit == 'km':
        length = length / 1000  # Convert meters to kilometers
        length = round(length, 2)  # Round to 2 decimal places
        length = f"{length} km"  # Append unit
    elif unit == 'miles':
        length = length * 0.000621371  # Convert meters to miles
        length = round(length, 2)  # Round to 2 decimal places
        length = f"{length} miles"  # Append unit
    else:
        length = f"{length} meters"  # Default to meters if unit is not km or miles

    times = tree.findall(".//time")
    timestamps = [parser.isoparse(time.text) for time in times]

    # Calculate route duration if timestamps are available
    duration = 0
    if timestamps:
        duration = (max(timestamps) - min(timestamps)).total_seconds()

    # Start and end points
    start_point = (0, 0)
    end_point = (0, 0)
    if track_points:
        start_point = round(track_points[0][0], 3), round(track_points[0][1], 3)
        end_point = round(track_points[-1][0], 3), round(track_points[-1][1], 3)

    return length, duration, start_point, end_point
