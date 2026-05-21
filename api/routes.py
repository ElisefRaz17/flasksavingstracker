import os
from flask import Blueprint, request, jsonify
from .supabase_client import supabase

BYPASS_SECRET = os.environ.get('VERCEL_AUTOMATION_BYPASS_SECRET')

def require_bypass_token():
    # Retrieve the token from the custom header
    provided_token = request.headers.get('x-vercel-protection-bypass')
    
    if not BYPASS_SECRET or provided_token != BYPASS_SECRET:
        # Return 401 if unauthorized
        abort(401, description="Invalid or missing bypass token.")
        
api_bp = Blueprint('api', __name__)


@api_bp.route('/users/create', methods=['POST'])
def create_item():
    require_bypass_token()
    data = request.json
    response = supabase.table('Users').insert(data).execute()
    return jsonify(response.data), 201

@api_bp.route('/users', methods=['GET'])
def get_items():
    require_bypass_token()
    response = supabase.table('Users').select("*").execute()
    return jsonify(response.data), 200

@api_bp.route('/items/<id>', methods=['PUT'])
def update_item(id):
    require_bypass_token()
    data = request.json
    response = supabase.table('Users').update(data).eq('id', id).execute()
    return jsonify(response.data), 200

@api_bp.route('/items/<id>', methods=['DELETE'])
def delete_item(id):
    require_bypass_token()
    response = supabase.table('Users').delete().eq('id', id).execute()
    return jsonify({"message": "Deleted successfully"}), 200
