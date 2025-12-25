# Socket.IO API Documentation

## Server Information

**URL**: `http://localhost:5000`  
**Protocol**: Socket.IO v4+  
**Transport**: WebSocket with polling fallback  
**Max File Size**: 500MB per file  

## Connection

### Python
```python
import socketio

# Create client
sio = socketio.Client()

# Connect to server
sio.connect('http://localhost:5000')

# Wait for events
sio.wait()
```

### JavaScript/Node.js
```javascript
const io = require('socket.io-client');

// Connect to server
const socket = io('http://localhost:5000');

// Handle events
socket.on('connected', (data) => {
  console.log('Connected:', data);
});
```

### Browser
```html
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
<script>
  const socket = io('http://localhost:5000');
</script>
```

## Events Reference

### Client → Server Events

#### `generate_video`
Submit a video processing job.

**Payload:**
```javascript
{
  video: string,              // Base64 encoded video file
  audio: string,              // Base64 encoded audio file
  video_filename: string,     // Original video filename (e.g., "input.mp4")
  audio_filename: string,     // Original audio filename (e.g., "audio.mp3")
  params: {
    // Audio parameters (optional)
    original_audio_volume: float,     // 0.0-2.0, default: 1.0
    uploaded_audio_volume: float,     // 0.0-2.0, default: 1.0
    audio_noise: float,               // 0.0-1.0, default: 0.0
    
    // Video parameters (optional)
    video_speed: float,               // 0.5-2.0, default: 1.0
    zoom_factor: float,               // 0.5-2.0, default: 1.0
    saturation: float,                // 0.0-2.0, default: 1.0 (0.0=B&W)
    
    // Color overlay (optional)
    color_overlay: string,            // Hex color (e.g., "#ff0000")
    color_overlay_opacity: float,     // 0.0-1.0, default: 0.0
    
    // Intro animation (optional)
    intro_animation: string,          // "none", "fade_in", "blur_to_clear"
    intro_duration: float             // 0.0-5.0 seconds, default: 2.0
  }
}
```

**Example:**
```python
# Python
sio.emit('generate_video', {
    'video': video_base64,
    'audio': audio_base64,
    'video_filename': 'my_video.mp4',
    'audio_filename': 'background.mp3',
    'params': {
        'intro_animation': 'fade_in',
        'intro_duration': 2.0,
        'zoom_factor': 1.2,
        'saturation': 1.3,
        'color_overlay': '#ff6b6b',
        'color_overlay_opacity': 0.15
    }
})
```

```javascript
// JavaScript
socket.emit('generate_video', {
  video: videoBase64,
  audio: audioBase64,
  video_filename: 'my_video.mp4',
  audio_filename: 'background.mp3',
  params: {
    intro_animation: 'fade_in',
    intro_duration: 2.0,
    zoom_factor: 1.2,
    saturation: 1.3
  }
});
```

---

### Server → Client Events

#### `connected`
Sent when client successfully connects to server.

**Payload:**
```javascript
{
  client_id: string,        // Unique client session ID
  message: string           // Welcome message
}
```

**Example Response:**
```json
{
  "client_id": "abc123def456",
  "message": "Connected to video processing server"
}
```

**Handler:**
```python
# Python
@sio.on('connected')
def on_connected(data):
    print(f"Client ID: {data['client_id']}")
    print(f"Message: {data['message']}")
```

```javascript
// JavaScript
socket.on('connected', (data) => {
  console.log('Client ID:', data.client_id);
  console.log('Message:', data.message);
});
```

---

#### `queue_update`
Broadcast to all connected clients when queue status changes.

**Payload:**
```javascript
{
  connected_users: int,      // Total number of connected clients
  queue_length: int,         // Number of jobs waiting in queue
  processing: boolean,       // Is a job currently being processed?
  your_position: int | null  // Your position in queue (null if not queued)
}
```

**Example Response:**
```json
{
  "connected_users": 3,
  "queue_length": 2,
  "processing": true,
  "your_position": 2
}
```

**Handler:**
```python
# Python
@sio.on('queue_update')
def on_queue_update(data):
    print(f"Connected users: {data['connected_users']}")
    print(f"Queue length: {data['queue_length']}")
    if data['your_position']:
        print(f"Your position: {data['your_position']}")
```

```javascript
// JavaScript
socket.on('queue_update', (data) => {
  console.log('Connected users:', data.connected_users);
  console.log('Queue length:', data.queue_length);
  if (data.your_position) {
    console.log('Your position:', data.your_position);
  }
});
```

