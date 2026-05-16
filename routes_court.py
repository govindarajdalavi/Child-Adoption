from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from models import db, Application, FollowUp, Notification, User
from functools import wraps
import os
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from datetime import datetime

court = Blueprint('court', __name__)

ALLOWED = {'pdf', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED

def court_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or \
                current_user.role != 'court':
            flash('Court access required!', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def send_notification(user_id, title, message):
    n = Notification(user_id=user_id, title=title, message=message)
    db.session.add(n)

@court.route('/court/dashboard')
@login_required
@court_required
def dashboard():
    pending = Application.query.filter_by(status='sent_to_court').all()
    notice_period = Application.query.filter_by(status='notice_period').all()
    scheduled = Application.query.filter_by(status='final_hearing_scheduled').all()
    approved = Application.query.filter_by(status='court_approved').all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    
    return render_template('court/dashboard.html',
        pending=pending, notice_period=notice_period,
        scheduled=scheduled, approved=approved,
        notifications=notifications)

@court.route('/court/file-petition/<int:app_id>', methods=['POST'])
@login_required
@court_required
def file_petition(app_id):
    application = Application.query.get_or_404(app_id)
    petition_date = request.form.get('petition_date')
    
    if petition_date:
        application.petition_filed_date = petition_date
        application.notice_period_start = petition_date
        application.status = 'notice_period'
        
        send_notification(application.parent_id,
            '⚖️ Petition Filed in Court',
            f'Legal adoption petition for {application.child.name} has been filed. The 30-day public notice period has started.')
            
        db.session.commit()
        flash('Petition filed! 30-day notice period started.', 'success')
    
    return redirect(url_for('court.dashboard'))

@court.route('/court/issue-temp-order/<int:app_id>', methods=['GET', 'POST'])
@login_required
@court_required
def issue_temp_order(app_id):
    application = Application.query.get_or_404(app_id)
    if request.method == 'POST':
        application.status = 'court_temp_order_issued'
        application.temp_order_number = request.form.get('temp_order_number')
        application.temp_order_date = request.form.get('temp_order_date')
        application.temp_order_judge = request.form.get('temp_order_judge')
        application.temp_order_conditions = request.form.get('temp_order_conditions')
        application.temp_order_issued = True
        
        scanned_file = request.files.get('temp_order_scan')
        if scanned_file and allowed_file(scanned_file.filename):
            filename = secure_filename(scanned_file.filename)
            scanned_file.save(os.path.join('static/uploads', filename))
            application.temp_order_scan = filename
            
        send_notification(application.parent_id,
            '⚖️ Temporary Foster Care Order Issued',
            f'Court has issued permission for foster care. Order: {application.temp_order_number}')
        db.session.commit()
        flash('Temporary order issued! Admin can now start foster care.', 'success')
        return redirect(url_for('court.dashboard'))
    return render_template('court/temp_order.html', application=application)

@court.route('/court/schedule-final/<int:app_id>', methods=['GET', 'POST'])
@login_required
@court_required
def schedule_final_hearing(app_id):
    application = Application.query.get_or_404(app_id)
    if request.method == 'POST':
        application.status = 'final_hearing_scheduled'
        application.final_hearing_date = request.form.get('hearing_date')
        application.final_hearing_time = request.form.get('hearing_time')
        application.final_hearing_venue = request.form.get('hearing_venue')
        application.final_hearing_room = request.form.get('hearing_room')
        application.final_judge_name = request.form.get('judge_name')
        send_notification(application.parent_id,
            '⚖️ Final Court Hearing Scheduled!',
            f'''Your final court hearing for {application.child.name} is scheduled.

DATE: {application.final_hearing_date}
TIME: {application.final_hearing_time}
VENUE: {application.final_hearing_venue}
ROOM: {application.final_hearing_room}
JUDGE: {application.final_judge_name}

All parties must appear physically.''')
        db.session.commit()
        flash('Final hearing scheduled!', 'success')
        return redirect(url_for('court.dashboard'))
    return render_template('court/schedule.html', application=application)

@court.route('/court/issue-final-order/<int:app_id>', methods=['GET', 'POST'])
@login_required
@court_required
def issue_final_order(app_id):
    application = Application.query.get_or_404(app_id)
    if request.method == 'POST':
        result = request.form.get('result')
        application.hearing_result = result
        application.final_order_number = request.form.get('order_number')
        application.final_order_date = request.form.get('order_date')
        scanned_file = request.files.get('scanned_order')
        if scanned_file and allowed_file(scanned_file.filename):
            filename = secure_filename(scanned_file.filename)
            scanned_file.save(os.path.join('static/uploads', filename))
            application.final_order_scan = filename
            
        if result == 'approved':
            application.status = 'court_approved'
            application.child.status = 'adopted'
            send_notification(application.parent_id,
                '🎉 Final Adoption Order Issued!',
                f'''Congratulations! The court has issued the final adoption order for {application.child.name}.

Court Order: {application.final_order_number}
Order Date: {application.final_order_date}

NEXT STEPS:
1. Collect physical certificate from court office
2. Update child birth certificate at Civil Registration Office
3. Social worker will visit 3 times over 1 year''')
            flash('Final order issued! Adoption successful!', 'success')
        else:
            application.status = 'rejected'
            application.child.status = 'available'
            send_notification(application.parent_id,
                '❌ Court Rejected Adoption',
                f'The court has rejected final adoption of {application.child.name}. Please contact court for details.')
            flash('Adoption rejected by court.', 'danger')
        db.session.commit()
        return redirect(url_for('court.dashboard'))
    return render_template('court/final_order.html', application=application)

@court.route('/court/assign_followup/<int:app_id>', methods=['GET', 'POST'])
@login_required
@court_required
def assign_followup(app_id):
    application = Application.query.get_or_404(app_id)
    socialworkers = User.query.filter_by(role='socialworker', is_verified=True).all()
    if request.method == 'POST':
        sw_id = int(request.form.get('social_worker_id'))
        visit_number = len(application.followups) + 1
        followup = FollowUp(
            application_id=app_id,
            social_worker_id=sw_id,
            visit_number=visit_number)
        db.session.add(followup)
        send_notification(sw_id,
            f'Follow Up Visit {visit_number} Assigned',
            f'Please conduct follow up visit {visit_number} of 3 for {application.child.name} adopted by {application.parent.name}.')
        db.session.commit()
        flash(f'Social worker assigned for visit {visit_number}!', 'success')
        return redirect(url_for('court.dashboard'))
    return render_template('court/assign_followup.html',
        application=application, socialworkers=socialworkers)

@court.route('/court/download-temp-order/<int:app_id>')
@login_required
def download_temp_order(app_id):
    application = Application.query.get_or_404(app_id)
    if not application.temp_order_issued:
        flash('Temporary order not issued yet.', 'danger')
        return redirect(url_for('parent.track'))
        
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Official Header
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 60, "DISTRICT FAMILY COURT, DHARWAD")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height - 80, "GOVERNMENT OF KARNATAKA")
    c.line(50, height - 90, width - 50, height - 90)
    
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, height - 120, "TEMPORARY FOSTER CARE ORDER")
    c.setFont("Helvetica", 11)
    c.drawCentredString(width/2, height - 135, "(Under Section 58 of Juvenile Justice Act 2015)")
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 170, f"Order Number: {application.temp_order_number}")
    c.drawString(width - 250, height - 170, f"Date of Issue: {application.temp_order_date}")
    
    c.setFont("Helvetica", 11)
    text = c.beginText(50, height - 210)
    text.setLineHeight(18)
    text.textLine(f"This order grants temporary foster care custody of the child named '{application.child.name}'")
    text.textLine(f"(Age: {application.child.age}, Gender: {application.child.gender}) to the prospective adoptive parent(s):")
    text.textLine("")
    text.textLine(f"Parent Name: {application.parent.name}")
    text.textLine(f"Address: {application.parent.address}")
    text.textLine("")
    text.textLine("This placement is subject to the following conditions:")
    text.textLine(f"- {application.temp_order_conditions or 'Standard CARA pre-adoption foster care regulations apply.'}")
    text.textLine("- Mandatory weekly visits by the assigned social worker.")
    text.textLine("- The child cannot be removed from the court's jurisdiction without prior permission.")
    text.textLine("")
    text.textLine("This is a temporary order preceding the final adoption decree.")
    c.drawText(text)
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(width - 250, height - 400, f"Hon'ble Judge: {application.temp_order_judge}")
    c.drawString(width - 250, height - 420, "District Family Court, Dharwad")
    
    # Official Seal
    c.circle(width - 150, height - 350, 30, stroke=1, fill=0)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width - 150, height - 350, "SEAL")
    
    c.save()
    buffer.seek(0)
    return Response(buffer, mimetype='application/pdf', headers={'Content-Disposition': f'attachment;filename=Temp_Order_{application.temp_order_number}.pdf'})

