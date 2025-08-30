from flask import Blueprint, request, jsonify
from src.models.knowledge_entry import KnowledgeEntry, db
from src.models.device import Device
from datetime import datetime
from sqlalchemy import desc

knowledge_bp = Blueprint(\'knowledge\', __name__)

# This function should only be called by the ESP32 device, not directly by a user
@knowledge_bp.route(\'/knowledge\', methods=[\'POST\'])
def receive_knowledge_entry():
    """Receive new knowledge base entry from ESP32 for owner approval"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                \'success\': False,
                \'message\': \'لم يتم استلام بيانات JSON\'
            }), 400
        
        # Verify device exists
        device_serial = data.get(\'device_id\')
        device = Device.query.filter_by(device_serial=device_serial).first()
        if not device:
            return jsonify({
                \'success\': False,
                \'message\': \'الجهاز غير مسجل\'
            }), 404

        # Create new knowledge entry object from ESP32 data
        knowledge_entry = KnowledgeEntry.create_from_esp32_data(data)
        
        db.session.add(knowledge_entry)
        db.session.commit()
        
        return jsonify({
            \'success\': True,
            \'entry_id\': knowledge_entry.id,
            \'message\': \'تم استلام إدخال المعرفة بنجاح. في انتظار موافقة المالك.\'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            \'success\': False,
            \'message\': f\'خطأ في استلام إدخال المعرفة: {str(e)}\'
        }), 500

# These functions should only be accessible by the owner (e.g., via an authenticated admin panel)
# For simplicity, we are not implementing full authentication here, but the intent is clear.
@knowledge_bp.route(\'/knowledge\', methods=[\'GET\'])
def get_knowledge_entries():
    """Get all knowledge base entries (pending and approved) - Owner Only"""
    try:
        # In a real application, add owner authentication here
        # if not is_owner_authenticated():
        #     return jsonify({'success': False, 'message': 'غير مصرح به'}), 403

        approved_filter = request.args.get(\'approved\', type=str) # \'true\', \'false\', or None

        query = KnowledgeEntry.query

        if approved_filter == \'true\':
            query = query.filter_by(approved=True)
        elif approved_filter == \'false\':
            query = query.filter_by(approved=False)
        
        entries = query.order_by(desc(KnowledgeEntry.timestamp)).all()
        
        return jsonify({
            \'success\': True,
            \'entries\': [e.to_dict() for e in entries]
        }), 200
        
    except Exception as e:
        return jsonify({
            \'success\': False,
            \'message\': f\'خطأ في استرجاع إدخالات المعرفة: {str(e)}\'
        }), 500

@knowledge_bp.route(\'/knowledge/<int:entry_id>/approve\', methods=[\'POST\'])
def approve_knowledge_entry(entry_id):
    """Approve a knowledge base entry - Owner Only"""
    try:
        # In a real application, add owner authentication here
        # if not is_owner_authenticated():
        #     return jsonify({'success': False, 'message': 'غير مصرح به'}), 403

        entry = KnowledgeEntry.query.get(entry_id)
        
        if not entry:
            return jsonify({
                \'success\': False,
                \'message\': \'إدخال المعرفة غير موجود\'
            }), 404
        
        entry.approved = True
        db.session.commit()

        # TODO: Add logic here to integrate this approved entry into the main calibration model
        # This would involve re-training or updating the model with the new data.
        # For now, it\'s just marked as approved.
        
        return jsonify({
            \'success\': True,
            \'message\': \'تمت الموافقة على إدخال المعرفة بنجاح\'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            \'success\': False,
            \'message\': f\'خطأ في الموافقة على إدخال المعرفة: {str(e)}\'
        }), 500

@knowledge_bp.route(\'/knowledge/<int:entry_id>/reject\', methods=[\'POST\'])
def reject_knowledge_entry(entry_id):
    """Reject and delete a knowledge base entry - Owner Only"""
    try:
        # In a real application, add owner authentication here
        # if not is_owner_authenticated():
        #     return jsonify({'success': False, 'message': 'غير مصرح به'}), 403

        entry = KnowledgeEntry.query.get(entry_id)
        
        if not entry:
            return jsonify({
                \'success\': False,
                \'message\': \'إدخال المعرفة غير موجود\'
            }), 404
        
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({
            \'success\': True,
            \'message\': \'تم رفض وحذف إدخال المعرفة بنجاح\'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            \'success\': False,
            \'message\': f\'خطأ في رفض إدخال المعرفة: {str(e)}\'
        }), 500




