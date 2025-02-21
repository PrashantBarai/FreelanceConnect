from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
import bcrypt
# from flask_cors import CORS

app = Flask(__name__)
# CORS(app)
app.secret_key = "your_secret_key_here"

# Configure Flask Session

# MongoDB Connection (Raw pymongo)
client = MongoClient("mongodb://localhost:27017/")
db = client["freelanceconnect"]
users_collection = db["users"]

@app.route("/")
def home():
    return render_template("landingpage.html")

# Route for Signup Page
@app.route("/auth/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        user_type = data.get("user_type")

        # Check if user exists
        if users_collection.find_one({"email": email}):
            return jsonify({"message": "User already exists"}), 400

        # Hash password
        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Insert user into MongoDB
        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": password,
            "hashed_password": hashed_pw,
            "user_type": user_type
        })

        return redirect(url_for("login"))

    return render_template("signup.html")

# Route for Login Page
@app.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.form
        username = data.get("username")
        password = data.get("password")

        user = users_collection.find_one({"username": username})

        if user and bcrypt.checkpw(password.encode("utf-8"), user["hashed_password"]):
            session["username"] = user["username"]
            session['user_type'] = user['user_type']
            session['email'] = user['email']
            return redirect(url_for("dashboard"))

        return jsonify({"message": "Invalid credentials"}), 401

    return render_template("login.html")

# Dashboard Route (Protected)
@app.route("/dashboard")
def dashboard():
    if "username" in session:
        return f"Welcome, {session['username']}! You are logged in as a {session['user_type']}."
    return redirect(url_for("login"))

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
