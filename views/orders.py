from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields, validates, ValidationError

from models import db
from models.cart import Cart
from models.order import Order, OrderItem
from models.textbook import Textbook

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")

class OrderItemSchema(Schema):
    id = fields.Int(dump_only=True)
    textbook_id = fields.Int(required=True)
    quantity = fields.Int(required=True)
    price = fields.Float(dump_only=True)

class OrderSchema(Schema):
    id = fields.Int(dump_only=True)
    school_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
    total_amount = fields.Float(dump_only=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    items = fields.List(fields.Nested(OrderItemSchema), required=True)

@orders_bp.route("/cart", methods=["GET"])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        return jsonify({"message": "カートは空です。"}), 404
    return jsonify(cart.to_dict()), 200

@orders_bp.route("/cart/add", methods=["POST"])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.json
    textbook_id = data.get("textbook_id")
    quantity = data.get("quantity", 1)

    textbook = Textbook.query.get_or_404(textbook_id)
    if textbook.stock < quantity:
        return jsonify({"message": "在庫が不足しています。"}), 400

    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

    cart.add_item(textbook, quantity)
    db.session.commit()

    return jsonify({"message": "商品がカートに追加されました。"}), 200

@orders_bp.route("/checkout", methods=["POST"])
@jwt_required()
def checkout():
    user_id = get_jwt_identity()
    cart = Cart.query.filter_by(user_id=user_id).first_or_404()

    if not cart.items:
        return jsonify({"message": "カートに商品がありません。"}), 400

    order = Order(school_id=cart.user.school_id, user_id=user_id, total_amount=cart.total_amount)
    db.session.add(order)

    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            textbook_id=item.textbook_id,
            quantity=item.quantity,
            price=item.textbook.price
        )
        db.session.add(order_item)
        item.textbook.stock -= item.quantity

    db.session.delete(cart)
    db.session.commit()

    return jsonify({"message": "注文が正常に完了しました。"}), 201

@orders_bp.route("/", methods=["GET"])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).all()
    return OrderSchema(many=True).jsonify(orders), 200

@orders_bp.route("/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.filter_by(id=order_id, user_id=user_id).first_or_404()
    return OrderSchema().jsonify(order), 200

