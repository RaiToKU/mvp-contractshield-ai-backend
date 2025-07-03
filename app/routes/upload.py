from flask import Blueprint, request, jsonify

upload_bp = Blueprint('upload_bp', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    # 文件上传逻辑
    return jsonify({'message': 'File uploaded'})

@upload_bp.route('/export/<file_id>', methods=['GET'])
def export_file(file_id):
    # 文件导出逻辑
    return jsonify({'message': f'Exporting file {file_id}'})