from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.textbook import Textbook
from models.user import User
from models.category import Category
from models.school import School
from extensions import db

textbooks_bp = Blueprint('textbooks', __name__)

@textbooks_bp.route('/', methods=['GET'])
def get_textbooks():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category_id = request.args.get('category_id', type=int)
        school_id = request.args.get('school_id', type=int)
        search = request.args.get('search', '')
        
        query = Textbook.query
        
        if category_id:
            query = query.filter(Textbook.category_id == category_id)
        if school_id:
            query = query.filter(Textbook.school_id == school_id)
        if search:
            query = query.filter(Textbook.title.contains(search))
        
        textbooks = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'textbooks': [textbook.to_dict() for textbook in textbooks.items],
            'total': textbooks.total,
            'pages': textbooks.pages,
            'current_page': page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@textbooks_bp.route('/<int:textbook_id>', methods=['GET'])
def get_textbook(textbook_id):
    try:
        textbook = Textbook.query.get(textbook_id)
        if not textbook:
            return jsonify({'error': 'Textbook not found'}), 404
        return jsonify(textbook.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@textbooks_bp.route('/', methods=['POST'])
@jwt_required()
def create_textbook():
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        required_fields = ['title', 'author', 'isbn', 'price', 'category_id', 'school_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        textbook = Textbook(
            title=data['title'],
            author=data['author'],
            isbn=data['isbn'],
            price=data['price'],
            stock_quantity=data.get('stock_quantity', 0),
            description=data.get('description'),
            image_url=data.get('image_url'),
            category_id=data['category_id'],
            school_id=data['school_id']
        )
        textbook.save()
        
        return jsonify({
            'message': 'Textbook created successfully',
            'textbook': textbook.to_dict()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@textbooks_bp.route('/<int:textbook_id>', methods=['PUT'])
@jwt_required()
def update_textbook(textbook_id):
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        textbook = Textbook.query.get(textbook_id)
        if not textbook:
            return jsonify({'error': 'Textbook not found'}), 404
        
        data = request.get_json()
        updatable_fields = ['title', 'author', 'isbn', 'price', 'stock_quantity', 'description', 'image_url', 'category_id', 'school_id']
        for field in updatable_fields:
            if field in data:
                setattr(textbook, field, data[field])
        
        textbook.save()
        return jsonify({
            'message': 'Textbook updated successfully',
            'textbook': textbook.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@textbooks_bp.route('/<int:textbook_id>', methods=['DELETE'])
@jwt_required()
def delete_textbook(textbook_id):
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        textbook = Textbook.query.get(textbook_id)
        if not textbook:
            return jsonify({'error': 'Textbook not found'}), 404
        
        textbook.delete()
        return jsonify({'message': 'Textbook deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@textbooks_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.all()
        return jsonify([category.to_dict() for category in categories]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@textbooks_bp.route('/schools', methods=['GET'])
def get_schools():
    try:
        schools = School.query.all()
        return jsonify([school.to_dict() for school in schools]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
