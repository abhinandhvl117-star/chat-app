from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import Length, Optional, ValidationError, DataRequired  
from flask_login import current_user


class EditProfileForm(FlaskForm):

    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),     
            Length(min=3, max=64, message='Username must be 3–64 characters.')
        ]
    )

    bio = TextAreaField(
        'About Me',
        validators=[
            Optional(),
            Length(max=500, message='Bio must be 500 characters or fewer.')
        ]
    )

    profile_picture = FileField(
        'Profile Picture',
        validators=[
            Optional(),
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'gif', 'webp'],
                'Images only (jpg, png, gif, webp).'
            )
        ]
    )

    submit = SubmitField('Save Changes')

    def validate_username(self, field):
        from app.models import User                            
        if field.data != current_user.username:
            user = User.query.filter_by(username=field.data).first()
            if user:
                raise ValidationError('Username already taken.')