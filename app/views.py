from app import app, db, models, bcrypt
from .models import User
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify, abort
from flask_login import login_user, login_required, logout_user, current_user
from .forms import FileUploadForm, RegistrationForm, LoginForm, UserSearch
from werkzeug.utils import secure_filename
from datetime import datetime
import json 
from functools import wraps


# role for manager pages
# decorate manager pages with this role
def manger_required():
    def decorator(func):
        @wraps(func)
        def authorize(*args, **kwargs):
            # queries database to see if current user is manager
            if not current_user.is_manager():
                abort(401) # not authorized
            return func(*args, **kwargs)
        return authorize
    return decorator


@app.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if request.method == 'POST':
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            
            if user.account_active != True:
                flash("Account is deactivated, please contact support.", category="error")
                return redirect(url_for("login"))

            elif bcrypt.check_password_hash(user.password_hash, form.password.data):
                flash("Logged in!", category="success")
                login_user(user, remember=True)
                if user.manager == True:
                    return redirect(url_for("manager"))

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
        user = User(email=email, first_name=first_name, last_name=last_name, password_hash=hashed_password, date_created=datetime.now(), account_active=True, manager=False)
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
            users = User.query.filter_by(email=UserSearchForm.userEmail.data).all()

    else:
        users = User.query.all()

    return render_template("manage_users.html", users=users, UserSearch=UserSearchForm)

@app.route('/view_revenue')
@manger_required()
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
    """render map page from templates

    Returns:
        render_template: render template, with map.html
    """
    # file upload form
    all_routes = models.Route.query.all()
    file_upload_form = FileUploadForm()
    routes = current_user.routes

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
            name=uploadedFile.filename,
            upload_time=datetime.now().date(),
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

    return render_template("user.html", title='Map', FileUploadForm=file_upload_form, route=route, routes=routes, all_routes=all_routes)


# for user search (manger view)
@app.route('/emails')
def tagsDic():
    allEmails = User.query.all()
    # turn all the emails into a dictionary
    dicEmails = [i.email_as_dict() for i in allEmails]
    # change dictionary into a json
    return jsonify(dicEmails)



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


