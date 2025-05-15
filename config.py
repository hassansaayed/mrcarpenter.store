# config.py

import os

class Config:
    SECRET_KEY = 'changeme123'  # Replace with a secure key in production
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app.config['ENV'] = 'production'
app.config['DEBUG'] = False