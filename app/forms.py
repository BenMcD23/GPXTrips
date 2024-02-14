from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import InputRequired, Length


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(), Length(min=3, max=16)]
    )
    password = PasswordField(
        "Password", validators=[InputRequired(), Length(min=8, max=16)]
    )
    confirm_password = PasswordField("Confirm Password", validators=[InputRequired()])


class LoginForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(), Length(min=3, max=16)]
    )
    password = PasswordField(
        "Password", validators=[InputRequired(), Length(min=8, max=16)]
    )