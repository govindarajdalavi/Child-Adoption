from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from models import db, Child, Application, User, HomeStudy, Notification, Complaint, CWCOrder, FollowUp, ChildConsent, AuditLog
from datetime import datetime, timedelta
from sqlalchemy import extract
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or \
                current_user.role != 'admin':
            flash('Admin access required!', 'danger')
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

@admin.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    total_children = Child.query.count()
    available = Child.query.filter_by(
        status='available').count()
    pending_cwc = Child.query.filter_by(
        status='cwc_review').count()
    pending_send_cwc = Child.query.filter_by(
        status='registered').count()
    pending_verify = Child.query.filter_by(
        status='legally_free').count()
    legally_free = Child.query.filter_by(
        status='legally_free').count()
    pending_apps = Application.query.filter_by(
        status='pending').count()
    home_study_pending = HomeStudy.query.filter_by(
        status='pending').count()
    pending_homestudy = HomeStudy.query.filter_by(
        status='pending').count()
    court_cases = Application.query.filter_by(
        status='hearing_scheduled').count()
    in_court = Application.query.filter_by(
        status='hearing_scheduled').count()
    adopted = Child.query.filter_by(
        status='adopted').count()
    open_complaints = Complaint.query.filter_by(
        status='open').count()
    total_orphanages = User.query.filter_by(
        role='orphanage').count()
    total_parents = User.query.filter_by(
        role='parent').count()
    pending_workers = User.query.filter_by(
        role='socialworker',
        is_verified=False).count()
    pending_orphanages = User.query.filter_by(
        role='orphanage',
        is_verified=False).count()
    recent_apps = Application.query.order_by(
        Application.applied_at.desc()).limit(5).all()
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False).order_by(
        Notification.created_at.desc()).limit(5).all()

    # Chart Data
    app_status_labels = [
        'Pending', 'Approved', 'Foster Care',
        'Court', 'Adopted', 'Rejected'
    ]
    app_status_data = [
        Application.query.filter_by(status='pending').count(),
        Application.query.filter_by(status='admin_approved').count(),
        Application.query.filter_by(status='foster_care').count(),
        Application.query.filter_by(status='hearing_scheduled').count(),
        Application.query.filter_by(status='court_approved').count(),
        Application.query.filter_by(status='rejected').count(),
    ]

    children_labels = [
        'Registered', 'CWC Review', 'Available',
        'Under Process', 'Foster Care', 'Adopted'
    ]
    children_data = [
        Child.query.filter_by(status='registered').count(),
        Child.query.filter_by(status='cwc_review').count(),
        Child.query.filter_by(status='available').count(),
        Child.query.filter_by(status='under_process').count(),
        Child.query.filter_by(status='foster_care').count(),
        Child.query.filter_by(status='adopted').count(),
    ]

    age_labels = [
        '0-2 yrs', '3-5 yrs', '6-10 yrs',
        '11-15 yrs', '16-18 yrs'
    ]
    age_data = [
        Child.query.filter(Child.age <= 2).count(),
        Child.query.filter(Child.age >= 3, Child.age <= 5).count(),
        Child.query.filter(Child.age >= 6, Child.age <= 10).count(),
        Child.query.filter(Child.age >= 11, Child.age <= 15).count(),
        Child.query.filter(Child.age >= 16).count(),
    ]

    monthly_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        d = datetime.now() - timedelta(days=30 * i)
        label = d.strftime('%b %Y')
        count = Application.query.filter(
            extract('month', Application.applied_at) == d.month,
            extract('year', Application.applied_at) == d.year
        ).count()
        monthly_labels.append(label)
        monthly_data.append(count)

    return render_template('admin/dashboard.html',
        total_children=total_children,
        available=available,
        pending_cwc=pending_cwc,
        pending_send_cwc=pending_send_cwc,
        pending_verify=pending_verify,
        legally_free=legally_free,
        pending_apps=pending_apps,
        home_study_pending=home_study_pending,
        pending_homestudy=pending_homestudy,
        court_cases=court_cases,
        in_court=in_court,
        adopted=adopted,
        open_complaints=open_complaints,
        total_orphanages=total_orphanages,
        total_parents=total_parents,
        pending_workers=pending_workers,
        pending_orphanages=pending_orphanages,
        recent_apps=recent_apps,
        notifications=notifications,
        app_status_labels=app_status_labels,
        app_status_data=app_status_data,
        children_labels=children_labels,
        children_data=children_data,
        age_labels=age_labels,
        age_data=age_data,
        monthly_labels=monthly_labels,
        monthly_data=monthly_data,
    )

@admin.route('/admin/children')
@login_required
@admin_required
def manage_children():
    children = Child.query.all()
    return render_template('admin/children.html',
        children=children)

