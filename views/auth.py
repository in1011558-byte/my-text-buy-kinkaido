from flask import Blueprint, request, jsonify
from models.user import User
from extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    school_id = data.get("school_id") # Assuming school_id is provided during registration

    if not username or not email or not password or not school_id:
        return jsonify({"message": "Missing username, email, password, or school_id"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 409

    new_user = User(username=username, email=email, school_id=school_id)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    # ログインロジックをここに追加
    return jsonify({"message": "Login endpoint not implemented yet"}), 501

@auth_bp.route("/logout", methods=["POST"])
def logout():
    # ログアウトロジックをここに追加
    return jsonify({"message": "Logout endpoint not implemented yet"}), 501
