from app import app, db, models, bcrypt
from .models import User
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .forms import FileUploadForm, RegistrationForm, LoginForm
from werkzeug.utils import secure_filename
from DAL import add_route, get_route
from datetime import datetime
import json
import gpxpy
import os

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
                "Email already in use. Please choose a different email.", "error"
            )
            return render_template("registration.html", title="Register", form=form)

        # Password validation
        if password != confirm_password:
            flash(
                "Passwords do not match. Please make sure your passwords match.",
                "error",
            )
            return render_template("registration.html", title="Register", form=form)

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
        user = User(email=email, first_name=first_name, last_name=last_name, password_hash=hashed_password, date_created=datetime.now())
        db.session.add(user)
        db.session.commit()

        flash("User added successfully!", "success")

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

@app.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    """Render map page from templates.

    Returns:
        render_template: render template, with map.html
    """
    # File upload form
    file_upload_form = FileUploadForm()
    routes = current_user.routes

    route = None

    # If the form is submitted and is valid
    '''if request.method == 'POST' and file_upload_form.validate_on_submit():
        # Get the uploaded file
        uploaded_file = request.files['file_upload']
        
        # Read the data from the file
        gpx_data = uploaded_file.read()

        # Check GPX file structure validation
        if is_valid_gpx_structure(gpx_data):
            try:
                # Generate BLOB from GPX data
                gpx_blob = str(gpx_data).encode('ascii')

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
                flash("An error occurred while processing the GPX file.", "danger")
        else:
            flash("Invalid GPX file structure. Please upload a valid GPX file.", "danger")'''

    return render_template("user.html", title='Map', FileUploadForm=file_upload_form, route=route, routes=routes)


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
                    route = models.Route(
                        name=file.filename,
                        upload_time=datetime.now(),
                        gpx_data=gpx_blob
                    )

                    current_user.routes.append(route)

                    # Commit changes to the database
                    db.session.commit()

                    flash("GPX file uploaded successfully!", "success")
                    return jsonify({'message': 'File uploaded successfully'})
                except Exception as e:
                    db.session.rollback()  # Rollback changes if an exception occurs
                    print(f"Error: {e}")
                    flash("An error occurred while processing the GPX file.", "danger")
                    return jsonify({'error': 'Internal server error'}), 500
            else:
                flash("Invalid GPX file structure. Please upload a valid GPX file.", "danger")
                return jsonify({'error': 'Invalid GPX file structure'}), 400
        else:
            print('No file provided')
            return jsonify({'error': 'No file provided'}), 400
    else:
        print('Form validation failed')
        # Provide a more detailed error response for form validation failure
        return jsonify({'error': 'Form validation failed', 'errors': form.errors}), 400