@admin.route('/admin/children/search')
@login_required
@admin_required
def search_children():
    q = request.args.get('q', '')
    gender = request.args.get('gender', '')
    status = request.args.get('status', '')
    age_min = request.args.get('age_min', 0, type=int)
    age_max = request.args.get('age_max', 18, type=int)
    query = Child.query
    if q:
        query = query.filter(Child.name.ilike(f'%{q}%'))
    if gender:
        query = query.filter_by(gender=gender)
    if status:
        query = query.filter_by(status=status)
    query = query.filter(
        Child.age >= age_min,
        Child.age <= age_max)
    children = query.all()
    return render_template('admin/children.html',
        children=children,
        q=q, gender=gender,
        status=status,
        age_min=age_min,
        age_max=age_max)

@admin.route('/admin/child/send-cwc/<int:child_id>',
    methods=['POST'])
@login_required
@admin_required
def send_to_cwc(child_id):
    child = Child.query.get_or_404(child_id)
    child.status = 'cwc_review'
    db.session.commit()
    cwc_officers = User.query.filter_by(role='cwc').all()
    for cwc in cwc_officers:
        send_notification(
            cwc.id,
            'New Child for CWC Review',
            f'{child.name} registered by {child.registered_by.organization_name} requires CWC investigation.'
        )
    db.session.commit()
    flash(f'{child.name} sent to CWC for review!',
        'success')
    return redirect(url_for('admin.manage_children'))

@admin.route('/admin/child/verify/<int:child_id>',
    methods=['POST'])
@login_required
@admin_required
def verify_child(child_id):
    child = Child.query.get_or_404(child_id)
    child.status = 'available'
    db.session.commit()
    flash(f'{child.name} verified and listed!', 'success')
    return redirect(url_for('admin.manage_children'))

@admin.route('/admin/orphanages')
@login_required
@admin_required
def manage_orphanages():
    orphanages = User.query.filter_by(
        role='orphanage').all()
    return render_template('admin/orphanages.html',
        orphanages=orphanages)

@admin.route('/admin/parents')
@login_required
@admin_required
def manage_parents():
    parents = User.query.filter_by(role='parent').all()
    homestudies = HomeStudy.query.all()
    workers = User.query.filter_by(
        role='socialworker',
        is_verified=True).all()
    return render_template('admin/parents.html',
        parents=parents,
        homestudies=homestudies,
        workers=workers)

@admin.route('/admin/assign-homestudy/<int:parent_id>',
    methods=['POST'])
@login_required
@admin_required
def assign_homestudy(parent_id):
    worker_id = request.form.get('worker_id')
    if not worker_id:
        flash('Please select a social worker!', 'warning')
        return redirect(url_for('admin.manage_parents'))
    existing = HomeStudy.query.filter_by(
        parent_id=parent_id).first()
    if existing:
        flash('Home study already assigned!', 'warning')
        return redirect(url_for('admin.manage_parents'))
    study = HomeStudy(
        parent_id=parent_id,
        social_worker_id=int(worker_id),
        status='assigned'
    )
    db.session.add(study)
    send_notification(
        int(worker_id),
        'New Home Study Assigned',
        'You have been assigned a home study. Please visit the parent and submit your report.'
    )
    send_notification(
        parent_id,
        'Home Study Scheduled',
        'A social worker has been assigned for your home study. They will contact you shortly.'
    )
    db.session.commit()
    flash('Social worker assigned!', 'success')
    return redirect(url_for('admin.manage_parents'))

@admin.route('/admin/applications')
@login_required
@admin_required
def manage_applications():
    applications = Application.query.order_by(
        Application.applied_at.desc()).all()
    return render_template('admin/applications.html',
        applications=applications)

@admin.route('/admin/application/<int:app_id>',
    methods=['GET', 'POST'])
