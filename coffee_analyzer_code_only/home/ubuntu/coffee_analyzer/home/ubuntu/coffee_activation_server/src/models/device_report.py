from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class DeviceReport(db.Model):
    """Model for device operation reports"""
    __tablename__ = 'device_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(32), nullable=False, index=True)
    measurement_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    uptime_hours = db.Column(db.Float, default=0.0)
    wifi_signal = db.Column(db.Integer, default=0)  # RSSI value
    free_heap = db.Column(db.Integer, default=0)    # Available memory
    current_mode = db.Column(db.Integer, default=0) # Operating mode
    additional_data = db.Column(db.Text, default='{}')  # JSON string for extra data
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<DeviceReport {self.device_id}: {self.measurement_count} measurements, {self.error_count} errors>'
    
    def to_dict(self):
        """Convert report object to dictionary"""
        additional_data_dict = {}
        try:
            additional_data_dict = json.loads(self.additional_data) if self.additional_data else {}
        except:
            additional_data_dict = {}
            
        return {
            'id': self.id,
            'device_id': self.device_id,
            'measurement_count': self.measurement_count,
            'error_count': self.error_count,
            'uptime_hours': self.uptime_hours,
            'wifi_signal': self.wifi_signal,
            'free_heap': self.free_heap,
            'current_mode': self.current_mode,
            'additional_data': additional_data_dict,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def error_rate(self):
        """Calculate error rate as percentage"""
        if self.measurement_count == 0:
            return 0.0
        return round((self.error_count / self.measurement_count) * 100, 2)
    
    @property
    def health_status(self):
        """Determine device health based on error rate and other factors"""
        if self.error_rate > 5:
            return "يحتاج صيانة"
        elif self.error_rate > 2:
            return "جيد"
        elif self.wifi_signal < -70:
            return "إشارة ضعيفة"
        else:
            return "ممتاز"

