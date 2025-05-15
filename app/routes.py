# app/routes.py

from flask import Blueprint, render_template, url_for, flash, redirect, request, jsonify
from app import db
from app.forms import RegistrationForm, LoginForm
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
# from flask import request, jsonify
from app import limiter

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created. You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute") 
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login failed. Check email and password.', 'danger')
    return render_template('login.html', form=form)

## Ajax vuln request
@main.route('/api/v1/accounts/login/ajax', methods=['POST'])
def ajax_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        return jsonify({"success": True})
    
    return jsonify({"success": False}), 401



@main.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

## Link routes

from app.forms import LinkForm
from app.models import Link

@main.route('/add_link', methods=['GET', 'POST'])
@login_required
def add_link():
    form = LinkForm()
    if form.validate_on_submit():
        new_link = Link(title=form.title.data, url=form.url.data, owner=current_user)
        db.session.add(new_link)
        db.session.commit()
        flash('Link added!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('link_form.html', form=form, action='Add')

@main.route('/edit_link/<int:link_id>', methods=['GET', 'POST'])
@login_required
def edit_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.owner != current_user:
        flash("You can't edit someone else's link!", 'danger')
        return redirect(url_for('main.dashboard'))
    form = LinkForm(obj=link)
    if form.validate_on_submit():
        link.title = form.title.data
        link.url = form.url.data
        db.session.commit()
        flash('Link updated!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('link_form.html', form=form, action='Edit')

@main.route('/delete_link/<int:link_id>', methods=['POST'])
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.owner != current_user:
        flash("You can't delete someone else's link!", 'danger')
        return redirect(url_for('main.dashboard'))
    db.session.delete(link)
    db.session.commit()
    flash('Link deleted.', 'info')
    return redirect(url_for('main.dashboard'))

## Access Profiles

@main.route('/u/<string:username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)

