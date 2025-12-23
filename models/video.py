"""Video data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VideoConfig:
    """Configuration for video processing."""
    
    output_path: str = "temp/video/merged_video.mp4"
    target_width: int = 1920
    target_height: int = 1080
    fps: int = 90
    high_quality: bool = True
    include_subtitles: bool = True
    language: str = "en"
    fake_metadata: bool = True
    voice_path: Optional[str] = None
    bgm_path: Optional[str] = None
    bgm_volume: float = 0.05
    
    def to_dict(self):
        """Convert to dictionary for video processor."""
        return {
            'output_path': self.output_path,
            'target_width': self.target_width,
            'target_height': self.target_height,
            'fps': self.fps,
            'high_quality': self.high_quality,
            'include_subtitles': self.include_subtitles,
            'language': self.language,
            'fake_metadata': self.fake_metadata,
            'voice_path': self.voice_path,
            'bgm_path': self.bgm_path,
            'bgm_volume': self.bgm_volume,
        }


@dataclass
class VideoFile:
    """Represents a video file."""
    
    filename: str
    path: str
    size: int = 0
    duration: float = 0.0
    
    def __str__(self):
        return f"{self.filename} ({self.size / 1024 / 1024:.2f} MB)"
