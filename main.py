import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
import bcrypt
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

client = MongoClient("mongodb://localhost:27017/")
db = client["freelanceconnect"]
users_collection = db["users"]
posts_collection = db["posts"]

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def landingpage():
    return render_template("landingpage.html")

@app.route("/auth/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.form
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        user_type = data.get("user_type")

        if users_collection.find_one({"email": email}):
            return jsonify({"message": "User already exists"}), 400

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        users_collection.insert_one({
            "username": username,
            "email": email,
            "hashed_password": hashed_pw,
            "user_type": user_type
        })
        return redirect(url_for("login"))
    return render_template("signup.html")


@app.route("/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.form
        username = data.get("username")
        password = data.get("password")

        user = users_collection.find_one({"username": username})

        if user and bcrypt.checkpw(password.encode("utf-8"), user["hashed_password"]):
            session["username"] = user["username"]
            session["user_type"] = user["user_type"]
            session["email"] = user["email"]
            session["userid"] = str(user["_id"])
            return redirect(url_for("home"))

        return jsonify({"message": "Invalid credentials"}), 401

    return render_template("login.html")

@app.route("/home", methods=["GET", "POST"])
def home():
    if "userid" in session:
        if session["user_type"].lower() == "client":
            return render_template("client_dashboard.html")
        elif session["user_type"].lower() == "freelancer":
            return render_template("freelancer_dashboard.html")
    return redirect(url_for("login"))



@app.route("/home/posts", methods=["GET", "POST"])
def posts():
    print("Request method:", request.method)  # Debugging
    if "userid" in session and session["userid"] == session["userid"] and session["user_type"].lower() == "client":
        if request.method == "POST":
            print("Form submitted!")  # Debugging
            title = request.form.get("title")
            description = request.form.get("description")
            document = request.files.get("document")

            print("Title:", title)  # Debugging
            print("Description:", description)  # Debugging
            print("Document:", document.filename if document else "No document")  # Debugging

            if not title or not description:
                print("Missing fields!")  # Debugging
                return "Missing title or description", 400

            post_data = {
                "client_id": session["userid"],
                "title": title,
                "description": description
            }
            if document:
                filename = document.filename
                document.save(f"uploads/{filename}") 
                post_data["document"] = filename

            posts_collection.insert_one(post_data)
            print("Post stored in collection!")  # Debugging
            return redirect(url_for("home"))

        return render_template("client_dashboard.html")  # Ensure this template exists
    return redirect(url_for("login"))


@app.route("/home/my_posts")
def my_posts():
    if "userid" not in session or session["user_type"].lower() != "client":
        return redirect(url_for("login"))
    client_id = session["userid"]
    posts = list(posts_collection.find({"client_id": client_id}))

    return render_template("home.html", posts=posts)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landingpage"))

if __name__ == "__main__":
    app.run(debug=True)
