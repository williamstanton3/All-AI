from flask_wtf import FlaskForm
from wtforms.fields import PasswordField, SubmitField, EmailField, BooleanField
from wtforms.validators import InputRequired, Email, EqualTo, Length

class RegisterForm(FlaskForm):
    email = EmailField("Email: ", validators=[InputRequired()])
    password = PasswordField("Password: ", 
        validators=[InputRequired(), Length(min=8, max=256)])
    confirm_password = PasswordField(
    'Confirm Password',
    validators=[
        InputRequired(),
        EqualTo('password', message="Passwords don't match")
    ])

    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = EmailField("Email: ", validators=[InputRequired()])
    password = PasswordField("Password: ", 
        validators=[InputRequired(), Length(min=8, max=256)])
    submit = SubmitField("Login")
