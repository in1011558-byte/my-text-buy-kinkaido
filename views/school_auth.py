from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.school_auth import SchoolAuth
from models.school import School
from models.user import User
from extensions import db

school_auth_bp = Blueprint('school_auth', __name__)

@school_auth_bp.route('/register', methods=['POST'])
def register_school():
    try:
        data = request.get_json()
        required_fields = ['school_name', 'prefecture', 'city', 'address', 'contact_person', 'contact_email', 'contact_phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        existing_school = School.query.filter_by(school_name=data['school_name']).first()
        if existing_school:
            return jsonify({'error': 'School already exists'}), 400
        
        school_auth = SchoolAuth(
            school_name=data['school_name'],
            prefecture=data['prefecture'],
            city=data['city'],
            address=data['address'],
            contact_person=data['contact_person'],
            contact_email=data['contact_email'],
            contact_phone=data['contact_phone'],
            registration_documents=data.get('registration_documents'),
            status='pending'
        )
        school_auth.save()
        
        return jsonify({
            'message': 'School registration request submitted successfully',
            'request_id': school_auth.id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@school_auth_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_school_requests():
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        status = request.args.get('status', 'pending')
        requests = SchoolAuth.query.filter_by(status=status).all()
        
        return jsonify([req.to_dict() for req in requests]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@school_auth_bp.route('/requests/<int:request_id>/approve', methods=['POST'])
@jwt_required()
def approve_school_request(request_id):
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        school_request = SchoolAuth.query.get(request_id)
        if not school_request:
            return jsonify({'error': 'Request not found'}), 404
        
        if school_request.status != 'pending':
            return jsonify({'error': 'Request already processed'}), 400
        
        school = School(
            school_name=school_request.school_name,
            prefecture=school_request.prefecture,
            city=school_request.city,
            address=school_request.address,
            phone=school_request.contact_phone,
            email=school_request.contact_email
        )
        school.save()
        
        school_request.status = 'approved'
        school_request.approved_by = user_id
        school_request.approved_at = db.func.now()
        school_request.save()
        
        return jsonify({
            'message': 'School request approved successfully',
            'school': school.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@school_auth_bp.route('/requests/<int:request_id>/reject', methods=['POST'])
@jwt_required()
def reject_school_request(request_id):
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        school_request = SchoolAuth.query.get(request_id)
        if not school_request:
            return jsonify({'error': 'Request not found'}), 404
        
        if school_request.status != 'pending':
            return jsonify({'error': 'Request already processed'}), 400
        
        data = request.get_json()
        rejection_reason = data.get('reason', 'No reason provided')
        
        school_request.status = 'rejected'
        school_request.rejection_reason = rejection_reason
        school_request.approved_by = user_id
        school_request.approved_at = db.func.now()
        school_request.save()
        
        return jsonify({
            'message': 'School request rejected successfully'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@school_auth_bp.route('/status/<int:request_id>', methods=['GET'])
def check_request_status(request_id):
    try:
        school_request = SchoolAuth.query.get(request_id)
        if not school_request:
            return jsonify({'error': 'Request not found'}), 404
        
        return jsonify({
            'status': school_request.status,
            'submitted_at': school_request.created_at.isoformat() if school_request.created_at else None,
            'processed_at': school_request.approved_at.isoformat() if school_request.approved_at else None,
            'rejection_reason': school_request.rejection_reason if school_request.status == 'rejected' else None
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
