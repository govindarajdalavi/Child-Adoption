from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

def init_login_manager(login_manager):
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

# ════════════════════════════════
# USER MODEL
# ════════════════════════════════
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True,
        nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.Text)
    organization_name = db.Column(db.String(200))
    license_number = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    photo = db.Column(db.String(200),
        default='default_user.png')
    is_verified = db.Column(db.Boolean, default=False)
    license_document = db.Column(db.String(200))
    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)
    children = db.relationship('Child',
        backref='registered_by', lazy=True)
    applications = db.relationship('Application',
        foreign_keys='Application.parent_id',
        backref='parent', lazy=True)
    home_studies_assigned = db.relationship('HomeStudy',
        foreign_keys='HomeStudy.social_worker_id',
        backref='social_worker', lazy=True)
    cwc_orders = db.relationship('CWCOrder',
        backref='cwc_officer', lazy=True)
    followups = db.relationship('FollowUp',
        foreign_keys='FollowUp.social_worker_id',
        backref='social_worker', lazy=True)
    notifications = db.relationship('Notification',
        backref='user', lazy=True)

# ════════════════════════════════
# CHILD MODEL
# ════════════════════════════════
class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    date_of_birth = db.Column(db.String(20))
    health_status = db.Column(db.String(200))
    background = db.Column(db.Text)
    how_child_came = db.Column(db.String(50))
    photo = db.Column(db.String(200),
        default='default_child.png')
    status = db.Column(db.String(30),
        default='registered')
    orphanage_id = db.Column(db.Integer,
        db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)
    cwc_order = db.relationship('CWCOrder',
        backref='child', lazy=True)
    applications = db.relationship('Application',
        backref='child', lazy=True)
    documents = db.relationship('ChildDocument',
        backref='child', lazy=True)

# ════════════════════════════════
# CHILD DOCUMENT MODEL
# ════════════════════════════════
class ChildDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer,
        db.ForeignKey('child.id'), nullable=False)
    doc_type = db.Column(db.String(50))
    file_path = db.Column(db.String(200))
    uploaded_by = db.Column(db.Integer,
        db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)

# ════════════════════════════════
# CWC ORDER MODEL
# JJ Act 2015 Section 36
# ════════════════════════════════
class CWCOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer,
        db.ForeignKey('child.id'), nullable=False)
    cwc_officer_id = db.Column(db.Integer,
        db.ForeignKey('user.id'), nullable=False)
    order_number = db.Column(db.String(100))
    investigation_notes = db.Column(db.Text)
    background_verified = db.Column(db.Boolean,
        default=False)
    medical_examined = db.Column(db.Boolean,
        default=False)
    status = db.Column(db.String(20),
        default='pending')
    order_date = db.Column(db.String(20))
    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)

# ════════════════════════════════
# HOME STUDY MODEL
# CARA Regulation 8
# ════════════════════════════════
class HomeStudy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer,
        db.ForeignKey('user.id'), nullable=False)
    social_worker_id = db.Column(db.Integer,
        db.ForeignKey('user.id'), nullable=True)
    visit_date = db.Column(db.String(20))
    house_condition = db.Column(db.String(50))
    financial_stability = db.Column(db.String(50))
    family_environment = db.Column(db.String(50))
    neighborhood = db.Column(db.String(50))
    reason_for_adoption = db.Column(db.Text)
    existing_children = db.Column(db.String(10))
    recommendation = db.Column(db.String(20))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20),
        default='pending')
    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)
    parent = db.relationship('User',
        foreign_keys=[parent_id],
        backref='home_study', lazy=True)

# ════════════════════════════════
# APPLICATION MODEL
# ════════════════════════════════
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer,
        db.ForeignKey('user.id'), nullable=False)
    child_id = db.Column(db.Integer,
        db.ForeignKey('child.id'), nullable=False)
    status = db.Column(db.String(30),
        default='pending')
    reason = db.Column(db.Text)
    income = db.Column(db.String(50))
    occupation = db.Column(db.String(100))
    family_size = db.Column(db.Integer)
    admin_notes = db.Column(db.Text)

    # ── Age Validation (CARA Guidelines 2022) ──
    parent_age = db.Column(db.Integer)
    spouse_age = db.Column(db.Integer)
    combined_age = db.Column(db.Integer)
    age_gap = db.Column(db.Integer)
    age_validated = db.Column(db.Boolean, default=False)

    # ── Documents ──
    id_proof = db.Column(db.String(200))
    income_proof = db.Column(db.String(200))
    marriage_cert = db.Column(db.String(200))
    medical_cert = db.Column(db.String(200))
    police_verification = db.Column(db.String(200))

    # ── Court Temporary Order ──
    temp_order_number = db.Column(db.String(100))
    temp_order_date = db.Column(db.String(20))
    temp_order_judge = db.Column(db.String(100))
    temp_order_conditions = db.Column(db.Text)
    temp_order_scan = db.Column(db.String(200))
    temp_order_issued = db.Column(db.Boolean, default=False)

    # ── Foster Care (only after temp order) ──
    foster_care_start = db.Column(db.String(20))
    foster_care_end = db.Column(db.String(20))
    foster_care_report = db.Column(db.Text)
    foster_care_approved_by_court = db.Column(db.Boolean, default=False)
    foster_care_status = db.Column(db.String(20))

    # ── Final Hearing ──
    petition_filed_date = db.Column(db.String(20))
    notice_period_start = db.Column(db.String(20))
    notice_period_end = db.Column(db.String(20))
    final_hearing_date = db.Column(db.String(20))
    final_hearing_time = db.Column(db.String(20))
    final_hearing_venue = db.Column(db.String(200))
    final_hearing_room = db.Column(db.String(50))
    final_judge_name = db.Column(db.String(100))
    hearing_result = db.Column(db.String(20))

    # ── Final Court Order ──
    final_order_number = db.Column(db.String(100))
    final_order_date = db.Column(db.String(20))
    final_order_scan = db.Column(db.String(200))

    applied_at = db.Column(db.DateTime,
        default=datetime.utcnow)
    updated_at = db.Column(db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow)

    # ── Consent Assessment (JJ Act 2015 §58(3)) ──
    # Only required when child.age >= 5
    consent_assigned_to = db.Column(db.Integer,
        db.ForeignKey('user.id'))

    followups = db.relationship('FollowUp',
        backref='application', lazy=True)
    complaints = db.relationship('Complaint',
        backref='application', lazy=True)
    child_consent = db.relationship('ChildConsent',
        backref='application', uselist=False,
        cascade='all, delete-orphan')

