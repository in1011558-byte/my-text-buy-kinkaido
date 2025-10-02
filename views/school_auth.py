from flask import Blueprint

school_auth_bp = Blueprint('school_auth', __name__)

@school_auth_bp.route('/test', methods=['GET'])
def test():
    return {'message': 'School auth working'}
