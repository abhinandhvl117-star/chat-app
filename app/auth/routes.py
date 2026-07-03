from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.auth.forms import RegistrationForm, LoginForm
from app.models import User
from app.extensions import db


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat.rooms'))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.lower().strip()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)                                        
        flash('Account created. You are now logged in.', 'success')
        return redirect(url_for('chat.rooms'))

    return render_template('auth/register.html', form=form, title='Register')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat.rooms'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')

        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        flash(f'Welcome back, {user.username}.', 'success')
        return redirect(url_for('chat.rooms'))

    return render_template('auth/login.html', form=form, title='Log In')


@auth_bp.route('/logout')                                      
@login_required
def logout():
    current_user.is_online = False
    db.session.commit()

    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))