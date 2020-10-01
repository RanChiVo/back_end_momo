# flask imports 
from flask import Flask, request, jsonify, make_response 
from flask_sqlalchemy import SQLAlchemy 
import uuid # for public id 
from  werkzeug.security import generate_password_hash, check_password_hash 
# imports for PyJWT authentication 
import jwt 
from datetime import datetime, timedelta 
from functools import wraps 
app = Flask(__name__) 
# configuration 
# NEVER HARDCODE YOUR CONFIGURATION IN YOUR CODE 
# INSTEAD CREATE A .env FILE AND STORE IN IT 
app.config['SECRET_KEY'] = 'your secret key'
# database name 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True 
db = SQLAlchemy(app) 
# Database ORMs 
class User(db.Model): 
    id = db.Column(db.Integer, primary_key = True) 
    public_id = db.Column(db.String(50), unique = True) 
    name = db.Column(db.String(100)) 
    phone = db.Column(db.String(70), unique = True) 
    password = db.Column(db.String(80))

class ProfileUser(db.Model):
    id_profile = db.Column(db.Integer, primary_key = True)
    id_user = db.Column(db.String(50), unique = True)
    name = db.Column(db.String(100))
    level = db.Column(db.Integer(100))
    point = db.Column(db.Integer(100))
    current_turn = db.Column(db.Integer(100))

class GameHistory(db.Model):
    id_match = db.Column(db.Integer, primary_key = True)
    id_user = db.Column(db.String(50))
    id_opponent = db.Column(db.String(50))
    match_status = db.Column(db.Integer(100))
    date_time = db.Column(db.String(50))

db.create_all()