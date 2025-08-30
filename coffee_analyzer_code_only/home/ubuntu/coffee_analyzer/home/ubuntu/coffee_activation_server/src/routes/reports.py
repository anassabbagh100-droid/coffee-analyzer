from flask import Blueprint, request, jsonify
from src.models.device import Device, db
from src.models.device_report import DeviceReport
from datetime import datetime, timedelta
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/devices/<device_id>/report', methods=['POST'])
def receive_device_report(device_id):
    """Receive and store device operation report"""
    try:
        data = request.get_json()
        
        # Verify device exists
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({
                'success': False,
                'message': 'الجهاز غير موجود'
            }), 404
        
        # Create new report
        new_report = DeviceReport(
            device_id=device_id,
            measurement_count=data.get('measurement_count', 0),
            error_count=data.get('error_count', 0),
            uptime_hours=data.get('uptime_hours', 0),
            wifi_signal=data.get('wifi_signal', 0),
            free_heap=data.get('free_heap', 0),
            current_mode=data.get('current_mode', 0),
            additional_data=data.get('additional_data', {})
        )
        
        db.session.add(new_report)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم استلام التقرير بنجاح'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في استلام التقرير: {str(e)}'
        }), 500

@reports_bp.route('/devices/<device_id>/reports', methods=['GET'])
def get_device_reports(device_id):
    """Get reports for a specific device"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query reports
        reports = DeviceReport.query.filter(
            DeviceReport.device_id == device_id,
            DeviceReport.created_at >= start_date
        ).order_by(DeviceReport.created_at.desc()).limit(limit).all()
        
        report_list = []
        for report in reports:
            report_list.append({
                'id': report.id,
                'measurement_count': report.measurement_count,
                'error_count': report.error_count,
                'uptime_hours': report.uptime_hours,
                'wifi_signal': report.wifi_signal,
                'free_heap': report.free_heap,
                'current_mode': report.current_mode,
                'created_at': report.created_at.isoformat(),
                'additional_data': report.additional_data
            })
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'reports': report_list,
            'total_count': len(report_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في استرجاع التقارير: {str(e)}'
        }), 500

@reports_bp.route('/devices/<device_id>/stats', methods=['GET'])
def get_device_stats(device_id):
    """Get device statistics and health summary"""
    try:
        # Get recent reports (last 7 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        reports = DeviceReport.query.filter(
            DeviceReport.device_id == device_id,
            DeviceReport.created_at >= start_date
        ).all()
        
        if not reports:
            return jsonify({
                'success': True,
                'device_id': device_id,
                'message': 'لا توجد تقارير متاحة للأيام السبعة الماضية'
            }), 200
        
        # Calculate statistics
        total_measurements = sum(r.measurement_count for r in reports)
        total_errors = sum(r.error_count for r in reports)
        avg_wifi_signal = sum(r.wifi_signal for r in reports) / len(reports)
        avg_free_heap = sum(r.free_heap for r in reports) / len(reports)
        max_uptime = max(r.uptime_hours for r in reports)
        
        # Calculate error rate
        error_rate = (total_errors / total_measurements * 100) if total_measurements > 0 else 0
        
        # Determine health status
        health_status = "ممتاز"
        if error_rate > 5:
            health_status = "يحتاج صيانة"
        elif error_rate > 2:
            health_status = "جيد"
        elif avg_wifi_signal < -70:
            health_status = "إشارة ضعيفة"
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'stats': {
                'total_measurements': total_measurements,
                'total_errors': total_errors,
                'error_rate': round(error_rate, 2),
                'avg_wifi_signal': round(avg_wifi_signal, 1),
                'avg_free_heap': round(avg_free_heap, 0),
                'max_uptime_hours': max_uptime,
                'health_status': health_status,
                'reports_count': len(reports),
                'period_days': 7
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في حساب الإحصائيات: {str(e)}'
        }), 500

@reports_bp.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """Get overall dashboard summary for all devices"""
    try:
        # Get all devices
        total_devices = Device.query.count()
        
        # Get devices by activation level
        level_counts = db.session.query(
            Device.activation_level,
            func.count(Device.id)
        ).group_by(Device.activation_level).all()
        
        level_stats = {}
        for level, count in level_counts:
            level_stats[level] = count
        
        # Get recent reports (last 24 hours)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=24)
        
        recent_reports = DeviceReport.query.filter(
            DeviceReport.created_at >= start_date
        ).all()
        
        active_devices = len(set(r.device_id for r in recent_reports))
        total_measurements_24h = sum(r.measurement_count for r in recent_reports)
        total_errors_24h = sum(r.error_count for r in recent_reports)
        
        return jsonify({
            'success': True,
            'summary': {
                'total_devices': total_devices,
                'active_devices_24h': active_devices,
                'total_measurements_24h': total_measurements_24h,
                'total_errors_24h': total_errors_24h,
                'activation_levels': level_stats,
                'last_updated': datetime.utcnow().isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء ملخص لوحة التحكم: {str(e)}'
        }), 500

@reports_bp.route('/devices/<device_id>/errors', methods=['GET'])
def get_device_errors(device_id):
    """Get error reports for a specific device"""
    try:
        limit = request.args.get('limit', 20, type=int)
        days = request.args.get('days', 7, type=int)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get reports with errors
        error_reports = DeviceReport.query.filter(
            DeviceReport.device_id == device_id,
            DeviceReport.error_count > 0,
            DeviceReport.created_at >= start_date
        ).order_by(DeviceReport.created_at.desc()).limit(limit).all()
        
        error_list = []
        for report in error_reports:
            error_list.append({
                'id': report.id,
                'error_count': report.error_count,
                'measurement_count': report.measurement_count,
                'error_rate': round((report.error_count / report.measurement_count * 100) if report.measurement_count > 0 else 0, 2),
                'created_at': report.created_at.isoformat(),
                'additional_data': report.additional_data
            })
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'error_reports': error_list,
            'total_count': len(error_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في استرجاع تقارير الأخطاء: {str(e)}'
        }), 500

