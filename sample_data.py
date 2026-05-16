"""
DDCAPMS — Demo Sample Data Script
Run once: python sample_data.py

Creates:
  - 2 Social Workers
  - 2 Orphanages
  - 5 Children (with CWC orders for available ones)
  - 3 Parents
  - 3 Applications (various stages including court_pending)
  - 3 Home Studies (completed)
"""

from app import create_app, bcrypt
from models import db, User, Child, Application, HomeStudy, CWCOrder

app = create_app()

with app.app_context():

    # ════════════════════════════════════════════════════
    # SOCIAL WORKERS
    # ════════════════════════════════════════════════════
    sw_data = [
        {'name': 'Rekha Joshi',  'email': 'rekha.sw@dharwad.gov.in',
         'password': 'sw123',    'phone': '9845011111',
         'address': 'Dharwad',   'organization_name': 'WCD Dept, Dharwad',
         'designation': 'Licensed Social Worker'},
        {'name': 'Suresh Patil', 'email': 'suresh.sw@dharwad.gov.in',
         'password': 'sw123',    'phone': '9845022222',
         'address': 'Hubballi',  'organization_name': 'WCD Dept, Dharwad',
         'designation': 'Senior Social Worker'},
        {'name': 'Priya Sharma', 'email': 'priya@socialworker.com',
         'password': 'worker123','phone': '9845098765',
         'address': 'Vidyanagar, Hubballi',
         'organization_name': 'WCD Department, Dharwad',
         'designation': 'Licensed Social Worker'},
    ]
    sw_objects = []
    for s in sw_data:
        existing = User.query.filter_by(email=s['email']).first()
        if not existing:
            hashed = bcrypt.generate_password_hash(
                s['password']).decode('utf-8')
            u = User(
                name=s['name'], email=s['email'],
                password=hashed, role='socialworker',
                phone=s['phone'], address=s['address'],
                organization_name=s['organization_name'],
                designation=s['designation'],
                is_verified=True)
            db.session.add(u)
            db.session.flush()
            sw_objects.append(u)
        else:
            sw_objects.append(existing)
    db.session.commit()
    print("Social Workers added!")

    # ════════════════════════════════════════════════════
    # ORPHANAGES
    # ════════════════════════════════════════════════════
    orph_data = [
        {'name': 'Sneha Bal Seva Kendra',
         'email': 'sneha@orphanage.com', 'password': 'orphan123',
         'phone': '9845012345', 'address': 'Vidyanagar, Hubballi',
         'organization_name': 'Sneha Bal Seva Kendra',
         'license_number': 'KAR-ORG-2018-001'},
        {'name': 'Shishu Mandir Trust',
         'email': 'shishu@orphanage.com', 'password': 'orphan123',
         'phone': '9844098765', 'address': 'Station Road, Dharwad',
         'organization_name': 'Shishu Mandir Trust',
         'license_number': 'KAR-ORG-2019-002'},
    ]
    orph_objects = []
    for o in orph_data:
        existing = User.query.filter_by(email=o['email']).first()
        if not existing:
            hashed = bcrypt.generate_password_hash(
                o['password']).decode('utf-8')
            u = User(
                name=o['name'], email=o['email'],
                password=hashed, role='orphanage',
                phone=o['phone'], address=o['address'],
                organization_name=o['organization_name'],
                license_number=o['license_number'],
                is_verified=True)
            db.session.add(u)
            db.session.flush()
            orph_objects.append(u)
        else:
            orph_objects.append(existing)
    db.session.commit()
    print("Orphanages added!")

    # ════════════════════════════════════════════════════
    # CHILDREN
    # ════════════════════════════════════════════════════
    children_data = [
        # age >= 5: consent assessment required when adopted
        {'name': 'Arjun Kumar', 'age': 5, 'gender': 'Male',
         'health_status': 'Healthy — all vaccinations complete',
         'background': 'Found near Hubballi railway station. Cheerful, loves cricket.',
         'how_child_came': 'abandoned', 'status': 'available',
         'orphanage_index': 0},
        {'name': 'Rahul Patil', 'age': 7, 'gender': 'Male',
         'health_status': 'Good — wears spectacles',
         'background': 'Lost parents in road accident. Studious, loves mathematics.',
         'how_child_came': 'orphaned', 'status': 'available',
         'orphanage_index': 1},
        {'name': 'Rohan Joshi', 'age': 6, 'gender': 'Male',
         'health_status': 'Good — fully vaccinated',
         'background': 'Father surrendered after mothers death. Loves football.',
         'how_child_came': 'surrendered', 'status': 'cwc_review',
         'orphanage_index': 0},
        # age < 5: consent not required
        {'name': 'Priya Devi', 'age': 3, 'gender': 'Female',
         'health_status': 'Healthy — mild iron deficiency treated',
         'background': 'Surrendered by mother due to extreme poverty. Loves singing.',
         'how_child_came': 'surrendered', 'status': 'available',
         'orphanage_index': 0},
        {'name': 'Anjali Nayak', 'age': 4, 'gender': 'Female',
         'health_status': 'Healthy — all checkups normal',
         'background': 'Surrendered at birth. Sweet and loves painting.',
         'how_child_came': 'surrendered', 'status': 'available',
         'orphanage_index': 1},
    ]
    child_objects = []
    cwc_officer = User.query.filter_by(role='cwc').first()

    for c in children_data:
        existing = Child.query.filter_by(name=c['name']).first()
        if not existing:
            child = Child(
                name=c['name'], age=c['age'], gender=c['gender'],
                health_status=c['health_status'],
                background=c['background'],
                how_child_came=c['how_child_came'],
                status=c['status'],
                orphanage_id=orph_objects[c['orphanage_index']].id)
            db.session.add(child)
            db.session.flush()
            # CWC order for available children
            if c['status'] == 'available' and cwc_officer:
                order = CWCOrder(
                    child_id=child.id,
                    cwc_officer_id=cwc_officer.id,
                    order_number=f'CWC/DHW/2026/00{child.id}',
                    investigation_notes=(
                        'Child background verified. '
                        'Medical examination completed. '
                        'Child declared legally free.'),
                    background_verified=True,
                    medical_examined=True,
                    status='legally_free',
                    order_date='2026-01-15')
                db.session.add(order)
            child_objects.append(child)
        else:
            child_objects.append(existing)
    db.session.commit()
    print("Children added!")

    # ════════════════════════════════════════════════════
    # PARENTS
    # ════════════════════════════════════════════════════
    parents_data = [
        {'name': 'Veena Desai',     'email': 'veena@gmail.com',
         'password': 'parent123',   'phone': '9880123456',
         'address': 'Vidyanagar, Hubballi - 580031'},
        {'name': 'Ramesh Kulkarni', 'email': 'ramesh@gmail.com',
         'password': 'parent123',   'phone': '9844567890',
         'address': 'Keshwapur, Hubballi - 580023'},
        {'name': 'Sunita Patil',    'email': 'sunita@gmail.com',
         'password': 'parent123',   'phone': '9886543210',
         'address': 'Station Road, Dharwad - 580001'},
    ]
    parent_objects = []
    for p in parents_data:
        existing = User.query.filter_by(email=p['email']).first()
        if not existing:
            hashed = bcrypt.generate_password_hash(
                p['password']).decode('utf-8')
            u = User(
                name=p['name'], email=p['email'],
                password=hashed, role='parent',
                phone=p['phone'], address=p['address'],
                is_verified=True)
            db.session.add(u)
            db.session.flush()
            parent_objects.append(u)
        else:
            parent_objects.append(existing)
    db.session.commit()
    print("Parents added!")

    # ════════════════════════════════════════════════════
    # HOME STUDIES (completed for all 3 parents)
    # ════════════════════════════════════════════════════
    for i, par in enumerate(parent_objects):
        existing = HomeStudy.query.filter_by(parent_id=par.id).first()
        if not existing:
            study = HomeStudy(
                parent_id=par.id,
                social_worker_id=sw_objects[i % len(sw_objects)].id,
                visit_date='2026-02-10',
                house_condition='good',
                financial_stability='good',
                family_environment='excellent',
                neighborhood='good',
                reason_for_adoption=(
                    'Genuine desire to provide loving home to a child.'),
                existing_children='No',
                recommendation='recommended',
                notes='Family is well settled and emotionally ready.',
                status='completed')
            db.session.add(study)
    db.session.commit()
    print("Home Studies added!")

    # ════════════════════════════════════════════════════
    # APPLICATIONS (demo scenarios for presentation)
    # ════════════════════════════════════════════════════
    apps_data = [
        # Veena → Arjun Kumar (age 5): court_pending stage (demo: full lifecycle)
        {'parent_index': 0, 'child_index': 0,
         'status': 'court_pending',
         'occupation': 'Teacher - KLE School Hubballi',
         'income': '8,50,000',
         'family_size': 2,
         'parent_age': 34, 'spouse_age': 36, 'age_gap': 29,
         'reason': ('Married 8 years, unable to have children. '
                    'We want to give a child a loving home.'),
         'admin_notes': 'Documents verified. Home study recommended. Sent to court.'},

        # Ramesh → Priya Devi (age 3): admin_approved (consent not needed, < 5)
        {'parent_index': 1, 'child_index': 3,
         'status': 'admin_approved',
         'occupation': 'Bank Manager - SBI Hubballi',
         'income': '6,00,000',
         'family_size': 3,
         'parent_age': 38, 'spouse_age': 35, 'age_gap': 35,
         'reason': ('We want to adopt and provide good education and '
                    'a loving home.'),
         'admin_notes': 'All documents verified. Approved.'},

        # Sunita → Rahul Patil (age 7): pending (demo: approve → triggers consent)
        {'parent_index': 2, 'child_index': 1,
         'status': 'pending',
         'occupation': 'Doctor - KIMS Hospital Hubballi',
         'income': '12,00,000',
         'family_size': 2,
         'parent_age': 40, 'spouse_age': 38, 'age_gap': 33,
         'reason': ('We have stable income and a big house. '
                    'Want to give a child a great life.'),
         'admin_notes': None},
    ]
    for a in apps_data:
        par = parent_objects[a['parent_index']]
        child = child_objects[a['child_index']]
        existing = Application.query.filter_by(
            parent_id=par.id, child_id=child.id).first()
        if not existing:
            application = Application(
                parent_id=par.id,
                child_id=child.id,
                status=a['status'],
                occupation=a['occupation'],
                income=a['income'],
                family_size=a['family_size'],
                parent_age=a.get('parent_age'),
                spouse_age=a.get('spouse_age'),
                age_gap=a.get('age_gap'),
                age_validated=True,
                reason=a['reason'],
                admin_notes=a['admin_notes'])
            db.session.add(application)
    db.session.commit()
    print("Applications added!")

    print()
    print("=" * 60)
    print("ALL SAMPLE DATA ADDED SUCCESSFULLY!")
    print("=" * 60)
    print("LOGIN CREDENTIALS:")
    print("-" * 60)
    print(f"{'Collector:':<15} collector@dharwad.gov.in  / collector123")
    print(f"{'Admin:':<15} admin@dharwad.gov.in       / admin123")
    print(f"{'CWC:':<15} cwc@dharwad.gov.in         / cwc123")
    print(f"{'Court:':<15} court@dharwad.gov.in       / court123")
    print(f"{'Social Worker:':<15} rekha.sw@dharwad.gov.in  / sw123")
    print(f"{'Orphanage:':<15} sneha@orphanage.com        / orphan123")
    print(f"{'Parent 1:':<15} veena@gmail.com            / parent123")
    print(f"{'Parent 2:':<15} ramesh@gmail.com           / parent123")
    print(f"{'Parent 3:':<15} sunita@gmail.com           / parent123")
    print("-" * 60)
    print()
    print("DEMO SCENARIO for PRESENTATION:")
    print("  1. Login as Admin > Approve Sunita Patil's application")
    print("     => Child (Rahul, age 7) triggers Consent Assessment!")
    print("  2. Login as Social Worker (rekha.sw@dharwad.gov.in)")
    print("     => See 'Child Consent Assessments' section")
    print("  3. Click 'Start Assessment' and fill the form")
    print("  4. Select 'Child appears willing' => moves to Foster Care")
    print("  5. OR select 'Child refused' => application paused!")
    print("-" * 60)