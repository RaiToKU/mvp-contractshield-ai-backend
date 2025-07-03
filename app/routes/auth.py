from flask import Blueprint, request, jsonify

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    # 登录逻辑
    return jsonify({'message': 'Login successful'})

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    # 刷新 token 逻辑
    return jsonify({'message': 'Token refreshed'})