---

#### `job_queued`
Sent to client when their job is successfully added to queue.

**Payload:**
```javascript
{
  job_id: string,       // Unique job identifier (UUID)
  position: int         // Position in queue (1 = next to process)
}
```

**Example Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "position": 3
}
```

**Handler:**
```python
# Python
@sio.on('job_queued')
def on_job_queued(data):
    print(f"Job ID: {data['job_id']}")
    print(f"Queue position: {data['position']}")
```

```javascript
// JavaScript
socket.on('job_queued', (data) => {
  console.log('Job ID:', data.job_id);
  console.log('Position:', data.position);
});
```

---

#### `log`
Real-time progress logs sent to the **job owner only** (not broadcast).

**Payload:**
```javascript
{
  type: string,         // "info", "success", "error", "progress"
  message: string,      // Log message
  timestamp: string,    // ISO 8601 timestamp
  progress: int | null  // Progress percentage (0-100), if available
}
```

**Example Responses:**
```json
// Info log
{
  "type": "info",
  "message": "🎬 Starting video processing...",
  "timestamp": "2025-12-23T14:50:34.123456"
}

// Progress log
{
  "type": "info",
  "message": "⚙️ Processing: 45%",
  "timestamp": "2025-12-23T14:50:45.678901",
  "progress": 45
}

// Success log
{
  "type": "success",
  "message": "✅ Processing complete!",
  "timestamp": "2025-12-23T14:51:20.456789",
  "progress": 100
}

// Error log
{
  "type": "error",
  "message": "❌ Invalid parameters",
  "timestamp": "2025-12-23T14:50:35.123456"
}
```

**Handler:**
```python
# Python
@sio.on('log')
def on_log(data):
    print(f"[{data['type']}] {data['message']}")
    if data.get('progress'):
        print(f"Progress: {data['progress']}%")
```

```javascript
// JavaScript
socket.on('log', (data) => {
  console.log(`[${data.type}] ${data.message}`);
  if (data.progress) {
    console.log(`Progress: ${data.progress}%`);
  }
});
```

---

#### `processing_complete`
Sent when video processing finishes (success or failure).

**Success Payload:**
```javascript
{
  success: true,
  job_id: string,           // Job identifier
  filename: string,         // Output filename
  video_data: string,       // Base64 encoded processed video
  size_mb: float            // File size in megabytes
}
```

**Failure Payload:**
```javascript
{
  success: false,
  error: string             // Error message
}
```

**Example Success Response:**
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "20251223_145034_output.mp4",
  "video_data": "AAAAIGZ0eXBpc29tAAACAGlzb21pc28y...",
  "size_mb": 12.45
}
```

**Example Failure Response:**
```json
{
  "success": false,
  "error": "Invalid parameters: video_speed must be between 0.5 and 2.0"
}
```

**Handler:**
```python
# Python
@sio.on('processing_complete')
def on_complete(data):
    if data['success']:
        # Save video
        video_bytes = base64.b64decode(data['video_data'])
        with open(f"output_{data['filename']}", 'wb') as f:
            f.write(video_bytes)
        print(f"Saved: output_{data['filename']}")
    else:
        print(f"Error: {data['error']}")
```

```javascript
// JavaScript
socket.on('processing_complete', (data) => {
  if (data.success) {
    // Download video
    const blob = base64ToBlob(data.video_data, 'video/mp4');
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = data.filename;
    a.click();
  } else {
    console.error('Error:', data.error);
  }
});
```

---

#### `error`
Sent when an error occurs during request processing.

**Payload:**
```javascript
{
  message: string       // Error description
}
```

**Example Response:**
```json
{
  "message": "Missing video or audio data"
}
```

**Handler:**
```python
# Python
@sio.on('error')
def on_error(data):
    print(f"Error: {data['message']}")
```

```javascript
// JavaScript
socket.on('error', (data) => {
  console.error('Error:', data.message);
});
```

---

## Complete Client Example

