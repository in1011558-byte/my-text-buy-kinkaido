from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import Schema, fields, validates, ValidationError

from models import db
from models.cart import Cart
from models.order import Order
from models.school import School
from utils.auth import create_error_response, create_success_response

orders_bp = Blueprint('orders', __name__)

# スキーマ定義
class AddToCartSchema(Schema):
    """カート追加用スキーマ"""
    textbook_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=lambda x: x > 0)

class UpdateCartSchema(Schema):
    """カート更新用スキーマ"""
    quantity = fields.Int(required=True, validate=lambda x: x > 0)

class CreateOrderSchema(Schema):
    """注文作成用スキーマ（支払方法削除）"""
    shipping_address = fields.Str()
    notes = fields.Str()

add_to_cart_schema = AddToCartSchema()
update_cart_schema = UpdateCartSchema()
create_order_schema = CreateOrderSchema()

# ==================== カート機能 ====================

@orders_bp.route('/cart', methods=['GET'])
@jwt_required()
def get_cart():
    """カート内容取得"""
    try:
        school_id = get_jwt_identity()
        
        cart_items = Cart.get_user_cart(school_id)
        cart_data = [item.to_dict() for item in cart_items]
        
        total_amount = Cart.get_cart_total(school_id)
        total_items = Cart.get_cart_item_count(school_id)
        
        return create_success_response({
            'cart_items': cart_data,
            'total_amount': float(total_amount),
            'total_items': total_items
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch cart: {str(e)}', status_code=500)

@orders_bp.route('/cart', methods=['POST'])
@jwt_required()
def add_to_cart():
    """カートに教科書追加"""
    try:
        json_data = request.get_json()
        if not json_data:
            return create_error_response('INVALID_INPUT', 'No input data provided')
        
        data = add_to_cart_schema.load(json_data)
        
    except ValidationError as e:
        return create_error_response('VALIDATION_ERROR', 'Validation failed', e.messages, 422)
    except Exception as e:
        return create_error_response('INVALID_INPUT', 'Invalid input data')
    
    try:
        school_id = get_jwt_identity()
        
        # カートに追加
        cart_item = Cart.add_or_update_item(
            school_id,
            data['textbook_id'],
            data['quantity']
        )
        
        cart_data = cart_item.to_dict()
        
        return create_success_response({
            'message': 'Item added to cart',
            'cart_item': cart_data
        }, status_code=201)
        
    except ValueError as e:
        return create_error_response('CART_ERROR', str(e), status_code=400)
    except Exception as e:
        db.session.rollback()
        return create_error_response('ADD_FAILED', f'Failed to add to cart: {str(e)}', status_code=500)

@orders_bp.route('/cart/<int:cart_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(cart_id):
    """カートアイテムの数量更新"""
    try:
        json_data = request.get_json()
        if not json_data:
            return create_error_response('INVALID_INPUT', 'No input data provided')
        
        data = update_cart_schema.load(json_data)
        
    except ValidationError as e:
        return create_error_response('VALIDATION_ERROR', 'Validation failed', e.messages, 422)
    except Exception as e:
        return create_error_response('INVALID_INPUT', 'Invalid input data')
    
    try:
        school_id = get_jwt_identity()
        
        cart_item = Cart.update_quantity(cart_id, school_id, data['quantity'])
        
        if cart_item is None:
            return create_success_response({'message': 'Item removed from cart'})
        
        cart_data = cart_item.to_dict()
        
        return create_success_response({
            'message': 'Cart item updated',
            'cart_item': cart_data
        })
        
    except ValueError as e:
        return create_error_response('CART_ERROR', str(e), status_code=400)
    except Exception as e:
        db.session.rollback()
        return create_error_response('UPDATE_FAILED', f'Failed to update cart: {str(e)}', status_code=500)

@orders_bp.route('/cart/<int:cart_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(cart_id):
    """カートからアイテム削除"""
    try:
        school_id = get_jwt_identity()
        
        success = Cart.remove_item(cart_id, school_id)
        
        if not success:
            return create_error_response('CART_ITEM_NOT_FOUND', 'Cart item not found', status_code=404)
        
        return create_success_response({'message': 'Item removed from cart'})
        
    except Exception as e:
        return create_error_response('DELETE_FAILED', f'Failed to remove from cart: {str(e)}', status_code=500)

@orders_bp.route('/cart/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """カート全体をクリア"""
    try:
        school_id = get_jwt_identity()
        
        Cart.clear_user_cart(school_id)
        
        return create_success_response({'message': 'Cart cleared'})
        
    except Exception as e:
        return create_error_response('CLEAR_FAILED', f'Failed to clear cart: {str(e)}', status_code=500)

# ==================== 注文機能 ====================

@orders_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    """注文履歴取得"""
    try:
        school_id = get_jwt_identity()
        
        # クエリパラメータ
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 注文検索
        orders_query = Order.search(user_id=school_id, status=status)
        
        # ページネーション
        pagination = orders_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        orders_data = [order.to_dict() for order in pagination.items]
        
        return create_success_response({
            'orders': orders_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch orders: {str(e)}', status_code=500)

@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    """注文詳細取得"""
    try:
        school_id = get_jwt_identity()
        
        order = Order.query.get(order_id)
        
        if not order:
            return create_error_response('ORDER_NOT_FOUND', 'Order not found', status_code=404)
        
        # 自分の学校の注文のみアクセス可能
        if order.user_id != school_id:
            return create_error_response('ACCESS_DENIED', 'Access denied', status_code=403)
        
        order_data = order.to_dict_with_items()
        
        return create_success_response({'order': order_data})
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch order: {str(e)}', status_code=500)

@orders_bp.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    """注文作成（支払方法削除）"""
    try:
        json_data = request.get_json()
        data = create_order_schema.load(json_data) if json_data else {}
        
    except ValidationError as e:
        return create_error_response('VALIDATION_ERROR', 'Validation failed', e.messages, 422)
    except Exception as e:
        return create_error_response('INVALID_INPUT', 'Invalid input data')
    
    try:
        school_id = get_jwt_identity()
        
        # カートから注文作成（支払方法はNone）
        order = Order.create_from_cart(
            user_id=school_id,
            payment_method=None,  # 支払方法削除
            shipping_address=data.get('shipping_address'),
            notes=data.get('notes')
        )
        
        order_data = order.to_dict_with_items()
        
        return create_success_response({
            'message': 'Order created successfully',
            'order': order_data
        }, status_code=201)
        
    except ValueError as e:
        return create_error_response('ORDER_ERROR', str(e), status_code=400)
    except Exception as e:
        db.session.rollback()
        return create_error_response('CREATE_FAILED', f'Failed to create order: {str(e)}', status_code=500)

@orders_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order(order_id):
    """注文キャンセル"""
    try:
        school_id = get_jwt_identity()
        
        order = Order.query.get(order_id)
        
        if not order:
            return create_error_response('ORDER_NOT_FOUND', 'Order not found', status_code=404)
        
        # 自分の学校の注文のみキャンセル可能
        if order.user_id != school_id:
            return create_error_response('ACCESS_DENIED', 'Access denied', status_code=403)
        
        # キャンセル実行
        json_data = request.get_json()
        reason = json_data.get('reason') if json_data else None
        
        order.cancel_order(reason)
        
        return create_success_response({'message': 'Order cancelled successfully'})
        
    except ValueError as e:
        return create_error_response('CANCEL_ERROR', str(e), status_code=400)
    except Exception as e:
        db.session.rollback()
        return create_error_response('CANCEL_FAILED', f'Failed to cancel order: {str(e)}', status_code=500)