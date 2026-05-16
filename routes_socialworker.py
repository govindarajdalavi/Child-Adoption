from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, HomeStudy, FollowUp, Application, User, Notification, ChildConsent, AuditLog, WeeklyVisit
from datetime import datetime
from functools import wraps

socialworker = Blueprint('socialworker', __name__)

def sw_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or \
                current_user.role != 'socialworker':
            flash('Social Worker access required!', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def send_notification(user_id, title, message):
    db.session.add(Notification(
        user_id=user_id, title=title, message=message))

# ════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════
@socialworker.route('/socialworker/dashboard')
@login_required
@sw_required
def dashboard():
    pending_studies = HomeStudy.query.filter_by(
        social_worker_id=current_user.id,
        status='assigned').all()
    completed_studies = HomeStudy.query.filter_by(
        social_worker_id=current_user.id,
        status='completed').all()
    # Child Consent Assessments assigned to this worker
    consent_apps = Application.query.filter_by(
        status='consent_assessment',
        consent_assigned_to=current_user.id).all()
    # Post-adoption follow-ups
    pending_followups = Application.query.filter_by(
        status='court_approved').all()
    # Pre-adoption foster care weekly visits
    foster_care_apps = Application.query.filter_by(status='foster_care').all()

    notifications = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).all()
    
    return render_template(
        'socialworker/dashboard.html',
        pending_studies=pending_studies,
        completed_studies=completed_studies,
        consent_apps=consent_apps,
        foster_care_apps=foster_care_apps,
        pending_followups=pending_followups,
        notifications=notifications)

# ════════════════════════════════════════════════════
# HOME STUDY  —  CARA Regulation 8
# ════════════════════════════════════════════════════
@socialworker.route(
    '/socialworker/homestudy/<int:study_id>',
    methods=['GET', 'POST'])
@login_required
@sw_required
def submit_homestudy(study_id):
    study = HomeStudy.query.get_or_404(study_id)
    if request.method == 'POST':
        study.visit_date          = request.form.get('visit_date')
        study.house_condition     = request.form.get('house_condition')
        study.financial_stability = request.form.get('financial_stability')
        study.family_environment  = request.form.get('family_environment')
        study.neighborhood        = request.form.get('neighborhood')
        study.reason_for_adoption = request.form.get('reason_for_adoption')
        study.existing_children   = request.form.get('existing_children')
        study.recommendation      = request.form.get('recommendation')
        study.notes               = request.form.get('notes')
        study.status              = 'completed'
        db.session.commit()

        for adm in User.query.filter_by(role='admin').all():
            send_notification(
                adm.id,
                'Home Study Completed',
                f'Home study for {study.parent.name} completed. '
                f'Recommendation: {study.recommendation}')
        send_notification(
            study.parent_id,
            'Home Study Completed',
            f'Your home study is done. '
            f'Recommendation: {study.recommendation}. '
            f'Admin will review shortly.')
        db.session.commit()
        flash('Home study report submitted!', 'success')
        return redirect(url_for('socialworker.dashboard'))
    return render_template('socialworker/homestudy.html', study=study)

# ════════════════════════════════════════════════════
# CHILD CONSENT ASSESSMENT
# JJ Act 2015 Section 58(3)
# Mandatory for children aged >= 5 years
# ════════════════════════════════════════════════════
@socialworker.route(
    '/socialworker/consent/<int:app_id>',
    methods=['GET', 'POST'])