### Python Full Example
```python
import socketio
import base64
import os

# Create client
sio = socketio.Client()

# Event handlers
@sio.on('connected')
def on_connected(data):
    print(f"✅ Connected: {data['client_id']}")

@sio.on('queue_update')
def on_queue_update(data):
    print(f"📊 Users: {data['connected_users']} | Queue: {data['queue_length']}")

@sio.on('log')
def on_log(data):
    if data.get('progress'):
        print(f"⏳ {data['message']} ({data['progress']}%)")
    else:
        print(f"ℹ️ {data['message']}")

@sio.on('job_queued')
def on_job_queued(data):
    print(f"📥 Job queued: {data['job_id']} (position {data['position']})")

@sio.on('processing_complete')
def on_complete(data):
    if data['success']:
        # Save result
        video_bytes = base64.b64decode(data['video_data'])
        with open(data['filename'], 'wb') as f:
            f.write(video_bytes)
        print(f"✅ Saved: {data['filename']}")
    else:
        print(f"❌ Error: {data['error']}")
    sio.disconnect()

# Connect
sio.connect('http://localhost:5000')

# Read and encode files
with open('video.mp4', 'rb') as f:
    video_data = base64.b64encode(f.read()).decode('utf-8')
with open('audio.mp3', 'rb') as f:
    audio_data = base64.b64encode(f.read()).decode('utf-8')

# Submit job
sio.emit('generate_video', {
    'video': video_data,
    'audio': audio_data,
    'video_filename': 'video.mp4',
    'audio_filename': 'audio.mp3',
    'params': {
        'intro_animation': 'fade_in',
        'zoom_factor': 1.2,
        'saturation': 1.3
    }
})

# Wait for completion
sio.wait()
```

### JavaScript Full Example
```javascript
const io = require('socket.io-client');
const fs = require('fs');

// Connect
const socket = io('http://localhost:5000');

// Event handlers
socket.on('connected', (data) => {
  console.log('✅ Connected:', data.client_id);
  
  // Read and encode files
  const video = fs.readFileSync('video.mp4').toString('base64');
  const audio = fs.readFileSync('audio.mp3').toString('base64');
  
  // Submit job
  socket.emit('generate_video', {
    video: video,
    audio: audio,
    video_filename: 'video.mp4',
    audio_filename: 'audio.mp3',
    params: {
      intro_animation: 'fade_in',
      zoom_factor: 1.2,
      saturation: 1.3
    }
  });
});

socket.on('queue_update', (data) => {
  console.log(`📊 Users: ${data.connected_users} | Queue: ${data.queue_length}`);
});

socket.on('log', (data) => {
  if (data.progress) {
    console.log(`⏳ ${data.message} (${data.progress}%)`);
  } else {
    console.log(`ℹ️ ${data.message}`);
  }
});

socket.on('job_queued', (data) => {
  console.log(`📥 Job queued: ${data.job_id} (position ${data.position})`);
});

socket.on('processing_complete', (data) => {
  if (data.success) {
    const buffer = Buffer.from(data.video_data, 'base64');
    fs.writeFileSync(data.filename, buffer);
    console.log(`✅ Saved: ${data.filename}`);
  } else {
    console.error(`❌ Error: ${data.error}`);
  }
  socket.disconnect();
});

socket.on('error', (data) => {
  console.error('❌ Error:', data.message);
});
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Missing video or audio data" | Required fields not provided | Include both `video` and `audio` in payload |
| "Failed to decode files" | Invalid base64 encoding | Ensure files are properly base64 encoded |
| "Invalid parameters" | Parameter out of range | Check parameter validation rules |
| "Processing failed" | FFmpeg error | Check server logs for details |

### Parameter Validation Rules

| Parameter | Type | Range | Default |
|-----------|------|-------|---------|
| original_audio_volume | float | 0.0 - 2.0 | 1.0 |
| uploaded_audio_volume | float | 0.0 - 2.0 | 1.0 |
| audio_noise | float | 0.0 - 1.0 | 0.0 |
| video_speed | float | 0.5 - 2.0 | 1.0 |
| zoom_factor | float | 0.5 - 2.0 | 1.0 |
| saturation | float | 0.0 - 2.0 | 1.0 |
| color_overlay_opacity | float | 0.0 - 1.0 | 0.0 |
| intro_animation | string | "none", "fade_in", "blur_to_clear" | "none" |
| intro_duration | float | 0.0 - 5.0 | 2.0 |

## Testing

### Test Connection
```python
import socketio

sio = socketio.Client()
sio.connect('http://localhost:5000')
print("Connected successfully!")
sio.disconnect()
```

### Test with Small Files
Start with small test files (< 10MB) to verify the flow before using large videos.

## Related Documentation

- **Usage Guide**: `socketio_usage.md`
- **Client Example**: `client_example.py`
- **Architecture**: `issue.md`
- **Effects**: `API_USAGE.md`
