from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Child, Application, Complaint, HomeStudy, Notification
import os
from werkzeug.utils import secure_filename

parent = Blueprint('parent', __name__)

ALLOWED = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED

@parent.route('/parent/dashboard')
@login_required
def dashboard():
    if current_user.role != 'parent':
        return redirect(url_for(f'{current_user.role}.dashboard'))
    applications = Application.query.filter_by(parent_id=current_user.id).all()
    home_study = HomeStudy.query.filter_by(parent_id=current_user.id).first()
    notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).order_by(
        Notification.created_at.desc()).all()
    return render_template('parent/dashboard.html',
        applications=applications,
        home_study=home_study,
        notifications=notifications)

@parent.route('/parent/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id).order_by(
        Notification.created_at.desc()).all()
    for n in notifications:
        n.is_read = True
    db.session.commit()
    return render_template('parent/notifications.html',
        notifications=notifications)

@parent.route('/parent/children')
@login_required
def view_children():
    home_study = HomeStudy.query.filter_by(
        parent_id=current_user.id,
        status='completed').first()
    if not home_study:
        flash('You must complete home study before applying!', 'warning')
        return redirect(url_for('parent.dashboard'))
    if home_study.recommendation == 'not_recommended':
        flash('Sorry! Your home study was not recommended.', 'danger')
        return redirect(url_for('parent.dashboard'))

    # Search & Filter
    q = request.args.get('q', '')
    gender = request.args.get('gender', '')
    age_min = request.args.get('age_min', 0, type=int)
    age_max = request.args.get('age_max', 18, type=int)
    health = request.args.get('health', '')

    query = Child.query.filter_by(status='available')
    if q:
        query = query.filter(Child.name.ilike(f'%{q}%'))
    if gender:
        query = query.filter_by(gender=gender)
    if health:
        query = query.filter(Child.health_status.ilike(f'%{health}%'))
    query = query.filter(Child.age >= age_min, Child.age <= age_max)
    children = query.all()

    return render_template('parent/children.html',
        children=children,
        q=q, gender=gender,
        age_min=age_min, age_max=age_max, health=health)

@parent.route('/parent/apply/<int:child_id>',
    methods=['GET', 'POST'])
@login_required
def apply(child_id):
    child = Child.query.get_or_404(child_id)

    existing = Application.query.filter_by(
        parent_id=current_user.id,
        child_id=child_id).first()
    if existing:
        flash('You already applied for this child!',
            'warning')
        return redirect(url_for('parent.view_children'))

    if request.method == 'POST':
        parent_age = int(
            request.form.get('parent_age', 0))
        spouse_age = int(
            request.form.get('spouse_age', 0) or 0)
        child_age = child.age

        # Server side age validation
        age_error = None
        if parent_age < 25:
            age_error = f"Parent must be minimum 25 years old. Your age: {parent_age}"
        elif child_age <= 2 and parent_age > 45:
            age_error = f"For child aged 0-2 years maximum parent age is 45. Your age: {parent_age}"
        elif child_age <= 8 and parent_age > 50:
            age_error = f"For child aged 2-8 years maximum parent age is 50. Your age: {parent_age}"
        elif child_age <= 18 and parent_age > 55:
            age_error = f"For child aged 8-18 years maximum parent age is 55. Your age: {parent_age}"
        elif (parent_age - child_age) < 25:
            age_error = f"Minimum 25 years age gap required. Current gap: {parent_age - child_age} years"
        elif spouse_age > 0 and (parent_age + spouse_age) > 110:
            age_error = f"Combined age exceeds 110 years. Combined: {parent_age + spouse_age}"

        if age_error:
            flash(f'Age Validation Failed: {age_error}',
                'danger')
            return render_template('parent/apply.html',
                child=child)

        # Save uploaded files
        saved = {}
        files = {
            'id_proof': request.files.get('id_proof'),
            'income_proof': request.files.get('income_proof'),
            'marriage_cert': request.files.get('marriage_cert'),
            'medical_cert': request.files.get('medical_cert'),
            'police_verification': request.files.get('police_verification'),
        }
        for key, file in files.items():
            if file and allowed_file(file.filename):
                name = secure_filename(file.filename)
                file.save(os.path.join(
                    'static/uploads', name))
                saved[key] = name

        application = Application(
            parent_id=current_user.id,
            child_id=child_id,
            reason=request.form.get('reason'),
            income=request.form.get('income'),
            occupation=request.form.get('occupation'),
            family_size=request.form.get('family_size'),
            parent_age=parent_age,
            spouse_age=spouse_age if spouse_age > 0 else None,
            combined_age=parent_age + spouse_age if spouse_age > 0 else None,
            age_gap=parent_age - child_age,
            age_validated=True,
            id_proof=saved.get('id_proof'),
            income_proof=saved.get('income_proof'),
            marriage_cert=saved.get('marriage_cert'),
            medical_cert=saved.get('medical_cert'),
            police_verification=saved.get(
                'police_verification'),
            status='pending'
        )
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully!',
            'success')
        return redirect(url_for('parent.dashboard'))

    return render_template('parent/apply.html',
        child=child)
@parent.route('/parent/track')
@login_required
def track():
    status_filter = request.args.get('status', 'all')
    if status_filter == 'all':
        applications = Application.query.filter_by(
            parent_id=current_user.id).all()
    else:
        applications = Application.query.filter_by(
            parent_id=current_user.id,
            status=status_filter).all()
    return render_template('parent/track.html',
        applications=applications,
        status_filter=status_filter)

@parent.route('/parent/complaint/<int:app_id>', methods=['GET', 'POST'])
@login_required
def file_complaint(app_id):
    application = Application.query.get_or_404(app_id)
    if request.method == 'POST':
        complaint = Complaint(
            application_id=app_id,
            filed_by=current_user.name,
            filed_by_role='parent',
            description=request.form.get('description'),
            is_urgent=True if request.form.get('is_urgent') else False)
        db.session.add(complaint)
        db.session.commit()
        flash('Complaint filed! Admin will investigate.', 'success')
        return redirect(url_for('parent.track'))
    return render_template('parent/complaint.html', application=application)