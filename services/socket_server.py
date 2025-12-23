"""Flask socket server for video upload and processing."""

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from views.server_view import ServerView
import os
from datetime import datetime


class SocketServer:
    """Flask-based socket server for receiving and processing videos."""
    
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
        self.server_view = ServerView()
        
        # Ensure upload directory exists
        self.upload_dir = os.path.join("temp", "res")
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Configure Flask routes."""
        
        @self.app.route('/generate', methods=['POST'])
        def generate():
            """
            Handle video and audio file uploads with advanced processing parameters.
            
            Expected form data:
            - video (file): Video file
            - audio (file): Audio file for overlay
            
            Optional processing parameters:
            - original_audio_volume (float): 0.0-2.0, default 1.0
            - uploaded_audio_volume (float): 0.0-2.0, default 1.0
            - audio_noise (float): 0.0-1.0, default 0.0
            - video_speed (float): 0.5-2.0, default 1.0
            - zoom_factor (float): 0.5-2.0, default 1.0
            - color_overlay (str): Hex color like #ff0000
            - color_overlay_opacity (float): 0.0-1.0, default 0.0
            - intro_animation (str): none/blur_to_clear/fade_in, default none
            - intro_duration (float): 0.0-5.0, default 2.0
            """
            try:
                # Check if files are in request
                if 'video' not in request.files or 'audio' not in request.files:
                    return jsonify({
                        'error': 'Missing video or audio file',
                        'message': 'Please provide both video and audio files'
                    }), 400
                
                video_file = request.files['video']
                audio_file = request.files['audio']
                
                # Check if files have names
                if video_file.filename == '' or audio_file.filename == '':
                    return jsonify({
                        'error': 'Empty filename',
                        'message': 'Both files must have valid filenames'
                    }), 400
                
                # Secure filenames
                video_filename = secure_filename(video_file.filename)
                audio_filename = secure_filename(audio_file.filename)
                
                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                video_filename = f"{timestamp}_{video_filename}"
                audio_filename = f"{timestamp}_{audio_filename}"
                
                # Save files
                video_path = os.path.join(self.upload_dir, video_filename)
                audio_path = os.path.join(self.upload_dir, audio_filename)
                
                video_file.save(video_path)
                audio_file.save(audio_path)
                
                # Log upload
                video_size = os.path.getsize(video_path)
                audio_size = os.path.getsize(audio_path)
                
                self.server_view.show_upload_info(video_filename, video_size)
                self.server_view.show_upload_info(audio_filename, audio_size)
                
                # Parse processing parameters from form data
                from models.processing_params import ProcessingParams
                
                try:
                    params = ProcessingParams.from_dict(request.form)
                    
                    # Validate parameters
                    errors = params.validate()
                    if errors:
                        return jsonify({
                            'error': 'Invalid parameters',
                            'details': errors
                        }), 400
                    
                    # Log parameters
                    print(f"📊 Processing parameters:")
                    print(f"   Original audio volume: {params.original_audio_volume}")
                    print(f"   Uploaded audio volume: {params.uploaded_audio_volume}")
                    print(f"   Audio noise: {params.audio_noise}")
                    print(f"   Video speed: {params.video_speed}x")
                    print(f"   Zoom factor: {params.zoom_factor}x")
                    print(f"   Saturation: {params.saturation}")
                    if params.color_overlay:
                        print(f"   Color overlay: {params.color_overlay} ({params.color_overlay_opacity})")
                    if params.intro_animation != "none":
                        print(f"   Intro: {params.intro_animation} ({params.intro_duration}s)")
                    
                except ValueError as e:
                    return jsonify({
                        'error': 'Parameter parsing error',
                        'message': str(e)
                    }), 400
                
                self.server_view.show_processing()
                
                # Import advanced processor
                from services.advanced_processor import process_video_with_effects
                
                # Process video with effects
                output_filename = f"{timestamp}_output.mp4"
                output_path = os.path.abspath(os.path.join("temp", "video", output_filename))
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Call advanced processor with all parameters
                result = process_video_with_effects(
                    video_path=video_path,
                    audio_path=audio_path,
                    output_path=output_path,
                    params=params,
                    target_width=1920,
                    target_height=1080,
                    fps=90,
                    high_quality=True,
                    fake_metadata=True,
                    progress_callback=lambda msg: print(msg)
                )
                
                if result and os.path.exists(result):
                    # Return the processed video
                    return send_file(
                        result,
                        mimetype='video/mp4',
                        as_attachment=True,
                        download_name=output_filename
                    )
                else:
                    return jsonify({
                        'error': 'Processing failed',
                        'message': 'Video processing failed. Check server logs.'
                    }), 500
                    
            except Exception as e:
                print(f"Error processing request: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'error': 'Server error',
                    'message': str(e)
                }), 500
        
        @self.app.route('/', methods=['GET'])
        def index():
            """Root endpoint with server info."""
            return jsonify({
                'name': 'Video Export Server',
                'version': '1.0.0',
                'endpoints': {
                    '/generate': 'POST - Upload video and audio files for processing'
                }
            })
        
        # Logging for all requests
        @self.app.before_request
        def log_request():
            """Log incoming requests."""
            if request.path != '/':  # Don't log root requests
                self.server_view.show_request_info(
                    request.method,
                    request.path,
                    200
                )
        
    def run(self):
        """Start the Flask server."""
        # Disable Flask's default logging for cleaner output
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        # Run server
        self.app.run(
            host=self.host,
            port=self.port,
            debug=False,
            threaded=True
        )
