import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
import bcrypt
from werkzeug.utils import secure_filename
import base64
from utils.utils import convert_lists_to_html

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

client = MongoClient("mongodb://localhost:27017/")
db = client["freelanceconnect"]
users_collection = db["users"]
posts_collection = db["posts"]
file_collection = db['files']


UPLOAD_FOLDER = "client_uploads"
ALLOWED_EXTENSIONS = {"pdf", "jpg", "png", "docx"}
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
        user_type = session.get("user_type", "").lower()
        if user_type == "client":
            posts = list(posts_collection.find({}))
            
            for post in posts:
                post["_id"] = str(post["_id"])
                post["Content"] = convert_lists_to_html(post["Content"])
            print(posts)  
            return render_template("client/client_dashboard.html", posts=posts)
        elif user_type == "freelancer":
            return render_template("freelancer_dashboard.html")
        return redirect(url_for("login"))
    return redirect(url_for("login"))



@app.route("/home/posts", methods=["GET", "POST"])
def posts():
    print("Request method:", request.method)

    if "userid" in session and session["user_type"].lower() == "client":
        if request.method == "POST":
            print("Form submitted!")

            title = request.form.get("title")
            content = request.form.get("description")
            documents = request.files.getlist("document")

            print("Title:", title)
            print("Content:", content)
            print("Documents:", [doc.filename for doc in documents] if documents else "No document")

            if not title or not content:
                print("Missing fields!")
                return "Missing title or content", 400

            post_data = {
                "Title": title,
                "Content": content,
                "Multimedia": [],
                "Comments": [],
                "UID": session["userid"],
                "user_type": session["user_type"]
            }

            inserted_post = posts_collection.insert_one(post_data)
            post_id = str(inserted_post.inserted_id)  # Get post ID

            # Define user-specific folder path
            user_folder = os.path.join(app.config["UPLOAD_FOLDER"], f"client_{session['userid']}")
            post_folder = os.path.join(user_folder, "posts", post_id, "multimedia")

            os.makedirs(post_folder, exist_ok=True)  # Ensure folder exists

            # Save uploaded documents
            for doc in documents:
                if doc and allowed_file(doc.filename):
                    filename = secure_filename(doc.filename)
                    file_path = os.path.join(post_folder, filename)
                    doc.save(file_path)
                    post_data["Multimedia"].append(file_path)  # Store file path

            posts_collection.update_one({"_id": inserted_post.inserted_id}, {"$set": post_data})

            print("Post stored in collection!")
            return redirect(url_for("home"))

        return render_template("client/client_dashboard.html")

    return redirect(url_for("login"))



@app.route("/home/myposts")
def my_posts():
    if "userid" not in session or session["user_type"].lower() != "client":
        return redirect(url_for("login"))
    client_id = session["userid"]
    posts = list(posts_collection.find({"UID": client_id}))

    return render_template("myposts.html", posts=posts)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landingpage"))

if __name__ == "__main__":
    app.run(debug=True)
