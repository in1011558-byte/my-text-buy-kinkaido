from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, validates, ValidationError

from models import db
from models.school import School
from models.school_auth import SchoolAuth
from utils.auth import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

class SchoolSchema(Schema):
    id = fields.Int(dump_only=True)
    school_name = fields.Str(required=True)
    prefecture = fields.Str(required=True)
    city = fields.Str(required=True)
    address = fields.Str()
    phone = fields.Str()
    email = fields.Email()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class SchoolAuthSchema(Schema):
    id = fields.Int(dump_only=True)
    school_id = fields.Int(required=True)
    email = fields.Email(required=True)
    password = fields.Str(load_only=True, required=True)

@admin_bp.route("/schools", methods=["POST"])
@admin_required()
def create_school():
    schema = SchoolSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    if School.query.filter_by(school_name=data["school_name"]).first():
        return jsonify({"message": "この学校名は既に使用されています。"}), 409

    # 学校作成
    school = School(
        school_name=data["school_name"],
        prefecture=data["prefecture"],
        city=data["city"],
        address=data.get("address"),
        phone=data.get("phone"),
        email=data.get("email")
    )
    db.session.add(school)
    db.session.commit()

    return SchoolSchema().jsonify(school), 201

@admin_bp.route("/schools", methods=["GET"])
@admin_required()
def get_schools():
    schools = School.query.all()
    return SchoolSchema(many=True).jsonify(schools), 200

@admin_bp.route("/schools/<int:school_id>", methods=["GET"])
@admin_required()
def get_school(school_id):
    school = School.query.get_or_404(school_id)
    return SchoolSchema().jsonify(school), 200

@admin_bp.route("/schools/<int:school_id>", methods=["PUT"])
@admin_required()
def update_school(school_id):
    school = School.query.get_or_404(school_id)
    schema = SchoolSchema()
    try:
        data = schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    for key, value in data.items():
        setattr(school, key, value)
    db.session.commit()

    return SchoolSchema().jsonify(school), 200

@admin_bp.route("/schools/<int:school_id>", methods=["DELETE"])
@admin_required()
def delete_school(school_id):
    school = School.query.get_or_404(school_id)
    db.session.delete(school)
    db.session.commit()
    return jsonify({"message": "学校が正常に削除されました。"}), 204

@admin_bp.route("/school_auths", methods=["POST"])
@admin_required()
def create_school_auth():
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

    return SchoolAuthSchema().jsonify(school_auth), 201

@admin_bp.route("/school_auths", methods=["GET"])
@admin_required()
def get_school_auths():
    school_auths = SchoolAuth.query.all()
    return SchoolAuthSchema(many=True).jsonify(school_auths), 200

@admin_bp.route("/school_auths/<int:school_auth_id>", methods=["GET"])
@admin_required()
def get_school_auth(school_auth_id):
    school_auth = SchoolAuth.query.get_or_404(school_auth_id)
    return SchoolAuthSchema().jsonify(school_auth), 200

@admin_bp.route("/school_auths/<int:school_auth_id>", methods=["PUT"])
@admin_required()
def update_school_auth(school_auth_id):
    school_auth = SchoolAuth.query.get_or_404(school_auth_id)
    schema = SchoolAuthSchema()
    try:
        data = schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    for key, value in data.items():
        if key == "password":
            school_auth.set_password(value)
        else:
            setattr(school_auth, key, value)
    db.session.commit()

    return SchoolAuthSchema().jsonify(school_auth), 200

@admin_bp.route("/school_auths/<int:school_auth_id>", methods=["DELETE"])
@admin_required()
def delete_school_auth(school_auth_id):
    school_auth = SchoolAuth.query.get_or_404(school_auth_id)
    db.session.delete(school_auth)
    db.session.commit()
    return jsonify({"message": "学校認証アカウントが正常に削除されました。"}), 204

