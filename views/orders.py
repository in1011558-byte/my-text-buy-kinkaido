from flask import Blueprint

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/test', methods=['GET'])
def test():
    return {'message': 'Orders working'}
