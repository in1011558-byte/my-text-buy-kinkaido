from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields

from models import db
from models.textbook import Textbook
from models.category import Category
from utils.auth import admin_required

textbooks_bp = Blueprint("textbooks", __name__, url_prefix="/textbooks")

class TextbookSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    author = fields.Str(required=True)
    publisher = fields.Str(required=True)
    price = fields.Float(required=True)
    stock = fields.Int(required=True)
    category_id = fields.Int(required=True)
    school_id = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class TextbookSearchSchema(Schema):
    query = fields.Str(required=True)

@textbooks_bp.route("/", methods=["GET"])
@jwt_required()
def get_textbooks():
    school_id = get_jwt_identity() # Assuming JWT identity is school_id for school users
    textbooks = Textbook.query.filter_by(school_id=school_id).all()
    return TextbookSchema(many=True).jsonify(textbooks), 200

@textbooks_bp.route("/<int:textbook_id>", methods=["GET"])
@jwt_required()
def get_textbook(textbook_id):
    school_id = get_jwt_identity()
    textbook = Textbook.query.filter_by(id=textbook_id, school_id=school_id).first_or_404()
    return TextbookSchema().jsonify(textbook), 200

@textbooks_bp.route("/search", methods=["GET"])
@jwt_required()
def search_textbooks():
    schema = TextbookSearchSchema()
    try:
        args = schema.load(request.args)
    except ValidationError as err:
        return jsonify(err.messages), 400

    search_query = f"%{args["query"]}%"
    school_id = get_jwt_identity()

    textbooks = Textbook.query.filter(
        Textbook.school_id == school_id,
        db.or_(
            Textbook.title.like(search_query),
            Textbook.author.like(search_query),
            Textbook.publisher.like(search_query)
        )
    ).all()

    return TextbookSchema(many=True).jsonify(textbooks), 200

@textbooks_bp.route("/", methods=["POST"])
@admin_required()
def create_textbook():
    schema = TextbookSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    textbook = Textbook(
        title=data["title"],
        author=data["author"],
        publisher=data["publisher"],
        price=data["price"],
        stock=data["stock"],
        category_id=data["category_id"],
        school_id=data["school_id"]
    )
    db.session.add(textbook)
    db.session.commit()

    return TextbookSchema().jsonify(textbook), 201

@textbooks_bp.route("/<int:textbook_id>", methods=["PUT"])
@admin_required()
def update_textbook(textbook_id):
    textbook = Textbook.query.get_or_404(textbook_id)
    schema = TextbookSchema()
    try:
        data = schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    for key, value in data.items():
        setattr(textbook, key, value)
    db.session.commit()

    return TextbookSchema().jsonify(textbook), 200

@textbooks_bp.route("/<int:textbook_id>", methods=["DELETE"])
@admin_required()
def delete_textbook(textbook_id):
    textbook = Textbook.query.get_or_404(textbook_id)
    db.session.delete(textbook)
    db.session.commit()
    return jsonify({"message": "教科書が正常に削除されました。"}), 204

