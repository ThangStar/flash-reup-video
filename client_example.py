"""
Example Socket.IO client for video processing.
Demonstrates how to connect, submit jobs, receive progress updates, and download results.
"""

import socketio
import base64
import os
import sys

# Create Socket.IO client
sio = socketio.Client()

# Track current job
current_job_id = None


@sio.on('connected')
def on_connected(data):
    """Handle connection confirmation."""
    print(f"✅ Connected to server")
    print(f"   Client ID: {data['client_id']}")
    print(f"   {data['message']}")
    print()


@sio.on('queue_update')
def on_queue_update(data):
    """Handle queue status updates."""
    print(f"📊 Queue Status:")
    print(f"   Connected users: {data['connected_users']}")
    print(f"   Queue length: {data['queue_length']}")
    print(f"   Processing: {'Yes' if data['processing'] else 'No'}")
    
    if data.get('your_position'):
        print(f"   Your position: {data['your_position']}")
    print()


@sio.on('log')
def on_log(data):
    """Handle log messages from server."""
    emoji_map = {
        'info': 'ℹ️',
        'success': '✅',
        'error': '❌',
        'progress': '⏳'
    }
    
    emoji = emoji_map.get(data['type'], 'ℹ️')
    message = data['message']
    
    # Add progress bar if available
    if 'progress' in data and data['progress'] is not None:
        progress = data['progress']
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"{emoji} {message}")
        print(f"   [{bar}] {progress}%")
    else:
        print(f"{emoji} {message}")


@sio.on('job_queued')
def on_job_queued(data):
    """Handle job queued confirmation."""
    global current_job_id
    current_job_id = data['job_id']
    print(f"📥 Job queued successfully")
    print(f"   Job ID: {data['job_id']}")
    print(f"   Queue position: {data['position']}")
    print()


@sio.on('processing_complete')
def on_processing_complete(data):
    """Handle processing completion."""
    global current_job_id
    
    if data['success']:
        print()
        print(f"🎉 Processing complete!")
        print(f"   Filename: {data['filename']}")
        print(f"   Size: {data['size_mb']:.2f} MB")
        
        # Save video
        output_filename = f"output_{data['filename']}"
        video_data = base64.b64decode(data['video_data'])
        
        with open(output_filename, 'wb') as f:
            f.write(video_data)
        
        print(f"   Saved to: {output_filename}")
        print()
    else:
        print()
        print(f"❌ Processing failed")
        print(f"   Error: {data.get('error', 'Unknown error')}")
        print()
    
    current_job_id = None
    
    # Disconnect after receiving result
    print("Disconnecting...")
    sio.disconnect()


@sio.on('error')
def on_error(data):
    """Handle errors."""
    print(f"❌ Error: {data.get('message', 'Unknown error')}")
    print()


def submit_job(server_url, video_path, audio_path, params=None):
    """
    Submit a video processing job.
    
    Args:
        server_url: Server URL (e.g., 'http://localhost:5000')
        video_path: Path to video file
        audio_path: Path to audio file
        params: Optional processing parameters dict
    """
    if params is None:
        params = {}
    
    # Check files exist
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return False
    
    print(f"📂 Loading files...")
    print(f"   Video: {video_path}")
    print(f"   Audio: {audio_path}")
    
    # Read and encode files
    with open(video_path, 'rb') as f:
        video_data = base64.b64encode(f.read()).decode('utf-8')
    
    with open(audio_path, 'rb') as f:
        audio_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"✅ Files loaded")
    print()
    
    # Connect to server
    print(f"🔌 Connecting to {server_url}...")
    try:
        sio.connect(server_url)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    # Submit job
    print(f"📤 Submitting job...")
    sio.emit('generate_video', {
        'video': video_data,
        'audio': audio_data,
        'video_filename': os.path.basename(video_path),
        'audio_filename': os.path.basename(audio_path),
        'params': params
    })
    
    # Wait for completion
    sio.wait()
    return True


if __name__ == "__main__":
    # Configuration
    SERVER_URL = "http://localhost:5000"
    
    # Check arguments
    if len(sys.argv) < 3:
        print("Usage: python client_example.py <video_file> <audio_file>")
        print()
        print("Example:")
        print("  python client_example.py input.mp4 voice.mp3")
        print()
        print("With effects:")
        print("  python client_example.py input.mp4 voice.mp3 --fade-in --zoom 1.2")
        sys.exit(1)
    
    video_file = sys.argv[1]
    audio_file = sys.argv[2]
    
    # Parse optional parameters
    params = {}
    
    # Simple argument parsing
    args = sys.argv[3:]
    i = 0
    while i < len(args):
        arg = args[i]
        
        if arg == '--fade-in':
            params['intro_animation'] = 'fade_in'
            params['intro_duration'] = 2.0
        elif arg == '--blur':
            params['intro_animation'] = 'blur_to_clear'
            params['intro_duration'] = 2.0
        elif arg == '--zoom' and i + 1 < len(args):
            params['zoom_factor'] = float(args[i + 1])
            i += 1
        elif arg == '--speed' and i + 1 < len(args):
            params['video_speed'] = float(args[i + 1])
            i += 1
        elif arg == '--saturation' and i + 1 < len(args):
            params['saturation'] = float(args[i + 1])
            i += 1
        elif arg == '--bw':
            params['saturation'] = 0.0
        elif arg == '--color' and i + 1 < len(args):
            params['color_overlay'] = args[i + 1]
            params['color_overlay_opacity'] = 0.2
            i += 1
        
        i += 1
    
    # Display header
    print("="*60)
    print("VIDEO PROCESSING CLIENT")
    print("="*60)
    print()
    
    if params:
        print("📊 Effects enabled:")
        for key, value in params.items():
            print(f"   {key}: {value}")
        print()
    
    # Submit job
    submit_job(SERVER_URL, video_file, audio_file, params)
