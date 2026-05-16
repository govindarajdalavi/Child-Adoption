from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from models import db, User, Child, Application, CWCOrder, HomeStudy, FollowUp, Complaint, Notification
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime
from functools import wraps

collector = Blueprint('collector', __name__)

def collector_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or \
                current_user.role != 'collector':
            flash('Access denied!', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@collector.route('/collector/dashboard')
@login_required
@collector_required
def dashboard():
    total_children = Child.query.count()
    available = Child.query.filter_by(status='available').count()
    adopted = Child.query.filter_by(status='adopted').count()
    total_applications = Application.query.count()
    court_approved = Application.query.filter_by(status='court_approved').count()
    total_orphanages = User.query.filter_by(role='orphanage').count()
    total_parents = User.query.filter_by(role='parent').count()
    total_socialworkers = User.query.filter_by(role='socialworker').count()
    open_complaints = Complaint.query.filter_by(status='open').count()
    urgent_complaints = Complaint.query.filter_by(status='open', is_urgent=True).count()
    pending_cwc = Child.query.filter_by(status='cwc_review').count()
    recent_apps = Application.query.order_by(Application.applied_at.desc()).limit(5).all()
    
    # Chart Data
    app_status_labels = ['Pending', 'Approved', 'Foster Care', 'Court', 'Adopted', 'Rejected']
    app_status_data = [
        Application.query.filter_by(status='pending').count(),
        Application.query.filter_by(status='admin_approved').count(),
        Application.query.filter_by(status='foster_care').count(),
        Application.query.filter_by(status='hearing_scheduled').count(),
        Application.query.filter_by(status='court_approved').count(),
        Application.query.filter_by(status='rejected').count(),
    ]

    children_labels = ['Registered', 'CWC Review', 'Available', 'Under Process', 'Foster Care', 'Adopted']
    children_data = [
        Child.query.filter_by(status='registered').count(),
        Child.query.filter_by(status='cwc_review').count(),
        Child.query.filter_by(status='available').count(),
        Child.query.filter_by(status='under_process').count(),
        Child.query.filter_by(status='foster_care').count(),
        Child.query.filter_by(status='adopted').count(),
    ]

    from sqlalchemy import extract
    from datetime import timedelta
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

    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    return render_template('collector/dashboard.html',
        total_children=total_children,
        available=available,
        adopted=adopted,
        total_applications=total_applications,
        court_approved=court_approved,
        total_orphanages=total_orphanages,
        total_parents=total_parents,
        total_socialworkers=total_socialworkers,
        open_complaints=open_complaints,
        urgent_complaints=urgent_complaints,
        pending_cwc=pending_cwc,
        recent_apps=recent_apps,
        notifications=notifications,
        app_status_labels=app_status_labels,
        app_status_data=app_status_data,
        children_labels=children_labels,
        children_data=children_data,
        monthly_labels=monthly_labels,
        monthly_data=monthly_data
    )

@collector.route('/collector/manage-users')
@login_required
@collector_required
def manage_users():
    orphanages = User.query.filter_by(role='orphanage').all()
    socialworkers = User.query.filter_by(role='socialworker').all()
    return render_template('collector/users.html',
        orphanages=orphanages,
        socialworkers=socialworkers)

@collector.route('/collector/verify-user/<int:uid>', methods=['POST'])
@login_required
@collector_required
def verify_user(uid):
    user = User.query.get_or_404(uid)
    user.is_verified = True
    db.session.commit()
    flash(f'{user.name} has been verified!', 'success')
    return redirect(url_for('collector.manage_users'))

@collector.route('/collector/complaints')
@login_required
@collector_required
def view_complaints():
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    return render_template('collector/complaints.html', complaints=complaints)

@collector.route('/collector/orphanages')
@login_required
@collector_required
def orphanages():
    return redirect(url_for('collector.manage_users'))

@collector.route('/collector/orphanage/verify/<int:oid>', methods=['POST'])
@login_required
@collector_required
def verify_orphanage(oid):
    user = User.query.get_or_404(oid)
    user.is_verified = True
    db.session.commit()
    flash(f'{user.name} verified!', 'success')
    return redirect(url_for('collector.manage_users'))

@collector.route('/collector/social-workers')
@login_required
@collector_required
def social_workers():
    return redirect(url_for('collector.manage_users'))

@collector.route('/collector/social-worker/verify/<int:wid>', methods=['POST'])
@login_required
@collector_required
def verify_worker(wid):
    user = User.query.get_or_404(wid)
    user.is_verified = True
    db.session.commit()
    flash(f'{user.name} verified!', 'success')
    return redirect(url_for('collector.manage_users'))

@collector.route('/collector/all-cases')
@login_required
@collector_required
def all_cases():
    applications = Application.query.order_by(Application.applied_at.desc()).all()
    return render_template('collector/all_cases.html', applications=applications)

@collector.route('/collector/report')
@login_required
@collector_required
def generate_report():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 50,
        "District Child Adoption Monitoring Report")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height - 70,
        "District Collectorate, Dharwad")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 95,
        f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
    c.drawString(50, height - 110,
        "Under: Juvenile Justice Act 2015 & CARA Guidelines 2022")
    c.line(50, height - 120, width - 50, height - 120)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, height - 145, "District Summary")
    c.setFont("Helvetica", 11)
    stats = [
        f"Total Orphanages Registered: {User.query.filter_by(role='orphanage').count()}",
        f"Total Children Registered: {Child.query.count()}",
        f"Children Pending CWC Review: {Child.query.filter_by(status='cwc_review').count()}",
        f"Children Legally Free: {Child.query.filter_by(status='legally_free').count()}",
        f"Children Available for Adoption: {Child.query.filter_by(status='available').count()}",
        f"Children in Foster Care: {Child.query.filter_by(status='foster_care').count()}",
        f"Children in Court Process: {Child.query.filter_by(status='court_process').count()}",
        f"Children Successfully Adopted: {Child.query.filter_by(status='adopted').count()}",
        f"Total Parents Registered: {User.query.filter_by(role='parent').count()}",
        f"Total Applications Filed: {Application.query.count()}",
        f"Applications Pending: {Application.query.filter_by(status='pending').count()}",
        f"Applications in Court: {Application.query.filter_by(status='hearing_scheduled').count()}",
        f"Court Approved Adoptions: {Application.query.filter_by(status='court_approved').count()}",
        f"Completed Adoptions: {Application.query.filter_by(status='completed').count()}",
        f"Open Complaints: {Complaint.query.filter_by(status='open').count()}",
    ]
    y = height - 170
    for stat in stats:
        c.drawString(70, y, f"• {stat}")
        y -= 20
    c.line(50, y - 5, width - 50, y - 5)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y - 25,
        "This report is generated as per JJ Act 2015 Section 56-60")
    c.drawString(50, y - 42,
        "and CARA Guidelines 2022 Regulation 12-13")
    c.save()
    buffer.seek(0)
    return Response(buffer, mimetype='application/pdf',
        headers={'Content-Disposition':
            'attachment;filename=district_adoption_report.pdf'})
