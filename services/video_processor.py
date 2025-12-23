"""
Video processing module with FFmpeg integration.
Supports GPU-accelerated video encoding and concatenation.
"""

import os
import json
import subprocess
import random
from datetime import datetime, timedelta


def check_gpu_available(gpu_type="nvidia"):
    """
    Kiểm tra xem GPU có khả dụng hay không.
    
    Args:
        gpu_type (str): Loại GPU ('nvidia' hoặc 'amd')
    
    Returns:
        tuple: (bool, str) - (Có GPU hay không, tên encoder)
    """
    gpu_type = gpu_type.lower()
    
    if gpu_type == "nvidia":
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            if result.returncode == 0:
                return True, "h264_nvenc"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    elif gpu_type == "amd":
        # AMD uses h264_amf encoder
        # Check if ffmpeg has amf support
        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                text=True
            )
            if "h264_amf" in result.stdout:
                return True, "h264_amf"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    return False, "libx264"


def process_single_video(
    video_path,
    audio_path,
    output_path="temp/video/output.mp4",
    target_width=1920,
    target_height=1080,
    fps=90,
   high_quality=True,
    fake_metadata=True,
    progress_callback=None
):
    """
    Xử lý một video đơn với audio overlay.
    
    Args:
        video_path (str): Đường dẫn đến video gốc.
        audio_path (str): Đường dẫn đến audio overlay.
        output_path (str): Đường dẫn file video đầu ra.
        target_width (int): Chiều rộng của video đầu ra.
        target_height (int): Chiều cao của video đầu ra.
        fps (int): Khung hình trên giây.
        high_quality (bool): True để dùng chất lượng cao.
        fake_metadata (bool): True để thêm metadata CapCut.
        progress_callback (callable, optional): Hàm callback để báo tiến trình.
    
    Returns:
        str: Đường dẫn đến file video đã xử lý nếu thành công, ngược lại None.
    """
    
    def log(message):
        """Helper function to log messages and call progress callback."""
        print(message)
        if progress_callback:
            progress_callback(message)
    
    try:
        # Check if files exist
        if not os.path.exists(video_path):
            log(f"Lỗi: Không tìm thấy video: {video_path}")
            return None
        
        if not os.path.exists(audio_path):
            log(f"Lỗi: Không tìm thấy audio: {audio_path}")
            return None
        
        log(f"🎬 Processing video: {video_path}")
        log(f"🎵 With audio: {audio_path}")
        
        # Get video duration
        try:
            duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", video_path]
            video_duration = float(subprocess.check_output(duration_cmd, universal_newlines=True).strip())
            log(f"📏 Video duration: {video_duration:.2f} seconds")
        except Exception as e:
            log(f"⚠️ Could not get video duration: {e}")
            video_duration = 0
        
        # Build FFmpeg command
        ffmpeg_cmd = ["ffmpeg", "-y"]
        ffmpeg_cmd.extend(["-threads", "0"])
        ffmpeg_cmd.extend(["-hwaccel", "auto"])
        
        # Input files
        ffmpeg_cmd.extend(["-i", video_path])
        ffmpeg_cmd.extend(["-i", audio_path])
        
        # Filter complex - scale video and process audio
        filter_complex = (
            f"[0:v:0]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
            f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"setsar=1,fps={fps},format=yuv420p[outv];"
        )
        
        # Audio processing - loop audio if shorter than video
        if video_duration > 0:
            filter_complex += f"[1:a:0]aloop=loop=-1:size=2e+09,atrim=end={video_duration}[outa]"
        else:
            filter_complex += "[1:a:0]aloop=loop=-1:size=2e+09[outa]"
        
        ffmpeg_cmd.extend(["-filter_complex", filter_complex])
        ffmpeg_cmd.extend(["-map", "[outv]", "-map", "[outa]"])
        
        if video_duration <= 0:
            ffmpeg_cmd.append("-shortest")
        
        # Check GPU availability based on settings
        from models.settings import Settings
        gpu_type = Settings.get_gpu_type()
        has_gpu, encoder = check_gpu_available(gpu_type)
        
        if has_gpu:
            if gpu_type == "nvidia":
                log(f"🎮 Using NVIDIA GPU hardware encoding ({encoder})")
            else:
                log(f"🎮 Using AMD GPU hardware encoding ({encoder})")
        else:
            log(f"💻 Using CPU software encoding ({encoder})")
            log("   ⚠️  Hardware encoding not available for selected GPU type")
        
        # Quality settings
        if high_quality:
            log("Using HIGH quality settings")
            if has_gpu:
                if gpu_type == "nvidia":
                    video_params = [
                        "-c:v", encoder,
                        "-preset", "p7", "-tune", "hq", "-rc", "vbr",
                        "-cq", "18", "-b:v", "6M", "-maxrate", "10M",
                        "-pix_fmt", "yuv420p",
                        "-rc-lookahead", "0",
                        "-surfaces", "1"
                    ]
                else:  # AMD
                    video_params = [
                        "-c:v", encoder,
                        "-quality", "quality",  # AMD preset: speed, balanced, quality
                        "-rc", "vbr_latency",
                        "-qp_i", "18", "-qp_p", "18",
                        "-b:v", "6M", "-maxrate", "10M",
                        "-pix_fmt", "yuv420p"
                    ]
            else:
                video_params = [
                    "-c:v", encoder,
                    "-preset", "slow", "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-threads", "0"
                ]
            audio_params = [
                "-c:a", "aac",
                "-b:a", "320k",
                "-ar", "48000",
                "-aac_coder", "fast",
                "-profile:a", "aac_low"
            ]
        else:
            log("Using NORMAL quality settings")
            if has_gpu:
                if gpu_type == "nvidia":
                    video_params = [
                        "-c:v", encoder,
                        "-preset", "p4", "-tune", "hq", "-b:v", "2M",
                        "-rc-lookahead", "0",
                        "-surfaces", "1"
                    ]
                else:  # AMD
                    video_params = [
                        "-c:v", encoder,
                        "-quality", "balanced",  # AMD preset: speed, balanced, quality
                        "-rc", "vbr_latency",
                        "-b:v", "2M",
                        "-pix_fmt", "yuv420p"
                    ]
            else:
                video_params = [
                    "-c:v", encoder,
                    "-preset", "medium", "-crf", "23",
                    "-threads", "0"
                ]
            audio_params = [
                "-c:a", "aac",
                "-b:a", "128k",
                "-aac_coder", "fast",
                "-profile:a", "aac_low"
            ]
        
        ffmpeg_cmd.extend(video_params)
        ffmpeg_cmd.extend(audio_params)
        
        # Add fake metadata
        if fake_metadata:
            log("📝 Adding CapCut metadata...")
            
            random_days = random.randint(0, 30)
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            creation_time = datetime.now() - timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
            creation_time_str = creation_time.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
            
            capcut_versions = ["3.9.0", "3.8.0", "3.7.0", "3.6.0", "4.0.0", "4.1.0"]
            version = random.choice(capcut_versions)
            
            metadata_params = [
                "-metadata", f"creation_time={creation_time_str}",
                "-metadata", "encoder=CapCut",
                "-metadata", f"comment=Edited with CapCut {version}",
                "-metadata", "software=CapCut Video Editor",
                "-metadata", f"application=com.lemon.lvoverseas_{version}",
                "-metadata:s:v:0", "handler_name=CapCut Video Handler",
                "-metadata:s:v:0", "vendor_id=capt",
                "-metadata:s:a:0", "handler_name=CapCut Audio Handler",
                "-metadata:s:a:0", "vendor_id=capt"
            ]
            ffmpeg_cmd.extend(metadata_params)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        ffmpeg_cmd.append(output_path)
        
        # Execute FFmpeg
        log("Executing FFmpeg command...")
        log(' '.join(f'"{arg}"' if ' ' in arg else arg for arg in ffmpeg_cmd))
        
        process = subprocess.run(ffmpeg_cmd, check=True, text=True, encoding='utf-8')
        
        log(f"✅ Video processed successfully! Saved to: {output_path}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        log(f"❌ FFmpeg error during processing")
        return None
    except Exception as e:
        log(f"❌ Unexpected error: {e}")
        return None


def merge_videos_template(
    output_path="temp/video/merged_video.mp4",
    high_quality=True,
    target_width=1920,
    target_height=1080,
    include_subtitles=True,
    language="en",
    fps=90,
    fake_metadata=True,
    voice_path=None,
    bgm_path=None,
    bgm_volume=0.05,
    progress_callback=None
):
    """
    Nối các video clip từ file template.json bằng GPU (NVIDIA h264_nvenc) hoặc CPU (libx264).
    Hàm này sẽ tự động phát hiện GPU và sử dụng hardware encoding nếu có, nếu không sẽ fallback về CPU.
    Tự động chuẩn hóa các video có độ phân giải khác nhau về cùng một kích thước trước khi nối.

    Args:
        output_path (str): Đường dẫn file video đầu ra.
        high_quality (bool): True để dùng thiết lập chất lượng cao, False cho chất lượng thường.
        target_width (int): Chiều rộng của video đầu ra.
        target_height (int): Chiều cao của video đầu ra.
        include_subtitles (bool): True để thêm phụ đề nếu có, False để bỏ qua phụ đề.
        language (str): Ngôn ngữ để chọn font phù hợp (vi/vietnamese cho tiếng Việt).
        fps (int): Khung hình trên giây (frames per second).
        fake_metadata (bool): True để thêm metadata giả mạo như CapCut, False để không thêm.
        voice_path (str, optional): Đường dẫn đến file giọng nói để thay thế âm thanh gốc. Nếu có, âm thanh video sẽ bị tắt.
        bgm_path (str, optional): Đường dẫn đến file nhạc nền. Nhạc nền sẽ chạy xuyên suốt video với âm lượng nhỏ.
        bgm_volume (float): Âm lượng nhạc nền (0.0 - 1.0), mặc định 0.05 (5%).
        progress_callback (callable, optional): Hàm callback để báo tiến trình (nhận chuỗi tin nhắn).

    Returns:
        str: Đường dẫn đến file video đã nối nếu thành công, ngược lại trả về None.
    """
    
    def log(message):
        """Helper function to log messages and call progress callback."""
        print(message)
        if progress_callback:
            progress_callback(message)
    
    try:
        # 1. Đọc danh sách video từ file JSON
        template_path = "temp/json/template.json"
        if not os.path.exists(template_path):
            log(f"Lỗi: Không tìm thấy file '{template_path}'.")
            return None
            
        with open(template_path, "r", encoding='utf-8') as f:
            template = json.load(f)['scenes']

        video_paths = []
        for scene in template:
            if 'video_path' in scene and scene['video_path']:
                video_path = os.path.normpath(scene['video_path'])
                if os.path.exists(video_path):
                    video_paths.append(video_path)
                else:
                    log(f"⚠️ Cảnh báo: Không tìm thấy video tại {video_path}")

        if not video_paths:
            log("Không tìm thấy video nào trong file template.json.")
            return None

        num_videos = len(video_paths)
        log(f"Bắt đầu nối {num_videos} video clips...")
        
        # Check if voice replacement is requested
        use_voice = voice_path and os.path.exists(voice_path)
        if use_voice:
            log(f"🎤 Sử dụng file giọng nói để thay thế âm thanh: {voice_path}")
        
        # Check if background music is requested
        use_bgm = bgm_path and os.path.exists(bgm_path)
        if use_bgm:
            log(f"🎵 Thêm nhạc nền: {bgm_path} (âm lượng: {int(bgm_volume*100)}%)")
        
        # Lấy thời lượng video tổng cộng (ước tính từ video đầu tiên)
        video_duration = 0
        if use_voice or use_bgm:
            try:
                duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "default=noprint_wrappers=1:nokey=1", video_paths[0]]
                video_duration = float(subprocess.check_output(duration_cmd, universal_newlines=True).strip())
                log(f"📏 Thời lượng video: {video_duration:.2f} giây")
            except Exception as e:
                log(f"⚠️ Không thể lấy thời lượng video: {e}, sẽ dùng -shortest")

        # 2. Xây dựng lệnh FFmpeg với các flag tối ưu tốc độ
        ffmpeg_cmd = ["ffmpeg", "-y"]
        # Thêm flag để tăng tốc độ xử lý
        ffmpeg_cmd.extend(["-threads", "0"])  # Tự động dùng tất cả CPU cores
        ffmpeg_cmd.extend(["-hwaccel", "auto"])  # Tự động dùng hardware acceleration nếu có
        
        for path in video_paths:
            ffmpeg_cmd.extend(["-i", path])
        
        # Add voice file as input if provided
        if use_voice:
            ffmpeg_cmd.extend(["-i", voice_path])
            voice_input_idx = num_videos  # Voice file index
        
        # Add background music as input if provided
        if use_bgm:
            ffmpeg_cmd.extend(["-i", bgm_path])
            bgm_input_idx = num_videos + (1 if use_voice else 0)  # BGM index

        # ==================== FILTER COMPLEX ====================
        # Tạo chuỗi filter_complex để scale, pad và sau đó concat
        filter_parts = []
        concat_inputs = ""
        for i in range(num_videos):
            # Với mỗi video, tạo một chuỗi filter để scale và pad nó về kích thước chuẩn
            filter_parts.append(
                f"[{i}:v:0]scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
                f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color=black,"
                f"setsar=1,fps={fps},format=yuv420p[v{i}]"
            )
            # Chuẩn bị các stream để đưa vào bộ lọc concat
            if not use_voice:
                concat_inputs += f"[v{i}][{i}:a:0]"
            else:
                concat_inputs += f"[v{i}]"

        # Nối tất cả các stream đã chuẩn hóa lại
        if use_voice:
            concat_filter_final = f"{concat_inputs}concat=n={num_videos}:v=1:a=0[outv]"
        else:
            concat_filter_final = f"{concat_inputs}concat=n={num_videos}:v=1:a=1[outv][outa]"
        
        log(f"🎥 Sử dụng FPS: {fps}")
        
        # Thêm phụ đề đẹp vào filter complex (chỉ khi include_subtitles=True)
        subtitle_path = "temp/videos/transcript.srt"
        if include_subtitles and os.path.exists(subtitle_path):
            log(f"📝 Thêm phụ đề từ: {subtitle_path}")
            subtitle_path_abs = os.path.abspath(subtitle_path).replace("\\", "/")
            subtitle_path_escaped = subtitle_path_abs.replace(":", "\\:")
            
            # Đường dẫn font tùy chỉnh
            font_dir = os.path.abspath("temp/fonts").replace("\\", "/")
            font_dir_escaped = font_dir.replace(":", "\\:")
            
            # Chọn font dựa trên ngôn ngữ
            if language.lower() in ["vi", "vietnamese", "tiếng việt"]:
                font_name = "Roboto-Medium"
                log(f"🔤 Sử dụng font Roboto-Medium cho tiếng Việt")
                
                subtitle_filter = f"[outv]subtitles='{subtitle_path_escaped}':fontsdir='{font_dir_escaped}':force_style='FontName={font_name},FontSize=12,PrimaryColour=&H95E3FF&,OutlineColour=&H38570D&,BorderStyle=1,Outline=2,Shadow=0,Bold=1,Alignment=2,MarginV=30'[outv_sub]"
                complex_filter_string = ";".join(filter_parts) + ";" + concat_filter_final + ";" + subtitle_filter
                output_video_label = "[outv_sub]"
            else:
                font_name = "Luckiest Guy"
                log(f"🔤 Sử dụng font Luckiest Guy")
                
                subtitle_filter = f"[outv]subtitles='{subtitle_path_escaped}':fontsdir='{font_dir_escaped}':force_style='FontName={font_name},FontSize=12,PrimaryColour=&H95E3FF&,OutlineColour=&H38570D&,BorderStyle=1,Outline=2,Shadow=0,Bold=1,Alignment=2,MarginV=30'[outv_sub]"
                complex_filter_string = ";".join(filter_parts) + ";" + concat_filter_final + ";" + subtitle_filter
                output_video_label = "[outv_sub]"
        else:
            if include_subtitles:
                log(f"⚠️ Không tìm thấy file phụ đề: {subtitle_path}")
            complex_filter_string = ";".join(filter_parts) + ";" + concat_filter_final
            output_video_label = "[outv]"

        # Xử lý audio riêng nếu có voice hoặc bgm
        if use_voice or use_bgm:
            audio_filters = []
            
            # Xử lý voice nếu có
            if use_voice:
                if video_duration > 0:
                    audio_filters.append(f"[{voice_input_idx}:a:0]aloop=loop=-1:size=2e+09,atrim=end={video_duration}[voice]")
                else:
                    audio_filters.append(f"[{voice_input_idx}:a:0]aloop=loop=-1:size=2e+09[voice]")
            
            # Xử lý background music nếu có
            if use_bgm:
                if video_duration > 0:
                    audio_filters.append(f"[{bgm_input_idx}:a:0]aloop=loop=-1:size=2e+09,atrim=end={video_duration},volume={bgm_volume}[bgm]")
                else:
                    audio_filters.append(f"[{bgm_input_idx}:a:0]aloop=loop=-1:size=2e+09,volume={bgm_volume}[bgm]")
            
            # Mix audio streams nếu có cả voice và bgm
            if use_voice and use_bgm:
                audio_filters.append("[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=2[outa]")
            elif use_voice:
                audio_filters.append("[voice]anull[outa]")
            elif use_bgm:
                if concat_filter_final.endswith("[outv][outa]"):
                    audio_filters.append("[outa][bgm]amix=inputs=2:duration=longest:dropout_transition=2[outa_final]")
                    output_audio_label = "[outa_final]"
                else:
                    output_audio_label = "[bgm]"
            
            # Kết hợp video filter và audio filter
            final_filter = complex_filter_string + ";" + ";".join(audio_filters)
            
            ffmpeg_cmd.extend(["-filter_complex", final_filter])
            
            # Map streams
            if use_bgm and not use_voice:
                ffmpeg_cmd.extend(["-map", output_video_label, "-map", output_audio_label])
            else:
                ffmpeg_cmd.extend(["-map", output_video_label, "-map", "[outa]"])
            
            # Nếu không lấy được duration, dùng -shortest
            if video_duration <= 0:
                ffmpeg_cmd.append("-shortest")
        else:
            # Không có voice hoặc bgm, dùng audio từ video gốc
            ffmpeg_cmd.extend(["-filter_complex", complex_filter_string])
            ffmpeg_cmd.extend(["-map", output_video_label, "-map", "[outa]"])

        # 3. Kiểm tra và chọn encoder (GPU hoặc CPU)
        from models.settings import Settings
        gpu_type = Settings.get_gpu_type()
        has_gpu, encoder = check_gpu_available(gpu_type)
        
        if has_gpu:
            if gpu_type == "nvidia":
                log(f"🎮 Phát hiện NVIDIA GPU - Sử dụng hardware encoding ({encoder})")
            else:
                log(f"🎮 Phát hiện AMD GPU - Sử dụng hardware encoding ({encoder})")
        else:
            log(f"💻 Không phát hiện GPU - Sử dụng software encoding ({encoder})")
            log("   ⚠️  Encoding sẽ chậm hơn nhưng vẫn hoạt động bình thường")

        # 4. Chọn thiết lập chất lượng với tối ưu tốc độ
        if high_quality:
            log("Sử dụng thiết lập chất lượng CAO.")
            if has_gpu:
                if gpu_type == "nvidia":
                    video_params = [
                        "-c:v", encoder,
                        "-preset", "p7", "-tune", "hq", "-rc", "vbr",
                        "-cq", "18", "-b:v", "6M", "-maxrate", "10M",
                        "-pix_fmt", "yuv420p",
                        "-rc-lookahead", "0",
                        "-surfaces", "1"
                    ]
                else:  # AMD
                    video_params = [
                        "-c:v", encoder,
                        "-quality", "quality",  # AMD preset: speed, balanced, quality
                        "-rc", "vbr_latency",
                        "-qp_i", "18", "-qp_p", "18",
                        "-b:v", "6M", "-maxrate", "10M",
                        "-pix_fmt", "yuv420p"
                    ]
            else:
                video_params = [
                    "-c:v", encoder,
                    "-preset", "slow", "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-threads", "0"
                ]
            audio_params = [
                "-c:a", "aac",
                "-b:a", "320k",
                "-ar", "48000",
                "-aac_coder", "fast",
                "-profile:a", "aac_low"
            ]
        else:
            log("Sử dụng thiết lập chất lượng THƯỜNG.")
            if has_gpu:
                if gpu_type == "nvidia":
                    video_params = [
                        "-c:v", encoder,
                        "-preset", "p4", "-tune", "hq", "-b:v", "2M",
                        "-rc-lookahead", "0",
                        "-surfaces", "1"
                    ]
                else:  # AMD
                    video_params = [
                        "-c:v", encoder,
                        "-quality", "balanced",  # AMD preset: speed, balanced, quality
                        "-rc", "vbr_latency",
                        "-b:v", "2M",
                        "-pix_fmt", "yuv420p"
                    ]
            else:
                video_params = [
                    "-c:v", encoder,
                    "-preset", "medium", "-crf", "23",
                    "-threads", "0"
                ]
            audio_params = [
                "-c:a", "aac",
                "-b:a", "128k",
                "-aac_coder", "fast",
                "-profile:a", "aac_low"
            ]

        ffmpeg_cmd.extend(video_params)
        ffmpeg_cmd.extend(audio_params)
        
        # 5. Thêm metadata giả mạo để trông như CapCut xuất (nếu được bật)
        if fake_metadata:
            log("📝 Thêm metadata giả mạo CapCut...")
            
            # Tạo timestamp ngẫu nhiên trong vòng 30 ngày gần đây
            random_days = random.randint(0, 30)
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            creation_time = datetime.now() - timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
            creation_time_str = creation_time.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
            
            # Random CapCut version
            capcut_versions = [
                "3.9.0",
                "3.8.0", 
                "3.7.0",
                "3.6.0",
                "4.0.0",
                "4.1.0"
            ]
            version = random.choice(capcut_versions)
            
            metadata_params = [
                "-metadata", f"creation_time={creation_time_str}",
                "-metadata", "encoder=CapCut",
                "-metadata", f"comment=Edited with CapCut {version}",
                "-metadata", "software=CapCut Video Editor",
                "-metadata", f"application=com.lemon.lvoverseas_{version}",
                "-metadata:s:v:0", "handler_name=CapCut Video Handler",
                "-metadata:s:v:0", "vendor_id=capt",
                "-metadata:s:a:0", "handler_name=CapCut Audio Handler",
                "-metadata:s:a:0", "vendor_id=capt"
            ]
            
            ffmpeg_cmd.extend(metadata_params)
        else:
            log("⚠️ Không thêm metadata giả mạo (fake_metadata=False)")
        
        # Đảm bảo thư mục output tồn tại
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        ffmpeg_cmd.append(output_path)

        # 6. Thực thi lệnh
        log("Lệnh FFmpeg sẽ được thực thi:")
        log(' '.join(f'"{arg}"' if ' ' in arg else arg for arg in ffmpeg_cmd))
        
        process = subprocess.run(ffmpeg_cmd, check=True, text=True, encoding='utf-8')
        
        log(f"✅ Nối video thành công! File đã lưu tại: {output_path}")
        return output_path

    except FileNotFoundError:
        log("Lỗi: Không tìm thấy file 'temp/json/template.json'.")
        return None
    except subprocess.CalledProcessError as e:
        log(f"❌ Lỗi khi chạy FFmpeg để nối video:")
        return None
    except Exception as e:
        log(f"Đã xảy ra lỗi không xác định: {e}")
        return None
