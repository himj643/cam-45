from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import requests
from requests.auth import HTTPBasicAuth
import random
import base64
import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
db = SQLAlchemy(app)

# M-Pesa API credentials
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_LIPA_NA_MPESA_SHORTCODE_PASSWORD = os.getenv('MPESA_LIPA_NA_MPESA_SHORTCODE_PASSWORD')
MPESA_LIPA_NA_MPESA_SHORTCODE_KEY = os.getenv('MPESA_LIPA_NA_MPESA_SHORTCODE_KEY')

# Create User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    referral_code = db.Column(db.String(100), unique=True, nullable=False)
    referral_count = db.Column(db.Integer, default=0)

# Home route
@app.route('/')
def home():
    return render_template("register.html")

# Register route
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    referral_code = str(random.randint(1000, 9999))
    new_user = User(username=username, password=password, referral_code=referral_code)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
    return render_template('login.html')

# User Dashboard route
@app.route('/dashboard', methods=['GET'])
def dashboard():
    user = User.query.get(session.get('user_id'))
    if user:
        return render_template('dashboard.html', user=user)
    return redirect(url_for('login'))

# M-Pesa Payment request function
def make_mpesa_payment(amount, phone_number):
    access_token = get_token()
    headers = {
        "Authorization": "Bearer " + access_token
    }

    payload = {
        "Shortcode": MPESA_SHORTCODE,
        "Amount": amount,
        "PhoneNumber": phone_number,
        "AccountReference": "MoneyStarPayment",
        "TransactionType": "PayBill",
        "TransactionID": "MONEY-" + str(random.randint(1000000, 9999999)),
        "Currency": "KES",
    }

    mpesa_api_url = "https://sandbox.safaricom.co.ke/mpesa/express/v1/submit"
    response = requests.post(mpesa_api_url, headers=headers, data=payload)
    return response.json()

# M-Pesa Token generation function
def get_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    api_key = os.getenv('API_KEY')
    api_secret = os.getenv('API_SECRET')
    auth = HTTPBasicAuth(api_key, api_secret)
    response = requests.get(api_url, auth=auth)
    return response.json()["access_token"]

# M-Pesa Payment route
@app.route('/make_mpesa_payment', methods=['POST'])
def process_mpesa_payment():
    phone_number = request.form['phone_number']
    amount = 100  # Fixed amount, can be dynamic
    make_mpesa_payment(amount, phone_number)
    return redirect(url_for('dashboard'))

# Main
if __name__ == "__main__":
    app.run(debug=True)