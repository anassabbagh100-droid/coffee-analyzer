from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Measurement(db.Model):
    """Model for coffee measurement data including NIR readings and estimated CO2"""
    __tablename__ = 'measurements'
    
    id = db.Column(db.Integer, primary_key=True)
    device_serial = db.Column(db.String(32), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # NIR sensor data (stored as JSON)
    nir_data = db.Column(db.Text, nullable=False)  # JSON string containing NIR channel readings
    
    # Estimated values
    estimated_co2 = db.Column(db.Float, nullable=True)  # CO2 estimate in ppm
    estimated_protein = db.Column(db.Float, nullable=True) # New field for estimated protein
    estimated_amino_acids = db.Column(db.Float, nullable=True) # New field for estimated amino acids
    estimated_minerals = db.Column(db.Float, nullable=True) # New field for estimated minerals
    estimated_flavor_compounds = db.Column(db.Float, nullable=True) # New field for estimated flavor compounds
    estimated_moisture = db.Column(db.Float, nullable=True) # New field for estimated moisture
    
    # Sample information
    sample_name = db.Column(db.String(120), nullable=True)
    sample_type = db.Column(db.String(120), nullable=True)
    coffee_type = db.Column(db.Integer, nullable=True) # New field for coffee type (0: Green, 1: Roasted, 2: Ground)
    coffee_origin = db.Column(db.Integer, nullable=True) # New field for coffee origin
    
    # Additional metadata
    measurement_mode = db.Column(db.Integer, default=0)  # Operating mode when measurement was taken
    quality_score = db.Column(db.Float, nullable=True)   # Quality assessment score (0-100)
    notes = db.Column(db.Text, nullable=True)            # User notes or additional information
    
    # Analysis results (if available)
    analysis_results = db.Column(db.Text, nullable=True)  # JSON string for detailed analysis
    
    def __repr__(self):
        return f'<Measurement {self.device_serial}: {self.sample_name or "Unknown"} at {self.timestamp}>'
    
    def to_dict(self):
        """Convert measurement object to dictionary"""
        nir_data_dict = {}
        analysis_results_dict = {}
        
        try:
            nir_data_dict = json.loads(self.nir_data) if self.nir_data else {}
        except:
            nir_data_dict = {}
            
        try:
            analysis_results_dict = json.loads(self.analysis_results) if self.analysis_results else {}
        except:
            analysis_results_dict = {}
            
        return {
            'id': self.id,
            'device_serial': self.device_serial,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'nir_data': nir_data_dict,
            'estimated_co2': self.estimated_co2,
            'estimated_protein': self.estimated_protein,
            'estimated_amino_acids': self.estimated_amino_acids,
            'estimated_minerals': self.estimated_minerals, # Include minerals
            'estimated_flavor_compounds': self.estimated_flavor_compounds, # Include flavor compounds
            'estimated_moisture': self.estimated_moisture, # Include moisture
            'sample_name': self.sample_name,
            'sample_type': self.sample_type,
            'coffee_type': self.coffee_type, # Include coffee type
            'coffee_origin': self.coffee_origin, # Include coffee origin
            'measurement_mode': self.measurement_mode,
            'quality_score': self.quality_score,
            'notes': self.notes,
            'analysis_results': analysis_results_dict
        }
    
    @property
    def nir_channels(self):
        """Get NIR channel data as dictionary"""
        try:
            return json.loads(self.nir_data) if self.nir_data else {}
        except:
            return {}
    
    @nir_channels.setter
    def nir_channels(self, value):
        """Set NIR channel data from dictionary"""
        self.nir_data = json.dumps(value) if value else '{}'
    
    @property
    def analysis(self):
        """Get analysis results as dictionary"""
        try:
            return json.loads(self.analysis_results) if self.analysis_results else {}
        except:
            return {}
    
    @analysis.setter
    def analysis(self, value):
        """Set analysis results from dictionary"""
        self.analysis_results = json.dumps(value) if value else '{}'
    
    def get_nir_channel(self, channel_index):
        """Get specific NIR channel value"""
        nir_data = self.nir_channels
        return nir_data.get(f'channel{channel_index}', 0)
    
    def set_nir_channel(self, channel_index, value):
        """Set specific NIR channel value"""
        nir_data = self.nir_channels
        nir_data[f'channel{channel_index}'] = value
        self.nir_channels = nir_data
    
    @classmethod
    def create_from_esp32_data(cls, data):
        """Create measurement from ESP32 JSON data"""
        measurement = cls()
        measurement.device_serial = data.get('device_serial', '')
        measurement.nir_channels = data.get('nir_readings', {})
        measurement.estimated_co2 = data.get('estimated_co2')
        measurement.estimated_protein = data.get('estimated_protein')
        measurement.estimated_amino_acids = data.get('estimated_amino_acids')
        measurement.estimated_minerals = data.get('estimated_minerals') # Extract minerals
        measurement.estimated_flavor_compounds = data.get('estimated_flavor_compounds') # Extract flavor compounds
        measurement.estimated_moisture = data.get('estimated_moisture') # Extract moisture
        
        sample_info = data.get('sample_info', {})
        measurement.sample_name = sample_info.get('name')
        measurement.sample_type = sample_info.get('type')
        measurement.coffee_type = data.get('coffee_type') # Extract coffee type
        measurement.coffee_origin = data.get('coffee_origin') # Extract coffee origin
        
        # Parse timestamp if provided
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            try:
                measurement.timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                measurement.timestamp = datetime.utcnow()
        else:
            measurement.timestamp = datetime.utcnow()
        
        return measurement






