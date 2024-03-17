from app import models

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, BooleanField
from wtforms.validators import InputRequired, Length, Email, ValidationError, DataRequired, EqualTo
from flask_wtf.file import FileField


def emailSearch_Validator(form, userEmail):
    # if the tag isnt in the database and isnt an empty string
    if not models.User.query.filter_by(email=userEmail.data).all() and userEmail.data != "":
        raise ValidationError('That user email does not exist')


class RegistrationForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    first_name = StringField("First Name", validators=[
                             InputRequired(), Length(min=3, max=128)])
    last_name = StringField("Last Name", validators=[
                            InputRequired(), Length(min=3, max=128)])
    password = PasswordField("Password", validators=[
                             InputRequired(), Length(min=8, max=32)])
    confirm_password = PasswordField("Confirm Password", validators=[
                                     InputRequired(), EqualTo('password')])
    TandCConfirm = BooleanField('Accept Terms and Conditions')


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[
                             InputRequired(), Length(min=8, max=32)])
    rememberMe = BooleanField('Remember Me')


class FileUploadForm(FlaskForm):
    file_upload = FileField('File')
    submit_file = SubmitField('Submit')


class UserSearch(FlaskForm):
    userEmail = StringField('userEmail', validators=[emailSearch_Validator])
    submitSearch = SubmitField('Search')

# User Management Forms


class SubscriptionForm(FlaskForm):
    cancel_subscription = SubmitField('Cancel Subscription')
    renew_subscription = SubmitField('Renew Subscription')


class AccountForm(FlaskForm):
    change_email = SubmitField('Change Email')
    change_password = SubmitField('Change Password')
    delete_account = SubmitField('Delete Account')


class ChangeEmailForm(FlaskForm):
    new_email = StringField('New Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Change Email')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[
                                 DataRequired(), Length(min=8, max=32)])
    new_password = PasswordField('New Password', validators=[
                                 DataRequired(), Length(min=8, max=32)])
    confirm_password = PasswordField('Confirm New Password', validators=[
                                     DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')
