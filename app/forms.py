from app import models

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, BooleanField, IntegerField, FloatField
from wtforms.validators import InputRequired, Length, Email, ValidationError, DataRequired, EqualTo
from flask_wtf.file import FileField
from .funcs import getCurrentBuisnessWeek
import re


def emailSearch_Validator(form, userEmail):
    # if the email isnt in the database and isnt an empty string
    if not models.User.query.filter_by(email=userEmail.data).all() and userEmail.data != "":
        raise ValidationError('That user email does not exist.')


def revWeeks_Validator(form, weeks):
    numberOfWeeks = getCurrentBuisnessWeek()
    if weeks.data > numberOfWeeks:
        raise ValidationError("There are only " +
                              str(numberOfWeeks) + " weeks of data.")

    elif weeks.data <= 0:
        raise ValidationError("Value must be larger than 0. (1+)")


def price_Validator(form, new_price):
    if not re.match(r'^[0-9]\d*(\.\d{1,2})?$', str(new_price.data)):
        raise ValidationError("Incorrect price format. Only 2 dp allowed.")

    elif new_price.data <= 0:
        raise ValidationError("Price must be larger than 0.")

    # elif len(new_price.data.rsplit('.')[-1]) == 2:
    #     print('2 digits after decimal point')


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

    submit_register = SubmitField('Register')


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[InputRequired(), Email()])
    password = PasswordField("Password", validators=[
                             InputRequired(), Length(min=8, max=32)])
    rememberMe = BooleanField('Remember Me')
    submit_login = SubmitField('Login')


class FileUploadForm(FlaskForm):
    file_upload = FileField('File')
    submit_file = SubmitField('Submit')


class UserSearch(FlaskForm):
    userEmail = StringField('userEmail', validators=[emailSearch_Validator])
    submitSearch = SubmitField('Search')


class ChangeRevWeeks(FlaskForm):
    weeks = IntegerField('weeks', validators=[
                         InputRequired(), revWeeks_Validator])
    submitWeeks = SubmitField('Submit')


# to change prices
class ChangeWeeklyPrice(FlaskForm):
    weekly_new_price = FloatField('new_price', validators=[
                                  InputRequired(), price_Validator])
    weekly_submit_price = SubmitField('Update')


class ChangeMonthlyPrice(FlaskForm):
    monthly_new_price = FloatField('new_price', validators=[
                                   InputRequired(), price_Validator])
    monthly_submit_price = SubmitField('Update')


class ChangeYearlyPrice(FlaskForm):
    yearly_new_price = FloatField('new_price', validators=[
                                  InputRequired(), price_Validator])
    yearly_submit_price = SubmitField('Update')


# User Management Forms
class SubscriptionForm(FlaskForm):
    cancel_subscription = SubmitField('Cancel Subscription')


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
