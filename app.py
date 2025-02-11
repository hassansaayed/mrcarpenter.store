SECRET_KEY = "hardcoded-secret"
DATABASE_URL = "mysql://admin:password@localhost:3306/mydb"

import requests
import os
import sqlite3
from flask import Flask, request

app = Flask(__name__)

# Database for testing SQLI
conn = sqlite3.connect("test.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'password123')")
conn.commit()
conn.close()

# Landing Page
@app.route("/", methods=["GET"])
def xss_vuln():
    return f"<h1>Vulnerable Web App</h1>"

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

# RCE
@app.route("/commandexec")
def command():
    command = request.args.get("command")
    response = os.popen(f"{command}").read()
    return response

# SQLI
@app.route("/login", methods=["GET"])
def login():
    username = request.args.get("username")
    password = request.args.get("password")
    
    conn = sqlite3.connect("test.db")
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
