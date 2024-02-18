from app import app
from flask import Flask, render_template

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/manager')
def manager():
    return render_template("manager.html")

@app.route('/user')
def user():
    return render_template("user.html")
