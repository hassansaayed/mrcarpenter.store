from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_wtf import FlaskForm
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://quicklinks_db_user:BlqLOpfSIcZHXaqW7KBlgkVEncObLRGw@dpg-d0jhmrm3jp1c739uot30-a.oregon-postgres.render.com/quicklinks_db'
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:new_password@localhost/dbname?charset=utf8mb4'


app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 300,
    'pool_pre_ping': True
}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
limiter = Limiter(get_remote_address, app=app)

### MODELS ###
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)  # Already has length
    email = db.Column(db.String(120), unique=True, nullable=False)     # Already has length
    password = db.Column(db.String(500), nullable=False)  # Changed from 2000 to 500
    links = db.relationship('Link', backref='owner', lazy=True)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # Added length
    url = db.Column(db.String(255), nullable=False)    # Added length
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

### FORMS ###
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError('That username is taken.')

    def validate_email(self, email):
        if User.query.filter_by(email=email.data).first():
            raise ValidationError('That email is already registered.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class LinkForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    url = StringField('URL', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('Save Link')

### ROUTES ###
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed.', 'danger')
    return render_template('login.html', form=form)

@app.route('/api/v1/accounts/login/ajax', methods=['POST'])
def ajax_login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and check_password_hash(user.password, data.get('password')):
        login_user(user)
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/add_link', methods=['GET', 'POST'])
@login_required
def add_link():
    form = LinkForm()
    if form.validate_on_submit():
        new_link = Link(title=form.title.data, url=form.url.data, owner=current_user)
        db.session.add(new_link)
        db.session.commit()
        flash('Link added!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('link_form.html', form=form, action='Add')

@app.route('/edit_link/<int:link_id>', methods=['GET', 'POST'])
@login_required
def edit_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.owner != current_user:
        flash("You can't edit someone else's link!", 'danger')
        return redirect(url_for('dashboard'))
    form = LinkForm(obj=link)
    if form.validate_on_submit():
        link.title = form.title.data
        link.url = form.url.data
        db.session.commit()
        flash('Link updated!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('link_form.html', form=form, action='Edit')

@app.route('/delete_link/<int:link_id>', methods=['POST'])
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.owner != current_user:
        flash("You can't delete someone else's link!", 'danger')
    else:
        db.session.delete(link)
        db.session.commit()
        flash('Link deleted.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/u/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)

### CREATE DB ###
with app.app_context():
    db.create_all()  # Safe - won't touch existing data
    print("Verified database tables")

if __name__ == '__main__':
    app.run(debug=False)
