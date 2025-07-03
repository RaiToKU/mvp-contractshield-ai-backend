from flask import Blueprint, request, jsonify

billing_bp = Blueprint('billing_bp', __name__)

@billing_bp.route('/stripe', methods=['POST'])
def stripe_webhook():
    # Stripe webhook 逻辑
    return jsonify({'status': 'success'})