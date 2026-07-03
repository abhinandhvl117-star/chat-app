import os
import uuid
from flask import render_template, redirect, url_for, flash, current_app, abort, request  
from flask_login import login_required, current_user
from PIL import Image
from app.profile import profile_bp
from app.profile.forms import EditProfileForm
from app.models import User
from app.extensions import db


def save_profile_picture(file_storage):
    parts = file_storage.filename.rsplit('.', 1)
    if len(parts) < 2:                                 
        raise ValueError('File has no extension.')
    ext = parts[1].lower()
    filename = f'avatar_{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    img = Image.open(file_storage)
    if img.mode in ('RGBA', 'P', 'CMYK'):
        img = img.convert('RGB')
    img.thumbnail((256, 256))
    img.save(filepath)
    return filename


@profile_bp.route('/<username>')
@login_required
def view(username):
    user = User.query.filter_by(username=username).first_or_404()
    is_self = (user.id == current_user.id)
    is_friend = current_user.is_friend_with(user) if not is_self else False
    request_sent = current_user.has_pending_request_to(user) if not is_self else False

    friends = user.get_friends()

    return render_template(
        'profile/view.html',
        user=user,
        is_self=is_self,
        is_friend=is_friend,
        request_sent=request_sent,
        friends=friends,
        title=f"{user.username}'s Profile"
    )


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditProfileForm()

    if form.validate_on_submit():
        current_user.username = form.username.data.strip()
        current_user.bio = (form.bio.data or '').strip() 

        if form.profile_picture.data:
            old_pic = current_user.profile_picture
            if old_pic and old_pic != 'default.png':
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_pic)
                if os.path.exists(old_path):
                    os.remove(old_path)

            filename = save_profile_picture(form.profile_picture.data)
            current_user.profile_picture = filename

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile.view', username=current_user.username))

    elif request.method == 'GET':                        
        form.username.data = current_user.username
        form.bio.data = current_user.bio

    return render_template('profile/edit.html', form=form, title='Edit Profile')

