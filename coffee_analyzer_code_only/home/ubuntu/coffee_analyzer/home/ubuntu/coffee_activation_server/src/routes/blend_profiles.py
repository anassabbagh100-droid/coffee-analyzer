from flask import Blueprint, request, jsonify
from src.models.device import Device, db
from src.models.blend_profile import BlendProfile, BlendSample
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime

blend_profiles_bp = Blueprint('blend_profiles', __name__)

@blend_profiles_bp.route('/devices/<device_id>/profiles', methods=['POST'])
def create_blend_profile(device_id):
    """Create a new blend profile for a device"""
    try:
        data = request.get_json()
        
        # Verify device exists and has blend_profiles activation
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({
                'success': False,
                'message': 'الجهاز غير موجود'
            }), 404
        
        if device.activation_level not in ['blend_profiles', 'custom']:
            return jsonify({
                'success': False,
                'message': 'هذا المستوى غير مفعل لهذا الجهاز'
            }), 403
        
        profile_name = data.get('profile_name')
        description = data.get('description', '')
        samples = data.get('samples', [])  # List of coffee samples with their readings
        
        if not profile_name or not samples:
            return jsonify({
                'success': False,
                'message': 'اسم التوليفة والعينات مطلوبة'
            }), 400
        
        # Create new blend profile
        new_profile = BlendProfile(
            device_id=device_id,
            profile_name=profile_name,
            description=description,
            sample_count=len(samples)
        )
        
        db.session.add(new_profile)
        db.session.flush()  # Get the profile ID
        
        # Add samples to the profile
        for sample_data in samples:
            sample = BlendSample(
                profile_id=new_profile.id,
                sample_name=sample_data.get('sample_name', ''),
                sensor_reading_1=sample_data.get('sensor_reading_1', 0),
                sensor_reading_2=sample_data.get('sensor_reading_2', 0),
                sensor_reading_3=sample_data.get('sensor_reading_3', 0),
                chemical_data=json.dumps(sample_data.get('chemical_data', {})),
                notes=sample_data.get('notes', '')
            )
            db.session.add(sample)
        
        # Calculate and store profile signature (average of all samples)
        avg_reading_1 = sum(s.get('sensor_reading_1', 0) for s in samples) / len(samples)
        avg_reading_2 = sum(s.get('sensor_reading_2', 0) for s in samples) / len(samples)
        avg_reading_3 = sum(s.get('sensor_reading_3', 0) for s in samples) / len(samples)
        
        signature = {
            'avg_reading_1': avg_reading_1,
            'avg_reading_2': avg_reading_2,
            'avg_reading_3': avg_reading_3,
            'std_reading_1': np.std([s.get('sensor_reading_1', 0) for s in samples]),
            'std_reading_2': np.std([s.get('sensor_reading_2', 0) for s in samples]),
            'std_reading_3': np.std([s.get('sensor_reading_3', 0) for s in samples])
        }
        
        new_profile.profile_signature = json.dumps(signature)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'profile_id': new_profile.id,
            'profile_name': profile_name,
            'sample_count': len(samples),
            'signature': signature,
            'message': 'تم إنشاء التوليفة المرجعية بنجاح'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء التوليفة: {str(e)}'
        }), 500

@blend_profiles_bp.route('/devices/<device_id>/profiles', methods=['GET'])
def get_blend_profiles(device_id):
    """Get all blend profiles for a device"""
    try:
        profiles = BlendProfile.query.filter_by(device_id=device_id).all()
        
        profile_list = []
        for profile in profiles:
            # Get samples for this profile
            samples = BlendSample.query.filter_by(profile_id=profile.id).all()
            
            profile_data = {
                'id': profile.id,
                'profile_name': profile.profile_name,
                'description': profile.description,
                'sample_count': profile.sample_count,
                'created_at': profile.created_at.isoformat(),
                'samples': [sample.to_dict() for sample in samples]
            }
            
            # Add signature if available
            if profile.profile_signature:
                try:
                    profile_data['signature'] = json.loads(profile.profile_signature)
                except:
                    profile_data['signature'] = {}
            
            profile_list.append(profile_data)
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'profiles': profile_list,
            'total_count': len(profile_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في استرجاع التوليفات: {str(e)}'
        }), 500

