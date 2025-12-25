# Socket.IO Video Processing API - Usage Guide

## Overview

The video processing server uses **Socket.IO** for real-time bidirectional communication. Videos are processed using **Google Cloud Storage (GCS) URLs** instead of uploading files directly.

## Connection

### Client-Side (JavaScript/TypeScript)

```typescript
import { io } from 'socket.io-client'

const socket = io('http://localhost:5000', {
    transports: ['polling', 'websocket'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    timeout: 20000
})
```

### Python Client

```python
import socketio

sio = socketio.Client()
sio.connect('http://localhost:5000')
```

## Events

### Client → Server

#### `generate_video`
Send video processing request using GCS URLs.

**Required Parameters:**
```typescript
{
    video_url: string,      // GCS URL of video to process
    audio_url: string,      // GCS URL of audio (can be same as video_url)
    params: {
        // Audio Control
        original_audio_volume?: number,    // 0.0 - 2.0, default: 1.0
        uploaded_audio_volume?: number,    // 0.0 - 2.0, default: 1.0
        audio_noise?: number,              // 0.0 - 1.0, default: 0.0
        
        // Video Effects
        video_speed?: number,              // 0.5 - 2.0, default: 1.0
        zoom_factor?: number,              // 0.5 - 2.0, default: 1.0
        saturation?: number,               // 0.0 - 2.0, default: 1.0
        
        // Color Overlay
        color_overlay?: string,            // Hex color, e.g. "#ff0000"
        color_overlay_opacity?: number,    // 0.0 - 1.0, default: 0.0
        
        // Intro Animation
        intro_animation?: string,          // "none" | "blur_to_clear" | "fade_in"
        intro_duration?: number            // 0.0 - 5.0, default: 2.0
    }
}
```

**Example:**
```typescript
socket.emit('generate_video', {
    video_url: 'https://storage.googleapis.com/bucket/video.mp4',
    audio_url: 'https://storage.googleapis.com/bucket/video.mp4',
    params: {
        video_speed: 1.2,
        zoom_factor: 1.05,
        saturation: 1.1,
        intro_animation: 'fade_in',
        intro_duration: 2.5
    }
})
```

### Server → Client

#### `connected`
Sent when client successfully connects.

```typescript
{
    client_id: string,
    message: string
}
```

#### `job_queued`
Sent when video processing job is added to queue.

```typescript
{
    job_id: string,
    position: number    // Position in queue
}
```

#### `queue_update`
Sent periodically to all connected clients.

```typescript
{
    connected_users: number,
    queue_length: number,
    processing: boolean,
    your_position?: number    // Your position in queue (if queued)
}
```

#### `log`
Real-time processing logs.

```typescript
{
    type: 'info' | 'error' | 'success',
    message: string,
    timestamp: string,
    progress?: number    // 0-100 (if available)
}
```

#### `processing_complete`
Sent when video processing is finished.

**Success:**
```typescript
{
    success: true,
    job_id: string,
    video_url: string,    // GCS URL of processed video
    size_mb: number
}
```

**Error:**
```typescript
{
    success: false,
    error: string
}
```

#### `error`
Sent when an error occurs.

```typescript
{
    message: string
}
```

## Complete Example (TypeScript/React)

```typescript
import { io, Socket } from 'socket.io-client'
import { toast } from 'sonner'

const connectToServer = () => {
    const socket = io('http://localhost:5000', {
        transports: ['polling', 'websocket'],
        reconnection: true
    })

    // Connection events
    socket.on('connect', () => {
        console.log('✅ Connected to server')
    })

    socket.on('connected', (data) => {
        console.log('Server message:', data.message)
    })

    // Queue events
    socket.on('job_queued', (data) => {
        toast.success(`Video queued at position ${data.position}`)
    })

    socket.on('queue_update', (data) => {
        console.log('Queue status:', data)
    })

    // Processing events
    socket.on('log', (data) => {
        console.log(`[${data.type}]`, data.message)
        if (data.progress) {
            console.log('Progress:', data.progress + '%')
        }
    })

    socket.on('processing_complete', (data) => {
        if (data.success && data.video_url) {
            toast.success('Video processed!')
            // Download or display video
            window.open(data.video_url, '_blank')
        } else {
            toast.error(data.error || 'Processing failed')
        }
    })

    // Error events
    socket.on('error', (data) => {
        toast.error(data.message)
    })

    return socket
}

// Send processing request
const processVideo = (socket: Socket, videoUrl: string) => {
    socket.emit('generate_video', {
        video_url: videoUrl,
        audio_url: videoUrl,
        params: {
            video_speed: 1.15,
            zoom_factor: 1.05,
            intro_animation: 'fade_in',
            intro_duration: 2.0
        }
    })
}
```

