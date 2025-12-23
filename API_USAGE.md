# Advanced Video Processing API - Usage Guide

## API Endpoint

**POST** `/generate`

## Basic Usage

Upload a video and audio file:

```bash
curl -X POST http://localhost:5000/generate \
  -F "video=@input.mp4" \
  -F "audio=@voice.mp3" \
  -o output.mp4
```

## Advanced Parameters

### Audio Control

#### Original Audio Volume
Adjust volume of original video audio (0.0 - 2.0):
```bash
-F "original_audio_volume=0.5"  # 50% volume
-F "original_audio_volume=1.5"  # 150% volume
```

#### Uploaded Audio Volume
Adjust volume of uploaded audio file (0.0 - 2.0):
```bash
-F "uploaded_audio_volume=1.2"  # 120% volume
```

#### Audio Noise
Add pink noise to audio (0.0 - 1.0):
```bash
-F "audio_noise=0.1"  # 10% noise
```

### Video Effects

#### Video Speed
Adjust playback speed (0.5 - 2.0):
```bash
-F "video_speed=1.2"   # 1.2x faster
-F "video_speed=0.8"   # 0.8x slower
```

#### Zoom
Zoom in or out (0.5 - 2.0):
```bash
-F "zoom_factor=1.1"  # 110% zoom in
-F "zoom_factor=0.9"  # 90% zoom out
```

#### Saturation
Adjust color saturation (0.0 - 2.0):
```bash
-F "saturation=0.0"   # Black and white
-F "saturation=1.0"   # Normal colors  
-F "saturation=1.5"   # 150% saturated colors
```

#### Color Overlay
Add color tint with opacity:
```bash
-F "color_overlay=#ff0000" \
-F "color_overlay_opacity=0.2"  # 20% red overlay
```

#### Intro Animation
Add intro effect:
```bash
# Blur to clear
-F "intro_animation=blur_to_clear" \
-F "intro_duration=3.0"  # 3 seconds

# Fade in
-F "intro_animation=fade_in" \
-F "intro_duration=2.0"  # 2 seconds
```

## Complete Examples

### Example 1: Loud Audio + Fast Speed
```bash
curl -X POST http://localhost:5000/generate \
  -F "video=@input.mp4" \
  -F "audio=@voice.mp3" \
  -F "uploaded_audio_volume=1.5" \
  -F "video_speed=1.2" \
  -o fast_loud.mp4
```

### Example 2: Cinematic Effect
```bash
curl -X POST http://localhost:5000/generate \
  -F "video=@input.mp4" \
  -F "audio=@voice.mp3" \
  -F "zoom_factor=1.1" \
  -F "color_overlay=#1a1a1a" \
  -F "color_overlay_opacity=0.15" \
  -F "intro_animation=blur_to_clear" \
  -F "intro_duration=3.0" \
  -o cinematic.mp4
```

### Example 3: All Effects Combined
```bash
curl -X POST http://localhost:5000/generate \
  -F "video=@input.mp4" \
  -F "audio=@voice.mp3" \
  -F "original_audio_volume=0.3" \
  -F "uploaded_audio_volume=1.8" \
  -F "audio_noise=0.05" \
  -F "video_speed=1.15" \
  -F "zoom_factor=1.05" \
  -F "color_overlay=#ff6b6b" \
  -F "color_overlay_opacity=0.1" \
  -F "intro_animation=fade_in" \
  -F "intro_duration=2.5" \
  -o full_effects.mp4
```

## Response

**Success (200):**
Returns the processed video file as MP4.

**Error (400):**
```json
{
  "error": "Invalid parameters",
  "details": [
    "video_speed must be between 0.5 and 2.0"
  ]
}
```

**Error (500):**
```json
{
  "error": "Processing failed",
  "message": "Video processing failed. Check server logs."
}
```

## Parameter Defaults

| Parameter | Default | Min | Max |
|-----------|---------|-----|-----|
| original_audio_volume | 1.0 | 0.0 | 2.0 |
| uploaded_audio_volume | 1.0 | 0.0 | 2.0 |
| audio_noise | 0.0 | 0.0 | 1.0 |
| video_speed | 1.0 | 0.5 | 2.0 |
| zoom_factor | 1.0 | 0.5 | 2.0 |
| saturation | 1.0 | 0.0 | 2.0 |
| color_overlay_opacity | 0.0 | 0.0 | 1.0 |
| intro_duration | 2.0 | 0.0 | 5.0 |

## Tips

- **Audio Balance**: Use `original_audio_volume=0.5` and `up loaded_audio_volume=1.5` to emphasize voiceover
- **Speed**: 1.1-1.3x is good for dynamic content without being too fast
- **Zoom**: 1.05-1.1x adds subtle cinematic feel
- **Color Overlay**: Keep opacity under 0.3 for subtle effects
- **Noise**: 0.05-0.1 adds texture without being annoying
