import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        error = None
        
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif role not in ['teacher', 'student']:
            error = 'Invalid role.'
        elif User.query.filter_by(username=username).first() is not None:
            error = f"User {username} is already registered."
            
        if error is None:
            user = User(username=username, password=password, role=role)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('auth.login'))
            
        flash(error)
            
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        if current_user.is_teacher():
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
            
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        error = None
        user = User.query.filter_by(username=username).first()
        
        if user is None:
            error = 'Incorrect username.'
        elif not user.check_password(password):
            error = 'Incorrect password.'
            
        if error is None:
            login_user(user)
            
            if user.is_teacher():
                return redirect(url_for('teacher.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
                
        flash(error)
            
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login')) 