from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config
from models import db, init_login_manager, ChildConsent, AuditLog  # noqa: F401 — needed for db.create_all()
import os

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    init_login_manager(login_manager)

    from routes_auth import auth
    from routes_collector import collector
    from routes_admin import admin
    from routes_cwc import cwc
    from routes_orphanage import orphanage
    from routes_socialworker import socialworker
    from routes_court import court
    from routes_parent import parent

    app.register_blueprint(auth)
    app.register_blueprint(collector)
    app.register_blueprint(admin)
    app.register_blueprint(cwc)
    app.register_blueprint(orphanage)
    app.register_blueprint(socialworker)
    app.register_blueprint(court)
    app.register_blueprint(parent)

    with app.app_context():
        db.create_all()
        create_default_users()

    return app

def create_default_users():
    from models import User
    users = [
        {
            'name': 'District Collector',
            'email': 'collector@dharwad.gov.in',
            'password': 'collector123',
            'role': 'collector',
            'organization_name':
                'District Collectorate, Dharwad',
            'designation':
                'District Collector, Dharwad'
        },
        {
            'name': 'WCD Admin',
            'email': 'admin@dharwad.gov.in',
            'password': 'admin123',
            'role': 'admin',
            'organization_name':
                'Women & Child Development, Dharwad',
            'designation':
                'District Program Officer'
        },
        {
            'name': 'CWC Officer',
            'email': 'cwc@dharwad.gov.in',
            'password': 'cwc123',
            'role': 'cwc',
            'organization_name':
                'Child Welfare Committee, Dharwad',
            'designation':
                'CWC Chairperson'
        },
        {
            'name': 'Court Clerk',
            'email': 'court@dharwad.gov.in',
            'password': 'court123',
            'role': 'court',
            'organization_name':
                'District Family Court, Hubballi-Dharwad',
            'designation':
                'Senior Court Clerk'
        },
    ]
    for u in users:
        if not User.query.filter_by(
                email=u['email']).first():
            hashed = bcrypt.generate_password_hash(
                u['password']).decode('utf-8')
            user = User(
                name=u['name'],
                email=u['email'],
                password=hashed,
                role=u['role'],
                organization_name=u.get(
                    'organization_name'),
                designation=u.get('designation'),
                is_verified=True
            )  # type: ignore[call-arg]
            db.session.add(user)
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)