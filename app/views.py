import re

from app import app, db, models
from flask import render_template, request, redirect, url_for, send_file
from .forms import FileUploadForm
from werkzeug.utils import secure_filename
from DAL import add_route, get_route


@app.route('/', methods=['GET', 'POST'])
def map():
    """render map page from templates

    Returns:
        render_template: render template, with map.html
    """
    # file upload form
    file_upload_form = FileUploadForm()

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
