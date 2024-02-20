from flask import render_template, flash, request, redirect, url_for
from app import app, db, bcrypt
from flask_login import login_user, login_required, logout_user
from .models import User
from .forms import RegistrationForm, LoginForm
from datetime import datetime

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
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
            return render_template("register.html", title="Register", form=form)

        if password != confirm_password:
            flash(
                "Passwords do not match. Please make sure your passwords match.",
                "error",
            )
            return render_template("register.html", title="Register", form=form)

        selected_plan = form.plan.data
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

    return render_template("register.html", title="Register", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
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

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))