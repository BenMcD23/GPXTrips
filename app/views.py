from app import app
from flask import render_template, request, redirect, url_for, send_file


@app.route('/')
def map():
    """render map page from templates

    Returns:
        _type_: render template, with map.html
    """
    return render_template('map.html', title='Map')


@app.route('/', methods=['POST'])
def upload_file():
    """for user file upload

    Returns:
        _type_: nothing for now
    """
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
    return None
