from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from app import bcrypt
import os
from werkzeug.utils import secure_filename

auth = Blueprint('auth', __name__)

ALLOWED = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED

def get_dashboard_url(role):
    role_map = {
        'collector': 'collector.dashboard',
        'admin': 'admin.dashboard',
        'cwc': 'cwc.dashboard',
        'orphanage': 'orphanage.dashboard',
        'socialworker': 'socialworker.dashboard',
        'court': 'court.dashboard',
        'parent': 'parent.dashboard'
    }
    endpoint = role_map.get(role)
    return url_for(endpoint) if endpoint else url_for('auth.login')

@auth.route('/')
def home():
    from models import Child, Application
    total_children = Child.query.count()
    total_adoptions = Application.query.filter_by(status='completed').count()
    foster_care = Application.query.filter(Application.status.in_(['foster_care', 'court_temp_order_issued'])).count()
    
    return render_template('index.html', 
                           total_children=total_children, 
                           total_adoptions=total_adoptions, 
                           foster_care=foster_care)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(get_dashboard_url(current_user.role))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter email and password!', 'warning')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            if user.role in ['socialworker', 'orphanage'] and not user.is_verified:
                flash('Your account is pending verification! '
                      'Admin will verify your documents and '
                      'activate your account shortly.', 'warning')
                return render_template('auth/login.html')
            login_user(user)
            flash(f'Welcome, {user.name}!', 'success')
            return redirect(get_dashboard_url(user.role))
        else:
            flash('Invalid email or password!', 'danger')
            return render_template('auth/login.html')

    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role', 'parent')
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        organization_name = request.form.get('organization_name', '').strip()
        license_number = request.form.get('license_number', '').strip()
        designation = request.form.get('designation', '').strip()

        if not email or not name or not password:
            flash('Name, Email and Password are required!', 'warning')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered! Please login.', 'danger')
            return redirect(url_for('auth.login'))

        upload_folder = os.path.join('static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        photo_name = 'default_user.png'
        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '' \
                and allowed_file(photo_file.filename):
            filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(upload_folder, filename))
            photo_name = filename

        sw_license_name = None
        sw_file = request.files.get('sw_license')
        if sw_file and sw_file.filename != '' \
                and allowed_file(sw_file.filename):
            sw_name = secure_filename(sw_file.filename)
            sw_file.save(os.path.join(upload_folder, sw_name))
            sw_license_name = sw_name

        employee_id_name = None
        emp_file = request.files.get('employee_id')
        if emp_file and emp_file.filename != '' \
                and allowed_file(emp_file.filename):
            emp_name = secure_filename(emp_file.filename)
            emp_file.save(os.path.join(upload_folder, emp_name))
            employee_id_name = emp_name

        org_license_name = None
        org_file = request.files.get('org_license')
        if org_file and org_file.filename != '' \
                and allowed_file(org_file.filename):
            org_name = secure_filename(org_file.filename)
            org_file.save(os.path.join(upload_folder, org_name))
            org_license_name = org_name

        license_document = sw_license_name or org_license_name

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        is_verified = True if role == 'parent' else False

        user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            phone=phone,
            address=address,
            organization_name=organization_name,
            license_number=license_number,
            designation=designation,
            photo=photo_name,
            license_document=license_document,
            is_verified=is_verified
        )

        db.session.add(user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Email already registered! Please login.', 'danger')
            return redirect(url_for('auth.login'))
        

        if role == 'socialworker':
            flash('Registration submitted! Your account '
                  'will be activated after admin verifies '
                  'your license documents.', 'warning')
        elif role == 'orphanage':
            flash('Registration submitted! Your account '
                  'will be activated after admin verifies '
                  'your orphanage documents.', 'warning')
        else:
            flash('Registration successful! Please login.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('auth.login'))