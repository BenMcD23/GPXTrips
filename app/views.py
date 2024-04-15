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
from functools import wraps
from io import BytesIO

# our functions
from .funcs import *


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
    column_list = ['sender_user_id', 'receiver_user_id']


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
    """allows user to login, all validation done here"""
    # get all prices
    priceArray = getPrices()

    # Create an instance of the LoginForm
    loginForm = LoginForm()

    # if submit button pressed and form is valid
    if request.method == 'POST':
        # Query the user by email
        user = User.query.filter_by(email=loginForm.email.data).first()

        # if the user email doesnt exist in database
        if not user:
            flash("Account does not exist!", category="error")

        # if the account isnt active
        elif not user.account_active:
            flash("Account is deactivated, please contact support.",
                  category="error")

        # if password is correct, login user
        elif user.check_password(loginForm.password.data):
            remember_me = loginForm.rememberMe.data
            login_user(user, remember=remember_me)

            # if they're a manager, redirect to manager page
            if user.manager:
                return redirect(url_for("manager"))

            # otherwise they're just a normal user, redirect to user page
            return redirect(url_for("user"))

        # other wise, password is incorrect
        else:
            flash("Password is wrong!", category="error")

        return redirect(url_for("login"))

    return render_template("login.html", title="Login", priceArray=priceArray, loginForm=loginForm)


@app.route("/register", methods=["GET", "POST"])
def register():
    """allows user to register, all validation done here"""
    # Register route
    # Create an instance of the RegistrationForm
    registerForm = RegistrationForm()

    # if submit button pressed and form is valid
    if request.method == 'POST':
        # Request data from form
        email = registerForm.email.data
        first_name = registerForm.first_name.data
        last_name = registerForm.last_name.data
        password = registerForm.password.data
        confirm_password = registerForm.confirm_password.data
        tandc_confirm = registerForm.TandCConfirm.data

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

    return render_template("registration.html", title="Register", registerForm=registerForm)


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
    """allows manager to edit the prices
    does not change price in stripe"""
    # get all plans
    allPlans = Plan.query.all()
    # get all prices
    priceArray = getPrices()

    # all forms initialisation
    WeeklyPriceForm = ChangeWeeklyPrice()
    MonthlyPriceForm = ChangeMonthlyPrice()
    YearlyPriceForm = ChangeYearlyPrice()

    # check if any of the forms have been submitted
    # when they have, change the price in the db and array
    if (WeeklyPriceForm.weekly_submit_price.data and
            WeeklyPriceForm.validate_on_submit()):
        allPlans[0].price = WeeklyPriceForm.weekly_new_price.data
        db.session.commit()
        priceArray[0] = '£{:.2f}'.format(
            round(WeeklyPriceForm.weekly_new_price.data, 2))

    if (MonthlyPriceForm.monthly_submit_price.data and
            MonthlyPriceForm.validate_on_submit()):
        allPlans[1].price = MonthlyPriceForm.monthly_new_price.data
        db.session.commit()
        priceArray[1] = '£{:.2f}'.format(
            round(MonthlyPriceForm.monthly_new_price.data, 2))

    if (YearlyPriceForm.yearly_submit_price.data and
            YearlyPriceForm.validate_on_submit()):
        allPlans[2].price = YearlyPriceForm.yearly_new_price.data
        db.session.commit()
        priceArray[2] = '£{:.2f}'.format(
            round(YearlyPriceForm.yearly_new_price.data, 2))

    return render_template("edit_prices.html", priceArray=priceArray, WeeklyPriceForm=WeeklyPriceForm, MonthlyPriceForm=MonthlyPriceForm, YearlyPriceForm=YearlyPriceForm)


@app.route('/faq')
@manger_required()
def faq():
    return render_template("faq.html")


