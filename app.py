import requests
import os
import psycopg2
from flask import Flask, request

app = Flask(__name__)

# Load secret key & database URL from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "hardcoded-secret")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@localhost:5432/mydb")

# Connect to PostgreSQL (Render)
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# Landing Page
@app.route("/", methods=["GET"])
def index():
    return "<h1>Vulnerable Web App</h1>"

# XSS
@app.route("/xss", methods=["GET", "POST"])
def xss_vuln():
    user_input = request.args.get("input", "")
    return f"<h1>User Input: {user_input}</h1>"

# SSRF
@app.route("/fetch-url")
def fetch_url():
    url = request.args.get("url")
    response = requests.get(url)
    return response.text

# IDOR
@app.route("/profile/<user_id>")
def profile(user_id):
    return f"<h1>Welcome, User {user_id}!</h1>"

# SQLI
@app.route("/login", methods=["GET"])
def login():
    username = request.args.get("username")
    password = request.args.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()

    if user:
        return "Login Successful!"
    else:
        return "Invalid Credentials"

if __name__ == "__main__":
    app.run(debug=True)
