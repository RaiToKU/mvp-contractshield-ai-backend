from flask import Blueprint, request, jsonify

search_bp = Blueprint('search_bp', __name__)

@search_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    # 搜索逻辑
    return jsonify({'message': f'Search results for: {query}'})