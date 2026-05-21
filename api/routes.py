from flask import Blueprint, request, jsonify
from .supabase_client import supabase

api_bp = Blueprint('api', __name__)

@api_bp.route('/users/create', methods=['POST'])
def create_item():
    data = request.json
    response = supabase.table('Users').insert(data).execute()
    return jsonify(response.data), 201

@api_bp.route('/users', methods=['GET'])
def get_items():
    response = supabase.table('Users').select("*").execute()
    return jsonify(response.data), 200

@api_bp.route('/items/<id>', methods=['PUT'])
def update_item(id):
    data = request.json
    response = supabase.table('Users').update(data).eq('id', id).execute()
    return jsonify(response.data), 200

@api_bp.route('/items/<id>', methods=['DELETE'])
def delete_item(id):
    response = supabase.table('Users').delete().eq('id', id).execute()
    return jsonify({"message": "Deleted successfully"}), 200
