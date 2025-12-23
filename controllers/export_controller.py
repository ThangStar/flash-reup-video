"""Controller for video export functionality."""

from views.menu_view import MenuView
from models.video import VideoConfig
from services.video_processor import merge_videos_template
from rich.progress import Progress, SpinnerColumn, TextColumn
import os
import uuid


class ExportController:
    """Handles video export workflow."""
    
    def __init__(self):
        self.view = MenuView()
    
    def _get_filter_templates(self):
        """Get available filter templates."""
        from models.processing_params import ProcessingParams
        
        templates = {
            "1": {
                "name": "Original (No Effects)",
                "params": ProcessingParams()
            },
            "2": {
                "name": "Black & White",
                "params": ProcessingParams(
                    saturation=0.0,  # Full desaturation for black & white
                    intro_animation="none"
                )
            },
            "3": {
                "name": "Red Tint (Warm)",
                "params": ProcessingParams(
                    uploaded_audio_volume=1.3,
                    color_overlay="#ff6b6b",
                    color_overlay_opacity=0.15,
                    intro_animation="fade_in",
                    intro_duration=1.5
                )
            },
            "4": {
                "name": "Blue Tint (Cool)",
                "params": ProcessingParams(
                    uploaded_audio_volume=1.2,
                    color_overlay="#4dabf7",
                    color_overlay_opacity=0.12,
                    intro_animation="fade_in",
                    intro_duration=1.5
                )
            },
            "5": {
                "name": "Bright & Vibrant",
                "params": ProcessingParams(
                    original_audio_volume=0.6,
                    uploaded_audio_volume=1.6,
                    video_speed=1.2,
                    zoom_factor=1.08,
                    intro_animation="blur_to_clear",
                    intro_duration=1.0
                )
            },
            "6": {
                "name": "Dark & Moody",
                "params": ProcessingParams(
                    original_audio_volume=0.4,
                    uploaded_audio_volume=1.4,
                    audio_noise=0.03,
                    video_speed=0.95,
                    color_overlay="#1a1a1a",
                    color_overlay_opacity=0.25,
                    intro_animation="blur_to_clear",
                    intro_duration=3.0
                )
            },
            "7": {
                "name": "Fast & Energetic",
                "params": ProcessingParams(
                    original_audio_volume=0.5,
                    uploaded_audio_volume=1.7,
                    video_speed=1.3,
                    zoom_factor=1.1,
                    color_overlay="#ffec99",
                    color_overlay_opacity=0.08,
                    intro_animation="fade_in",
                    intro_duration=0.5
                )
            },
            "8": {
                "name": "Slow & Smooth",
                "params": ProcessingParams(
                    original_audio_volume=0.7,
                    uploaded_audio_volume=1.2,
                    video_speed=0.85,
                    zoom_factor=1.05,
                    intro_animation="blur_to_clear",
                    intro_duration=3.5
                )
            },
            "9": {
                "name": "Cinematic",
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
                )
            }
        }
        
        return templates
    
    def test_export(self):
        """Run test video export with filter template selection."""
        self.view.clear_screen()
        self.view.show_panel(
            "🎥 Test Video Export - Filter Templates",
            "Test video reup with different filter presets",
            "cyan"
        )
        print()
        
        # Check if test files exist
        test_video = "test.mp4"
        test_audio = "test.mp3"
        
        if not os.path.exists(test_video):
            self.view.show_error(f"Test video file not found: {test_video}")
            self.view.show_info("Please place a test.mp4 file in the root directory")
            self.view.wait_for_enter()
            return
        
        if not os.path.exists(test_audio):
            self.view.show_error(f"Test audio file not found: {test_audio}")
            self.view.show_info("Please place a test.mp3 file in the root directory")
            self.view.wait_for_enter()
            return
        
        self.view.show_success("Found test files!")
        self.view.show_info(f"Video: {test_video}")
        self.view.show_info(f"Audio: {test_audio}")
        print()
        
        # Show filter template menu
        templates = self._get_filter_templates()
        
        self.view.print_separator()
        print()
        self.view.show_info("📋 Select Filter Template:")
        print()
        
        for key, template in templates.items():
            self.view.show_info(f"[{key}] {template['name']}")
        
        self.view.show_info("[0] Cancel")
        print()
        
        choice = self.view.get_choice()
        
        if choice == '0':
            return
        
        if choice not in templates:
            self.view.show_error("Invalid choice")
            self.view.wait_for_enter()
            return
        
        # Get selected template
        selected_template = templates[choice]
        params = selected_template['params']
        
        self.view.clear_screen()
        self.view.show_panel(
            f"🎬 Processing with: {selected_template['name']}",
            "Applying filter template to your video",
            "green"
        )
        print()
        
        # Output configuration
        # random output path
        output_path = "temp/video/" + str(uuid.uuid4()) + ".mp4"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Show configuration
        self.view.show_info("📹 Processing Configuration:")
        self.view.show_info(f"  Output: {output_path}")
        self.view.show_info(f"  Resolution: 1920x1080")
        self.view.show_info(f"  FPS: 90")
        self.view.show_info(f"  Quality: High")
        print()
        
        # Show applied effects (only non-default values)
        self.view.show_info("🎨 Applied Effects:")
        if params.saturation != 1.0:
            if params.saturation == 0.0:
                self.view.show_info(f"  ⬛ Black & White")
            else:
                self.view.show_info(f"  🎨 Saturation: {int(params.saturation*100)}%")
        if params.original_audio_volume != 1.0:
            self.view.show_info(f"  🔊 Original audio: {int(params.original_audio_volume*100)}%")
        if params.uploaded_audio_volume != 1.0:
            self.view.show_info(f"  🔊 Uploaded audio: {int(params.uploaded_audio_volume*100)}%")
        if params.audio_noise > 0:
            self.view.show_info(f"  🔉 Audio noise: {int(params.audio_noise*100)}%")
        if params.video_speed != 1.0:
            self.view.show_info(f"  ⏩ Video speed: {params.video_speed}x")
        if params.zoom_factor != 1.0:
            self.view.show_info(f"  🔍 Zoom: {params.zoom_factor}x")
        if params.color_overlay and params.color_overlay_opacity > 0:
            self.view.show_info(f"  🎨 Color overlay: {params.color_overlay} ({int(params.color_overlay_opacity*100)}%)")
        if params.intro_animation != "none":
            self.view.show_info(f"  ✨ Intro: {params.intro_animation} ({params.intro_duration}s)")
        
        if (params.original_audio_volume == 1.0 and params.uploaded_audio_volume == 1.0 and 
            params.audio_noise == 0 and params.video_speed == 1.0 and params.zoom_factor == 1.0 and
            params.intro_animation == "none"):
            self.view.show_info("  ✨ No effects (original quality)")
        
        print()
        
        # Progress callback
        def progress_callback(message):
            print(message)
        
        try:
            self.view.show_info("Starting video processing...")
            print()
            
            # Import advanced processor
            from services.advanced_processor import process_video_with_effects
            
            # Process with selected template
            result = process_video_with_effects(
                video_path=test_video,
                audio_path=test_audio,
                output_path=output_path,
                params=params,
                target_width=1920,
                target_height=1080,
                fps=90,
                high_quality=True,
                fake_metadata=True,
                progress_callback=progress_callback
            )
            
            print()
            if result:
                self.view.show_success(f"Video processing completed successfully!")
                self.view.show_info(f"Output file: {result}")
                
                # Show file size
                if os.path.exists(result):
                    size_mb = os.path.getsize(result) / 1024 / 1024
                    self.view.show_info(f"File size: {size_mb:.2f} MB")
            else:
                self.view.show_error("Processing failed - check the log above for details")
                
        except Exception as e:
            print()
            self.view.show_error(f"Error during processing: {str(e)}")
            import traceback
            traceback.print_exc()
        
        self.view.wait_for_enter()
