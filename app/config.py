import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SECRET_KEY = "iamasecreaaakey"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    DEBUG = True

    def __init__(self):
        basedir = os.path.abspath(os.path.dirname(__file__))
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