## Complete Example (Python)

```python
import socketio
import time

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('✅ Connected to server')

@sio.on('connected')
def on_connected(data):
    print(f"Server: {data['message']}")

@sio.on('job_queued')
def on_job_queued(data):
    print(f"📥 Job queued at position {data['position']}")

@sio.on('log')
def on_log(data):
    print(f"[{data['type']}] {data['message']}")

@sio.on('processing_complete')
def on_complete(data):
    if data['success']:
        print(f"✅ Video URL: {data['video_url']}")
        print(f"📊 Size: {data['size_mb']:.2f} MB")
    else:
        print(f"❌ Error: {data['error']}")

# Connect to server
sio.connect('http://localhost:5000')

# Send processing request
sio.emit('generate_video', {
    'video_url': 'https://storage.googleapis.com/bucket/video.mp4',
    'audio_url': 'https://storage.googleapis.com/bucket/video.mp4',
    'params': {
        'video_speed': 1.2,
        'zoom_factor': 1.05,
        'saturation': 1.1
    }
})

# Wait for processing
sio.wait()
```

## Parameter Reference

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `original_audio_volume` | number | 1.0 | 0.0 | 2.0 | Original video audio volume |
| `uploaded_audio_volume` | number | 1.0 | 0.0 | 2.0 | Uploaded audio volume |
| `audio_noise` | number | 0.0 | 0.0 | 1.0 | Pink noise amount |
| `video_speed` | number | 1.0 | 0.5 | 2.0 | Playback speed multiplier |
| `zoom_factor` | number | 1.0 | 0.5 | 2.0 | Zoom level |
| `saturation` | number | 1.0 | 0.0 | 2.0 | Color saturation |
| `color_overlay` | string | null | - | - | Hex color (e.g. "#ff0000") |
| `color_overlay_opacity` | number | 0.0 | 0.0 | 1.0 | Overlay opacity |
| `intro_animation` | string | "none" | - | - | "none", "blur_to_clear", "fade_in" |
| `intro_duration` | number | 2.0 | 0.0 | 5.0 | Intro animation duration (seconds) |

## Tips & Best Practices

### Video URLs
- ✅ Use public GCS URLs for video/audio
- ✅ Ensure URLs are accessible from server
- ✅ Videos should be in common formats (MP4, MOV, etc.)

### Effect Recommendations
- **Audio Balance**: Use `original_audio_volume=0.5` and `uploaded_audio_volume=1.5` for clear voiceover
- **Speed**: 1.1-1.3x for dynamic content without being too fast
- **Zoom**: 1.05-1.1x for subtle cinematic feel
- **Color Overlay**: Keep opacity under 0.3 for natural look
- **Noise**: 0.05-0.1 adds texture without being annoying

### Performance
- Queue system handles multiple requests
- Real-time progress updates via `log` events
- Processed videos uploaded to GCS automatically
- Public URLs returned for easy download/sharing

## Server Configuration

### GCS Setup
1. Create GCS bucket (e.g., `eos_pages_content`)
2. Place credentials at `eos_reup_server/temp/json/credentials.json`
3. Update bucket name in `models/settings.py`:
   ```python
   GCP_BUCKET_NAME = "your-bucket-name"
   ```

### Running Server
```bash
cd eos_reup_server
.\venv\Scripts\activate
py .\app.py
# Select option 2: "Run Socket Server"
```

Server will run on `http://0.0.0.0:5000`

## Troubleshooting

### Connection Issues
- Ensure server is running on correct port
- Check firewall settings
- Verify Socket.IO client version compatibility

### Processing Errors
- Verify GCS URLs are public/accessible
- Check video file format compatibility
- Review server logs for detailed errors
- Ensure GCS credentials are properly configured

### Upload Failures
- Verify GCS bucket exists and is accessible
- Check credentials have write permissions
- Ensure bucket has uniform access enabled (not legacy ACL)