@login_required
@sw_required
def consent_assessment(app_id):
    application = Application.query.get_or_404(app_id)

    # Guard: only the assigned worker can assess
    if (application.consent_assigned_to and
            application.consent_assigned_to != current_user.id):
        flash('This consent assessment is assigned to another '
              'social worker.', 'warning')
        return redirect(url_for('socialworker.dashboard'))

    if request.method == 'POST':
        consent_status = request.form.get('consent_status')
        child_reaction = request.form.get('child_reaction')

        consent = ChildConsent(
            application_id=app_id,
            assessed_by=current_user.id,
            child_age_at_assessment=application.child.age,
            assessment_date=request.form.get(
                'assessment_date',
                datetime.utcnow().strftime('%Y-%m-%d')),
            child_met_parents=request.form.get('child_met_parents', 'yes'),
            child_reaction=child_reaction,
            verbal_response=request.form.get('verbal_response'),
            body_language=request.form.get('body_language'),
            consent_status=consent_status,
            notes=request.form.get('notes'))
        db.session.add(consent)

        # ── Business logic ────────────────────────────────────────
        if consent_status == 'willing':
            application.status = 'admin_approved'
            send_notification(
                application.parent_id,
                'Child Consent Obtained ✅',
                f'{application.child.name} has consented to the adoption. '
                f'Pre-adoption foster care will begin shortly.')
            for adm in User.query.filter_by(role='admin').all():
                send_notification(
                    adm.id,
                    'Child Consent ✅ — Ready for Foster Care',
                    f'{application.child.name} (App #{app_id}) consented. '
                    f'Please schedule pre-adoption foster care.')
            flash('Child consent obtained! Proceeding to foster care.', 'success')

        elif consent_status == 'needs_time':
            # Application stays in consent_assessment, re-visit needed
            send_notification(
                application.parent_id,
                'Child Needs More Time ⚠️',
                f'{application.child.name} needs more time to feel comfortable. '
                f'A follow-up visit will be scheduled.')
            for adm in User.query.filter_by(role='admin').all():
                send_notification(
                    adm.id,
                    '⚠️ Child Consent — Needs More Time',
                    f'{application.child.name} (App #{app_id}) needs more time. '
                    f'Re-assessment required.')
            flash('Recorded. Child needs more time — re-assessment will '
                  'be scheduled.', 'warning')

        else:  # refused
            # JJ Act §58(3): adoption CANNOT proceed if child refuses
            application.status = 'consent_refused'
            application.child.status = 'available'   # back to the pool

            send_notification(
                application.parent_id,
                '❌ Application Paused — Child Refused',
                f'{application.child.name} (age {application.child.age}) '
                f'has refused the adoption under JJ Act 2015 §58(3). '
                f'Your application has been paused. '
                f'You may apply for a different child.')

            for adm in User.query.filter_by(role='admin').all():
                send_notification(
                    adm.id,
                    f'❌ URGENT: Child Refused — App #{app_id}',
                    f'{application.child.name} refused adoption with '
                    f'{application.parent.name}. Application paused. '
                    f'Child returned to available pool.')

            for court in User.query.filter_by(role='court').all():
                send_notification(
                    court.id,
                    'Child Refused Adoption — Case Withdrawn',
                    f'App #{app_id} ({application.child.name}) paused: '
                    f'child refused under JJ Act §58(3). No court action needed.')

            flash('Application paused — child refused. All parties notified. '
                  'Child returned to available pool.', 'danger')

        # Audit trail
        db.session.add(AuditLog(
            user_id=current_user.id,
            action='consent_assessment',
            entity_type='application',
            entity_id=app_id,
            details=f'Status: {consent_status}, Reaction: {child_reaction}',
            ip_address=request.remote_addr))
        db.session.commit()
        return redirect(url_for('socialworker.dashboard'))

    return render_template('socialworker/consent.html',
        application=application)

# ════════════════════════════════════════════════════
# POST-ADOPTION FOLLOW UP  —  CARA Regulation 13
# 3 visits: 1 month / 6 months / 1 year
# ════════════════════════════════════════════════════
@socialworker.route(
    '/socialworker/followup/<int:app_id>',
    methods=['GET', 'POST'])
