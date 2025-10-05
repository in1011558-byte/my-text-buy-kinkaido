from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields

from models import db
from models.textbook import Textbook
from models.category import Category
from utils.auth import create_error_response, create_success_response

textbooks_bp = Blueprint('textbooks', __name__)

@textbooks_bp.route('', methods=['GET'])
@jwt_required()
def get_textbooks():
    """教科書一覧取得（フィルター機能付き）"""
    try:
        # クエリパラメータ取得
        category_id = request.args.get('category_id', type=int)
        grade_level = request.args.get('grade_level')
        subject = request.args.get('subject')
        in_stock_only = request.args.get('in_stock_only', 'true').lower() == 'true'
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 検索クエリ構築（キーワード検索は削除）
        textbooks_query = Textbook.search(
            category_id=category_id,
            grade_level=grade_level,
            subject=subject,
            in_stock_only=in_stock_only
        )
        
        # ページネーション
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

@textbooks_bp.route('/<int:textbook_id>', methods=['GET'])
@jwt_required()
def get_textbook(textbook_id):
    """教科書詳細取得"""
    try:
        textbook = Textbook.query.get(textbook_id)
        
        if not textbook or not textbook.is_active:
            return create_error_response('TEXTBOOK_NOT_FOUND', 'Textbook not found', status_code=404)
        
        textbook_data = textbook.to_dict()
        
        return create_success_response({'textbook': textbook_data})
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch textbook: {str(e)}', status_code=500)

@textbooks_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """カテゴリ一覧取得"""
    try:
        categories = Category.get_active_categories()
        categories_data = [category.to_dict() for category in categories]
        
        return create_success_response({
            'categories': categories_data,
            'total': len(categories_data)
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch categories: {str(e)}', status_code=500)

@textbooks_bp.route('/filters', methods=['GET'])
@jwt_required()
def get_filter_options():
    """フィルターオプション取得（学年・科目の選択肢）"""
    try:
        # 学年の選択肢
        grade_levels = db.session.query(Textbook.grade_level).filter(
            Textbook.is_active == True,
            Textbook.grade_level.isnot(None)
        ).distinct().all()
        
        # 科目の選択肢
        subjects = db.session.query(Textbook.subject).filter(
            Textbook.is_active == True,
            Textbook.subject.isnot(None)
        ).distinct().all()
        
        grade_levels_list = [grade[0] for grade in grade_levels if grade[0]]
        subjects_list = [subject[0] for subject in subjects if subject[0]]
        
        return create_success_response({
            'grade_levels': sorted(grade_levels_list),
            'subjects': sorted(subjects_list)
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch filter options: {str(e)}', status_code=500)