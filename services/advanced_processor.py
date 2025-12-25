"""Advanced video processing with multiple effects."""

import os
import subprocess
import random
from datetime import datetime, timedelta
from models.processing_params import ProcessingParams




def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def process_video_with_effects(
    video_path,
    audio_path,
    output_path,
    params: ProcessingParams,
    target_width=1920,
    target_height=1080,
    fps=90,
    high_quality=True,
    fake_metadata=True,
    progress_callback=None
):
    """
    Process video with advanced effects including audio/video manipulations.
    
    Args:
        video_path (str): Input video path
        audio_path (str): Input audio path for overlay
        output_path (str): Output video path
        params (ProcessingParams): Processing parameters for effects
        target_width (int): Target width
        target_height (int): Target height  
        fps (int): Frames per second
        high_quality (bool): Use high quality encoding
        fake_metadata (bool): Add CapCut metadata
        progress_callback (callable): Progress callback function
        
    Returns:
        str: Output path if successful, None otherwise
    """
    
    def log(message):
        if progress_callback:
            progress_callback(message)
        else:
            print(message)
    
    try:
        # Validate parameters
        errors = params.validate()
        if errors:
            for error in errors:
                log(f"❌ Parameter error: {error}")
            return None
        
        # Check files exist
        if not os.path.exists(video_path):
            log(f"❌ Video not found: {video_path}")
            return None
        if not os.path.exists(audio_path):
            log(f"❌ Audio not found: {audio_path}")
            return None
        
        log(f"🎬 Processing video with effects...")
        log(f"📹 Video: {video_path}")
        log(f"🎵 Audio: {audio_path}")
        
        # Get video duration
        try:
            duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", video_path]
            # Also tpool this check just in case
            video_duration = float(subprocess.check_output(duration_cmd, universal_newlines=True).strip())
            log(f"📏 Duration: {video_duration:.2f}s")
        except Exception as e:
            log(f"⚠️  Could not get duration: {e}")
            video_duration = 0
        
        # Build FFmpeg command
        ffmpeg_cmd = ["ffmpeg", "-y", "-threads", "0", "-hwaccel", "auto"]
        
        # Input files
        ffmpeg_cmd.extend(["-i", video_path, "-i", audio_path])
        
        # Build filter complex
        video_filters = []
        audio_filters = []
        
        # === VIDEO FILTERS ===
        
        # 1. Video speed
        if params.video_speed != 1.0:
            speed_factor = 1.0 / params.video_speed
            video_filters.append(f"setpts={speed_factor}*PTS")
            log(f"⏩ Speed: {params.video_speed}x")
        
        # 2. Scale and pad to target resolution
        video_filters.append(
            f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black"
        )
        
        # 3. Zoom
        if params.zoom_factor != 1.0:
            zoom = params.zoom_factor
            video_filters.append(f"scale=iw*{zoom}:ih*{zoom}")
            video_filters.append(f"crop={target_width}:{target_height}")
            log(f"🔍 Zoom: {zoom}x")
        
        # 4. Saturation (for black & white or color adjustments)
        if params.saturation != 1.0:
            if params.saturation == 0.0:
                # Full desaturation = black & white
                video_filters.append("hue=s=0")
                log(f"⬛ Black & White filter")
            else:
                # Adjust saturation
                video_filters.append(f"hue=s={params.saturation}")
                log(f"🎨 Saturation: {int(params.saturation*100)}%")
        
        # 5. Intro animation
        if params.intro_animation == "blur_to_clear" and params.intro_duration > 0:
            # Blur that fades to clear over intro_duration
            blur_amount = 20
            video_filters.append(
                f"boxblur={blur_amount}:enable='if(lt(t,{params.intro_duration}),1,0)'"
            )
            log(f"✨ Intro: blur to clear ({params.intro_duration}s)")
        elif params.intro_animation == "fade_in" and params.intro_duration > 0:
            video_filters.append(f"fade=in:st=0:d={params.intro_duration}")
            log(f"✨ Intro: fade in ({params.intro_duration}s)")
        
        # 6. Color overlay
        if params.color_overlay and params.color_overlay_opacity > 0:
            try:
                r, g, b = hex_to_rgb(params.color_overlay)
                opacity = params.color_overlay_opacity
                inv_opacity = 1.0 - opacity
                
                # Apply color tint using geq
                video_filters.append(
                    f"geq="
                    f"r='r(X,Y)*{inv_opacity}+{r}*{opacity}':"
                    f"g='g(X,Y)*{inv_opacity}+{g}*{opacity}':"
                    f"b='b(X,Y)*{inv_opacity}+{b}*{opacity}'"
                )
                log(f"🎨 Color overlay: {params.color_overlay} ({int(opacity*100)}%)")
            except Exception as e:
                log(f"⚠️  Invalid color overlay: {e}")
        
        # Set FPS and format
        video_filters.append(f"fps={fps},format=yuv420p")
        
        # Combine video filters
        video_filter_str = ",".join(video_filters)
        full_video_filter = f"[0:v]{video_filter_str}[v_out]"
        
        # === AUDIO FILTERS ===
        
        # 1. Adjust original video audio volume
        if params.original_audio_volume != 1.0:
            audio_filters.append(f"[0:a]volume={params.original_audio_volume}[orig_a]")
            log(f"🔊 Original audio: {int(params.original_audio_volume*100)}%")
        else:
            audio_filters.append("[0:a]anull[orig_a]")
        
        # 2. Adjust uploaded audio volume
        uploaded_audio_label = "[1:a]"
        if params.uploaded_audio_volume != 1.0:
            audio_filters.append(f"[1:a]volume={params.uploaded_audio_volume}[upload_a]")
            uploaded_audio_label = "[upload_a]"
            log(f"🔊 Uploaded audio: {int(params.uploaded_audio_volume*100)}%")
        else:
            audio_filters.append("[1:a]anull[upload_a]")
            uploaded_audio_label = "[upload_a]"
        
        # 3. Add audio noise if requested
        if params.audio_noise > 0 and video_duration > 0:
            noise_amount = params.audio_noise
            audio_filters.append(
                f"anoisesrc=d={video_duration}:c=pink:r=48000:a={noise_amount}[noise]"
            )
            audio_filters.append(
                f"{uploaded_audio_label}[noise]amix=inputs=2:duration=first[upload_a_noisy]"
            )
            uploaded_audio_label = "[upload_a_noisy]"
            log(f"🔉 Audio noise: {int(noise_amount*100)}%")
        
        # 4. Loop uploaded audio to match video duration
        if video_duration > 0:
            audio_filters.append(
                f"{uploaded_audio_label}aloop=loop=-1:size=2e+09,atrim=end={video_duration}[upload_final]"
            )
        else:
            audio_filters.append(
                f"{uploaded_audio_label}aloop=loop=-1:size=2e+09[upload_final]"
            )
        
        # 5. Mix original and uploaded audio
        audio_filters.append("[orig_a][upload_final]amix=inputs=2:duration=longest[a_out]")
        
        # Combine all filters
        filter_complex = ";".join([full_video_filter] + audio_filters)
        
        ffmpeg_cmd.extend(["-filter_complex", filter_complex])
        ffmpeg_cmd.extend(["-map", "[v_out]", "-map", "[a_out]"])
        
        if video_duration <= 0:
            ffmpeg_cmd.append("-shortest")
        
        # GPU Detection and encoding
        from models.settings import Settings
        from services.video_processor import check_gpu_available
        
        gpu_type = Settings.get_gpu_type()
        has_gpu, encoder = check_gpu_available(gpu_type)
        
        if has_gpu:
            log(f"🎮 Using {gpu_type.upper()} GPU ({encoder})")
        else:
            log(f"💻 Using CPU encoding ({encoder})")
        
        # Quality settings
        if high_quality:
            if has_gpu:
                if gpu_type == "nvidia":
                    video_params = [
                        "-c:v", encoder, "-preset", "p7", "-tune", "hq",
                        "-rc", "vbr", "-cq", "18", "-b:v", "6M",
                        "-maxrate", "10M", "-pix_fmt", "yuv420p"
                    ]
                else:  # AMD
                    video_params = [
                        "-c:v", encoder, "-quality", "quality",
                        "-rc", "vbr_latency", "-qp_i", "18", "-qp_p", "18",
                        "-b:v", "6M", "-maxrate", "10M", "-pix_fmt", "yuv420p"
                    ]
            else:
                video_params = [
                    "-c:v", encoder, "-preset", "slow", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-threads", "0"
                ]
        else:
            if has_gpu:
                if gpu_type == "nvidia":
                    video_params = [
                        "-c:v", encoder, "-preset", "p4", "-tune", "hq",
                        "-b:v", "2M"
                    ]
                else:  # AMD
                    video_params = [
                        "-c:v", encoder, "-quality", "balanced",
                        "-rc", "vbr_latency", "-b:v", "2M"
                    ]
            else:
                video_params = [
                    "-c:v", encoder, "-preset", "medium",
                    "-crf", "23", "-threads", "0"
                ]
        
        audio_params = ["-c:a", "aac", "-b:a", "320k" if high_quality else "128k"]
        
        ffmpeg_cmd.extend(video_params)
        ffmpeg_cmd.extend(audio_params)
        
        # Add metadata if requested
        if fake_metadata:
            log("📝 Adding CapCut metadata...")
            random_days = random.randint(0, 30)
            creation_time = datetime.now() - timedelta(days=random_days)
            creation_time_str = creation_time.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
            version = random.choice(["3.9.0", "4.0.0", "4.1.0"])
            
            metadata_params = [
                "-metadata", f"creation_time={creation_time_str}",
                "-metadata", "encoder=CapCut",
                "-metadata", f"comment=Edited with CapCut {version}",
                "-metadata", "software=CapCut Video Editor"
            ]
            ffmpeg_cmd.extend(metadata_params)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        ffmpeg_cmd.append(output_path)
        
        # Execute
        log("⚙️  Executing FFmpeg...")
        log(' '.join(f'"{arg}"' if ' ' in arg else arg for arg in ffmpeg_cmd))
        
        # Capture both stdout and stderr for debugging
        log("🐛 DEBUG: About to execute FFmpeg...")
        
        def run_ffmpeg():
            return subprocess.run(
                ffmpeg_cmd, 
                check=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace'
            )
            
        process = run_ffmpeg()
        log("🐛 DEBUG: FFmpeg execution completed.")
        
        # Log any FFmpeg output (usually goes to stderr)
        if process.stderr:
            # Only log first/last few lines to avoid spam
            stderr_lines = process.stderr.strip().split('\n')
            if len(stderr_lines) > 10:
                log("📋 FFmpeg output (first 5 lines):")
                for line in stderr_lines[:5]:
                    if line.strip():
                        log(f"   {line}")
                log(f"   ... ({len(stderr_lines)-10} lines omitted) ...")
                log("📋 FFmpeg output (last 5 lines):")
                for line in stderr_lines[-5:]:
                    if line.strip():
                        log(f"   {line}")
            else:
                log("📋 FFmpeg output:")
                for line in stderr_lines:
                    if line.strip():
                        log(f"   {line}")
        
        log(f"✅ Processing complete! Saved to: {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        log(f"❌ FFmpeg error during processing")
        return None
    except Exception as e:
        log(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None
