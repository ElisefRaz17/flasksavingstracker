from flask import Flask, request, jsonify
from flask_cors import CORS
from database import supabase
import logging
import jwt
from functools import wraps
from flask_marshmallow import Marshmallow
import os
from schemas.goals import GoalSchema

app = Flask(__name__)
ma = Marshmallow(app)
CORS(app)

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
goal_schema = GoalSchema()
logging.basicConfig(level=logging.ERROR)
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization'].split(" ")
            if len(auth_header) == 2 and auth_header[0] == "Bearer":
                token = auth_header[1]
        if not token:
            return jsonify({"message":"Missing authentication token"}), 401
        try:
            payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
            request.user_id = payload.get("sub")
        except jwt.ExpiredSignatureError:
            return jsonify({"message":"Token has expired"}),401
        except jwt.InvalidTokenError:
            return jsonify({"message":"Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated
@app.errorhandler(Exception)
def handle_exception(e):
    # Pass the actual error message to the logs
    app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
    # Return a clean JSON response instead of a generic 500
    return jsonify(error="Internal Server Error", message=str(e)), 500
# CREATE
@app.route('/api/users', methods=['POST'])
def create_item():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name', '')
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    try:
        # Register the user in Supabase Auth
        # You can pass additional metadata like full_name into the data dictionary
        user = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name}
            }
        })
        
        return jsonify({"message": "User registered successfully!", "user": user.user.id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# READ (All)
@app.route('/api/users', methods=['GET'])
def get_items():
    response = supabase.table("Users").select("*").execute()
    return jsonify(response.data), 200

# READ (Single)
@app.route('/api/users/<item_id>', methods=['GET'])
def get_item(item_id):
    response = supabase.table("Users").select("*").eq("id", item_id).execute()
    if not response.data:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(response.data[0]), 200
@require_auth
@app.route('/api/goals', methods=['POST'])
def create_goal():
    data = request.json
    response = supabase.table("Goals").insert({
        "name": data['name'],
        "deadline": data.get('deadline'), # Optional
        "target_amount": data['target_amount']
    }).execute()
    
    return jsonify(response.data), 201
@require_auth
@app.route('/api/deposit',methods=['POST'])
def add_deposit():
    data = request.json
    response = supabase.table("Deposits").insert({
        "goal_id": data['goal_id'],
        "user_id":data['user_id'],
        "amount":data["amount"],
        "note":data.get("note")
    }).execute()
    return jsonify(response.data), 201
    
if __name__ == '__main__':
    app.run(debug=True)
