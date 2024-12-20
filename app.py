import certifi
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, supports_credentials=True)

uri = "mongodb+srv://mchuangyc:4M66JTGdJ8HIyQXZ@cluster0.fcc8s.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where())

try:
    client.admin.command('ping')
    print("Pinged development. Connection to MongoDB is successful")
except Exception as e:
    print(e)

db = client["Juny-V2"]
collection = db["users"]

@app.route("/")
def home():
    return "Connected"

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "email and password are required"}), 400

    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    if user["password"] == password:
        # Handle streak calculation
        last_login = user.get("last_login")
        today = datetime.utcnow().date()

        if last_login:
            last_login_date = datetime.strptime(last_login, "%Y-%m-%d").date()
            if last_login_date == today - timedelta(days=1):
                user["streak"] += 1
            elif last_login_date < today - timedelta(days=1):
                user["streak"] = 1  # Reset streak
        else:
            user["streak"] = 1  # First login sets streak to 1

        collection.update_one(
            {"email": email},
            {"$set": {"last_login": today.strftime("%Y-%m-%d"), "streak": user["streak"]}}
        )

        response = jsonify({"status": "success", "message": "Login successful", "streak": user["streak"]})
        response.set_cookie("email", email)
        return response, 200
    else:
        return jsonify({"status": "error", "message": "Invalid password"}), 401

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"status": "error", "message": "email and password are required"}), 400

    if collection.find_one({"email": email}):
        return jsonify({"status": "error", "message": "Email already exists"}), 400

    collection.insert_one({
        "email": email,
        "password": password,
        "premium": False,
        "streak": 0,
        "shells": 0,
        "temp3": 0,
        "last_login": None,
    })

    response = jsonify({"status": "success", "message": "User registered successfully"})
    response.set_cookie("email", email)
    return response, 201

@app.route("/streak", methods=["GET"])
def get_streak():
    email = request.args.get("email")  # Retrieve email from query parameters
    if not email:
        return jsonify({"status": "error", "message": "Email is required"}), 400

    user = collection.find_one({"email": email})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    return jsonify({"status": "success", "streak": user.get("streak", 0)}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
