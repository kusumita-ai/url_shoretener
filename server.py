"""from flask import Flask, request, jsonify, redirect, render_template
import time
import random
import string
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["url_shortener"]
collection = db["urls"]

# Generate random short code
def generate_short_code(length=5):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not collection.find_one({"short_code": code}):
            return code

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/shorten", methods=["POST"])
def shorten_url():
    # Handle both JSON and Form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    print("Received Data:", data)

    long_url = data.get("url")
    password = data.get("password", "")
    expiration_minutes = int(data.get("expiration", 60))

    if not long_url:
        return jsonify({"error": "Missing URL"}), 400

    short_code = generate_short_code()
    expiration_time = int(time.time()) + (expiration_minutes * 60)

    collection.insert_one({
        "short_code": short_code,
        "long_url": long_url,
        "password": generate_password_hash(password) if password else "",  # Store hash
        "expires_at": expiration_time
    })

    short_url = request.host_url + short_code

    return jsonify({
        "short_url": short_url,
        "expires_in": f"{expiration_minutes} minutes"
    })

@app.route("/<short_code>", methods=["GET", "POST"])
def redirect_to_original(short_code):
    url_data = collection.find_one({"short_code": short_code})

    if not url_data:
        return jsonify({"error": "Short URL not found"}), 404

    current_time = int(time.time())
    if current_time > url_data["expires_at"]:
        expired_minutes = (current_time - url_data["expires_at"]) // 60
        return jsonify({"error": f"This short URL expired {expired_minutes} minutes ago!"}), 410

    # If password protection exists
    if url_data["password"]:
        if request.method == "POST":
            entered_password = request.form.get("password")
            if check_password_hash(url_data["password"], entered_password):
                return redirect(url_data["long_url"])
            else:
                return render_template("password_prompt.html", short_code=short_code, error="Incorrect password")

        return render_template("password_prompt.html", short_code=short_code)

    return redirect(url_data["long_url"])

if __name__ == "__main__":
    app.run(debug=True)"""

from flask import Flask, request, jsonify, redirect, render_template
import time
import random
import string
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")
db = client["url_shortener"]
collection = db["urls"]
users_collection = db["users"]  # New collection for users

# Generate random short code
def generate_short_code(length=5):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not collection.find_one({"short_code": code}):
            return code

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/shorten", methods=["POST"])
def shorten_url():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form

    print("Received Data:", data)

    long_url = data.get("url")
    password = data.get("password", "")
    expiration_minutes = int(data.get("expiration", 60))

    if not long_url:
        return jsonify({"error": "Missing URL"}), 400

    short_code = generate_short_code()
    expiration_time = int(time.time()) + (expiration_minutes * 60)

    collection.insert_one({
        "short_code": short_code,
        "long_url": long_url,
        "password": generate_password_hash(password) if password else "",
        "expires_at": expiration_time
    })
    print("Inserted into MongoDB:", {
    "short_code": short_code,
    "long_url": long_url,
    "password": "HIDDEN",  # Don't print actual hash
    "expires_at": expiration_time
})

    short_url = request.host_url + short_code

    return jsonify({
        "short_url": short_url,
        "expires_in": f"{expiration_minutes} minutes"
    })

@app.route("/<short_code>", methods=["GET", "POST"])
def redirect_to_original(short_code):
    url_data = collection.find_one({"short_code": short_code})

    if not url_data:
        return jsonify({"error": "Short URL not found"}), 404

    current_time = int(time.time())
    if current_time > url_data["expires_at"]:
        expired_minutes = (current_time - url_data["expires_at"]) // 60
        return jsonify({"error": f"This short URL expired {expired_minutes} minutes ago!"}), 410

    if url_data["password"]:
        if request.method == "POST":
            entered_password = request.form.get("password")
            if check_password_hash(url_data["password"], entered_password):
                return redirect(url_data["long_url"])
            else:
                return render_template("password_prompt.html", short_code=short_code, error="Incorrect password")
        return render_template("password_prompt.html", short_code=short_code)

    return redirect(url_data["long_url"])

# ------------------------------
# ✅ New: User Registration Route
# ------------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 409

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({
        "username": username,
        "password": hashed_password
    })

    return jsonify({"message": "User registered successfully"}), 201

# ---------------------------
# ✅ New: User Login Route
# ---------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = users_collection.find_one({"username": username})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({"message": "Login successful", "username": username}), 200

if __name__ == "__main__":
       app.run(debug=True)
