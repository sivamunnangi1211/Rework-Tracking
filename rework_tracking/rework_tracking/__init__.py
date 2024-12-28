import os

from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    load_dotenv('local.env')
    app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost/rework_tracking"
    #app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://anilkusuma:anilkusuma@localhost/rework_tracking"
    app.config['SECRET_KEY'] = "controlytics"
    # Initialize plugins
    db.init_app(app)

    return app

