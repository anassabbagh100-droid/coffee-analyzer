from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class BlendProfile(db.Model):
    """Model for coffee blend profiles (reference blends)"""
    __tablename__ = 'blend_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(32), nullable=False, index=True)
    profile_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, default='')
    sample_count = db.Column(db.Integer, default=0)
    profile_signature = db.Column(db.Text, default='{}')  # JSON string with average readings and statistics
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with samples
    samples = db.relationship('BlendSample', backref='profile', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BlendProfile {self.profile_name} for {self.device_id}>'
    
    def to_dict(self):
        """Convert profile object to dictionary"""
        signature_dict = {}
        try:
            signature_dict = json.loads(self.profile_signature) if self.profile_signature else {}
        except:
            signature_dict = {}
            
        return {
            'id': self.id,
            'device_id': self.device_id,
            'profile_name': self.profile_name,
            'description': self.description,
            'sample_count': self.sample_count,
            'profile_signature': signature_dict,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class BlendSample(db.Model):
    """Model for individual coffee samples within a blend profile"""
    __tablename__ = 'blend_samples'
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('blend_profiles.id'), nullable=False)
    sample_name = db.Column(db.String(100), default='')
    sensor_reading_1 = db.Column(db.Float, default=0.0)
    sensor_reading_2 = db.Column(db.Float, default=0.0)
    sensor_reading_3 = db.Column(db.Float, default=0.0)
    chemical_data = db.Column(db.Text, default='{}')  # JSON string with chemical analysis if available
    notes = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BlendSample {self.sample_name} in profile {self.profile_id}>'
    
    def to_dict(self):
        """Convert sample object to dictionary"""
        chemical_data_dict = {}
        try:
            chemical_data_dict = json.loads(self.chemical_data) if self.chemical_data else {}
        except:
            chemical_data_dict = {}
            
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'sample_name': self.sample_name,
            'sensor_reading_1': self.sensor_reading_1,
            'sensor_reading_2': self.sensor_reading_2,
            'sensor_reading_3': self.sensor_reading_3,
            'chemical_data': chemical_data_dict,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def sensor_readings_array(self):
        """Get sensor readings as array for calculations"""
        return [self.sensor_reading_1, self.sensor_reading_2, self.sensor_reading_3]

