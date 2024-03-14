from app import models

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, BooleanField, IntegerField
from wtforms.validators import InputRequired, Length, Email, ValidationError
from flask_wtf.file import FileField
from .funcs import getCurrentBuisnessWeek

def emailSearch_Validator(form, userEmail):
    # if the email isnt in the database and isnt an empty string
    if not models.User.query.filter_by(email=userEmail.data).all() and userEmail.data!="":
        raise ValidationError('That user email does not exist')

def revWeeks_Validator(form, weeks):
    numberOfWeeks = getCurrentBuisnessWeek()
    if weeks.data > numberOfWeeks:
        raise ValidationError("There are only " + str(numberOfWeeks) + " weeks of data")

    elif weeks.data <= 0:
        raise ValidationError("Value must be larger than 0 (1+)")

class RegistrationForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    first_name = StringField("First Name", validators=[InputRequired(), Length(min=3, max=128)])
    last_name = StringField("Last Name", validators=[InputRequired(), Length(min=3, max=128)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=32)])
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired()])
    TandCConfirm = BooleanField('Accept Terms and Conditions')


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=32)])
    rememberMe = BooleanField('Remember Me')


class FileUploadForm(FlaskForm):
    file_upload = FileField('File')
    submit_file = SubmitField('Submit')


class UserSearch(FlaskForm):
    userEmail = StringField('userEmail', validators=[emailSearch_Validator])
    submitSearch = SubmitField('Search')

class ChangeRevWeeks(FlaskForm):
    weeks = IntegerField('newRev', validators=[InputRequired(), revWeeks_Validator])
    submitWeeks = SubmitField('Submit')