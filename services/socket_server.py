"""Flask-SocketIO server for video upload and processing with queue system."""

from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from views.server_view import ServerView
import os
import base64
import tempfile
import threading
from datetime import datetime
from queue import Queue
from typing import Dict, Optional
import uuid


class VideoJob:
    """Represents a video processing job."""
    
    def __init__(self, client_id: str, video_data: bytes, audio_data: bytes, 
                 video_filename: str, audio_filename: str, params: dict):
        self.job_id = str(uuid.uuid4())
        self.client_id = client_id
        self.video_data = video_data
        self.audio_data = audio_data
        self.video_filename = video_filename
        self.audio_filename = audio_filename
        self.params = params
        self.created_at = datetime.now()
        self.status = "queued"  # queued, processing, completed, failed


class SocketServer:
    """Flask-SocketIO server for receiving and processing videos with queue system."""
    
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'video-processing-secret-key'
        self.app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
        
        # Initialize SocketIO with eventlet
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='eventlet',
            max_http_buffer_size=500 * 1024 * 1024,
            ping_timeout=120,
            ping_interval=25
        )
        
        self.server_view = ServerView()
        
        # Queue system
        self.job_queue = Queue()
        self.connected_clients: Dict[str, dict] = {}  # sid -> client info
        self.processing_job: Optional[VideoJob] = None
        self.completed_jobs: Dict[str, str] = {}  # job_id -> output_path
        
        # Ensure upload directory exists
        self.upload_dir = os.path.join("temp", "res")
        self.output_dir = os.path.join("temp", "video")
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Start processing worker
        self.worker_thread = threading.Thread(target=self._process_queue_worker, daemon=True)
        self.worker_running = True
        
        # Setup event handlers
        self.setup_events()
    
    def _emit_log(self, client_id: str, message: str, log_type: str = "info", progress: Optional[int] = None):
        """Send log message to specific client."""
        data = {
            'type': log_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        if progress is not None:
            data['progress'] = progress
        
        self.socketio.emit('log', data, room=client_id)
        print(f"[{client_id[:8]}] {message}")
    
    def _broadcast_queue_status(self):
        """Broadcast queue status to all connected clients."""
        queue_list = list(self.job_queue.queue)
        
        for sid, client_info in self.connected_clients.items():
            # Find client's position in queue
            position = None
            for idx, job in enumerate(queue_list):
                if job.client_id == sid:
                    position = idx + 1
                    break
            
            status = {
                'connected_users': len(self.connected_clients),
                'queue_length': self.job_queue.qsize(),
                'processing': self.processing_job is not None,
                'your_position': position
            }
            
            self.socketio.emit('queue_update', status, room=sid)
    
    def setup_events(self):
        """Setup SocketIO event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            client_id = request.sid
            self.connected_clients[client_id] = {
                'connected_at': datetime.now(),
                'ip': request.remote_addr
            }
            
            self.server_view.show_info(f"✅ Client connected: {client_id[:8]}... ({len(self.connected_clients)} total)")
            
            # Send initial queue status
            self._broadcast_queue_status()
            
            emit('connected', {
                'client_id': client_id,
                'message': 'Connected to video processing server'
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            client_id = request.sid
            
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
                self.server_view.show_info(f"❌ Client disconnected: {client_id[:8]}... ({len(self.connected_clients)} remaining)")
                
                # Update queue status for remaining clients
                self._broadcast_queue_status()
        
        @self.socketio.on('generate_video')
        def handle_generate_video(data):
            """
            Handle video generation request.
            
            Expected data:
            {
                'video': str (base64),
                'audio': str (base64),
                'video_filename': str,
                'audio_filename': str,
                'params': {
                    'original_audio_volume': float,
                    'uploaded_audio_volume': float,
                    'audio_noise': float,
                    'video_speed': float,
                    'zoom_factor': float,
                    'saturation': float,
                    'color_overlay': str,
                    'color_overlay_opacity': float,
                    'intro_animation': str,
                    'intro_duration': float
                }
            }
            """
            client_id = request.sid
            
            try:
                # Validate request
                if 'video' not in data or 'audio' not in data:
                    self._emit_log(client_id, "❌ Missing video or audio data", "error")
                    emit('error', {'message': 'Missing video or audio data'})
                    return
                
                # Decode base64 data
                try:
                    video_data = base64.b64decode(data['video'])
                    audio_data = base64.b64decode(data['audio'])
                except Exception as e:
                    self._emit_log(client_id, f"❌ Failed to decode files: {str(e)}", "error")
                    emit('error', {'message': f'Failed to decode files: {str(e)}'})
                    return
                
                # Get filenames
                video_filename = secure_filename(data.get('video_filename', 'video.mp4'))
                audio_filename = secure_filename(data.get('audio_filename', 'audio.mp3'))
                
                # Get parameters (with defaults)
                params = data.get('params', {})
                
                # Create job
                job = VideoJob(
                    client_id=client_id,
                    video_data=video_data,
                    audio_data=audio_data,
                    video_filename=video_filename,
                    audio_filename=audio_filename,
                    params=params
                )
                
                # Add to queue
                self.job_queue.put(job)
                
                queue_position = self.job_queue.qsize()
                self._emit_log(
                    client_id, 
                    f"📥 Job queued (Position: {queue_position})",
                    "info"
                )
                
                # Broadcast queue update
                self._broadcast_queue_status()
                
                emit('job_queued', {
                    'job_id': job.job_id,
                    'position': queue_position
                })
                
            except Exception as e:
                self._emit_log(client_id, f"❌ Error: {str(e)}", "error")
                emit('error', {'message': str(e)})
                import traceback
                traceback.print_exc()
    
    def _process_queue_worker(self):
        """Background worker to process jobs from queue."""
        while self.worker_running:
            try:
                # Get next job (blocks until available)
                job = self.job_queue.get(timeout=1)
                self.processing_job = job
                
                # Broadcast queue update
                self._broadcast_queue_status()
                
                # Process the job
                self._process_job(job)
                
                self.processing_job = None
                self.job_queue.task_done()
                
                # Broadcast queue update
                self._broadcast_queue_status()
                
            except Exception as e:
                if "Empty" not in str(type(e).__name__):
                    print(f"Worker error: {e}")
                    import traceback
                    traceback.print_exc()
    
    def _process_job(self, job: VideoJob):
        """Process a video job."""
        client_id = job.client_id
        
        try:
            job.status = "processing"
            self._emit_log(client_id, "🎬 Starting video processing...", "info")
            
            # Save uploaded files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"{timestamp}_{job.video_filename}"
            audio_filename = f"{timestamp}_{job.audio_filename}"
            
            video_path = os.path.abspath(os.path.join(self.upload_dir, video_filename))
            audio_path = os.path.abspath(os.path.join(self.upload_dir, audio_filename))
            
            with open(video_path, 'wb') as f:
                f.write(job.video_data)
            with open(audio_path, 'wb') as f:
                f.write(job.audio_data)
            
            video_size = len(job.video_data)
            audio_size = len(job.audio_data)
            
            self._emit_log(client_id, f"📹 Video: {video_filename} ({video_size / 1024 / 1024:.2f} MB)", "info")
            self._emit_log(client_id, f"🎵 Audio: {audio_filename} ({audio_size / 1024 / 1024:.2f} MB)", "info")
            
            # Parse processing parameters
            from models.processing_params import ProcessingParams
            
            try:
                params = ProcessingParams.from_dict(job.params)
                errors = params.validate()
                
                if errors:
                    for error in errors:
                        self._emit_log(client_id, f"❌ {error}", "error")
                    
                    self.socketio.emit('processing_complete', {
                        'success': False,
                        'error': 'Invalid parameters: ' + ', '.join(errors)
                    }, room=client_id)
                    return
                
                # Log parameters
                self._emit_log(client_id, "📊 Processing parameters:", "info")
                self._emit_log(client_id, f"   Original audio: {int(params.original_audio_volume*100)}%", "info")
                self._emit_log(client_id, f"   Uploaded audio: {int(params.uploaded_audio_volume*100)}%", "info")
                self._emit_log(client_id, f"   Noise: {int(params.audio_noise*100)}%", "info")
                self._emit_log(client_id, f"   Speed: {params.video_speed}x", "info")
                self._emit_log(client_id, f"   Zoom: {params.zoom_factor}x", "info")
                self._emit_log(client_id, f"   Saturation: {params.saturation}", "info")
                
                if params.color_overlay:
                    self._emit_log(client_id, f"   Color: {params.color_overlay} ({int(params.color_overlay_opacity*100)}%)", "info")
                if params.intro_animation != "none":
                    self._emit_log(client_id, f"   Intro: {params.intro_animation} ({params.intro_duration}s)", "info")
                
            except ValueError as e:
                self._emit_log(client_id, f"❌ Parameter error: {str(e)}", "error")
                self.socketio.emit('processing_complete', {
                    'success': False,
                    'error': str(e)
                }, room=client_id)
                return
            
            # Process video
            from services.advanced_processor import process_video_with_effects
            
            output_filename = f"{timestamp}_output.mp4"
            output_path = os.path.abspath(os.path.join(self.output_dir, output_filename))
            
            # Progress callback
            def progress_callback(message):
                # Parse progress from message if possible
                progress = None
                if "%" in message:
                    try:
                        # Try to extract percentage
                        parts = message.split("%")
                        num_str = parts[0].split()[-1]
                        progress = int(float(num_str))
                    except:
                        pass
                
                self._emit_log(client_id, message, "info", progress)
            
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
                progress_callback=progress_callback
            )
            
            if result and os.path.exists(result):
                job.status = "completed"
                self.completed_jobs[job.job_id] = result
                
                file_size = os.path.getsize(result) / 1024 / 1024
                self._emit_log(client_id, f"✅ Processing complete! ({file_size:.2f} MB)", "success", 100)
                
                # Read file as base64 for transmission
                with open(result, 'rb') as f:
                    video_base64 = base64.b64encode(f.read()).decode('utf-8')
                
                self.socketio.emit('processing_complete', {
                    'success': True,
                    'job_id': job.job_id,
                    'filename': output_filename,
                    'video_data': video_base64,
                    'size_mb': file_size
                }, room=client_id)
                
                # Cleanup input files
                try:
                    os.remove(video_path)
                    os.remove(audio_path)
                except:
                    pass
            else:
                job.status = "failed"
                self._emit_log(client_id, "❌ Processing failed", "error")
                self.socketio.emit('processing_complete', {
                    'success': False,
                    'error': 'Video processing failed'
                }, room=client_id)
        
        except Exception as e:
            job.status = "failed"
            self._emit_log(client_id, f"❌ Error: {str(e)}", "error")
            self.socketio.emit('processing_complete', {
                'success': False,
                'error': str(e)
            }, room=client_id)
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Start the SocketIO server."""
        # Start worker thread
        self.worker_thread.start()
        
        self.server_view.show_info("🚀 Socket.IO server starting...")
        self.server_view.show_info(f"📡 Listening on {self.host}:{self.port}")
        self.server_view.show_info("📋 Queue system enabled")
        
        # Run SocketIO server
        self.socketio.run(
            self.app,
            host=self.host,
            port=self.port,
            debug=False,
            use_reloader=False
        )
