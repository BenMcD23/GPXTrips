from app import app
from flask import Flask, render_template

@app.route('/manager')
def manager():
    return render_template("manager.html")

@app.route('/user')
def user():
    return render_template("user.html")