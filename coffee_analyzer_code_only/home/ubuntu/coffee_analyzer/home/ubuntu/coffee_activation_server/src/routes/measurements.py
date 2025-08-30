from flask import Blueprint, request, jsonify
from src.models.measurement import Measurement, db
from src.models.device import Device
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from src.analysis.coffee_composition import (
    estimate_co2, estimate_protein, estimate_amino_acids, 
    estimate_minerals, estimate_flavor_compounds, estimate_moisture,
    get_calibration_data_for_coffee
)

measurements_bp = Blueprint("measurements", __name__)

@measurements_bp.route("/measurements", methods=["POST"])
def receive_measurement():
    """Receive measurement data from ESP32 device"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "لم يتم استلام بيانات JSON"
            }), 400
        
        device_serial = data.get("device_serial")
        nir_readings = data.get("nir_readings")
        
        if not device_serial or not nir_readings:
            return jsonify({
                "success": False,
                "message": "الرقم التسلسلي وقراءات NIR مطلوبة"
            }), 400
        
        # Verify device exists
        device = Device.query.filter_by(device_serial=device_serial).first()
        if not device:
            return jsonify({
                "success": False,
                "message": "الجهاز غير مسجل"
            }), 404
        
        # Create new measurement object from ESP32 data
        measurement = Measurement.create_from_esp32_data(data)
        
        db.session.add(measurement)
        db.session.commit()
        
        # Update device last seen
        device.last_seen = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "measurement_id": measurement.id,
            "message": "تم استلام وحفظ القياس بنجاح"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"خطأ في استلام القياس: {str(e)}"
        }), 500

@measurements_bp.route("/measurements/<device_serial>", methods=["GET"])
def get_device_measurements(device_serial):
    """Get measurements for a specific device"""
    try:
        # Get query parameters
        limit = request.args.get("limit", 50, type=int)
        days = request.args.get("days", 30, type=int)
        sample_type = request.args.get("sample_type", None)
        coffee_type = request.args.get("coffee_type", type=int) # New: Filter by coffee type
        coffee_origin = request.args.get("coffee_origin", type=int) # New: Filter by coffee origin
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = Measurement.query.filter(
            Measurement.device_serial == device_serial,
            Measurement.timestamp >= start_date
        )
        
        if sample_type:
            query = query.filter(Measurement.sample_type == sample_type)
        if coffee_type is not None: # Apply filter if coffee_type is provided
            query = query.filter(Measurement.coffee_type == coffee_type)
        if coffee_origin is not None: # Apply filter if coffee_origin is provided
            query = query.filter(Measurement.coffee_origin == coffee_origin)
        
        measurements = query.order_by(desc(Measurement.timestamp)).limit(limit).all()
        
        measurement_list = [m.to_dict() for m in measurements]
        
        return jsonify({
            "success": True,
            "device_serial": device_serial,
            "measurements": measurement_list,
            "total_count": len(measurement_list),
            "period_days": days
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"خطأ في استرجاع القياسات: {str(e)}"
        }), 500

@measurements_bp.route("/measurements/<int:measurement_id>", methods=["GET"])
def get_measurement_details(measurement_id):
    """Get detailed information for a specific measurement"""
    try:
        measurement = Measurement.query.get(measurement_id)
        
        if not measurement:
            return jsonify({
                "success": False,
                "message": "القياس غير موجود"
            }), 404
        
        return jsonify({
            "success": True,
            "measurement": measurement.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"خطأ في استرجاع تفاصيل القياس: {str(e)}"
        }), 500

@measurements_bp.route("/measurements/<int:measurement_id>", methods=["PUT"])
def update_measurement(measurement_id):
    """Update measurement with additional information (e.g., sample name, notes)"""
    try:
        data = request.get_json()
        measurement = Measurement.query.get(measurement_id)
        
        if not measurement:
            return jsonify({
                "success": False,
                "message": "القياس غير موجود"
            }), 404
        
        # Update allowed fields
        if "sample_name" in data:
            measurement.sample_name = data["sample_name"]
        if "sample_type" in data:
            measurement.sample_type = data["sample_type"]
        # Removed direct update of coffee_type from this endpoint
        # if "coffee_type" in data: # New: Update coffee type
        #     measurement.coffee_type = data["coffee_type"]
        if "notes" in data:
            measurement.notes = data["notes"]
        if "quality_score" in data:
            measurement.quality_score = data["quality_score"]
        if "analysis_results" in data:
            measurement.analysis = data["analysis_results"]
        if "estimated_protein" in data:
            measurement.estimated_protein = data["estimated_protein"]
        if "estimated_amino_acids" in data:
            measurement.estimated_amino_acids = data["estimated_amino_acids"]
        if "estimated_minerals" in data:
            measurement.estimated_minerals = data["estimated_minerals"]
        if "estimated_flavor_compounds" in data:
            measurement.estimated_flavor_compounds = data["estimated_flavor_compounds"]
        if "estimated_moisture" in data:
            measurement.estimated_moisture = data["estimated_moisture"]
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "measurement": measurement.to_dict(),
            "message": "تم تحديث القياس بنجاح"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"خطأ في تحديث القياس: {str(e)}"
        }), 500

@measurements_bp.route("/measurements/<device_serial>/stats", methods=["GET"])
def get_measurement_stats(device_serial):
    """Get measurement statistics for a device"""
    try:
        days = request.args.get("days", 30, type=int)
        coffee_type = request.args.get("coffee_type", type=int) # New: Filter by coffee type
        coffee_origin = request.args.get("coffee_origin", type=int) # New: Filter by coffee origin
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query
        query = Measurement.query.filter(
            Measurement.device_serial == device_serial,
            Measurement.timestamp >= start_date
        )
        if coffee_type is not None:
            query = query.filter(Measurement.coffee_type == coffee_type)
        if coffee_origin is not None:
            query = query.filter(Measurement.coffee_origin == coffee_origin)

        measurements = query.all()
        
        if not measurements:
            return jsonify({
                "success": True,
                "device_serial": device_serial,
                "message": f"لا توجد قياسات للأيام الـ {days} الماضية"
            }), 200
        
        # Calculate statistics
        total_measurements = len(measurements)
        
        # CO2 statistics
        co2_values = [m.estimated_co2 for m in measurements if m.estimated_co2 is not None]
        co2_stats = {}
        if co2_values:
            co2_stats = {
                "count": len(co2_values),
                "average": round(sum(co2_values) / len(co2_values), 2),
                "min": min(co2_values),
                "max": max(co2_values)
            }
        
        # Protein statistics (New)
        protein_values = [m.estimated_protein for m in measurements if m.estimated_protein is not None]
        protein_stats = {}
        if protein_values:
            protein_stats = {
                "count": len(protein_values),
                "average": round(sum(protein_values) / len(protein_values), 2),
                "min": min(protein_values),
                "max": max(protein_values)
            }

        # Amino Acids statistics (New)
        amino_acids_values = [m.estimated_amino_acids for m in measurements if m.estimated_amino_acids is not None]
        amino_acids_stats = {}
        if amino_acids_values:
            amino_acids_stats = {
                "count": len(amino_acids_values),
                "average": round(sum(amino_acids_values) / len(amino_acids_values), 2),
                "min": min(amino_acids_values),
                "max": max(amino_acids_values)
            }

        # Minerals statistics (New)
        minerals_values = [m.estimated_minerals for m in measurements if m.estimated_minerals is not None]
        minerals_stats = {}
        if minerals_values:
            minerals_stats = {
                "count": len(minerals_values),
                "average": round(sum(minerals_values) / len(minerals_values), 2),
                "min": min(minerals_values),
                "max": max(minerals_values)
            }

        # Flavor Compounds statistics (New)
        flavor_compounds_values = [m.estimated_flavor_compounds for m in measurements if m.estimated_flavor_compounds is not None]
        flavor_compounds_stats = {}
        if flavor_compounds_values:
            flavor_compounds_stats = {
                "count": len(flavor_compounds_values),
                "average": round(sum(flavor_compounds_values) / len(flavor_compounds_values), 2),
                "min": min(flavor_compounds_values),
                "max": max(flavor_compounds_values)
            }
        
        # Moisture statistics (New)
        moisture_values = [m.estimated_moisture for m in measurements if m.estimated_moisture is not None]
        moisture_stats = {}
        if moisture_values:
            moisture_stats = {
                "count": len(moisture_values),
                "average": round(sum(moisture_values) / len(moisture_values), 2),
                "min": min(moisture_values),
                "max": max(moisture_values)
            }
        
        # Sample type distribution
        sample_types = {}
        for m in measurements:
            if m.sample_type:
                sample_types[m.sample_type] = sample_types.get(m.sample_type, 0) + 1
        
        # Coffee type distribution (New)
        coffee_types_dist = {}
        for m in measurements:
            if m.coffee_type is not None:
                coffee_types_dist[str(m.coffee_type)] = coffee_types_dist.get(str(m.coffee_type), 0) + 1

        # Quality score statistics
        quality_scores = [m.quality_score for m in measurements if m.quality_score is not None]
        quality_stats = {}
        if quality_scores:
            quality_stats = {
                "count": len(quality_scores),
                "average": round(sum(quality_scores) / len(quality_scores), 2),
                "min": min(quality_scores),
                "max": max(quality_scores)
            }
        
        # Daily measurement counts
        daily_counts = {}
        for m in measurements:
            date_key = m.timestamp.date().isoformat()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        return jsonify({
            "success": True,
            "device_serial": device_serial,
            "stats": {
                "total_measurements": total_measurements,
                "period_days": days,
                "co2_statistics": co2_stats,
                "protein_statistics": protein_stats, 
                "amino_acids_statistics": amino_acids_stats, 
                "minerals_statistics": minerals_stats, 
                "flavor_compounds_statistics": flavor_compounds_stats, 
                "moisture_statistics": moisture_stats, 
                "sample_type_distribution": sample_types,
                "coffee_type_distribution": coffee_types_dist, # Include coffee type distribution
                "quality_statistics": quality_stats,
                "daily_measurement_counts": daily_counts,
                "first_measurement": measurements[-1].timestamp.isoformat() if measurements else None,
                "last_measurement": measurements[0].timestamp.isoformat() if measurements else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"خطأ في حساب إحصائيات القياسات: {str(e)}"
        }), 500

@measurements_bp.route("/measurements/<device_serial>/export", methods=["GET"])
def export_measurements(device_serial):
    """Export measurements data for analysis"""
    try:
        days = request.args.get("days", 30, type=int)
        format_type = request.args.get("format", "json")  # json or csv
        coffee_type = request.args.get("coffee_type", type=int) # New: Filter by coffee type
        coffee_origin = request.args.get("coffee_origin", type=int) # New: Filter by coffee origin
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get measurements
        query = Measurement.query.filter(
            Measurement.device_serial == device_serial,
            Measurement.timestamp >= start_date
        )
        if coffee_type is not None:
            query = query.filter(Measurement.coffee_type == coffee_type)
        if coffee_origin is not None:
            query = query.filter(Measurement.coffee_origin == coffee_origin)

        measurements = query.order_by(Measurement.timestamp).all()
        
        if format_type == "csv":
            # Return CSV format
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                "ID", "Timestamp", "Sample Name", "Sample Type", "Coffee Type", "Coffee Origin", # Add coffee origin
                "Estimated CO2", "Estimated Protein", "Estimated Amino Acids", 
                "Estimated Minerals", "Estimated Flavor Compounds", "Estimated Moisture", 
                "Quality Score", "Notes"
            ])
            
            # Write data
            for m in measurements:
                writer.writerow([
                    m.id, m.timestamp.isoformat(), m.sample_name or "",
                    m.sample_type or "", m.coffee_type, m.coffee_origin, # Include coffee origin
                    m.estimated_co2 or "", 
                    m.estimated_protein or "", m.estimated_amino_acids or "", 
                    m.estimated_minerals or "", m.estimated_flavor_compounds or "", 
                    m.estimated_moisture or "", 
                    m.quality_score or "", m.notes or ""
                ])
            
            output.seek(0)
            return output.getvalue(), 200, {
                "Content-Type": "text/csv",
                "Content-Disposition": f"attachment; filename=measurements_{device_serial}_{days}days.csv"
            }
        
        else:
            # Return JSON format
            measurement_list = [m.to_dict() for m in measurements]
            
            return jsonify({
                "success": True,
                "device_serial": device_serial,
                "export_date": datetime.utcnow().isoformat(),
                "period_days": days,
                "total_count": len(measurement_list),
                "measurements": measurement_list
            }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"خطأ في تصدير القياسات: {str(e)}"
        }), 500

@measurements_bp.route("/measurements/<device_serial>/co2-trends", methods=["GET"])
def get_co2_trends(device_serial):
    """Get CO2 trends and patterns for a device"""
    try:
        days = request.args.get("days", 30, type=int)
        coffee_type = request.args.get("coffee_type", type=int)
        coffee_origin = request.args.get("coffee_origin", type=int)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get measurements
        query = Measurement.query.filter(
            Measurement.device_serial == device_serial,
            Measurement.timestamp >= start_date,
            Measurement.estimated_co2.isnot(None)
        )
        if coffee_type is not None:
            query = query.filter(Measurement.coffee_type == coffee_type)
        if coffee_origin is not None:
            query = query.filter(Measurement.coffee_origin == coffee_origin)

        measurements = query.order_by(Measurement.timestamp).all()
        
        # Prepare data for plotting
        trend_data = [
            {
                "timestamp": m.timestamp.isoformat(),
                "co2_level": m.estimated_co2
            }
            for m in measurements
        ]
        
        return jsonify({
            "success": True,
            "device_serial": device_serial,
            "trend_data": trend_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"خطأ في استرجاع اتجاهات CO2: {str(e)}"
        }), 500

# New endpoint for calibration data
@measurements_bp.route("/calibration_data", methods=["GET"])
def get_calibration_data():
    """Provide calibration data based on coffee type and origin"""
    try:
        coffee_type = request.args.get("coffee_type", type=int)
        coffee_origin = request.args.get("coffee_origin", type=int)
        
        if coffee_type is None or coffee_origin is None:
            return jsonify({
                "success": False,
                "message": "نوع البن والأصل مطلوبان"
            }), 400
        
        # Get calibration data from the analysis module
        calibration_data = get_calibration_data_for_coffee(coffee_type, coffee_origin)
        
        return jsonify({
            "success": True,
            "calibration_data": calibration_data
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"خطأ في استرجاع بيانات المعايرة: {str(e)}"
        }), 500


