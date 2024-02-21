from app import app, db, models, bcrypt
from .models import User
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_login import login_user, login_required, logout_user
from .forms import FileUploadForm, RegistrationForm, LoginForm
from werkzeug.utils import secure_filename
from DAL import add_route, get_route
from datetime import datetime


@app.route('/', methods=['GET', 'POST'])
def map():
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

        # adds to database
        add_route(data)

        # this gets rid of all the \n in the string, cant be used with them
        route = get_route()
        splitData = route.split("\\n")
        route = "".join(splitData)[2:][:-1]

    return render_template('map.html', title='Map', FileUploadForm=file_upload_form, route=route)
  
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if request.method == 'POST':
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password_hash, form.password.data):
                flash("Logged in!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("map"))
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
        user = User(email=email, first_name=first_name, last_name=last_name, password_hash=hashed_password, date_created=datetime.now())
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

@app.route('/user')
def user():
    return render_template("user.html")