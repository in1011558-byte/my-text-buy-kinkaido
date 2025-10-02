from flask import Blueprint

textbooks_bp = Blueprint('textbooks', __name__)

@textbooks_bp.route('/test', methods=['GET'])
def test():
    return {'message': 'Textbooks working'}
