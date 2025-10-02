from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validates, ValidationError
from datetime import datetime

from models import db
from models.school_auth import SchoolAuth
from models.school import School

school_auth_bp = Blueprint("school_auth", __name__, url_prefix="/school_auth")

class SchoolAuthSchema(Schema):
    id = fields.Int(dump_only=True)
    school_id = fields.Int(required=True)
    email = fields.Email(required=True)
    password = fields.Str(load_only=True, required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates("school_id")
    def validate_school_id(self, value):
        if not School.query.get(value):
            raise ValidationError("指定された学校IDは存在しません。")

class SchoolAuthLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

@school_auth_bp.route("/register", methods=["POST"])
def register_school_auth():
    schema = SchoolAuthSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    if SchoolAuth.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "このメールアドレスは既に使用されています。"}), 409

    school_auth = SchoolAuth(
        school_id=data["school_id"],
        email=data["email"]
    )
    school_auth.set_password(data["password"])

    db.session.add(school_auth)
    db.session.commit()

    return jsonify({"message": "学校認証アカウントが正常に登録されました。"}), 201

@school_auth_bp.route("/login", methods=["POST"])
def login_school_auth():
    schema = SchoolAuthLoginSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    school_auth = SchoolAuth.query.filter_by(email=data["email"]).first()

    if school_auth and school_auth.check_password(data["password"]):
        access_token = create_access_token(identity=school_auth.id)
        refresh_token = create_refresh_token(identity=school_auth.id)
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200
    else:
        return jsonify({"message": "無効な認証情報です。"}), 401

@school_auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_school_auth():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify(access_token=access_token), 200

@school_auth_bp.route("/protected", methods=["GET"])
@jwt_required()
def protected_school_auth():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

