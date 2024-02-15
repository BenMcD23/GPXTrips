from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SubmitField

class FileUploadForm(FlaskForm):
    file_upload = FileField('File')
    submit_file = SubmitField('Submit')