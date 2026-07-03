from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    ValidationError
)



class RegistrationForm(FlaskForm):

    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(min=3, max=50, message='Username must be 3–50 characters.')
        ]
    )

    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.')
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),        
            Length(min=8, message='Password must be at least 8 characters.')  
        ]
    )

    password2 = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords must match.')
        ]
    )

    submit = SubmitField('Create Account')

    def validate_username(self, field):
        from app.models import User                              
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('Username already taken. Please create another.')

    def validate_email(self, field):
        from app.models import User                              
        user = User.query.filter_by(email=field.data.lower()).first()
        if user:
            raise ValidationError('Email already registered. Please log in.')


class LoginForm(FlaskForm):

    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Enter a valid email address.')
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.')
        ]
    )

    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')