@court.route('/court/download-final-order/<int:app_id>')
@login_required
def download_final_order(app_id):
    application = Application.query.get_or_404(app_id)
    if application.status != 'court_approved':
        flash('Final adoption order not issued yet.', 'danger')
        return redirect(url_for('parent.track'))
        
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Official Header
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 60, "DISTRICT FAMILY COURT, DHARWAD")
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width/2, height - 80, "GOVERNMENT OF KARNATAKA")
    c.line(50, height - 90, width - 50, height - 90)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 120, "FINAL ADOPTION DECREE")
    c.setFont("Helvetica", 11)
    c.drawCentredString(width/2, height - 135, "(Under Section 59 of Juvenile Justice Act 2015)")
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 170, f"Decree Number: {application.final_order_number}")
    c.drawString(width - 250, height - 170, f"Date of Decree: {application.final_order_date}")
    
    c.setFont("Helvetica", 11)
    text = c.beginText(50, height - 220)
    text.setLineHeight(20)
    text.textLine("UPON UPON THE PETITION filed before this honorable court, and after reviewing")
    text.textLine("the Child Welfare Committee clearances, Home Study reports, and the performance")
    text.textLine("during the pre-adoption foster care period, IT IS HEREBY ORDERED AND DECREED:")
    text.textLine("")
    text.textLine(f"1. The child previously known as '{application.child.name}' (Age: {application.child.age},")
    text.textLine(f"   Gender: {application.child.gender}) is legally adopted by {application.parent.name}.")
    text.textLine("")
    text.textLine("2. From this day forward, the child shall have all the legal rights, privileges,")
    text.textLine("   and obligations of a biological child born to the adoptive parent(s).")
    text.textLine("")
    text.textLine(f"3. The parent(s) residing at {application.parent.address} shall assume")
    text.textLine("   full legal custody, care, and financial responsibility of the child.")
    text.textLine("")
    text.textLine("4. Post-adoption monitoring shall be conducted for a period of two years as per")
    text.textLine("   CARA Regulations 2022.")
    c.drawText(text)
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(width - 250, height - 500, f"Hon'ble Judge: {application.final_judge_name or 'Presiding Judge'}")
    c.drawString(width - 250, height - 520, "District Family Court, Dharwad")
    
    # Official Seal
    c.circle(width - 150, height - 430, 40, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(width - 150, height - 430, "OFFICIAL")
    c.drawCentredString(width - 150, height - 440, "COURT SEAL")
    
    c.save()
    buffer.seek(0)
    return Response(buffer, mimetype='application/pdf', headers={'Content-Disposition': f'attachment;filename=Final_Adoption_Order_{application.final_order_number}.pdf'})