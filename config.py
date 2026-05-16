from urllib.parse import quote_plus

password = quote_plus('Tarun@123')

class Config:
    SECRET_KEY = 'dharwad_adoption_system_2026'
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:{password}@localhost/adoption'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024