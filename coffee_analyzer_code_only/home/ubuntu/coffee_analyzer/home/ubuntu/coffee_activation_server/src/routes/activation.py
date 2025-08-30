from flask import Blueprint, request, jsonify
from src.models.device import Device, db
from datetime import datetime
import secrets
import string

activation_bp = Blueprint('activation', __name__)

# Generate activation keys
def generate_activation_key(prefix="", length=12):
    """Generate a secure activation key with optional prefix"""
    chars = string.ascii_uppercase + string.digits
    key = ''.join(secrets.choice(chars) for _ in range(length))
    return f"{prefix}{key}" if prefix else key

@activation_bp.route('/devices', methods=['POST'])
def register_device():
    """Register a new device with serial number"""
    try:
        data = request.get_json()
        device_serial = data.get('device_serial', '')
        device_name = data.get('device_name', 'جهاز جديد')
        first_boot_date = data.get('first_boot_date', None)
        first_internet_date = data.get('first_internet_date', None)
        
        if not device_serial:
            return jsonify({
                'success': False,
                'message': 'الرقم التسلسلي مطلوب'
            }), 400
        
        # Check if device already exists
        existing_device = Device.query.filter_by(device_serial=device_serial).first()
        if existing_device:
            # Update existing device with new information
            existing_device.device_name = device_name
            existing_device.last_seen = datetime.utcnow()
            
            # Update first boot date if provided and not already set
            if first_boot_date and not existing_device.first_boot_date:
                try:
                    existing_device.first_boot_date = datetime.fromisoformat(first_boot_date.replace('Z', '+00:00'))
                except:
                    pass
            
            # Update first internet date if provided and not already set
            if first_internet_date and not existing_device.first_internet_date:
                try:
                    existing_device.first_internet_date = datetime.fromisoformat(first_internet_date.replace('Z', '+00:00'))
                except:
                    existing_device.first_internet_date = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'device_id': existing_device.device_id,
                'device_serial': existing_device.device_serial,
                'device_name': existing_device.device_name,
                'activation_level': existing_device.activation_level,
                'activation_key': existing_device.activation_key,
                'message': 'تم تحديث معلومات الجهاز'
            }), 200
        
        # Generate unique device ID for backward compatibility
        device_id = Device.generate_device_id()
        while Device.query.filter_by(device_id=device_id).first():
            device_id = Device.generate_device_id()
        
        # Parse manufacture date from serial number
        manufacture_date = Device.parse_serial_date(device_serial)
        
        new_device = Device(
            device_id=device_id,
            device_serial=device_serial,
            device_name=device_name,
            activation_level='basic',
            manufacture_date=manufacture_date
        )
        
        # Set first boot date if provided
        if first_boot_date:
            try:
                new_device.first_boot_date = datetime.fromisoformat(first_boot_date.replace('Z', '+00:00'))
            except:
                pass
        
        # Set first internet date
        if first_internet_date:
            try:
                new_device.first_internet_date = datetime.fromisoformat(first_internet_date.replace('Z', '+00:00'))
            except:
                new_device.first_internet_date = datetime.utcnow()
        else:
            new_device.first_internet_date = datetime.utcnow()
        
        db.session.add(new_device)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'device_serial': device_serial,
            'device_name': device_name,
            'activation_level': 'basic',
            'message': 'تم تسجيل الجهاز بنجاح'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تسجيل الجهاز: {str(e)}'
        }), 500

@activation_bp.route('/devices/<device_serial>/status', methods=['GET'])
def get_device_status(device_serial):
    """Get current activation status for a device using serial number"""
    try:
        device = Device.query.filter_by(device_serial=device_serial).first()
        
        if not device:
            return jsonify({
                'success': False,
                'message': 'الجهاز غير موجود'
            }), 404
        
        # Update last seen timestamp
        device.last_seen = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'device_id': device.device_id,
            'device_serial': device.device_serial,
            'device_name': device.device_name,
            'activation_level': device.activation_level,
            'activation_key': device.activation_key,
            'manufacture_date': device.manufacture_date.isoformat() if device.manufacture_date else None,
            'first_boot_date': device.first_boot_date.isoformat() if device.first_boot_date else None,
            'first_internet_date': device.first_internet_date.isoformat() if device.first_internet_date else None,
            'last_seen': device.last_seen.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في استرجاع حالة الجهاز: {str(e)}'
        }), 500

@activation_bp.route('/devices/<device_serial>/activate', methods=['POST'])
def activate_device(device_serial):
    """Activate a device to a specific level"""
    try:
        data = request.get_json()
        activation_level = data.get('activation_level', 'basic')
        
        # Validate activation level
        valid_levels = ['basic', 'professional', 'advanced', 'custom', 'blend_profiles']
        if activation_level not in valid_levels:
            return jsonify({
                'success': False,
                'message': 'مستوى التفعيل غير صحيح'
            }), 400
        
        device = Device.query.filter_by(device_serial=device_serial).first()
        
        if not device:
            return jsonify({
                'success': False,
                'message': 'الجهاز غير موجود'
            }), 404
        
        # Generate new activation key for this device and level
        key_prefix = {
            'basic': 'BAS-',
            'professional': 'PRO-',
            'advanced': 'ADV-',
            'custom': 'CUS-',
            'blend_profiles': 'BLP-'
        }.get(activation_level, 'UNK-')
        
        # Include device serial in key generation for uniqueness
        device_suffix = device_serial.split('-')[-1][:4]  # Last 4 chars of serial
        activation_key = generate_activation_key(key_prefix + device_suffix + '-', 8)
        
        device.activation_level = activation_level
        device.activation_key = activation_key
        device.last_seen = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'device_serial': device_serial,
            'activation_level': activation_level,
            'activation_key': activation_key,
            'message': f'تم تفعيل الجهاز إلى المستوى {activation_level}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تفعيل الجهاز: {str(e)}'
        }), 500

@activation_bp.route('/devices', methods=['GET'])
def list_devices():
    """List all registered devices"""
    try:
        devices = Device.query.all()
        device_list = []
        
        for device in devices:
            device_data = device.to_dict()
            # Add calculated fields
            device_data['days_since_manufacture'] = None
            device_data['days_since_first_boot'] = None
            device_data['days_since_first_internet'] = None
            
            if device.manufacture_date:
                device_data['days_since_manufacture'] = (datetime.utcnow().date() - device.manufacture_date).days
            
            if device.first_boot_date:
                device_data['days_since_first_boot'] = (datetime.utcnow() - device.first_boot_date).days
            
            if device.first_internet_date:
                device_data['days_since_first_internet'] = (datetime.utcnow() - device.first_internet_date).days
            
            device_list.append(device_data)
        
        return jsonify({
            'success': True,
            'devices': device_list,
            'total_count': len(device_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في استرجاع قائمة الأجهزة: {str(e)}'
        }), 500

@activation_bp.route('/devices/<device_serial>/report', methods=['POST'])
def receive_device_report(device_serial):
    """Receive operational report from device"""
    try:
        data = request.get_json()
        
        device = Device.query.filter_by(device_serial=device_serial).first()
        
        if not device:
            return jsonify({
                'success': False,
                'message': 'الجهاز غير موجود'
            }), 404
        
        # Update last seen timestamp
        device.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Store report data (this would typically go to a separate reports table)
        # For now, just acknowledge receipt
        
        return jsonify({
            'success': True,
            'message': 'تم استلام التقرير بنجاح'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في استلام التقرير: {str(e)}'
        }), 500