# ════════════════════════════════
# FOLLOW UP MODEL
# CARA Regulation 13
# ════════════════════════════════
class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer,
        db.ForeignKey('application.id'),
        nullable=False)
    social_worker_id = db.Column(db.Integer,
        db.ForeignKey('user.id'), nullable=True)
    visit_number = db.Column(db.Integer)
    visit_date = db.Column(db.String(20))
    child_health = db.Column(db.String(100))
    child_happy = db.Column(db.String(20))
    school_going = db.Column(db.String(20))
    family_bonding = db.Column(db.String(50))
    complaints_found = db.Column(db.Text)
    overall_status = db.Column(db.String(20))
    action_needed = db.Column(db.Text)
    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)

# ════════════════════════════════
# WEEKLY VISIT MODEL (Foster Care)
# ════════════════════════════════
class WeeklyVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'))
    social_worker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    visit_date = db.Column(db.String(20))
    child_condition = db.Column(db.String(50))
    parent_behavior = db.Column(db.String(50))
    child_happy = db.Column(db.String(10))
    marks_or_injuries = db.Column(db.String(10))
    details = db.Column(db.Text)
    action_taken = db.Column(db.Text)
    emergency_removal = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    application = db.relationship('Application', backref=db.backref('weekly_visits', lazy=True))
    social_worker = db.relationship('User', backref=db.backref('weekly_visits_done', lazy=True))

# ════════════════════════════════
# COMPLAINT MODEL
# ════════════════════════════════
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer,
        db.ForeignKey('application.id'),
        nullable=False)
    filed_by = db.Column(db.String(100))
    filed_by_role = db.Column(db.String(50))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')
    admin_action = db.Column(db.Text)
    is_urgent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)

# ════════════════════════════════
# CHILD CONSENT MODEL
# JJ Act 2015 Section 58(3)
# Mandatory for children >= 5 yrs
# ════════════════════════════════
class ChildConsent(db.Model):
    __tablename__ = 'child_consent'
    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(db.Integer,
        db.ForeignKey('application.id',
            ondelete='CASCADE'),
        nullable=False, unique=True)

    # Social worker who performed the assessment
    assessed_by = db.Column(db.Integer,
        db.ForeignKey('user.id',
            ondelete='SET NULL'))

    # Age of child at time of assessment
    child_age_at_assessment = db.Column(db.Integer)

    # Assessment date (ISO string YYYY-MM-DD)
    assessment_date = db.Column(db.String(20),
        nullable=False)

    # Q1: Did child meet the parents?  'yes' / 'no'
    child_met_parents = db.Column(db.String(10),
        nullable=False)

    # Q2: Child reaction
    # 'happy' | 'neutral' | 'uncomfortable' | 'refused'
    child_reaction = db.Column(db.String(50),
        nullable=False)

    # Q3: Verbal response (children > 5 yrs)
    verbal_response = db.Column(db.Text)

    # Q4: Body language observations
    body_language = db.Column(db.Text)

    # Q5: Social worker recommendation
    # 'willing' | 'needs_time' | 'refused'
    consent_status = db.Column(db.String(20),
        nullable=False)

    # Additional notes
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)

    # Relationship to assessor
    assessor = db.relationship('User',
        foreign_keys=[assessed_by])

    @property
    def is_refused(self):
        return (self.consent_status == 'refused' or
                self.child_reaction == 'refused')

    @property
    def recommendation_label(self):
        return {
            'willing': 'Child appears willing ✅',
            'needs_time': 'Child needs more time ⚠️',
            'refused': 'Child refused ❌'
        }.get(self.consent_status, self.consent_status)

    @property
    def reaction_label(self):
        return {
            'happy': 'Happy and comfortable 😊',
            'neutral': 'Neutral 😐',
            'uncomfortable': 'Uncomfortable 😟',
            'refused': 'Refused / Scared 😨'
        }.get(self.child_reaction, self.child_reaction)

# ════════════════════════════════
# NOTIFICATION MODEL
# ════════════════════════════════
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
        db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)

# ════════════════════════════════
# AUDIT LOG MODEL
# Every action recorded for full
# transparency (anti-corruption)
# ════════════════════════════════
class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
        db.ForeignKey('user.id', ondelete='SET NULL'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))  # 'application','child',etc
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime,
        default=datetime.utcnow)