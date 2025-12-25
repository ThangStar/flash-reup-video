"""Controller for socket server management."""

from views.server_view import ServerView
from views.menu_view import MenuView
from services.worker_service import WorkerService
from models.settings import Settings
import queue
import threading
import time
from collections import deque
from rich.live import Live
from rich.layout import Layout


class ServerController:
    """Manages worker service operations."""
    
    def __init__(self):
        self.server_view = ServerView()
        self.menu_view = MenuView()
        self.worker_service = None
    
    def start_server(self):
        """Start the Worker service with TUI."""
        # Ensure directories exist
        Settings.ensure_directories()
        
        # Init resources
        log_queue = queue.Queue()
        log_buffer = deque(maxlen=50) # Keep last 50 lines buffer
        
        self.worker_service = WorkerService(log_queue=log_queue)
        
        # Create Layout
        layout = self.server_view.create_dashboard_layout()
        
        # Initial content
        layout["left"].update(self.server_view.get_status_panel_content(port=Settings.SERVER_PORT))
        layout["right"].update(self.server_view.get_log_panel_content(["[dim]Waiting for logs...[/dim]"]))
        
        # Start Worker Thread
        worker_thread = threading.Thread(target=self.worker_service.run, daemon=True)
        worker_thread.start()
        
        # Run Live Display
        try:
            with Live(layout, refresh_per_second=4, screen=True) as live:
                while worker_thread.is_alive():
                    # Process all available logs
                    logs_changed = False
                    while not log_queue.empty():
                        try:
                            msg = log_queue.get_nowait()
                            
                            # Check for FFmpeg progress line to update in-place
                            is_progress = "frame=" in msg and "fps=" in msg.lower()
                            
                            if is_progress and log_buffer and "frame=" in log_buffer[-1] and "fps=" in log_buffer[-1].lower():
                                log_buffer[-1] = msg
                            else:
                                log_buffer.append(msg)
                            
                            logs_changed = True
                        except queue.Empty:
                            break
                    
                    # Update Log Panel only if changed
                    if logs_changed:
                        layout["right"].update(self.server_view.get_log_panel_content(list(log_buffer)))
                    
                    # Update Status Panel with animation or stats if needed
                    # For now just static refresh
                    
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            pass
        finally:
            print("Stopping worker...")
            self.worker_service.running = False
            worker_thread.join(timeout=2)
            
        self.menu_view.clear_screen()
        self.menu_view.wait_for_enter()
