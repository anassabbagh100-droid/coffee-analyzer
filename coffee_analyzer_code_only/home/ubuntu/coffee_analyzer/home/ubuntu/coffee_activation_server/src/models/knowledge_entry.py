from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class KnowledgeEntry(db.Model):
    """Model for knowledge base entries awaiting owner approval"""
    __tablename__ = 'knowledge_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    device_serial = db.Column(db.String(32), nullable=False, index=True)
    sample_name = db.Column(db.String(120), nullable=True)
    chemical_data = db.Column(db.Text, nullable=True) # JSON string of chemical values
    sensor_data = db.Column(db.Text, nullable=False) # JSON string of NIR sensor readings
    coffee_type = db.Column(db.Integer, nullable=True) # 0: Green, 1: Roasted, 2: Ground
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    approved = db.Column(db.Boolean, default=False) # Flag for owner approval
    
    def __repr__(self):
        return f'<KnowledgeEntry {self.device_serial}: {self.sample_name or "Unknown"} (Approved: {self.approved})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_serial': self.device_serial,
            'sample_name': self.sample_name,
            'chemical_data': json.loads(self.chemical_data) if self.chemical_data else {},
            'sensor_data': json.loads(self.sensor_data) if self.sensor_data else {},
            'coffee_type': self.coffee_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'approved': self.approved
        }

    @classmethod
    def create_from_esp32_data(cls, data):
        entry = cls()
        entry.device_serial = data.get('device_id', '')
        entry.sample_name = data.get('sample_name')
        entry.chemical_data = json.dumps(data.get('chemical_data', {}))
        entry.sensor_data = json.dumps(data.get('sensor_data', {}))
        entry.coffee_type = data.get('coffee_type')
        
        timestamp_str = data.get('timestamp')
        if timestamp_str:
            try:
                entry.timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                entry.timestamp = datetime.utcnow()
        else:
            entry.timestamp = datetime.utcnow()
        
        entry.approved = data.get('approved', False) # Default to false, owner must approve
        return entry


