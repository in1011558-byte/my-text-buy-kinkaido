from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from models.user import User
from extensions import db

auth_bp = Blueprint('auth', __name__)
blacklisted_tokens = set()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.find_by_email(email)
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.user_id)
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    blacklisted_tokens.add(jti)
    return jsonify({'message': 'Successfully logged out'}), 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    if user:
        return jsonify(user.to_dict()), 200
    return jsonify({'error': 'User not found'}), 404
