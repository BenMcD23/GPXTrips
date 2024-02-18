from app import app
from flask import Flask, render_template

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/registration')
def login():
    return render_template('registration.html')