@login_required
@sw_required
def submit_followup(app_id):
    application = Application.query.get_or_404(app_id)
    visit_number = len(application.followups) + 1
    if request.method == 'POST':
        followup = FollowUp(
            application_id=app_id,
            social_worker_id=current_user.id,
            visit_number=visit_number,
            visit_date=request.form.get('visit_date'),
            child_health=request.form.get('child_health'),
            child_happy=request.form.get('child_happy'),
            school_going=request.form.get('school_going'),
            family_bonding=request.form.get('family_bonding'),
            complaints_found=request.form.get('complaints_found'),
            overall_status=request.form.get('overall_status'),
            action_needed=request.form.get('action_needed'))
        db.session.add(followup)

        status = request.form.get('overall_status')
        if status == 'critical':
            application.status = 'court_pending'
            application.child.status = 'court_process'
            for court in User.query.filter_by(role='court').all():
                send_notification(
                    court.id,
                    '🚨 URGENT: Critical Follow Up Report',
                    f'Critical issue at visit {visit_number} for '
                    f'{application.child.name}. Immediate court review!')
            for role in ('admin', 'collector'):
                for u in User.query.filter_by(role=role).all():
                    send_notification(
                        u.id,
                        '🚨 Critical Post-Adoption Issue',
                        f'Visit {visit_number} for {application.child.name} '
                        f'flagged CRITICAL. Court notified.')
            flash('Critical issue reported! Court and admin notified!', 'danger')

        elif visit_number >= 3 and status == 'good':
            application.status = 'completed'
            send_notification(
                application.parent_id,
                '🎉 Adoption Completed!',
                f'All 3 follow-up visits complete. Adoption of '
                f'{application.child.name} is FINAL and LEGAL! '
                f'(CARA Regulation 13)')
            flash('All 3 visits complete! Adoption is FINAL!', 'success')
        else:
            flash(f'Follow up visit {visit_number} submitted!', 'success')

        db.session.commit()
        return redirect(url_for('socialworker.dashboard'))
    return render_template('socialworker/followup.html',
        application=application,
        visit_number=visit_number)

# ════════════════════════════════════════════════════
# WEEKLY FOSTER CARE VISITS
# ════════════════════════════════════════════════════
@socialworker.route(
    '/socialworker/weekly_visit/<int:app_id>',
    methods=['GET', 'POST'])
@login_required
@sw_required
def weekly_visit(app_id):
    application = Application.query.get_or_404(app_id)
    if request.method == 'POST':
        visit = WeeklyVisit(
            application_id=app_id,
            social_worker_id=current_user.id,
            visit_date=request.form.get('visit_date'),
            child_condition=request.form.get('child_condition'),
            parent_behavior=request.form.get('parent_behavior'),
            child_happy=request.form.get('child_happy'),
            marks_or_injuries=request.form.get('marks_or_injuries'),
            details=request.form.get('details'),
            action_taken=request.form.get('action_taken')
        )
        
        emergency_removal = request.form.get('emergency_removal') == 'on'
        visit.emergency_removal = emergency_removal
        db.session.add(visit)
        
        if emergency_removal:
            application.status = 'rejected'
            application.child.status = 'available'
            # Notify everyone
            for court in User.query.filter_by(role='court').all():
                send_notification(court.id, '🚨 EMERGENCY REMOVAL', f'Child {application.child.name} removed from foster care due to emergency!')
            for admin in User.query.filter_by(role='admin').all():
                send_notification(admin.id, '🚨 EMERGENCY REMOVAL', f'Child {application.child.name} removed from foster care!')
            for collector in User.query.filter_by(role='collector').all():
                send_notification(collector.id, '🚨 EMERGENCY REMOVAL', f'Child {application.child.name} removed from foster care. Parent blacklisted.')
            
            # Send notification to parent
            send_notification(application.parent_id, '🚨 FOSTER CARE TERMINATED', 'Your foster care has been terminated due to emergency removal. You are permanently blacklisted.')
            flash('EMERGENCY REMOVAL EXECUTED. Authorities notified and child returned.', 'danger')
        else:
            flash('Weekly visit report submitted successfully.', 'success')
            
        db.session.commit()
        return redirect(url_for('socialworker.dashboard'))
        
    return render_template('socialworker/weekly_visit.html', application=application)