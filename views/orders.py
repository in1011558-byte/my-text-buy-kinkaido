from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.order import Order, OrderItem
from models.cart import Cart
from models.textbook import Textbook
from models.user import User
from extensions import db

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    try:
        user_id = get_jwt_identity()
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        return jsonify([item.to_dict() for item in cart_items]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        textbook_id = data.get('textbook_id')
        quantity = data.get('quantity', 1)
        if not textbook_id:
            return jsonify({'error': 'textbook_id is required'}), 400
        textbook = Textbook.query.get(textbook_id)
        if not textbook:
            return jsonify({'error': 'Textbook not found'}), 404
        if textbook.stock_quantity < quantity:
            return jsonify({'error': 'Insufficient stock'}), 400
        existing_cart_item = Cart.query.filter_by(user_id=user_id, textbook_id=textbook_id).first()
        if existing_cart_item:
            existing_cart_item.quantity += quantity
            existing_cart_item.save()
            cart_item = existing_cart_item
        else:
            cart_item = Cart(user_id=user_id, textbook_id=textbook_id, quantity=quantity)
            cart_item.save()
        return jsonify({'message': 'Item added to cart successfully', 'cart_item': cart_item.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
        total_amount = 0
        order_items_data = []
        for cart_item in cart_items:
            textbook = cart_item.textbook
            if textbook.stock_quantity < cart_item.quantity:
                return jsonify({'error': f'Insufficient stock for {textbook.title}'}), 400
            item_total = textbook.price * cart_item.quantity
            total_amount += item_total
            order_items_data.append({
                'textbook_id': textbook.id,
                'quantity': cart_item.quantity,
                'unit_price': textbook.price,
                'total_price': item_total
            })
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            shipping_address=data.get('shipping_address'),
            payment_method=data.get('payment_method', 'cash_on_delivery'),
            status='pending'
        )
        order.save()
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                textbook_id=item_data['textbook_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
            order_item.save()
            textbook = Textbook.query.get(item_data['textbook_id'])
            textbook.stock_quantity -= item_data['quantity']
            textbook.save()
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return jsonify({'message': 'Order created successfully', 'order': order.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if user.role == 'admin':
            orders = Order.query.all()
        else:
            orders = Order.query.filter_by(user_id=user_id).all()
        return jsonify([order.to_dict() for order in orders]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
