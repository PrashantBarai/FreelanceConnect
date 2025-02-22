import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
import bcrypt
from werkzeug.utils import secure_filename
import base64
from utils.utils import convert_lists_to_html, save_profile_picture

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

client = MongoClient("mongodb://localhost:27017/")
db = client["freelanceconnect"]
users_collection = db["users"]
posts_collection = db["posts"]
file_collection = db['files']
profile_collection = db['profile']
reviews_collection = db['reviews']

UPLOAD_FOLDER = "client_uploads"
ALLOWED_EXTENSIONS = {"pdf", "jpg", "png", "docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["FREE_UPLOAD_FOLDER"] = "freelance_uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def landingpage():
    return render_template("landingpage.html")
from flask import send_from_directory

@app.route("/client_uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory("client_uploads", filename)

# @app.route("/home/profile/<uid>")
# def access_profile(uid):
#     return redirect(url_for("client_profile", userid=uid))


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
            "user_type": user_type,
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
        search_query = request.args.get("search", "").strip().lower()
        min_budget = request.args.get("min_budget", "")
        max_budget = request.args.get("max_budget", "")
        location_filter = request.args.get("location", "").strip().lower()

        filter_criteria = {}

        if search_query:
            filter_criteria["Title"] = {"$regex": search_query, "$options": "i"}  # Case-insensitive search
        
        if location_filter:
            filter_criteria["Location"] = {"$regex": location_filter, "$options": "i"}
        
        if min_budget.isdigit():
            filter_criteria["Budget"] = {"$gte": int(min_budget)}

        if max_budget.isdigit():
            if "Budget" in filter_criteria:
                filter_criteria["Budget"]["$lte"] = int(max_budget)
            else:
                filter_criteria["Budget"] = {"$lte": int(max_budget)}

        posts = list(posts_collection.find(filter_criteria))

        for post in posts:
            post["_id"] = str(post["_id"])
            post["Content"] = convert_lists_to_html(post["Content"])

        if user_type == "client":
            return render_template("client/client_dashboard.html", posts=posts)
        elif user_type == "freelancer":
            return render_template("freelancer/freelancer_dashboard.html", posts=posts)
        
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
            location = request.form.get("location")
            budget = request.form.get("budget")
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
                "Location":location,
                "Budget": budget,
                "Multimedia": [],
                "Comments": [],
                "UID": session["userid"],
                "user_type": session["user_type"]
            }
            inserted_post = posts_collection.insert_one(post_data)
            post_id = str(inserted_post.inserted_id)  
            user_folder = os.path.join(app.config["UPLOAD_FOLDER"], f"client_{session['userid']}")
            post_folder = os.path.join(user_folder, "posts", post_id, "multimedia")
            os.makedirs(post_folder, exist_ok=True)  
            for doc in documents:
                if doc and allowed_file(doc.filename):
                    filename = secure_filename(doc.filename)
                    file_path = os.path.join(post_folder, filename)
                    doc.save(file_path)
                    post_data["Multimedia"].append(file_path)  
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
    return render_template("client/myposts.html", posts=posts)




@app.route("/home/profile/client/<userid>", methods=["GET", "POST"])
def client_profile(userid):
    if "userid" not in session:
        return redirect(url_for("login"))
    
    if session['userid'] != userid:
        return redirect(url_for("client_profile", userid=session['userid'])) 

    client_data = profile_collection.find_one({"uid": userid})
    print(userid)
    
    if request.method == "POST":
        profile_pic = request.files.get("profile_pic")
        name = request.form.get("name")
        work_experience = request.form.get("work_experience")
        education = request.form.get("education")
        bio = request.form.get("bio")

        update_data = {
            "uid": userid,  # Ensure correct document key
            "name": name,
            "work_experience": work_experience,
            "education": education,
            "bio": bio
        }

        if profile_pic:
            profile_pic_path = save_profile_picture(profile_pic, userid)
            if profile_pic_path:
                update_data["profile_pic"] = profile_pic_path  # Store the path


        if client_data:
            profile_collection.update_one({"uid": userid}, {"$set": update_data})
        else:
            profile_collection.insert_one(update_data)
            curruser = users_collection.find_one({"uid": userid})
            curruser["profile_url"] = "localhost:5000/home/profile/client/" + userid

        return redirect(url_for("client_profile", userid=userid))

    client_data = profile_collection.find_one({"uid": userid})
    return render_template("client/profile.html", client=client_data, userid=userid)


@app.route("/home/profile/freelance/<userid>/add_review", methods=["POST"])
def add_review(userid):
    if "userid" not in session:
        return redirect(url_for("login"))

    rating = request.form.get("rating")
    review_text = request.form.get("review")

    if rating and review_text:
        review_data = {
            "uid": userid,
            "rating": rating,
            "review": review_text,
        }
        reviews_collection.insert_one(review_data)

    return redirect(url_for("freelancer_profile", userid=userid))

import os
import glob

@app.route("/home/profile/freelance/<userid>", methods=["GET", "POST"])
def freelancer_profile(userid):
    if "userid" not in session:
        return redirect(url_for("login"))
    
    if session['userid'] != userid:
        return redirect(url_for("freelancer_profile", userid=session['userid']))  
    
    client_data = profile_collection.find_one({"uid": userid})
    print(userid)

    if request.method == "POST":
        profile_pic = request.files.get("profile_pic")
        resume = request.files.get("resume")  # Get resume file
        name = request.form.get("name")
        work_experience = request.form.get("work_experience")
        education = request.form.get("education")
        bio = request.form.get("bio")
        hobbies = request.form.get("hobbies")

        update_data = {
            "uid": userid,
            "name": name,
            "work_experience": work_experience,
            "education": education,
            "bio": bio,
            "hobbies": hobbies
        }

        if profile_pic:
            profile_pic_path = save_profile_picture(profile_pic, userid)
            if profile_pic_path:
                update_data["profile_pic"] = profile_pic_path

        # Handle Resume File
        upload_dir = f"freelance_uploads/{userid}"
        os.makedirs(upload_dir, exist_ok=True)

        files = glob.glob(os.path.join(upload_dir, '*'))
        for file in files:
            if os.path.isfile(file):
                os.remove(file)

        if resume:
            resume_path = os.path.join(upload_dir, resume.filename)
            resume.save(resume_path)
            update_data["resume"] = resume_path

        print(f"Profile picture path: {profile_pic_path if profile_pic else 'No change'}")
        print(f"Resume saved at: {resume_path if resume else 'No change'}")

        # Update or insert profile data
        if client_data:
            profile_collection.update_one({"uid": userid}, {"$set": update_data})
        else:
            profile_collection.insert_one(update_data)
            curruser = users_collection.find_one({"uid": userid})
            if curruser:
                users_collection.update_one(
                    {"uid": userid},
                    {"$set": {"profile_url": f"localhost:5000/home/profile/freelance/{userid}"}}
                )

        return redirect(url_for("freelancer_profile", userid=userid))  

    client_data = profile_collection.find_one({"uid": userid})
    return render_template("freelancer/profile.html", client=client_data, userid=userid)




FREE_UPLOAD_FOLDER = "freelance_uploads"
from flask import Flask, request, redirect, url_for, render_template, jsonify
from werkzeug.utils import secure_filename
import os
from bson import json_util

@app.route("/home/freelanceposts", methods=["GET", "POST"])
def freelance_posts():
    print("Request method:", request.method)
    
    if "userid" in session and session["user_type"].lower() == "freelancer":
        if request.method == "POST":
            
            title = request.form.get("title")
            description = request.form.get("description")
            category = request.form.get("category")
            location = request.form.get("location")
            budget = request.form.get("budget")
            delivery_time = request.form.get("delivery_time")
            skills_required = request.form.get("skills_required")
            documents = request.files.getlist("documents")

            # # Debugging prints
            # print(f"Title: {title}, Description: {description}, Category: {category}, Location: {location}")
            # print(f"Budget: {budget}, Delivery Time: {delivery_time}, Skills: {skills_required}")
            # print("Documents:", [doc.filename for doc in documents] if documents else "No document")

            # # Validation
            # if not title or not description or not category or not delivery_time:
            #     print("Missing required fields!")
            #     return "Missing required fields", 400

            # Post data dictionary
            post_data = {
                "Title": title,
                "Content": description,
                "Category": category,
                "Location": location,
                "Budget": budget,
                "Delivery_time": delivery_time,
                "Skills_required": skills_required.split(",") if skills_required else [],
                "Multimedia": [],
                "Comments": [],
                "UID": session["userid"],
                "user_type": session["user_type"]
            }

            # Insert post into the collection
            inserted_post = posts_collection.insert_one(post_data)
            post_id = str(inserted_post.inserted_id)

            # Create directories
            user_folder = os.path.join(app.config["FREE_UPLOAD_FOLDER"], f"freelancer_{session['userid']}")
            post_folder = os.path.join(user_folder, "posts", post_id, "multimedia")
            os.makedirs(post_folder, exist_ok=True)

            # Handle file uploads
            for doc in documents:
                if doc and allowed_file(doc.filename):
                    filename = secure_filename(doc.filename)
                    file_path = os.path.join(post_folder, filename)
                    doc.save(file_path)
                    post_data["Multimedia"].append(filename)  
            posts_collection.update_one({"_id": inserted_post.inserted_id}, {"$set": post_data})
            print("Post stored in collection!")
            return redirect(url_for("home"))

       
        posts = list(posts_collection.find({}))  # Show all posts

        return render_template("freelancer/freelancer_dashboard.html", posts=posts)
   
    return redirect(url_for("login"))

@app.route("/home/clients")
def client_chatroom():
    if "userid" not in session:
        return redirect(url_for("login"))
    clients = users_collection.find({"user_type": "client"}) 
    return render_template("freelancer/clients.html", clients=clients)


@app.route("/home/chatroom")
def home_clients():
    if "userid" not in session:
        return redirect(url_for("login"))
    user = users_collection.find_one({"_id": ObjectId(session["userid"])})
    if user and "chatrooms" in user:
        chatrooms = user["chatrooms"]
    else:
        chatrooms = []

    return render_template("client/chatroom.html", chatrooms=chatrooms)



from flask import Flask, render_template, session, request, redirect, url_for
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from bson import ObjectId
from datetime import datetime
from pymongo import MongoClient

socketio = SocketIO(app)


chatroom_collection = db['chatroom']

@app.route("/start_chat", methods=["POST"])
def start_chat():
    if "userid" in session:
        freelancer_id = session["userid"]  # ID of the freelancer
        client_id = request.form.get("other_user_id")  # ID of the client
        room_id = str(ObjectId())  # Generate a unique room ID

        session["room_id"] = room_id
        session["other_user_id"] = client_id
        users_collection.update_one(
            {"_id": ObjectId(freelancer_id)},
            {"$addToSet": {"chatrooms": room_id}}  
        )
        users_collection.update_one(
            {"_id": ObjectId(client_id)},
            {"$addToSet": {"chatrooms": room_id}}  
        )

        # Initialize the chatroom in the collection
        chatroom_collection.insert_one({
            "room_id": room_id,
            "client_id": client_id,
            "freelancer_id": freelancer_id,
            "client_msg": [],
            "freelancer_msg": []
        })

        return redirect(url_for("chat", room_id=room_id))
    return redirect(url_for("login"))

@app.route("/chat/<room_id>")
def chat(room_id):
    if "userid" in session:
        session["room_id"] = room_id
        return render_template("chat.html", room_id=room_id)
    return redirect(url_for("login"))

@socketio.on("join")
def handle_join(data):
    room = data["room"]
    join_room(room)
    send(f"{session.get('username')} has joined the chat.", to=room)

@socketio.on("message")
def handle_message(data):
    room = data["room"]
    message = data["message"]
    sender = session.get("username")
    timestamp = datetime.now().strftime("%H:%M")
    
    # Store message in the chatroom collection under the correct room
    if room:
        chatroom = chatroom_collection.find_one({"room_id": room})
        if chatroom:
            if sender == session.get("username"):  # Check if message sender is the logged in user
                if sender == chatroom["freelancer_id"]:
                    # Save message to freelancer's message array
                    chatroom_collection.update_one(
                        {"room_id": room},
                        {"$push": {"freelancer_msg": {"sender": sender, "message": message, "timestamp": timestamp}}}
                    )
                else:
                    # Save message to client's message array
                    chatroom_collection.update_one(
                        {"room_id": room},
                        {"$push": {"client_msg": {"sender": sender, "message": message, "timestamp": timestamp}}}
                    )
            else:
                # Assuming the other user is the client
                if sender == chatroom["freelancer_id"]:
                    chatroom_collection.update_one(
                        {"room_id": room},
                        {"$push": {"freelancer_msg": {"sender": sender, "message": message, "timestamp": timestamp}}}
                    )
                else:
                    chatroom_collection.update_one(
                        {"room_id": room},
                        {"$push": {"client_msg": {"sender": sender, "message": message, "timestamp": timestamp}}}
                    )

            # Emit message to the chatroom
            emit("message", {"sender": sender, "message": message, "timestamp": timestamp}, to=room)

@socketio.on("leave")
def handle_leave(data):
    room = data["room"]
    leave_room(room)
    send(f"{session.get('username')} has left the chat.", to=room)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landingpage"))

if __name__ == "__main__":
    app.run(debug=True)
    socketio.run(app, debug=True)
