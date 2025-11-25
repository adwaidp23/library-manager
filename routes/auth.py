from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db, bcrypt
from models import User
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('books.search'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role')     # Get the selected role
        admin_key = request.form.get('admin_key') # Get the entered key
        
        # --- SECURITY CHECK ---
        # Define your secret key here (In a real app, keep this in .env)
        SECRET_ADMIN_CODE = "LibraryMaster2025" 

        if role == 'admin':
            if admin_key != SECRET_ADMIN_CODE:
                flash('Invalid Admin Secret Key! Registration failed.', 'danger')
                return redirect(url_for('auth.register'))
        # ----------------------

        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Hash password
        pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create user with the selected role
        new_user = User(
            name=name, 
            email=email, 
            phone=phone, 
            password_hash=pw_hash,
            role=role  # <--- Save the verified role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Registration successful as {role}! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('books.search'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and user.verify_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('books.search'))
        
        flash('Invalid email or password.', 'danger')
        return redirect(url_for('auth.login'))
    
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
