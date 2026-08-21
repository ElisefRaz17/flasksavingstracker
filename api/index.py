from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from database import supabase
import logging
import jwt
from functools import wraps
from flask_marshmallow import Marshmallow
import os
from schemas.goals import GoalSchema

app = Flask(__name__)
ma = Marshmallow(app)
FRONTEND_ORIGINS = ["https://angularsavingstracker.vercel.app", "http://localhost:4200"]
CORS(app, supports_credentials=True, origins=FRONTEND_ORIGINS)
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 days

def set_refresh_cookie(response, access_token):
    # response.set_cookie(
    #     "refresh_token",
    #     refresh_token,
    #     httponly=True,
    #     secure=True,
    #     samesite="None",
    #     max_age=REFRESH_COOKIE_MAX_AGE,
    #     path="/api",
    # )
        response.set_cookie(
        "sb_access_token",
        access_token,
        httponly=True,
        secure=True,
        samesite="Lax"
    )


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")
# Supabase projects on the newer API key system sign tokens with an
# asymmetric key (ES256/RS256) instead of the legacy shared HS256 secret.
# PyJWKClient fetches/caches the current public signing key(s) so tokens
# verify correctly regardless of which signing method the project uses.
_jwks_client = jwt.PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json") if SUPABASE_URL else None
goal_schema = GoalSchema()
logging.basicConfig(level=logging.ERROR)
@app.route('/api/login-handler', methods=['POST'])
def login_handler():
    data = request.get_json(silent=True) or {}
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    if not access_token or not refresh_token:
        return jsonify({"error": "Access token and refresh token are required"}), 400

    response = jsonify({
        "status": "success",
        "message": "Session handled securely on backend"
    })
    set_refresh_cookie(response, access_token)
    return response, 200

@app.route('/api/refresh-session', methods=['GET'])
def refresh_session():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({"error": "No refresh token"}), 401

    try:
        auth_response = supabase.auth.refresh_session(refresh_token)
        session = auth_response.session
    except Exception:
        session = None
    if not session:
        return jsonify({"error": "Invalid or expired refresh token"}), 401

    response = jsonify({
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
    })
    set_refresh_cookie(response, session.refresh_token)
    return response, 200

@app.route('/api/logout', methods=['POST'])
def logout_handler():
    response = jsonify({"status": "success"})
    response.delete_cookie("refresh_token", path="/api")
    return response, 200

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        parts = auth_header.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1]:
            token = parts[1].strip()
        if not token:
            return jsonify({"message":"Missing authentication token"}), 401
        try:
            alg = jwt.get_unverified_header(token).get("alg")
            if alg == "HS256":
                signing_key = SUPABASE_JWT_SECRET
            elif _jwks_client:
                signing_key = _jwks_client.get_signing_key_from_jwt(token).key
            else:
                raise jwt.InvalidTokenError("No signing key available")
            payload = jwt.decode(token, signing_key, algorithms=["HS256", "ES256", "RS256"], audience="authenticated")
            request.user_id = payload.get("sub")
        except jwt.ExpiredSignatureError:
            return jsonify({"message":"Token has expired"}),401
        except jwt.InvalidTokenError:
            return jsonify({"message":"Invalid token"}), 401
        # Authenticate the Supabase client as this user so RLS policies apply
        supabase.postgrest.auth(token)
        return f(*args, **kwargs)
    return decorated
@app.errorhandler(Exception)
def handle_exception(e):
    # Let normal HTTP errors (404, 400, 401, ...) pass through unchanged;
    # only rewrite genuine unhandled exceptions as a clean 500 JSON body.
    if isinstance(e, HTTPException):
        return e
    app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
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
@app.route('/api/goals', methods=['POST'])
@require_auth
def create_goal():
    try:
        data = request.json
        response = supabase.table("Goals").insert({
            "name": data['name'],
            "deadline": data.get('deadline'), # Optional
            "target_amount": data['target_amount'],
            "user_id": request.user_id
        }).execute()

        return jsonify(response.data), 201
    except Exception as e:
        return jsonify({"error":str(e)}), 400

@app.route('/api/goals', methods=['GET'])
@require_auth
def get_goals():
    try:
        response = supabase.table("Goals").select("*").eq("user_id", request.user_id).execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error":f"Invalid session: {str(e)}"}),403

@app.route('/api/deposit', methods=['GET'])
@require_auth
def get_deposits():
    try:
        response = supabase.table("Deposits").select("*").eq("user_id", request.user_id).execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error":f"Invalid session: {str(e)}"}),403


@app.route('/api/deposit/<goal_id>',methods=["GET"])
@require_auth
def get_goal_deposits(goal_id):
    response = supabase.table("Deposits").select("*").eq("goal_id", goal_id).eq("user_id", request.user_id).execute()
    if not response.data:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(response.data), 200

@app.route('/api/goals/<goal_id>',methods=["PUT"])
@require_auth
def update_goal(goal_id):
    data = request.json
    if not data:
        return jsonify({"error":"No data provided"}), 400
    try:
        response = supabase.table("Goals").update({
        "name": data['name'],
        "deadline": data.get('deadline'), # Optional
        "target_amount": data['target_amount'],
        }).eq("id", goal_id).eq("user_id", request.user_id).execute()
        if response.data:
            return jsonify({"message":"Goal updated successfully","data":response.data}),200
        else:
            return jsonify({"error":"Item not found or no changes made"}),404
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@app.route('/api/goals/<goal_id>',methods=["DELETE"])
@require_auth
def delete_goal(goal_id):
    try:
        response = supabase.table("Goals").delete().eq("id",goal_id).eq("user_id", request.user_id).execute()
        if response.data:
            return jsonify({"message":"Goal deleted successfully","goal_id":response.data}),200
        else:
            return jsonify({"error":"Item not found"}),404
    except Exception as e:
        return jsonify({"error":str(e)}), 500


@app.route('/api/deposit',methods=['POST'])
@require_auth
def add_deposit():
    data = request.json
    response = supabase.table("Deposits").insert({
        "goal_id": data['goal_id'],
        "user_id": request.user_id,
        "amount":data["amount"],
        "note":data.get("note")
    }).execute()
    return jsonify(response.data), 201
    
if __name__ == '__main__':
    app.run(debug=True)
