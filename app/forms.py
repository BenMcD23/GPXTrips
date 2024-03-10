from app import models

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, RadioField, SubmitField
from wtforms.validators import InputRequired, Length, Email, ValidationError
from flask_wtf.file import FileField

def emailSearch_Validator(form, userEmail):
    # if the tag isnt in the database and isnt an empty string
    if not models.User.query.filter_by(email=userEmail.data).all() and userEmail.data!="":
        raise ValidationError('That user email does not exist')


class RegistrationForm(FlaskForm):
    email = EmailField(
        "Email", validators=[InputRequired(), Email()]
    )
    first_name = StringField(
        "First Name", validators=[InputRequired(), Length(min=3, max=128)]
    )
    last_name = StringField(
        "Last Name", validators=[InputRequired(), Length(min=3, max=128)]
    )
    password = PasswordField(
        "Password", validators=[InputRequired(), Length(min=8, max=32)]
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[InputRequired()]
    )


class LoginForm(FlaskForm):
    email = EmailField(
        "Email", validators=[InputRequired(), Email()]
    )
    password = PasswordField(
        "Password", validators=[InputRequired(), Length(min=8, max=32)]
    )

class FileUploadForm(FlaskForm):
    file_upload = FileField('File')
    submit_file = SubmitField('Submit')

class UserSearch(FlaskForm):
    userEmail = StringField('userEmail', validators=[emailSearch_Validator])
    submitSearch = SubmitField('Search')