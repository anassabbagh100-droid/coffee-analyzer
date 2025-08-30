from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        # Import models here to ensure they are registered with SQLAlchemy
        from src.models.user import User
        from src.models.device import Device
        from src.models.device_report import DeviceReport
        from src.models.blend_profile import BlendProfile, BlendSample
        from src.models.measurement import Measurement
        from src.models.knowledge_entry import KnowledgeEntry # Import new KnowledgeEntry model
        from src.models.calibration_data import CalibrationData # Import new CalibrationData model
        db.create_all() # Create database tables for all models

        # Register blueprints
        from src.routes.activation import activation_bp
        from src.routes.reports import reports_bp
        from src.routes.measurements import measurements_bp
        from src.routes.knowledge import knowledge_bp # Import new knowledge blueprint
        from src.routes.calibration import calibration_bp # Import new calibration blueprint

        app.register_blueprint(activation_bp, url_prefix='/api/activation')
        app.register_blueprint(reports_bp, url_prefix='/api/reports')
        app.register_blueprint(measurements_bp, url_prefix='/api/measurements')
        app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge') # Register new knowledge blueprint
        app.register_blueprint(calibration_bp, url_prefix='/api/calibration') # Register new calibration blueprint

    return app


