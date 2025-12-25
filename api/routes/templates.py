"""Templates API Blueprint - Provides video processing templates."""

from flask import Blueprint, jsonify
from models.processing_params import ProcessingParams

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('/api/templates', methods=['GET'])
def get_templates():
    """Get all available video processing templates."""
    
    templates = {
        "0": {
            "id": "0",
            "name": "Custom Setup",
            "description": "Tùy chỉnh các thông số theo ý bạn",
            "params": None  # Will be configured by user
        },
        "1": {
            "id": "1",
            "name": "Original (No Effects)",
            "description": "Giữ nguyên chất lượng gốc",
            "params": ProcessingParams().to_dict()
        },
        "2": {
            "id": "2",
            "name": "Black & White",
            "description": "Phong cách đen trắng cổ điển",
            "params": ProcessingParams(
                saturation=0.0,
                intro_animation="none"
            ).to_dict()
        },
        "3": {
            "id": "3",
            "name": "Red Tint (Warm)",
            "description": "Tông màu đỏ ấm áp",
            "params": ProcessingParams(
                uploaded_audio_volume=1.3,
                color_overlay="#ff6b6b",
                color_overlay_opacity=0.15,
                intro_animation="fade_in",
                intro_duration=1.5
            ).to_dict()
        },
        "4": {
            "id": "4",
            "name": "Blue Tint (Cool)",
            "description": "Tông màu xanh mát mẻ",
            "params": ProcessingParams(
                uploaded_audio_volume=1.2,
                color_overlay="#4dabf7",
                color_overlay_opacity=0.12,
                intro_animation="fade_in",
                intro_duration=1.5
            ).to_dict()
        },
        "5": {
            "id": "5",
            "name": "Bright & Vibrant",
            "description": "Sáng và sống động",
            "params": ProcessingParams(
                original_audio_volume=0.6,
                uploaded_audio_volume=1.6,
                video_speed=1.2,
                zoom_factor=1.08,
                intro_animation="blur_to_clear",
                intro_duration=1.0
            ).to_dict()
        },
        "6": {
            "id": "6",
            "name": "Dark & Moody",
            "description": "Tối và huyền bí",
            "params": ProcessingParams(
                original_audio_volume=0.4,
                uploaded_audio_volume=1.4,
                audio_noise=0.03,
                video_speed=0.95,
                color_overlay="#1a1a1a",
                color_overlay_opacity=0.25,
                intro_animation="blur_to_clear",
                intro_duration=3.0
            ).to_dict()
        },
        "7": {
            "id": "7",
            "name": "Fast & Energetic",
            "description": "Nhanh và năng động",
            "params": ProcessingParams(
                original_audio_volume=0.5,
                uploaded_audio_volume=1.7,
                video_speed=1.3,
                zoom_factor=1.1,
                color_overlay="#ffec99",
                color_overlay_opacity=0.08,
                intro_animation="fade_in",
                intro_duration=0.5
            ).to_dict()
        },
        "8": {
            "id": "8",
            "name": "Slow & Smooth",
            "description": "Chậm và mượt mà",
            "params": ProcessingParams(
                original_audio_volume=0.7,
                uploaded_audio_volume=1.2,
                video_speed=0.85,
                zoom_factor=1.05,
                intro_animation="blur_to_clear",
                intro_duration=3.5
            ).to_dict()
        },
        "9": {
            "id": "9",
            "name": "Cinematic",
            "description": "Phong cách điện ảnh",
            "params": ProcessingParams(
                original_audio_volume=0.5,
                uploaded_audio_volume=1.5,
                audio_noise=0.05,
                video_speed=1.15,
                zoom_factor=1.05,
                color_overlay="#1a1a1a",
                color_overlay_opacity=0.1,
                intro_animation="blur_to_clear",
                intro_duration=2.0
            ).to_dict()
        }
    }
    
    return jsonify({
        "success": True,
        "templates": templates
    })
