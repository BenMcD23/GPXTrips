from app import app
from flask import render_template

# render map page from templates
@app.route('/')
def map():
    return render_template('map.html', title='Map')