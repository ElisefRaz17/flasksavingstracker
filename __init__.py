from flask import Flask
from flask_cors import CORS
from api.routes import api_bp

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:4200"}})

    app.register_blueprint(api_bp, url_prefix='/api')
    return app
