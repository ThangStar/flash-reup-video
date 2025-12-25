"""Worker service for processing video jobs from Supabase queue."""

import time
import os
import json
from supabase import create_client, Client
from rich.console import Console
from models.settings import Settings
from services.advanced_processor import process_video_with_effects
from models.processing_params import ProcessingParams

console = Console()

from rich.markup import escape
import queue

class WorkerService:
    """Worker that polls Supabase for video processing jobs."""
    
    def __init__(self, log_queue=None):
        self.supabase: Client = None
        self.running = False
        self.log_queue = log_queue

    def log(self, message):
        """Log message to console or queue."""
        if self.log_queue:
            self.log_queue.put(message)
        else:
            console.print(message)
        
    def connect(self):
        """Connect to Supabase."""
        url = Settings.SUPABASE_URL
        key = Settings.SUPABASE_SERVICE_ROLE_KEY  # We need service role strictly for worker if possible, or anon if RLS allows
        # Since I don't have SERVICE_ROLE_KEY in Settings yet, I might default to ANON/PUBLISHABLE KEY
        # But for updating rows, we usually need proper auth or service role.
        # Assuming SUPABASE_KEY variable serves as the key.
        
        # NOTE: The user's settings usually have SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY.
        # If RLS is enabled, the worker needs headers or service role.
        # For now, I'll use what's available in Settings.
        
        # Check if we have credentials
        if not url or not key:
            # Try loading again or checking env
            Settings.load_config()
            url = Settings.SUPABASE_URL
            key = getattr(Settings, 'SUPABASE_SERVICE_ROLE_KEY', Settings.SUPABASE_PUBLISHABLE_KEY)
            
        if not url or not key:
            raise ValueError("Supabase URL or Key not configured")

        self.supabase = create_client(url, key)
        self.log(f"[green]✅ Connected to Supabase: {url}[/green]")

    def run(self):
        """Start the worker loop."""
        self.connect()
        self.running = True
        
        self.log("[bold cyan]🚀 Worker started. Waiting for jobs...[/bold cyan]")
        
        while self.running:
            try:
                # Poll for jobs with status 'chờ xử lý' (queued)
                # We limit to 1 job at a time
                response = self.supabase.table('video_enqueue')\
                    .select("*")\
                    .eq('status', 'chờ xử lý')\
                    .limit(1)\
                    .execute()
                
                jobs = response.data
                
                if jobs:
                    job = jobs[0]
                    self.process_job(job)
                else:
                    # No jobs, sleep a bit
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                self.log("\n[yellow]⚠️  Worker stopping...[/yellow]")
                self.running = False
                break
            except Exception as e:
                self.log(f"[red]❌ Worker error: {e}[/red]")
                time.sleep(5)

    def process_job(self, job):
        """Process a single job."""
        job_id = job['id']
        video_url = job['video_url']
        audio_url = job.get('audio_url', video_url)
        params_json = job.get('params', {})
        
        self.log(f"[cyan]🎬 Processing Job #{job_id}[/cyan]")
        
        try:
            # 1. Update status to 'đang xử lý'
            self.update_job_status(job_id, 'đang xử lý', 'Starting processing...')
            
            # 2. Parse params
            # If params is a string (JSON text), parse it. If dict, use as is.
            if isinstance(params_json, str):
                params_dict = json.loads(params_json)
            else:
                params_dict = params_json or {}
                
            params = ProcessingParams.from_dict(params_dict)
            
            # 3. Setup paths
            temp_dir = os.path.join("temp", "processing", str(job_id))
            os.makedirs(temp_dir, exist_ok=True)
            
            timestamp = int(time.time())
            video_path = os.path.join(temp_dir, f"input_{timestamp}.mp4")
            audio_path = os.path.join(temp_dir, f"input_audio_{timestamp}.mp3")
            output_path = os.path.join(temp_dir, f"output_{timestamp}.mp4")
            
            # 4. Download files
            self.update_job_status(job_id, 'đang xử lý', 'Downloading files...')
            # Simple download using requests (reusing logic would be better but I'll keeping it simple here)
            import requests
            
            def download_file(url, path):
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            
            download_file(video_url, video_path)
            if audio_url and audio_url != video_url:
                download_file(audio_url, audio_path)
            else:
                audio_path = video_path # FFmpeg will handle it
                
            # 5. Process
            def progress_callback(msg):
                # Escape the message to prevent it from ignoring square brackets in ffmpeg output
                safe_msg = escape(str(msg))
                self.log(f"[dim]{safe_msg}[/dim]")
                
            self.update_job_status(job_id, 'đang xử lý', 'Processing video effects...')
            
            result_path = process_video_with_effects(
                video_path=video_path,
                audio_path=audio_path,
                output_path=output_path,
                params=params,
                progress_callback=progress_callback
            )
            
            if result_path and os.path.exists(result_path):
                # 6. Upload result
                self.update_job_status(job_id, 'đang xử lý', 'Uploading result...')
                public_url = self.upload_to_gcs(result_path, f"{job_id}_{timestamp}.mp4")
                
                if public_url:
                    self.update_job_status(job_id, 'hoàn thành', 'Processing complete', url=public_url)
                    self.log(f"[green]✅ Job #{job_id} Completed![/green]")
                else:
                    raise Exception("Failed to upload result to GCS")
            else:
                raise Exception("Processing returned no result")
            
        except Exception as e:
            self.log(f"[red]❌ Job #{job_id} Failed: {e}[/red]")
            self.update_job_status(job_id, 'thất bại', str(e))
        finally:
            # Cleanup
            import shutil
            try:
                shutil.rmtree(os.path.dirname(video_path), ignore_errors=True)
            except:
                pass

    def update_job_status(self, job_id, status, message, url=None):
        """Update job status in Supabase."""
        data = {
            'status': status,
            'message': message,
            'updatedAt': 'now()'
        }
        if url:
            data['url'] = url
            
        self.supabase.table('video_enqueue').update(data).eq('id', job_id).execute()

    def upload_to_gcs(self, file_path, destination_blob_name):
        """Upload to GCS and return public URL."""
        from google.cloud import storage
        from google.oauth2 import service_account
        
        try:
            bucket_name = Settings.GCP_BUCKET_NAME
            # Assuming credentials.json is in temp/json/credentials.json relative to project root
            # or configured in Settings.
            # I'll rely on Settings having specific checks or just use default
            
            # Quick hack to find credentials
            base_dir = os.getcwd()
            credentials_path = os.path.join(base_dir, 'temp', 'json', 'credentials.json')
            
            if os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                storage_client = storage.Client(credentials=credentials)
            else:
                storage_client = storage.Client()
                
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_path)
            
            # Make public if possible or just use public link format
            # blob.make_public() # Might fail if bucket enforces uniform access
            
            return blob.public_url
        except Exception as e:
            self.log(f"[red]Upload error: {e}[/red]")
            return None