@blend_profiles_bp.route('/devices/<device_id>/match', methods=['POST'])
def match_sample_to_profiles(device_id):
    """Match a new sample against stored blend profiles"""
    try:
        data = request.get_json()
        
        # Get sample readings
        sample_readings = [
            data.get('sensor_reading_1', 0),
            data.get('sensor_reading_2', 0),
            data.get('sensor_reading_3', 0)
        ]
        
        if not any(sample_readings):
            return jsonify({
                'success': False,
                'message': 'قراءات المستشعر مطلوبة'
            }), 400
        
        # Get all profiles for this device
        profiles = BlendProfile.query.filter_by(device_id=device_id).all()
        
        if not profiles:
            return jsonify({
                'success': False,
                'message': 'لا توجد توليفات مرجعية محفوظة لهذا الجهاز'
            }), 404
        
        matches = []
        
        for profile in profiles:
            if not profile.profile_signature:
                continue
                
            try:
                signature = json.loads(profile.profile_signature)
                
                # Calculate similarity using cosine similarity
                profile_readings = [
                    signature.get('avg_reading_1', 0),
                    signature.get('avg_reading_2', 0),
                    signature.get('avg_reading_3', 0)
                ]
                
                # Calculate cosine similarity
                similarity = cosine_similarity([sample_readings], [profile_readings])[0][0]
                match_percentage = max(0, min(100, similarity * 100))
                
                # Calculate Euclidean distance for additional metric
                distance = np.linalg.norm(np.array(sample_readings) - np.array(profile_readings))
                
                # Consider standard deviation for tolerance
                tolerance_score = 100
                for i, reading in enumerate(sample_readings):
                    std_key = f'std_reading_{i+1}'
                    if std_key in signature and signature[std_key] > 0:
                        deviation = abs(reading - profile_readings[i]) / signature[std_key]
                        tolerance_score = min(tolerance_score, max(0, 100 - deviation * 20))
                
                # Combined score (weighted average)
                combined_score = (match_percentage * 0.6 + tolerance_score * 0.4)
                
                matches.append({
                    'profile_id': profile.id,
                    'profile_name': profile.profile_name,
                    'description': profile.description,
                    'match_percentage': round(match_percentage, 1),
                    'tolerance_score': round(tolerance_score, 1),
                    'combined_score': round(combined_score, 1),
                    'distance': round(distance, 2),
                    'recommendation': get_match_recommendation(combined_score)
                })
                
            except Exception as e:
                print(f"Error processing profile {profile.id}: {e}")
                continue
        
        # Sort by combined score (highest first)
        matches.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Get best match
        best_match = matches[0] if matches else None
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'sample_readings': sample_readings,
            'matches': matches,
            'best_match': best_match,
            'total_profiles': len(profiles),
            'analyzed_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في مطابقة العينة: {str(e)}'
        }), 500

@blend_profiles_bp.route('/devices/<device_id>/profiles/<int:profile_id>', methods=['DELETE'])
def delete_blend_profile(device_id, profile_id):
    """Delete a blend profile and all its samples"""
    try:
        profile = BlendProfile.query.filter_by(
            id=profile_id, 
            device_id=device_id
        ).first()
        
        if not profile:
            return jsonify({
                'success': False,
                'message': 'التوليفة غير موجودة'
            }), 404
        
        # Delete all samples first
        BlendSample.query.filter_by(profile_id=profile_id).delete()
        
        # Delete the profile
        db.session.delete(profile)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف التوليفة بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف التوليفة: {str(e)}'
        }), 500

@blend_profiles_bp.route('/devices/<device_id>/profiles/<int:profile_id>/samples', methods=['POST'])
def add_sample_to_profile(device_id, profile_id):
    """Add a new sample to an existing blend profile"""
    try:
        data = request.get_json()
        
        profile = BlendProfile.query.filter_by(
            id=profile_id, 
            device_id=device_id
        ).first()
        
        if not profile:
            return jsonify({
                'success': False,
                'message': 'التوليفة غير موجودة'
            }), 404
        
        # Create new sample
        new_sample = BlendSample(
            profile_id=profile_id,
            sample_name=data.get('sample_name', ''),
            sensor_reading_1=data.get('sensor_reading_1', 0),
            sensor_reading_2=data.get('sensor_reading_2', 0),
            sensor_reading_3=data.get('sensor_reading_3', 0),
            chemical_data=json.dumps(data.get('chemical_data', {})),
            notes=data.get('notes', '')
        )
        
        db.session.add(new_sample)
        
        # Update profile sample count
        profile.sample_count += 1
        
        # Recalculate profile signature
        all_samples = BlendSample.query.filter_by(profile_id=profile_id).all()
        all_samples.append(new_sample)  # Include the new sample
        
        avg_reading_1 = sum(s.sensor_reading_1 for s in all_samples) / len(all_samples)
        avg_reading_2 = sum(s.sensor_reading_2 for s in all_samples) / len(all_samples)
        avg_reading_3 = sum(s.sensor_reading_3 for s in all_samples) / len(all_samples)
        
        signature = {
            'avg_reading_1': avg_reading_1,
            'avg_reading_2': avg_reading_2,
            'avg_reading_3': avg_reading_3,
            'std_reading_1': np.std([s.sensor_reading_1 for s in all_samples]),
            'std_reading_2': np.std([s.sensor_reading_2 for s in all_samples]),
            'std_reading_3': np.std([s.sensor_reading_3 for s in all_samples])
        }
        
        profile.profile_signature = json.dumps(signature)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'sample_id': new_sample.id,
            'profile_id': profile_id,
            'updated_signature': signature,
            'message': 'تم إضافة العينة وتحديث التوليفة بنجاح'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إضافة العينة: {str(e)}'
        }), 500

def get_match_recommendation(score):
    """Get recommendation text based on match score"""
    if score >= 90:
        return "تطابق ممتاز - نفس التوليفة تقريباً"
    elif score >= 80:
        return "تطابق جيد جداً - قريب من التوليفة المرجعية"
    elif score >= 70:
        return "تطابق جيد - يحتاج تعديل طفيف"
    elif score >= 60:
        return "تطابق متوسط - يحتاج تعديل"
    elif score >= 40:
        return "تطابق ضعيف - يحتاج تعديل كبير"
    else:
        return "لا يوجد تطابق - مختلف تماماً عن التوليفة"

