from flask import Flask, request, jsonify
from flask_cors import CORS
from database import supabase
import logging

app = Flask(__name__)

CORS(app)

logging.basicConfig(level=logging.ERROR)

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
@app.route('/api/login',methods=['POST'])
def login():
    data = request.get_json()
    try:
        response = supabase.auth.sign_in_with_password({
            "email": data['email'],
            "password": data['password'],
        })
        return jsonify(response.model_dump()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401
# Flask Route
@app.route('/api/reset-password', methods=['POST'])
def request_reset():
    email = request.json.get('email')
    # redirectTo must match your dashboard configuration
    res = supabase.auth.reset_password_for_email(
        email, 
        {"redirect_to": "http://localhost:4200/update-password"}
    )
    return jsonify({"message": "Reset email sent"}), 200
@app.route('/api/update-password', methods=['POST'])
def update_password():
    # Supabase requires an active session to update the password
    # In a Flask setup, you typically pass the access_token from the frontend
    # token = request.headers.get('Authorization').split("Bearer ")[1]
    # new_password = request.json.get('password')
    
    # Set the session before updating
    data = request.get_json()
    new_password = data.get('password')
    access_token = request.headers.get('Authorization') # Extracted from the Angular request header

    if not access_token:
        return jsonify({"error": "No token provided"}), 401
    supabase.auth.session().access_token = access_token.replace("Bearer ", "")
    try:
        # 1. Verify session and Update the password using Supabase Python client
        response = supabase.auth.update_user(
            {"password": new_password} )
        
        # 2. Convert the UserResponse object to a JSON-serializable dictionary
        # Note: If you are using Supabase-py <2.0, use response.dict() instead
        response_dict = response.model_dump() 
        
        return jsonify({"success": True, "data": response_dict}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

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

# UPDATE
@app.route('/api/users/<item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    response = supabase.table("Users").update(data).eq("id", item_id).execute()
    return jsonify(response.data), 200

# DELETE
@app.route('/api/users/<item_id>', methods=['DELETE'])
def delete_item(item_id):
    response = supabase.table("Users").delete().eq("id", item_id).execute()
    return jsonify({"message": "Item deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True)
