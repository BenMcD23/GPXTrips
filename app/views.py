from flask import render_template, flash, request, redirect, url_for
from app import app, db, bcrypt
from flask_login import login_user
from .models import User

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash(
                "Passwords do not match. Please make sure your passwords match.",
                "error",
            )
            return render_template("register.html", title="Register", form=form)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash(
                "Username already taken. Please choose a different username.", "error"
            )
            return render_template("register.html", title="Register", form=form)

        hashed_password = bcrypt.generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash("User added successfully!", "success")

        return redirect(url_for("login"))

    return render_template("register.html", title="Register", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                flash("Logged in!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("home"))
            else:
                flash("Password is wrong!", category="error")
                return redirect(url_for("login"))
        else:
            flash("Username does not exist!", category="error")
            return redirect(url_for("login"))

    return render_template("login.html", title="Login", form=form)