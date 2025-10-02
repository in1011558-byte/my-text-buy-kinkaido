from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.textbook import Textbook
from models.order import Order
from models.school import School
from models.category import Category
from extensions import db
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required():
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    if not user or user.role != 'admin':
        return False
    return True

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    try:
        if not admin_required():
            return jsonify({'error': 'Admin access required'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = User.query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@jwt_required()
def update_user_role(user_id):
    try:
        if not admin_required():
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        new_role = data.get('role')
        
        if new_role not in ['student', 'admin']:
            return jsonify({'error': 'Invalid role'}), 400
        
        user.role = new_role
        user.save()
        
        return jsonify({
            'message': 'User role updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@jwt_required()
def update_user_status(user_id):
    try:
        if not admin_required():
            return jsonify({'error': 'Admin access required'}), 403
        
        user = User.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        is_active = data.get('is_active')
        
        if is_active is None:
            return jsonify({'error': 'is_active field is required'}), 400
        
        user.is_active = is_active
        user.save()
        
        return jsonify({
            'message': 'User status updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/schools', methods=['GET'])
@jwt_required()
def get_schools():
    try:
        if not admin_required():
            return jsonify({'error': 'Admin access required'}), 403
        
        schools = School.query.all()
        return jsonify([school.to_dict() for school in schools]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/schools', methods=['POST'])
@jwt_required()
def create_school():
    try:
        if not admin_required():
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        required_fields = ['school_name', 'prefecture', 'city', 'address']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        school = School(
            school_name=data['school_name'],
            prefecture=data['prefecture'],
            city=data['city'],
            address=data['address'],
            phone=data.get('phone'),
            email=data.get('email')
        )
        school.save()
        
        return jsonify({
            'message': 'School created successfully',
            'school': school.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/schools/<int:school_id>', methods=['PUT'])
@jwt_required()
def update_school(school_id):
    try:
        if not admin_required():
            return jsonify({'error': 'Admin access required'}), 403
        
        school = School.query.get(school_id)
        if not school:
            return jsonify({'error': 'School not found'}), 404
        
        data = request.get_json()
        updatable_fields = ['school_name', 'prefecture', 'city', 'address', 'phone', 'email']
        for field in updatable_fields:
            if field in data:
                setattr(school, field, data[field])
        
        school.save()
        return jsonify({
            'message': 'School updated successfully',
            'school': school.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    try:
        if not admin_required():
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data.get('category_name'):
            return jsonify({'error': 'category_name is required'}), 400
        
        category = Category(
            category_name=data['category_name'],
            description=data.get('description')
        )
        category.save()
        
        return jsonify({
            'message': 'Category created successfully',
            'category': category.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/reports/sales', methods=['GET'])
@jwt_required()
def sales_report():
    try:
        if not admin_required():
            return jsonify({'error': 'Admin access required'}), 403
        
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        orders = Order.query.filter(Order.created_at >= start_date).all()
        
        total_sales = sum(order.total_amount for order in orders)
        total_orders = len(orders)
        
        return jsonify({
            'period_days': days,
            'total_sales': total_sales,
            'total_orders': total_orders,
            'average_order_value': total_sales / total_orders if total_orders > 0 else 0
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/reports/inventory', methods=['GET'])
@jwt_required()
def inventory_report():
    try:
        if not admin_required():
            return jsonify({'error': 'Admin access required'}), 403
        
        low_stock_threshold = request.args.get('threshold', 10, type=int)
        
        textbooks = Textbook.query.all()
        low_stock_items = [tb for tb in textbooks if tb.stock_quantity <= low_stock_threshold]
        
        return jsonify({
            'total_textbooks': len(textbooks),
            'low_stock_items': [tb.to_dict() for tb in low_stock_items],
            'low_stock_count': len(low_stock_items)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
