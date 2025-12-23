"""Application settings and configuration."""

import os
import json


class Settings:
    """Application configuration settings."""
    
    # Server settings
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5000
    
    # Directory settings
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    TEMP_RES_DIR = os.path.join(TEMP_DIR, "res")
    TEMP_JSON_DIR = os.path.join(TEMP_DIR, "json")
    TEMP_VIDEO_DIR = os.path.join(TEMP_DIR, "video")
    CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
    
    # Video export defaults
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080
    DEFAULT_FPS = 90
    DEFAULT_QUALITY = True
    DEFAULT_SUBTITLES = True
    DEFAULT_LANGUAGE = "en"
    DEFAULT_METADATA = True
    
    # GPU settings
    GPU_TYPE = "nvidia"  # nvidia or amd
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        os.makedirs(cls.TEMP_RES_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_JSON_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_VIDEO_DIR, exist_ok=True)
    
    @classmethod
    def get_server_url(cls):
        """Get the full server URL."""
        return f"http://{cls.SERVER_HOST}:{cls.SERVER_PORT}"
    
    @classmethod
    def load_config(cls):
        """Load configuration from file."""
        if os.path.exists(cls.CONFIG_FILE):
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    cls.GPU_TYPE = config.get('gpu_type', 'nvidia')
                    cls.SERVER_PORT = config.get('server_port', 5000)
                    return True
            except Exception as e:
                print(f"Error loading config: {e}")
                return False
        return False
    
    @classmethod
    def save_config(cls):
        """Save configuration to file."""
        try:
            config = {
                'gpu_type': cls.GPU_TYPE,
                'server_port': cls.SERVER_PORT
            }
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    @classmethod
    def set_gpu_type(cls, gpu_type):
        """Set GPU type and save."""
        if gpu_type.lower() in ['nvidia', 'amd']:
            cls.GPU_TYPE = gpu_type.lower()
            cls.save_config()
            return True
        return False
    
    @classmethod
    def get_gpu_type(cls):
        """Get current GPU type."""
        return cls.GPU_TYPE
