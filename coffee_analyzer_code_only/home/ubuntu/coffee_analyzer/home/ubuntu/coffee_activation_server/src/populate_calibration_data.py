import os
import sys

# Add the parent directory to the sys.path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import create_app
from src.models.user import db # Import db directly
from src.models.calibration_data import CalibrationData

# Define Enums to match ESP32 code
class CoffeeType:
    COFFEE_GREEN = 0
    COFFEE_ROASTED = 1
    COFFEE_GROUND = 2
    COFFEE_UNKNOWN_TYPE = 3

class CoffeeOrigin:
    ORIGIN_UNKNOWN = 0
    ORIGIN_BRAZIL = 1
    ORIGIN_COLOMBIA = 2
    ORIGIN_COSTA_RICA = 3
    ORIGIN_HONDURAS = 4
    ORIGIN_GUATEMALA = 5
    ORIGIN_INDIA = 6
    ORIGIN_INDONESIA = 7
    ORIGIN_VIETNAM = 8
    ORIGIN_PERU = 9
    ORIGIN_TANZANIA = 10
    ORIGIN_UGANDA = 11
    ORIGIN_ETHIOPIA = 12
    ORIGIN_IVORY_COAST = 13
    ORIGIN_YEMEN = 14
    ORIGIN_SCA = 15
    ORIGIN_GLOBAL_ARABICA = 16
    ORIGIN_GLOBAL_ROBUSTA = 17

app = create_app()

with app.app_context():
    # db is already initialized in create_app(), no need to call db.init_app(app) here
    # db.create_all() # Ensure tables are created if not already
    print("Starting to populate calibration data...")

    # Clear existing data (optional, for development)
    # db.session.query(CalibrationData).delete()
    # db.session.commit()

    # Helper function to add or update data
    def add_or_update_calibration_data(coffee_type, coffee_origin, coffee_variety, data):
        entry = CalibrationData.query.filter_by(
            coffee_type=coffee_type,
            coffee_origin=coffee_origin,
            coffee_variety=coffee_variety
        ).first()

        if not entry:
            entry = CalibrationData(
                coffee_type=coffee_type,
                coffee_origin=coffee_origin,
                coffee_variety=coffee_variety
            )
            db.session.add(entry)
            print(f"Adding new entry: Type {coffee_type}, Origin {coffee_origin}, Variety {coffee_variety}")
        else:
            print(f"Updating existing entry: Type {coffee_type}, Origin {coffee_origin}, Variety {coffee_variety}")

        for key, value in data.items():
            setattr(entry, key, value)
        db.session.commit()

    # --- General Arabica & Robusta (SCA / Global Averages) ---
    # These are simplified dummy values. Real values would come from extensive research.
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_GLOBAL_ARABICA,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.1,
            "co2_offset": 0.0,
            "protein_coeff": 0.05,
            "protein_offset": 0.0,
            "amino_acids_coeff": 0.02,
            "amino_acids_offset": 0.0,
            "minerals_coeff": 0.01,
            "minerals_offset": 0.0,
            "flavor_compounds_coeff": 0.03,
            "flavor_compounds_offset": 0.0,
            "moisture_coeff": 0.08,
            "moisture_offset": 0.0,
        }
    )

    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_GLOBAL_ROBUSTA,
        coffee_variety="Robusta",
        data={
            "co2_coeff": 0.12,
            "co2_offset": 0.0,
            "protein_coeff": 0.06,
            "protein_offset": 0.0,
            "amino_acids_coeff": 0.025,
            "amino_acids_offset": 0.0,
            "minerals_coeff": 0.015,
            "minerals_offset": 0.0,
            "flavor_compounds_coeff": 0.02,
            "flavor_compounds_offset": 0.0,
            "moisture_coeff": 0.09,
            "moisture_offset": 0.0,
        }
    )

    # --- Specific Countries (Simplified Dummy Data) ---
    # Brazil (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_BRAZIL,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.105,
            "protein_coeff": 0.052,
            "moisture_coeff": 0.082,
        }
    )

    # Colombia (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_COLOMBIA,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.098,
            "protein_coeff": 0.051,
            "moisture_coeff": 0.078,
        }
    )

    # Costa Rica (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_COSTA_RICA,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.095,
            "protein_coeff": 0.050,
            "moisture_coeff": 0.075,
        }
    )

    # Honduras (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_HONDURAS,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.102,
            "protein_coeff": 0.053,
            "moisture_coeff": 0.080,
        }
    )

    # Guatemala (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_GUATEMALA,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.097,
            "protein_coeff": 0.049,
            "moisture_coeff": 0.077,
        }
    )

    # India (Robusta)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_INDIA,
        coffee_variety="Robusta",
        data={
            "co2_coeff": 0.125,
            "protein_coeff": 0.065,
            "moisture_coeff": 0.095,
        }
    )

    # Indonesia (Robusta)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_INDONESIA,
        coffee_variety="Robusta",
        data={
            "co2_coeff": 0.122,
            "protein_coeff": 0.063,
            "moisture_coeff": 0.092,
        }
    )

    # Vietnam (Robusta)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_VIETNAM,
        coffee_variety="Robusta",
        data={
            "co2_coeff": 0.130,
            "protein_coeff": 0.068,
            "moisture_coeff": 0.100,
        }
    )

    # Peru (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_PERU,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.100,
            "protein_coeff": 0.050,
            "moisture_coeff": 0.079,
        }
    )

    # Tanzania (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_TANZANIA,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.103,
            "protein_coeff": 0.054,
            "moisture_coeff": 0.081,
        }
    )

    # Uganda (Robusta)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_UGANDA,
        coffee_variety="Robusta",
        data={
            "co2_coeff": 0.128,
            "protein_coeff": 0.067,
            "moisture_coeff": 0.098,
        }
    )

    # Ethiopia (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_ETHIOPIA,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.096,
            "protein_coeff": 0.048,
            "moisture_coeff": 0.076,
        }
    )

    # Ivory Coast (Robusta)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_IVORY_COAST,
        coffee_variety="Robusta",
        data={
            "co2_coeff": 0.127,
            "protein_coeff": 0.066,
            "moisture_coeff": 0.097,
        }
    )

    # Yemen (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_YEMEN,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.101,
            "protein_coeff": 0.052,
            "moisture_coeff": 0.079,
        }
    )

    # SCA General (Arabica)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_SCA,
        coffee_variety="Arabica",
        data={
            "co2_coeff": 0.099,
            "protein_coeff": 0.050,
            "moisture_coeff": 0.078,
        }
    )

    # Default Unknown Type/Origin (Fallback)
    add_or_update_calibration_data(
        coffee_type=CoffeeType.COFFEE_UNKNOWN_TYPE,
        coffee_origin=CoffeeOrigin.ORIGIN_UNKNOWN,
        coffee_variety="Unknown",
        data={
            "co2_coeff": 0.1,
            "co2_offset": 0.0,
            "protein_coeff": 0.05,
            "protein_offset": 0.0,
            "amino_acids_coeff": 0.02,
            "amino_acids_offset": 0.0,
            "minerals_coeff": 0.01,
            "minerals_offset": 0.0,
            "flavor_compounds_coeff": 0.03,
            "flavor_compounds_offset": 0.0,
            "moisture_coeff": 0.08,
            "moisture_offset": 0.0,
        }
    )

    print("Calibration data population complete.")