@app.route('/manage_users', methods=["GET", "POST"])
@manger_required()
def manage_users():
    """shows all the users in the database
    can activate/deactivate the account + manager activate/deactivate
    also some info about the user"""

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
    theres a wiki on how the estimated stats work, but briefly explained here"""
    # this is the diff between the start week and current week
    # so number of weeks since first week
    currentWeek = getCurrentBuisnessWeek()

    # gets all the stats saved, in descending order of week (high to low)
    # apart from the current week, if its there, as we dont know if theres going to be more sales
    allWeekStats = SubscriptionStats.query.filter(SubscriptionStats.week_of_business != currentWeek).order_by(
        SubscriptionStats.week_of_business.desc()).all()

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
            CWGR_rev = ((allWeekStats[0].total_revenue / allWeekStats[-1].total_revenue) ** (
                1 / ((allWeekStats[0].week_of_business - allWeekStats[-1].week_of_business) + 1)))
            CWGR_cus = ((allWeekStats[0].num_customers / allWeekStats[-1].num_customers) ** (
                1 / ((allWeekStats[0].week_of_business - allWeekStats[-1].week_of_business) + 1)))

        # otherwise can use the lastest week and 4 entries before that
        # not necessarily 4 weeks, as can have weeks with 0, this is taken into account in the formula
        else:
            # Compound Weekly Growth Rate, based on lastest datapoint 4 datapoints ago in database
            CWGR_rev = ((allWeekStats[0].total_revenue / allWeekStats[3].total_revenue) ** (
                1 / ((allWeekStats[0].week_of_business - allWeekStats[3].week_of_business) + 1)))
            CWGR_cus = ((allWeekStats[0].num_customers / allWeekStats[3].num_customers) ** (
                1 / ((allWeekStats[0].week_of_business - allWeekStats[3].week_of_business) + 1)))

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
        week = SubscriptionStats.query.filter_by(
            week_of_business=currentWeek).first()

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
            weeks_past.insert(
                0, "Week " + str(currentWeek) + " (Current Week)")

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
    """friends page, can view manage friends + add new friends"""
    # Query all friends of the current user + pending friends requests
    if current_user_current_subscription(current_user.id) == False:
        # If user doesn't have an active subscription, redirect to user page
        return redirect(url_for('user'))
    return render_template("friends.html", current_user=current_user, friends=getFriends(current_user.id))


@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    """own users profile
    cancel sub + change email, pass + delete account"""
    # get all prices
    priceArray = getPrices()

    # Pass data to retrive user details
    # Variable to keep track of subscription auto renewal status for the user. By default, set to off
    autoRenewal = False

    # If user doesn't have an active subscription, redirect to user page
    if current_user_current_subscription(current_user.id) == False:
        return redirect(url_for('user'))

    if current_user_active_subscription(current_user.id) != False:
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
    """main map page
    displays tracks + friends"""
    # get all prices
    priceArray = getPrices()

    # File upload form
    all_routes = Route.query.filter_by(user_id=current_user.id).all()
    friends = getFriends(current_user.id)
    friend_routes = []
    friend_names = []
    friend_emails = []

    # loop through all friends and create arrays for routes
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
    getRouteInfoList(routes, route_info_list)
    getRouteInfoList(friend_routes, friend_route_info)

    # Disables the page unless set otherwise
    disabled = False

    # If User doesnt have an active subscription then display the subscribe card, and disable the rest of the poge
    if current_user_current_subscription(current_user.id) == False:
        disabled = True

    return render_template("user.html", title='Map', priceArray=priceArray, friend_names=friend_names, friend_emails=friend_emails, friend_routes=friend_route_info,  FileUploadForm=file_upload_form, routes=all_routes, route_info_list=route_info_list, disabled=disabled)


@app.route('/getUserRoute', methods=['GET'])
def getRoute():
    """gets all the current logged in users routes
    then sends them to JavaScript to be displayed"""
    # post all routes to JavaScript
    # get the current logged in users routes
    routes = current_user.routes

    # dic for all data go in, goes into json
    data = {}

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
    """gets alll the current users friends routes to be displayed"""
    # post all routes to JavaScript
    # get the friends of the currently logged in users
    friends = getFriends(current_user.id)
    routes = []

    # get the routes of the users friends
    for f in friends:
        for r in f.routes:
            routes.append(r)

    # dic for all data go in, goes into json
    data = {}

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
    """changes the state of the account when stripe webhook is ran?"""
    # get data posted
    data = request.get_json()

    # change the user account state in database
    User.query.filter_by(id=data["id"]).first().account_active = data["state"]
    db.session.commit()

    return jsonify(data=data)


@app.route('/accountManger', methods=['POST'])
def accountManger():
    """need explanation"""
    # get data posted
    data = request.get_json()

    # change the user account state in database
    User.query.filter_by(id=data["id"]).first().manager = data["state"]
    db.session.commit()

    return jsonify(data=data)


@app.route("/stripe")
def get_publishable_key():
    """gets stripe key"""
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)


@app.route("/checkout")
def checkout():
    """stripe checkout function
    after sucessfull checkout this is ran to,
    create the sub in stripe"""

    # this is will need to be changed on deploy
    domain_url = "http://localhost:5000/"
    # get the key
    stripe.api_key = stripe_keys["secret_key"]

    # try and add to stripe
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

    # return the error, shown in website
    except Exception as e:
        return jsonify(error=str(e)), 403


@app.route("/cancel_subscription", methods=['POST'])
def cancel_subscription():
    """allows the user to cancel their current sub
    still get access to website for length of current sub left"""
    # get the stripe key
    stripe.api_key = stripe_keys["secret_key"]

    # get the current sub
    latest_subscription = Subscription.query.filter_by(
        user_id=current_user.id, active=True).order_by(Subscription.date_start.desc()).first()

    # if theres a current sub
    if latest_subscription:
        # try and cancel the sub
        try:
            # Cancel the subscription (at the end of the billing period).
            stripe.Subscription.cancel(
                latest_subscription.subscription_id,
            )

            # Set the subscription as inactive.
            latest_subscription.active = False
            db.session.commit()

            return redirect(url_for("profile"))

        # if somehow the user could cancel a sub that didnt exist, show error
        except Exception as e:
            return jsonify(error=str(e)), 403

    # if somehow the user could cancel a sub that didnt exist, show error
    else:
        return jsonify(error="No active subscription found."), 403


@app.route("/success")
def success():
    """sucess when payment made"""
    return redirect(url_for('user'))


@app.route("/cancel")
def cancelled():
    """for when cancel payment"""
    flash("Payment cancelled.")
    return redirect(url_for('user'))


@app.route('/webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    """stripe webhook
    ran when new sub, or new sub payment comes out"""
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
        subscription_id = invoice_data['subscription']

        user = User.query.filter_by(email=customer_email).first()

        # Query the plan based on the plan_id of the subscription.
        plan = Plan.query.filter_by(stripe_price_id=plan_id).first()

        # Debugging test.
        print(user, plan, plan_id)
        print(subscription_id)

        # if successfull create the subscription and add price to stats
        if user and plan:
            create_subscription(user, plan, subscription_id, customer_id)
            print('Subscription created')

            # add to stats
            subCost = plan.price
            addToStats(subCost)

        else:
            print('User or plan not found')

    return jsonify({'success': True})


@app.route('/upload', methods=['POST'])
def upload_file():
    """allows user to upload a gpx file to their account
    also checks if gpx file is valid format"""
    form = FileUploadForm(request.form)

    # if form is submitted
    if form.validate_on_submit():
        # get the file uploaded
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

                    # if error
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
    """gets the routes to display on table
    main done this way so when a file is uploaded no refresh is needed
    uses jquery to update table without refresh
    (refresh removed all the routes on the map, had to reselect)"""
    # get the current logged in users routes
    routes = current_user.routes

    # list to store route information
    route_info_list = []

    # loop for all the routes
    for route in routes:
        # set the stats of the route
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
        length, duration, start_point, end_point = calculate_route_info(
            gpx_data)
        route_info['length'] = length
        route_info['duration'] = duration
        route_info['start'] = start_point
        route_info['end'] = end_point

        route_info_list.append(route_info)

    # return as JSON
    return jsonify(route_info_list)


@app.route('/getFriendsList', methods=['GET'])
def getFriendsList():
    """gets all the users friends"""

    # get friends
    friends = getFriends(current_user.id)
    friend_infos = []

    # for all the friends, get the friends info
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
    """allows user to remove a friend"""
    # get data posted
    data = request.get_json()
    # get the id of friend we want to remove
    friend_id = data["id"]

    # Attempt to retrieve the friendship one way
    friendship = Friendship.query.filter_by(
        user1_id=current_user.id, user2_id=friend_id).first()

    # Otherwise get it the other way
    if not friendship:
        friendship = Friendship.query.filter_by(
            user1_id=friend_id, user2_id=current_user.id).first()

    # Return error if friendship cannot be found in database
    if not friendship:
        return json.dumps({
            'error': 'Could not find friendship'
        })

    # delete friend
    db.session.delete(friendship)
    db.session.commit()

    return json.dumps({
        'status': 'OK'
    })


@app.route('/userSearch', methods=['POST'])
def userSearch():
    """so can search for friends"""
    # get data posted
    data = request.get_json()
    searchTerm = data["searchTerm"]

    # Query users against search term
    users = User.query.filter(User.email.contains(searchTerm)).all()

    # Get all outgoing friend requests to mark them as pending
    out_frequests = FriendRequest.query.filter_by(
        sender_user_id=current_user.id).all()
    pending_ids = []
    for frequest in out_frequests:
        pending_ids.append(frequest.receiver_user_id)

    # Get all friends to exclude them from results
    friend_ids = []
    for friend in getFriends(current_user.id):
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
        frequest = FriendRequest.query.filter_by(
            sender_user_id=user.id).first()
        frequest_id = -1
        if frequest:
            frequest_id = frequest.id

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
    """ran when adding friend"""
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
        'status': 'OK'
    })


@app.route('/getFriendRequestList', methods=['GET'])
def getFriendRequestList():
    """get all current users friend requests"""

    # query db for all the friend requests
    frequests = FriendRequest.query.filter_by(
        receiver_user_id=current_user.id).all()
    frequest_infos = []

    # loop for all the requests
    for frequest in frequests:
        # get requestors info to show on table
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


@app.route('/acceptFriendRequest', methods=['POST'])
def acceptFriendRequest():
    """ran when accepting friend request"""
    # get data posted
    data = request.get_json()
    id = data["id"]

    # find the friend request
    frequest = FriendRequest.query.get(id)

    # friend the sending user
    friendUser((User.query.get(frequest.sender_user_id)).id, current_user.id)

    # delete the friend request
    db.session.delete(frequest)
    db.session.commit()

    return json.dumps({
        'status': 'OK'
    })


@app.route('/declineFriendRequest', methods=['POST'])
def declineFriendRequest():
    """ran when declining friend request"""
    # get data posted
    data = request.get_json()
    id = data["id"]

    # find the friend request
    frequest = FriendRequest.query.get(id)

    # delete the friend request without friending sending user
    db.session.delete(frequest)
    db.session.commit()

    return json.dumps({
        'status': 'OK'
    })


# Routes for user profile.
@app.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    """allows user to change their email"""
    change_email_form = ChangeEmailForm()

    # when form submitted
    if change_email_form.validate_on_submit():

        new_email = change_email_form.new_email.data

        # Find the user's subscription
        subscription = Subscription.query.filter_by(
            user_id=current_user.id).first()

        # if they have a sub, then change the sub email
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
    """change password page"""
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
    """allows user to delete account
    doesnt delete in essence, but sets active flag to false,
    so cant login"""
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
    """allows the user to download their uploaded gpx files"""
    # Retrieve the route information from the database based on the provided route_id
    route = Route.query.get(route_id)

    # if the route exists
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
    """user can delete their routes"""
    # if been pressed
    if request.method == 'GET':
        # if there is no route id passed, theres an error
        if not route_id:
            return jsonify({'error': 'Route ID is missing'}), 400

        # Find the route by ID
        route = Route.query.get(route_id)

        # if can find the route with that id, also an error
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
