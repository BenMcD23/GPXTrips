from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, RadioField
from wtforms.validators import InputRequired, Length, Email


class RegistrationForm(FlaskForm):
    email = EmailField(
        "Email", validators=[InputRequired(), Email()]
    )
    first_name = StringField(
        "FirstName", validators=[InputRequired(), Length(min=3, max=16)]
    )
    last_name = StringField(
        "LastName", validators=[InputRequired(), Length(min=3, max=16)]
    )
    password = PasswordField(
        "Password", validators=[InputRequired(), Length(min=8, max=16)]
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[InputRequired()]
    )
    options = RadioField(
        'Options', choices=[('option1', 'Option 1'), ('option2', 'Option 2'), ('option3', 'Option 3')], validators=[InputRequired()]
    )


class LoginForm(FlaskForm):
    email = EmailField(
        "Email", validators=[InputRequired(), Email()]
    )
    password = PasswordField(
        "Password", validators=[InputRequired(), Length(min=8, max=16)]
    )

class FileUploadForm(FlaskForm):
    file_upload = FileField('File')
    submit_file = SubmitField('Submit')