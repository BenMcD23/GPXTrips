from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, RadioField, SubmitField
from wtforms.validators import InputRequired, Length, Email
from flask_wtf.file import FileField


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
    plan = RadioField(
        'Plan', choices=[('plan1', '1 Year - £70'), ('plan2', '1 Month - £35'), ('plan3', '1 Week - £10')], validators=[InputRequired()]
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