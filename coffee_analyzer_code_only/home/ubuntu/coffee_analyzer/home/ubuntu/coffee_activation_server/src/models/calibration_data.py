from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class CalibrationData(db.Model):
    """Model for storing reference chemical composition data for coffee calibration."""
    __tablename__ = 'calibration_data'

    id = db.Column(db.Integer, primary_key=True)
    coffee_type = db.Column(db.Integer, nullable=False) # 0: Green, 1: Roasted, 2: Ground
    coffee_origin = db.Column(db.Integer, nullable=False) # Enum for origin (e.g., Brazil, Colombia)
    coffee_variety = db.Column(db.String(50), nullable=True) # Arabica, Robusta

    # Chemical composition values (example fields, expand as needed)
    co2_coeff = db.Column(db.Float, nullable=True)
    co2_offset = db.Column(db.Float, nullable=True)
    protein_coeff = db.Column(db.Float, nullable=True)
    protein_offset = db.Column(db.Float, nullable=True)
    amino_acids_coeff = db.Column(db.Float, nullable=True)
    amino_acids_offset = db.Column(db.Float, nullable=True)
    minerals_coeff = db.Column(db.Float, nullable=True)
    minerals_offset = db.Column(db.Float, nullable=True)
    flavor_compounds_coeff = db.Column(db.Float, nullable=True)
    flavor_compounds_offset = db.Column(db.Float, nullable=True)
    moisture_coeff = db.Column(db.Float, nullable=True)
    moisture_offset = db.Column(db.Float, nullable=True)

    # Add more fields for other chemical components as needed
    # e.g., caffeine_coeff, caffeine_offset, chlorogenic_acid_coeff, etc.

    def __repr__(self):
        return f'<CalibrationData Type:{self.coffee_type} Origin:{self.coffee_origin} Variety:{self.coffee_variety}>'

    def to_dict(self):
        return {
            'id': self.id,
            'coffee_type': self.coffee_type,
            'coffee_origin': self.coffee_origin,
            'coffee_variety': self.coffee_variety,
            'co2_coeff': self.co2_coeff,
            'co2_offset': self.co2_offset,
            'protein_coeff': self.protein_coeff,
            'protein_offset': self.protein_offset,
            'amino_acids_coeff': self.amino_acids_coeff,
            'amino_acids_offset': self.amino_acids_offset,
            'minerals_coeff': self.minerals_coeff,
            'minerals_offset': self.minerals_offset,
            'flavor_compounds_coeff': self.flavor_compounds_coeff,
            'flavor_compounds_offset': self.flavor_compounds_offset,
            'moisture_coeff': self.moisture_coeff,
            'moisture_offset': self.moisture_offset,
        }


