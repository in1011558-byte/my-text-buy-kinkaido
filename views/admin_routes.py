from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from marshmallow import Schema, fields, validates, ValidationError

from models import db
from models.school import School
from models.school_auth import SchoolAuth
from models.user import User
from models.textbook import Textbook
from models.category import Category
from models.order import Order
from utils.auth import admin_required, create_error_response, create_success_response

admin_bp = Blueprint('admin', __name__)

# スキーマ定義
class SchoolCreateSchema(Schema):
    """学校作成用スキーマ"""
    school_name = fields.Str(required=True)
    prefecture = fields.Str(required=True)
    city = fields.Str(required=True)
    address = fields.Str()
    phone = fields.Str()
    email = fields.Email()
    login_id = fields.Str(required=True)
    password = fields.Str(required=True)

class SchoolUpdateSchema(Schema):
    """学校更新用スキーマ"""
    school_name = fields.Str()
    prefecture = fields.Str()
    city = fields.Str()
    address = fields.Str()
    phone = fields.Str()
    email = fields.Email()
    is_active = fields.Bool()

class TextbookCreateSchema(Schema):
    """教科書作成用スキーマ"""
    category_id = fields.Int(required=True)
    title = fields.Str(required=True)
    price = fields.Decimal(required=True, as_string=True)
    stock_quantity = fields.Int(required=True)
    grade_level = fields.Str()
    subject = fields.Str()
    image_url = fields.Str()

school_create_schema = SchoolCreateSchema()
school_update_schema = SchoolUpdateSchema()
textbook_create_schema = TextbookCreateSchema()

# ==================== 学校管理 ====================

