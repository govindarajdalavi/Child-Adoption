from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Child, CWCOrder, Notification, User, AuditLog
from datetime import datetime
from functools import wraps

cwc = Blueprint('cwc', __name__)

def cwc_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or \
                current_user.role != 'cwc':
            flash('CWC access required!', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def send_notification(user_id, title, message):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message
    )
    db.session.add(notification)

@cwc.route('/cwc/dashboard')
@login_required
@cwc_required
def dashboard():
    pending = Child.query.filter_by(status='cwc_review').all()
    orders = CWCOrder.query.filter_by(cwc_officer_id=current_user.id).all()
    legally_free = [o for o in orders if o.status == 'legally_free']
    rejected = [o for o in orders if o.status != 'legally_free']
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    return render_template('cwc/dashboard.html',
        pending=pending,
        orders=orders,
        legally_free=legally_free,
        rejected=rejected,
        notifications=notifications
    )

@cwc.route('/cwc/review/<int:child_id>',
    methods=['GET', 'POST'])
@login_required
@cwc_required
def review_child(child_id):
    child = Child.query.get_or_404(child_id)
    if request.method == 'POST':
        decision = request.form.get('decision')
        order = CWCOrder(
            child_id=child_id,
            cwc_officer_id=current_user.id,
            order_number=request.form.get(
                'order_number'),
            investigation_notes=request.form.get(
                'investigation_notes'),
            background_verified=True if request.form.get(
                'background_verified') else False,
            medical_examined=True if request.form.get(
                'medical_examined') else False,
            status=decision,
            order_date=request.form.get('order_date')
        )
        db.session.add(order)
        
        # Log action
        log = AuditLog(
            user_id=current_user.id,
            action=f'cwc_decision_{decision}',
            entity_type='child',
            entity_id=child.id,
            details=f'Order No: {request.form.get("order_number")}. Notes: {request.form.get("investigation_notes")}',
            ip_address=request.remote_addr
        )
        db.session.add(log)

        if decision == 'legally_free':
            child.status = 'legally_free'
            flash(f'{child.name} declared legally free for adoption! ✅', 'success')
            # Notify admin
            admins = User.query.filter_by(
                role='admin').all()
            for admin in admins:
                send_notification(
                    admin.id,
                    'Child Declared Legally Free',
                    f'{child.name} has been declared legally free for adoption by CWC. Please verify and list.'
                )
        else:
            child.status = 'cwc_rejected'
            flash('Child registration rejected by CWC.',
                'danger')
        db.session.commit()
        return redirect(url_for('cwc.dashboard'))
    return render_template('cwc/review.html',
        child=child)