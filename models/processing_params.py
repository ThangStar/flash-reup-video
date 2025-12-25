"""Processing parameters model for video effects."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessingParams:
    """Parameters for video processing effects."""
    
    # Audio parameters
    original_audio_volume: float = 1.0
    uploaded_audio_volume: float = 1.0
    audio_noise: float = 0.0
    
    # Video parameters
    video_speed: float = 1.0
    zoom_factor: float = 1.0
    saturation: float = 1.0  # 0.0 = black & white, 1.0 = normal, >1.0 = oversaturated
    
    # Color overlay
    color_overlay: Optional[str] = None
    color_overlay_opacity: float = 0.0
    
    # Intro animation
    intro_animation: str = "none"  # none, blur_to_clear, fade_in
    intro_duration: float = 2.0
    
    def validate(self):
        """Validate parameter ranges."""
        errors = []
        
        # Audio volume: 0.0 - 2.0
        if not (0.0 <= self.original_audio_volume <= 2.0):
            errors.append("original_audio_volume must be between 0.0 and 2.0")
        if not (0.0 <= self.uploaded_audio_volume <= 2.0):
            errors.append("uploaded_audio_volume must be between 0.0 and 2.0")
        
        # Audio noise: 0.0 - 1.0
        if not (0.0 <= self.audio_noise <= 1.0):
            errors.append("audio_noise must be between 0.0 and 1.0")
        
        # Video speed: 0.5 - 2.0
        if not (0.5 <= self.video_speed <= 2.0):
            errors.append("video_speed must be between 0.5 and 2.0")
        
        # Zoom: 0.5 - 2.0
        if not (0.5 <= self.zoom_factor <= 2.0):
            errors.append("zoom_factor must be between 0.5 and 2.0")
        
        # Saturation: 0.0 - 2.0
        if not (0.0 <= self.saturation <= 2.0):
            errors.append("saturation must be between 0.0 and 2.0")
        
        # Color overlay opacity: 0.0 - 1.0
        if not (0.0 <= self.color_overlay_opacity <= 1.0):
            errors.append("color_overlay_opacity must be between 0.0 and 1.0")
        
        # Intro animation
        if self.intro_animation not in ["none", "blur_to_clear", "fade_in"]:
            errors.append("intro_animation must be 'none', 'blur_to_clear', or 'fade_in'")
        
        # Intro duration: 0.0 - 5.0
        if not (0.0 <= self.intro_duration <= 5.0):
            errors.append("intro_duration must be between 0.0 and 5.0")
        
        return errors
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create ProcessingParams from dictionary."""
        return cls(
            original_audio_volume=float(data.get('original_audio_volume', 1.0)),
            uploaded_audio_volume=float(data.get('uploaded_audio_volume', 1.0)),
            audio_noise=float(data.get('audio_noise', 0.0)),
            video_speed=float(data.get('video_speed', 1.0)),
            zoom_factor=float(data.get('zoom_factor', 1.0)),
            saturation=float(data.get('saturation', 1.0)),
            color_overlay=data.get('color_overlay'),
            color_overlay_opacity=float(data.get('color_overlay_opacity', 0.0)),
            intro_animation=data.get('intro_animation', 'none'),
            intro_duration=float(data.get('intro_duration', 2.0))
        )
    
    def to_dict(self):
        """Convert ProcessingParams to dictionary."""
        return {
            'original_audio_volume': self.original_audio_volume,
            'uploaded_audio_volume': self.uploaded_audio_volume,
            'audio_noise': self.audio_noise,
            'video_speed': self.video_speed,
            'zoom_factor': self.zoom_factor,
            'saturation': self.saturation,
            'color_overlay': self.color_overlay,
            'color_overlay_opacity': self.color_overlay_opacity,
            'intro_animation': self.intro_animation,
            'intro_duration': self.intro_duration
        }

