from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from marshmallow import Schema, fields, validates, ValidationError
from datetime import datetime

from models import db
from models.school import School
from models.school_auth import SchoolAuth
from utils.auth import create_error_response, create_success_response

school_auth_bp = Blueprint('school_auth', __name__)

# スキーマ定義
class SchoolLoginSchema(Schema):
    """学校ログイン用スキーマ"""
    login_id = fields.Str(required=True)
    password = fields.Str(required=True)

school_login_schema = SchoolLoginSchema()

@school_auth_bp.route('/login', methods=['POST'])
def school_login():
    """学校アカウントでログイン"""
    try:
        json_data = request.get_json()
        if not json_data:
            return create_error_response('INVALID_INPUT', 'No input data provided')
        
        data = school_login_schema.load(json_data)
        
    except ValidationError as e:
        return create_error_response('VALIDATION_ERROR', 'Validation failed', e.messages, 422)
    except Exception as e:
        return create_error_response('INVALID_INPUT', 'Invalid input data')
    
    try:
        # 学校認証情報を検索
        school_auth = SchoolAuth.find_by_login_id(data['login_id'])
        
        # 認証チェック
        if not school_auth or not school_auth.check_password(data['password']):
            return create_error_response('INVALID_CREDENTIALS', 'Invalid login ID or password', status_code=401)
        
        # アクティブチェック
        if not school_auth.is_active or not school_auth.school.is_active:
            return create_error_response('SCHOOL_INACTIVE', 'School account is inactive', status_code=401)
        
        # JWTトークン生成（school_idを保存）
        access_token = create_access_token(
            identity=school_auth.school_id,
            additional_claims={'type': 'school', 'auth_id': school_auth.auth_id}
        )
        refresh_token = create_refresh_token(identity=school_auth.school_id)
        
        # レスポンスデータ
        school_data = {
            'school_id': school_auth.school.school_id,
            'school_name': school_auth.school.school_name,
            'prefecture': school_auth.school.prefecture,
            'city': school_auth.school.city,
            'login_id': school_auth.login_id
        }
        
        return create_success_response({
            'message': 'Login successful',
            'school': school_data,
            'access_token': access_token,
            'refresh_token': refresh_token
        })
        
    except Exception as e:
        return create_error_response('LOGIN_FAILED', f'Login failed: {str(e)}', status_code=500)

@school_auth_bp.route('/info', methods=['GET'])
@jwt_required()
def get_school_info():
    """ログイン中の学校情報を取得"""
    try:
        school_id = get_jwt_identity()
        
        school = School.query.get(school_id)
        if not school or not school.is_active:
            return create_error_response('SCHOOL_NOT_FOUND', 'School not found or inactive', status_code=404)
        
        school_data = school.to_dict()
        
        return create_success_response({'school': school_data})
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch school info: {str(e)}', status_code=500)

@school_auth_bp.route('/schools', methods=['GET'])
def get_active_schools():
    """有効な学校一覧を取得（ログイン画面用）"""
    try:
        schools = School.get_active_schools()
        schools_data = [{
            'school_id': school.school_id,
            'school_name': school.school_name,
            'prefecture': school.prefecture,
            'city': school.city
        } for school in schools]
        
        return create_success_response({
            'schools': schools_data,
            'total': len(schools_data)
        })
        
    except Exception as e:
        return create_error_response('FETCH_FAILED', f'Failed to fetch schools: {str(e)}', status_code=500)