@admin_bp.route('/schools', methods=['GET'])
@admin_required
def get_schools(current_user):
    """学校一覧取得"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search')
        prefecture = request.args.get('prefecture')
        
        schools_query = School.search(query=search, prefecture=prefecture)
        
        pagination = schools_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        schools_data = [school.to_dict() for school in pagination.items]
        
        return create_success_response({
            'schools': schools_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch schools: {str(e)}', status_code=500)

@admin_bp.route('/schools', methods=['POST'])
@admin_required
def create_school(current_user):
    """学校新規作成"""
    try:
        json_data = request.get_json()
        if not json_data:
            return create_error_response('INVALID_INPUT', 'No input data provided')
        
        data = school_create_schema.load(json_data)
        
    except ValidationError as e:
        return create_error_response('VALIDATION_ERROR', 'Validation failed', e.messages, 422)
    except Exception as e:
        return create_error_response('INVALID_INPUT', 'Invalid input data')
    
    try:
        # 学校作成
        school = School(
            school_name=data['school_name'],
            prefecture=data['prefecture'],
            city=data['city'],
            address=data.get('address'),
            phone=data.get('phone'),
            email=data.get('email')
        )
        school.save()
        
        # 学校の認証情報作成
        school_auth = SchoolAuth.create_for_school(
            school.school_id,
            data['login_id'],
            data['password']
        )
        
        school_data = school.to_dict()
        school_data['login_id'] = school_auth.login_id
        
        return create_success_response({
            'message': 'School created successfully',
            'school': school_data
        }, status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response('CREATE_FAILED', f'Failed to create school: {str(e)}', status_code=500)

@admin_bp.route('/schools/<int:school_id>', methods=['GET'])
@admin_required
def get_school(current_user, school_id):
    """学校詳細取得"""
    try:
        school = School.query.get(school_id)
        
        if not school:
            return create_error_response('SCHOOL_NOT_FOUND', 'School not found', status_code=404)
        
        school_data = school.to_dict()
        
        # 認証情報も含める
        if school.auth:
            school_data['login_id'] = school.auth.login_id
        
        return create_success_response({'school': school_data})
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch school: {str(e)}', status_code=500)

@admin_bp.route('/schools/<int:school_id>', methods=['PUT'])
@admin_required
def update_school(current_user, school_id):
    """学校情報更新"""
    try:
        json_data = request.get_json()
        if not json_data:
            return create_error_response('INVALID_INPUT', 'No input data provided')
        
        data = school_update_schema.load(json_data)
        
    except ValidationError as e:
        return create_error_response('VALIDATION_ERROR', 'Validation failed', e.messages, 422)
    except Exception as e:
        return create_error_response('INVALID_INPUT', 'Invalid input data')
    
    try:
        school = School.query.get(school_id)
        
        if not school:
            return create_error_response('SCHOOL_NOT_FOUND', 'School not found', status_code=404)
        
        # 更新
        for key, value in data.items():
            if hasattr(school, key) and value is not None:
                setattr(school, key, value)
        
        school.save()
        
        school_data = school.to_dict()
        
        return create_success_response({
            'message': 'School updated successfully',
            'school': school_data
        })
        
    except Exception as e:
        db.session.rollback()
        return create_error_response('UPDATE_FAILED', f'Failed to update school: {str(e)}', status_code=500)

@admin_bp.route('/schools/<int:school_id>', methods=['DELETE'])
@admin_required
def delete_school(current_user, school_id):
    """学校削除"""
    try:
        school = School.query.get(school_id)
        
        if not school:
            return create_error_response('SCHOOL_NOT_FOUND', 'School not found', status_code=404)
        
        # 学校名を保存
        school_name = school.school_name
        
        # 削除（カスケードで関連データも削除）
        school.delete()
        
        return create_success_response({
            'message': f'School "{school_name}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return create_error_response('DELETE_FAILED', f'Failed to delete school: {str(e)}', status_code=500)

# ==================== 生徒管理（タグ表示用） ====================

@admin_bp.route('/students', methods=['GET'])
@admin_required
def get_students(current_user):
    """生徒一覧取得（タグ表示用の簡易情報）"""
    try:
        school_id = request.args.get('school_id', type=int)
        grade = request.args.get('grade')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        students_query = User.search(school_id=school_id, role='student')
        
        if grade:
            students_query = students_query.filter_by(grade=grade)
        
        pagination = students_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # タグ表示用の簡易データ
        students_data = [{
            'user_id': student.user_id,
            'student_id': student.student_id,
            'full_name': student.full_name,
            'grade': student.grade,
            'class_name': student.class_name,
            'school_name': student.school.school_name if student.school else None
        } for student in pagination.items]
        
        return create_success_response({
            'students': students_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch students: {str(e)}', status_code=500)

@admin_bp.route('/students/<int:student_id>', methods=['GET'])
@admin_required
def get_student_detail(current_user, student_id):
    """生徒詳細情報取得（クリック時）"""
    try:
        student = User.query.get(student_id)
        
        if not student or not student.is_student:
            return create_error_response('STUDENT_NOT_FOUND', 'Student not found', status_code=404)
        
        # 詳細情報
        student_data = student.to_dict()
        
        # 注文履歴サマリー
        orders = Order.get_user_orders(student_id)
        student_data['orders_count'] = len(orders)
        student_data['total_spent'] = sum(float(order.total_amount) for order in orders)
        
        return create_success_response({'student': student_data})
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch student: {str(e)}', status_code=500)

# ==================== 教科書管理 ====================

@admin_bp.route('/textbooks', methods=['GET'])
@admin_required
def get_all_textbooks(current_user):
    """教科書一覧取得（管理者用）"""
    try:
        category_id = request.args.get('category_id', type=int)
        grade_level = request.args.get('grade_level')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        textbooks_query = Textbook.search(
            category_id=category_id,
            grade_level=grade_level,
            in_stock_only=False  # 管理者は在庫切れも表示
        )
        
        pagination = textbooks_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        textbooks_data = [textbook.to_dict() for textbook in pagination.items]
        
        return create_success_response({
            'textbooks': textbooks_data,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch textbooks: {str(e)}', status_code=500)

@admin_bp.route('/textbooks', methods=['POST'])
@admin_required
def create_textbook(current_user):
    """教科書新規作成"""
    try:
        json_data = request.get_json()
        if not json_data:
            return create_error_response('INVALID_INPUT', 'No input data provided')
        
        data = textbook_create_schema.load(json_data)
        
    except ValidationError as e:
        return create_error_response('VALIDATION_ERROR', 'Validation failed', e.messages, 422)
    except Exception as e:
        return create_error_response('INVALID_INPUT', 'Invalid input data')
    
    try:
        textbook = Textbook(
            category_id=data['category_id'],
            title=data['title'],
            price=data['price'],
            stock_quantity=data['stock_quantity'],
            grade_level=data.get('grade_level'),
            subject=data.get('subject'),
            image_url=data.get('image_url')
        )
        textbook.save()
        
        textbook_data = textbook.to_dict()
        
        return create_success_response({
            'message': 'Textbook created successfully',
            'textbook': textbook_data
        }, status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response('CREATE_FAILED', f'Failed to create textbook: {str(e)}', status_code=500)

@admin_bp.route('/textbooks/<int:textbook_id>', methods=['PUT'])
@admin_required
def update_textbook(current_user, textbook_id):
    """教科書更新"""
    try:
        json_data = request.get_json()
        if not json_data:
            return create_error_response('INVALID_INPUT', 'No input data provided')
        
        textbook = Textbook.query.get(textbook_id)
        
        if not textbook:
            return create_error_response('TEXTBOOK_NOT_FOUND', 'Textbook not found', status_code=404)
        
        # 更新
        allowed_fields = ['category_id', 'title', 'price', 'stock_quantity', 'grade_level', 'subject', 'image_url', 'is_active']
        for key, value in json_data.items():
            if key in allowed_fields and hasattr(textbook, key):
                setattr(textbook, key, value)
        
        textbook.save()
        
        textbook_data = textbook.to_dict()
        
        return create_success_response({
            'message': 'Textbook updated successfully',
            'textbook': textbook_data
        })
        
    except Exception as e:
        db.session.rollback()
        return create_error_response('UPDATE_FAILED', f'Failed to update textbook: {str(e)}', status_code=500)

@admin_bp.route('/textbooks/<int:textbook_id>', methods=['DELETE'])
@admin_required
def delete_textbook(current_user, textbook_id):
    """教科書削除"""
    try:
        textbook = Textbook.query.get(textbook_id)
        
        if not textbook:
            return create_error_response('TEXTBOOK_NOT_FOUND', 'Textbook not found', status_code=404)
        
        title = textbook.title
        textbook.delete()
        
        return create_success_response({
            'message': f'Textbook "{title}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return create_error_response('DELETE_FAILED', f'Failed to delete textbook: {str(e)}', status_code=500)

# ==================== 注文管理 ====================

@admin_bp.route('/orders', methods=['GET'])
@admin_required
def get_all_orders(current_user):
    """全注文一覧取得"""
    try:
        school_id = request.args.get('school_id', type=int)
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        orders_query = Order.search(user_id=school_id, status=status)
        
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

@admin_bp.route('/orders/<int:order_id>', methods=['GET'])
@admin_required
def get_order_detail(current_user, order_id):
    """注文詳細取得"""
    try:
        order = Order.query.get(order_id)
        
        if not order:
            return create_error_response('ORDER_NOT_FOUND', 'Order not found', status_code=404)
        
        order_data = order.to_dict_with_items()
        
        return create_success_response({'order': order_data})
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch order: {str(e)}', status_code=500)

@admin_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(current_user, order_id):
    """注文ステータス更新"""
    try:
        json_data = request.get_json()
        if not json_data or 'status' not in json_data:
            return create_error_response('INVALID_INPUT', 'Status is required')
        
        order = Order.query.get(order_id)
        
        if not order:
            return create_error_response('ORDER_NOT_FOUND', 'Order not found', status_code=404)
        
        order.update_status(json_data['status'], json_data.get('notes'))
        
        return create_success_response({
            'message': 'Order status updated successfully',
            'order': order.to_dict()
        })
        
    except ValueError as e:
        return create_error_response('STATUS_ERROR', str(e), status_code=400)
    except Exception as e:
        db.session.rollback()
        return create_error_response('UPDATE_FAILED', f'Failed to update order status: {str(e)}', status_code=500)

# ==================== カテゴリ管理 ====================

@admin_bp.route('/categories', methods=['GET'])
@admin_required
def get_all_categories(current_user):
    """カテゴリ一覧取得"""
    try:
        categories = Category.query.order_by(Category.category_name).all()
        categories_data = [cat.to_dict() for cat in categories]
        
        return create_success_response({
            'categories': categories_data,
            'total': len(categories_data)
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch categories: {str(e)}', status_code=500)

@admin_bp.route('/categories', methods=['POST'])
@admin_required
def create_category(current_user):
    """カテゴリ作成"""
    try:
        json_data = request.get_json()
        if not json_data or 'category_name' not in json_data:
            return create_error_response('INVALID_INPUT', 'Category name is required')
        
        category = Category(
            category_name=json_data['category_name'],
            description=json_data.get('description')
        )
        category.save()
        
        return create_success_response({
            'message': 'Category created successfully',
            'category': category.to_dict()
        }, status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return create_error_response('CREATE_FAILED', f'Failed to create category: {str(e)}', status_code=500)

# ==================== ダッシュボード ====================

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard_stats(current_user):
    """ダッシュボード統計情報"""
    try:
        # 統計情報収集
        total_schools = School.query.filter_by(is_active=True).count()
        total_students = User.query.filter_by(role='student', is_active=True).count()
        total_textbooks = Textbook.query.filter_by(is_active=True).count()
        
        # 注文統計
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        
        # 在庫アラート
        low_stock = Textbook.get_low_stock_textbooks()
        out_of_stock = Textbook.get_out_of_stock_textbooks()
        
        # 最近の注文
        recent_orders = Order.query.order_by(Order.ordered_at.desc()).limit(5).all()
        recent_orders_data = [order.to_dict() for order in recent_orders]
        
        return create_success_response({
            'stats': {
                'total_schools': total_schools,
                'total_students': total_students,
                'total_textbooks': total_textbooks,
                'total_orders': total_orders,
                'pending_orders': pending_orders
            },
            'inventory_alerts': {
                'low_stock_count': len(low_stock),
                'out_of_stock_count': len(out_of_stock),
                'low_stock_items': [tb.to_dict() for tb in low_stock[:5]],
                'out_of_stock_items': [tb.to_dict() for tb in out_of_stock[:5]]
            },
            'recent_orders': recent_orders_data
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch dashboard stats: {str(e)}', status_code=500)