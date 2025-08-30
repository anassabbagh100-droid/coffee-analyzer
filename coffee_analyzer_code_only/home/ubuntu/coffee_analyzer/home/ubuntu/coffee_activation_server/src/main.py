import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.models.device import Device
from src.models.device_report import DeviceReport
from src.models.blend_profile import BlendProfile, BlendSample
from src.models.measurement import Measurement # Import the new Measurement model
from src.routes.user import user_bp
from src.routes.activation import activation_bp
from src.routes.reports import reports_bp
from src.routes.blend_profiles import blend_profiles_bp
from src.routes.measurements import measurements_bp # Import the new measurements blueprint
from src.routes.calibration import calibration_bp # Import the new calibration blueprint

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

    # Enable CORS for all routes
    CORS(app)

    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(activation_bp, url_prefix='/api/activation')
    app.register_blueprint(reports_bp, url_prefix='/api/activation')
    app.register_blueprint(blend_profiles_bp, url_prefix='/api/blend')
    app.register_blueprint(measurements_bp, url_prefix='/api') # Register the new measurements blueprint
    app.register_blueprint(calibration_bp, url_prefix='/api/calibration') # Register the new calibration blueprint

    # uncomment if you need to use database
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
                return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "index.html not found", 404
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)


