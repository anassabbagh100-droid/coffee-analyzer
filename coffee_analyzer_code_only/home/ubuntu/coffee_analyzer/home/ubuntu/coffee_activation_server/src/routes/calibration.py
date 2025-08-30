from flask import Blueprint, request, jsonify
from src.models.calibration_data import CalibrationData, db
from src.models.user import User

calibration_bp = Blueprint("calibration", __name__)

# Helper function to check if user is owner
def is_owner(user_id):
    user = User.query.get(user_id)
    return user and user.role == "owner"

@calibration_bp.route("/calibration_data", methods=["GET"])
def get_calibration_data():
    """Retrieve calibration data based on coffee type and origin."""
    try:
        coffee_type = request.args.get("coffee_type", type=int)
        coffee_origin = request.args.get("coffee_origin", type=int)
        coffee_variety = request.args.get("coffee_variety", type=str)

        query = CalibrationData.query

        if coffee_type is not None:
            query = query.filter_by(coffee_type=coffee_type)
        if coffee_origin is not None:
            query = query.filter_by(coffee_origin=coffee_origin)
        if coffee_variety is not None:
            query = query.filter_by(coffee_variety=coffee_variety)

        calibration_entry = query.first()

        if calibration_entry:
            return jsonify({
                "success": True,
                "calibration_data": calibration_entry.to_dict()
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "لم يتم العثور على بيانات معايرة لهذا النوع والأصل."
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"خطأ في استرجاع بيانات المعايرة: {str(e)}"
        }), 500

@calibration_bp.route("/calibration_data", methods=["POST"])
def add_calibration_data():
    """Add new calibration data (Owner only)."""
    try:
        data = request.get_json()
        # For simplicity, assuming owner_id is passed in header or body for now
        # In a real app, this would be handled by authentication middleware
        owner_id = data.get("owner_id") 
        if not is_owner(owner_id):
            return jsonify({"success": False, "message": "غير مصرح به. المالك فقط يمكنه إضافة بيانات المعايرة."
            }), 403

        new_entry = CalibrationData(
            coffee_type=data["coffee_type"],
            coffee_origin=data["coffee_origin"],
            coffee_variety=data.get("coffee_variety"),
            co2_coeff=data.get("co2_coeff"),
            co2_offset=data.get("co2_offset"),
            protein_coeff=data.get("protein_coeff"),
            protein_offset=data.get("protein_offset"),
            amino_acids_coeff=data.get("amino_acids_coeff"),
            amino_acids_offset=data.get("amino_acids_offset"),
            minerals_coeff=data.get("minerals_coeff"),
            minerals_offset=data.get("minerals_offset"),
            flavor_compounds_coeff=data.get("flavor_compounds_coeff"),
            flavor_compounds_offset=data.get("flavor_compounds_offset"),
            moisture_coeff=data.get("moisture_coeff"),
            moisture_offset=data.get("moisture_offset"),
        )
        db.session.add(new_entry)
        db.session.commit()

        return jsonify({"success": True, "message": "تمت إضافة بيانات المعايرة بنجاح.", "id": new_entry.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"خطأ في إضافة بيانات المعايرة: {str(e)}"}), 500

@calibration_bp.route("/calibration_data/<int:entry_id>", methods=["PUT"])
def update_calibration_data(entry_id):
    """Update existing calibration data (Owner only)."""
    try:
        data = request.get_json()
        owner_id = data.get("owner_id") 
        if not is_owner(owner_id):
            return jsonify({"success": False, "message": "غير مصرح به. المالك فقط يمكنه تحديث بيانات المعايرة."
            }), 403

        entry = CalibrationData.query.get(entry_id)
        if not entry:
            return jsonify({"success": False, "message": "لم يتم العثور على إدخال المعايرة."
            }), 404

        for key, value in data.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        db.session.commit()

        return jsonify({"success": True, "message": "تم تحديث بيانات المعايرة بنجاح.", "id": entry.id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"خطأ في تحديث بيانات المعايرة: {str(e)}"}), 500

@calibration_bp.route("/calibration_data/<int:entry_id>", methods=["DELETE"])
def delete_calibration_data(entry_id):
    """Delete calibration data (Owner only)."""
    try:
        data = request.get_json()
        owner_id = data.get("owner_id") 
        if not is_owner(owner_id):
            return jsonify({"success": False, "message": "غير مصرح به. المالك فقط يمكنه حذف بيانات المعايرة."
            }), 403

        entry = CalibrationData.query.get(entry_id)
        if not entry:
            return jsonify({"success": False, "message": "لم يتم العثور على إدخال المعايرة."
            }), 404

        db.session.delete(entry)
        db.session.commit()

        return jsonify({"success": True, "message": "تم حذف بيانات المعايرة بنجاح."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"خطأ في حذف بيانات المعايرة: {str(e)}"}), 500


