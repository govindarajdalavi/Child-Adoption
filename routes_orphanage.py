from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Child, ChildDocument, Notification, User
from functools import wraps
import os
from werkzeug.utils import secure_filename

orphanage = Blueprint('orphanage', __name__)

ALLOWED = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED

def orphanage_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or \
                current_user.role != 'orphanage':
            flash('Orphanage access required!', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@orphanage.route('/orphanage/dashboard')
@login_required
@orphanage_required
def dashboard():
    children = Child.query.filter_by(
        orphanage_id=current_user.id).all()
    total = len(children)
    registered = sum(1 for c in children if c.status == 'registered')
    cwc_review = sum(1 for c in children if c.status == 'cwc_review')
    available = sum(1 for c in children if c.status == 'available')
    adopted = sum(1 for c in children if c.status == 'adopted')
    notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).all()
    return render_template('orphanage/dashboard.html',
        children=children, total=total,
        registered=registered, cwc_review=cwc_review,
        available=available, adopted=adopted,
        notifications=notifications)

@orphanage.route('/orphanage/add_child', methods=['GET', 'POST'])
@login_required
@orphanage_required
def add_child():
    if request.method == 'POST':
        photo_name = 'default_child.png'
        photo_file = request.files.get('photo')
        if photo_file and allowed_file(photo_file.filename):
            photo_name = secure_filename(photo_file.filename)
            photo_file.save(os.path.join('static/uploads', photo_name))
        child = Child(
            name=request.form.get('name'),
            age=request.form.get('age'),
            gender=request.form.get('gender'),
            date_of_birth=request.form.get('date_of_birth'),
            health_status=request.form.get('health_status'),
            background=request.form.get('background'),
            how_child_came=request.form.get('how_child_came'),
            photo=photo_name,
            orphanage_id=current_user.id,
            status='registered'
        )
        db.session.add(child)
        db.session.flush()

        def save_doc(file_key, doc_type):
            f = request.files.get(file_key)
            if f and allowed_file(f.filename):
                fname = secure_filename(f.filename)
                f.save(os.path.join('static/uploads', fname))
                doc = ChildDocument(
                    child_id=child.id,
                    doc_type=doc_type,
                    file_path=fname,
                    uploaded_by=current_user.id)
                db.session.add(doc)

        save_doc('surrender_cert', 'surrender_certificate')
        save_doc('birth_cert', 'birth_certificate')
        save_doc('medical_report', 'medical_report')
        db.session.commit()
        flash('Child registered! Submit to CWC for verification.', 'success')
        return redirect(url_for('orphanage.dashboard'))
    return render_template('orphanage/add_child.html')

@orphanage.route('/orphanage/submit_to_cwc/<int:child_id>', methods=['POST'])
@login_required
@orphanage_required
def submit_to_cwc(child_id):
    child = Child.query.get_or_404(child_id)
    child.status = 'cwc_review'
    cwc_officers = User.query.filter_by(role='cwc').all()
    for cwc in cwc_officers:
        n = Notification(
            user_id=cwc.id,
            title='New Child for CWC Review',
            message=f'Child {child.name} from {current_user.organization_name} requires CWC investigation.')
        db.session.add(n)
    db.session.commit()
    flash(f'{child.name} submitted to CWC for review!', 'success')
    return redirect(url_for('orphanage.dashboard'))

@orphanage.route('/orphanage/children')
@login_required
@orphanage_required
def my_children():
    children = Child.query.filter_by(orphanage_id=current_user.id).all()
    return render_template('orphanage/children.html', children=children)