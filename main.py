# from flask import Flask, jsonify
# from supabase import create_client, Client
# import os
# from dotenv import load_dotenv

# # Load environment variables (useful for local development)
# load_dotenv()

# app = Flask(__name__)

# # Fetch Supabase credentials
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# # Initialize Supabase Client
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# @app.route("/")
# def home():
#     return jsonify({"status": "online", "message": "Connected to Supabase on Vercel"})

# @app.route("/data")
# def get_data():
#     try:
#         response = supabase.table("Users").select("*").execute()
#         return jsonify(response.data)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=5001)
    
from __init__ import create_app
from flask_cors import CORS

app = create_app()
CORS(app, resources={r"/*": {"origins": "https://localhost:4200"}})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