@login_required
@admin_required
def review_application(app_id):
    application = Application.query.get_or_404(app_id)
    if request.method == 'POST':
        action = request.form.get('action')
        application.admin_notes = request.form.get(
            'admin_notes')
        if action == 'approve':
            child_age = application.child.age
            if child_age >= 5:
                # JJ Act 2015 §58(3): consent mandatory
                application.status = 'consent_assessment'
                application.child.status = 'under_process'
                # Assign to a verified social worker
                worker_id = request.form.get('consent_worker_id')
                if worker_id:
                    application.consent_assigned_to = int(worker_id)
                    send_notification(
                        int(worker_id),
                        '📝 New Child Consent Assessment',
                        f'Please conduct Child Consent Assessment for '
                        f'{application.child.name} (age {child_age}) '
                        f'as required by JJ Act 2015 §58(3). '
                        f'Parent: {application.parent.name}'
                    )
                send_notification(
                    application.parent_id,
                    'Application Approved — Consent Assessment Scheduled ✅',
                    f'Your application for {application.child.name} has been '
                    f'approved! Since the child is {child_age} years old, a '
                    f'Child Consent Assessment is required by law (JJ Act §58(3)). '
                    f'A social worker will visit the child and you will be notified.'
                )
                flash('Application approved! Consent Assessment assigned '
                      '(child is 5+ years — JJ Act §58(3) applies).', 'success')
            else:
                # Child < 5: consent not legally required, proceed directly
                application.status = 'admin_approved'
                application.child.status = 'under_process'
                send_notification(
                    application.parent_id,
                    'Application Approved! ✅',
                    f'Your application for {application.child.name} (age {child_age}) '
                    f'has been approved. Pre-adoption foster care will begin soon.'
                )
                flash('Application approved! (Child < 5 yrs — consent '
                      'assessment not required by law.)', 'success')
            # Audit log
            log = AuditLog(
                user_id=current_user.id,
                action='approve_application',
                entity_type='application',
                entity_id=application.id,
                details=f'Approved by {current_user.name}. '
                        f'Child age: {application.child.age}',
                ip_address=request.remote_addr
            )
            db.session.add(log)
        elif action == 'foster_care':
            flash('ERROR: Foster care requires court temporary order first! Please send case to court.', 'danger')
            return redirect(url_for('admin.review_application', app_id=application.id))
        elif action == 'send_to_court':
            application.status = 'sent_to_court'
            application.child.status = 'court_process'
            courts = User.query.filter_by(role='court').all()
            for court in courts:
                send_notification(
                    court.id,
                    'New Adoption Case Filed',
                    f'Application for {application.child.name} has been sent to court for Temporary Order.'
                )
            send_notification(
                application.parent_id,
                'Case Sent to Court 🏛️',
                f'Your case for {application.child.name} has been sent to District Family Court for a Temporary Foster Care Order.'
            )
            flash('Case sent to court for Temporary Order!', 'success')
        elif action == 'reject':
            application.status = 'rejected'
            application.child.status = 'available'
            send_notification(
                application.parent_id,
                'Application Rejected',
                f'Your application for {application.child.name} was rejected. Reason: {application.admin_notes}'
            )
            flash('Application rejected.', 'danger')
        db.session.commit()
        return redirect(url_for('admin.manage_applications'))
    workers = User.query.filter_by(
        role='socialworker', is_verified=True).all()
    return render_template(
        'admin/review_application.html',
        application=application,
        workers=workers)

@admin.route('/admin/homestudies')
@login_required
@admin_required
def view_homestudies():
    studies = HomeStudy.query.all()
    return render_template('admin/homestudies.html',
        studies=studies)

@admin.route('/admin/followups')
@login_required
@admin_required
def view_followups():
    followups = FollowUp.query.order_by(
        FollowUp.created_at.desc()).all()
    return render_template('admin/followups.html',
        followups=followups)

@admin.route('/admin/complaints')
@login_required
@admin_required
def complaints():
    complaints = Complaint.query.order_by(
        Complaint.created_at.desc()).all()
    return render_template('admin/complaints.html',
        complaints=complaints)

@admin.route('/admin/complaint/<int:cid>/update',
    methods=['POST'])
@login_required
@admin_required
def update_complaint(cid):
    complaint = Complaint.query.get_or_404(cid)
    complaint.status = request.form.get('status')
    complaint.admin_action = request.form.get(
        'admin_action')
    db.session.commit()
    flash('Complaint updated!', 'success')
    return redirect(url_for('admin.complaints'))

@admin.route('/admin/mark-notification-read/<int:nid>')
@login_required
@admin_required
def mark_read(nid):
    notification = Notification.query.get_or_404(nid)
    notification.is_read = True
    db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/verify-workers')
@login_required
@admin_required
def verify_workers():
    pending_workers = User.query.filter_by(
        role='socialworker',
        is_verified=False).all()
    verified_workers = User.query.filter_by(
        role='socialworker',
        is_verified=True).all()
    pending_orphanages = User.query.filter_by(
        role='orphanage',
        is_verified=False).all()
    verified_orphanages = User.query.filter_by(
        role='orphanage',
        is_verified=True).all()
    return render_template('admin/verify_workers.html',
        pending_workers=pending_workers,
        verified_workers=verified_workers,
        pending_orphanages=pending_orphanages,
        verified_orphanages=verified_orphanages)

@admin.route('/admin/approve-user/<int:uid>',
    methods=['POST'])
