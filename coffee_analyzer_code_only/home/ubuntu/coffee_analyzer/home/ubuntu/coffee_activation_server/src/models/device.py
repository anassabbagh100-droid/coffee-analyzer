from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Device(db.Model):
    """Model for coffee analyzer devices"""
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(32), unique=True, nullable=False, index=True)  # Old device_id for backward compatibility
    device_serial = db.Column(db.String(32), unique=True, nullable=False, index=True)  # New R3S-YYYYMMDD-XXXXXX format
    device_name = db.Column(db.String(100), default='')
    activation_level = db.Column(db.String(20), default='basic')  # basic, professional, advanced, custom, blend_profiles
    activation_key = db.Column(db.String(64), default='')
    
    # Manufacturing and operational dates
    manufacture_date = db.Column(db.Date, nullable=True)  # Date of manufacture (can be set manually)
    first_boot_date = db.Column(db.DateTime, nullable=True)  # First time device was powered on
    first_internet_date = db.Column(db.DateTime, nullable=True)  # First time device connected to internet
    
    # System timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When device was registered on server
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)  # Last communication with server
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Device {self.device_serial}: {self.device_name}>'
    
    def to_dict(self):
        """Convert device object to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'device_serial': self.device_serial,
            'device_name': self.device_name,
            'activation_level': self.activation_level,
            'activation_key': self.activation_key,
            'manufacture_date': self.manufacture_date.isoformat() if self.manufacture_date else None,
            'first_boot_date': self.first_boot_date.isoformat() if self.first_boot_date else None,
            'first_internet_date': self.first_internet_date.isoformat() if self.first_internet_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def generate_device_id():
        """Generate a unique device ID (for backward compatibility)"""
        return str(uuid.uuid4()).replace('-', '')[:16]
    
    @staticmethod
    def parse_serial_date(device_serial):
        """Extract date from device serial (R3S-YYYYMMDD-XXXXXX)"""
        try:
            parts = device_serial.split('-')
            if len(parts) >= 2 and parts[0] == 'R3S':
                date_str = parts[1]
                if len(date_str) == 8:
                    year = int(date_str[:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    return datetime(year, month, day).date()
        except:
            pass
        return None