@login_required
@admin_required
def approve_user(uid):
    user = User.query.get_or_404(uid)
    user.is_verified = True
    db.session.commit()
    send_notification(
        user.id,
        'Account Approved! ✅',
        'Your account has been verified and activated by District Admin. You can now login.'
    )
    db.session.commit()
    flash(f'{user.name} approved!', 'success')
    return redirect(url_for('admin.verify_workers'))

@admin.route('/admin/reject-user/<int:uid>',
    methods=['POST'])
@login_required
@admin_required
def reject_user(uid):
    user = User.query.get_or_404(uid)
    name = user.name
    db.session.delete(user)
    db.session.commit()
    flash(f'{name} rejected and removed!', 'danger')
    return redirect(url_for('admin.verify_workers'))

@admin.route('/admin/report')
@login_required
@admin_required
def generate_report():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height-50,
        "District Child Adoption Monitoring Report")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height-70,
        "District Collectorate, Dharwad — Karnataka")
    c.setFont("Helvetica", 10)
    c.drawString(50, height-95,
        f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
    c.drawString(50, height-110,
        "Under: Juvenile Justice Act 2015 & CARA Guidelines 2022")
    c.line(50, height-120, width-50, height-120)

    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, height-145, "Summary Statistics")
    c.setFont("Helvetica", 11)

    stats = [
        f"Total Orphanages: {User.query.filter_by(role='orphanage').count()}",
        f"Total Children Registered: {Child.query.count()}",
        f"Children Pending CWC: {Child.query.filter_by(status='registered').count()}",
        f"Children Available: {Child.query.filter_by(status='available').count()}",
        f"Children in Foster Care: {Child.query.filter_by(status='foster_care').count()}",
        f"Children in Court: {Child.query.filter_by(status='court_process').count()}",
        f"Children Adopted: {Child.query.filter_by(status='adopted').count()}",
        f"Total Parents Registered: {User.query.filter_by(role='parent').count()}",
        f"Total Applications: {Application.query.count()}",
        f"Pending Applications: {Application.query.filter_by(status='pending').count()}",
        f"Admin Approved: {Application.query.filter_by(status='admin_approved').count()}",
        f"In Court Process: {Application.query.filter_by(status='hearing_scheduled').count()}",
        f"Court Approved: {Application.query.filter_by(status='court_approved').count()}",
        f"Completed Adoptions: {Application.query.filter_by(status='completed').count()}",
        f"Rejected Applications: {Application.query.filter_by(status='rejected').count()}",
        f"Open Complaints: {Complaint.query.filter_by(status='open').count()}",
        f"Total Social Workers: {User.query.filter_by(role='socialworker').count()}",
        f"Follow Up Visits Done: {FollowUp.query.count()}",
    ]

    y = height - 170
    for stat in stats:
        c.drawString(70, y, f"• {stat}")
        y -= 22
        if y < 100:
            c.showPage()
            y = height - 50

    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y-10, "Recent Applications")
    c.setFont("Helvetica", 10)
    y -= 35

    apps = Application.query.order_by(
        Application.applied_at.desc()).limit(10).all()
    for app in apps:
        line = f"#{app.id} | {app.parent.name} → {app.child.name} | {app.status.upper()} | {app.applied_at.strftime('%d-%m-%Y')}"
        if y < 80:
            c.showPage()
            y = height - 50
        c.drawString(70, y, line)
        y -= 18

    c.save()
    buffer.seek(0)
    return Response(buffer,
        mimetype='application/pdf',
        headers={'Content-Disposition':
            'attachment;filename=adoption_report.pdf'})

# ─── JSON stats endpoint for admin dashboard auto-refresh ─────────────
from flask import jsonify

@admin.route('/admin/stats')
@login_required
@admin_required
def stats_api():
    """Returns key stats as JSON — polled every 60s by the dashboard."""
    return jsonify({
        'total_children':  Child.query.count(),
        'available':       Child.query.filter_by(status='available').count(),
        'pending_apps':    Application.query.filter_by(status='pending').count(),
        'consent_pending': Application.query.filter_by(
                               status='consent_assessment').count(),
        'foster_care':     Child.query.filter_by(status='foster_care').count(),
        'in_court':        Application.query.filter_by(
                               status='hearing_scheduled').count(),
        'adopted':         Child.query.filter_by(status='adopted').count(),
        'open_complaints': Complaint.query.filter_by(status='open').count(),
    })

# ─── All pending consent assessments (admin view) ────────────────────
@admin.route('/admin/consent-assessments')
@login_required
@admin_required
def consent_assessments():
    pending = Application.query.filter_by(
        status='consent_assessment').all()
    # outerjoin so this works even when child_consent table is empty
    completed = Application.query.outerjoin(ChildConsent).filter(
        ChildConsent.id.isnot(None)).all()
    return render_template('admin/consent_assessments.html',
        pending=pending,
        completed=completed)