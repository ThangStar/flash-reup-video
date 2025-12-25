"""Server status view for displaying server information."""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich import box
import socket


console = Console()


class ServerView:
    """Display server status and information."""
    
    @staticmethod
    def get_local_ip():
        """Get the local IP address."""
        try:
            # Create a socket to get the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    @staticmethod
    def show_server_info(host, port):
        """Display server connection information."""
        local_ip = ServerView.get_local_ip()
        
        # Create info table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Label", style="bold cyan")
        table.add_column("Value", style="bold green")
        
        table.add_row("🌐 Local IP:", local_ip)
        table.add_row("🔌 Port:", str(port))
        table.add_row("📡 Endpoint:", "/generate")
        table.add_row("", "")
        table.add_row("🔗 Server URL:", f"http://{local_ip}:{port}")
        table.add_row("📤 Upload URL:", f"http://{local_ip}:{port}/generate")
        
        panel = Panel(
            table,
            title="[bold yellow]⚡ SERVER RUNNING ⚡[/bold yellow]",
            border_style="bright_green",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        
        console.print(panel)
        console.print()
    
    @staticmethod
    def show_request_info(method, path, status_code):
        """Display request information."""
        status_color = "green" if status_code < 400 else "red"
        console.print(
            f"[bold white]{method}[/bold white] "
            f"[cyan]{path}[/cyan] "
            f"[{status_color}]{status_code}[/{status_color}]"
        )
    
    @staticmethod
    def show_upload_info(filename, size):
        """Display file upload information."""
        size_mb = size / 1024 / 1024
        console.print(f"[green]📥 Uploaded:[/green] [white]{filename}[/white] [dim]({size_mb:.2f} MB)[/dim]")
    
    @staticmethod
    def show_processing():
        """Display processing message."""
        console.print("[yellow]⚙️  Processing video...[/yellow]")
    
    @staticmethod
    def show_server_instructions():
        """Show usage instructions."""
        instructions = Text()
        instructions.append("📝 Usage Instructions:\n\n", style="bold cyan")
        instructions.append("Upload video and audio files using curl:\n", style="white")
        instructions.append('curl -X POST http://<IP>:<PORT>/generate \\\n', style="dim")
        instructions.append('  -F "video=@your_video.mp4" \\\n', style="dim")
        instructions.append('  -F "audio=@your_audio.mp3" \\\n', style="dim")
        instructions.append('  -o output.mp4\n\n', style="dim")
        instructions.append("Press Ctrl+C to stop the server", style="yellow")
        
        panel = Panel(
            instructions,
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2)
        )
        console.print(panel)
        console.print()

    @staticmethod
    def create_dashboard_layout():
        """Create the main dashboard layout."""
        from rich.layout import Layout
        layout = Layout()
        layout.split_row(
            Layout(name="left", size=50),
            Layout(name="right")
        )
        return layout

    @staticmethod
    def get_status_panel_content(port=8000):
        """Generate content for the status panel."""
        local_ip = ServerView.get_local_ip()
        
        # Grid for info
        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("Label", style="bold cyan")
        table.add_column("Value", style="bold green")
        
        table.add_row("🌐 IP:", local_ip)
        table.add_row("🔌 Port:", str(port))
        table.add_row("📡 Status:", "POLLING")
        table.add_row("", "")
        table.add_row("Queue:", "Supabase video_enqueue")
        
        # Instructions slightly different for panel
        instructions = Text()
        instructions.append("\n📝 Instructions:\n", style="bold yellow")
        instructions.append("Server is polling for jobs.\n", style="white")
        instructions.append("Press Ctrl+C to stop.", style="dim")
        
        from rich.console import Group
        content = Group(
            Text("✅ SERVER RUNNING", style="bold green justify-center"),
            Text("─" * 30, style="dim justify-center"),
            table,
            instructions
        )
        
        return Panel(
            content,
            title="[bold yellow]STATUS[/bold yellow]",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2),
            expand=True
        )

    @staticmethod
    def get_log_panel_content(log_lines):
        """Generate content for the log panel."""
        # Calculate max visible lines roughly to keep buffer sane
        # But rely on Panel(expand=True) for sizing
        # Using -6 for safety margin against headers/borders
        max_lines = max(10, console.height - 6)
        
        # Sanitize logs: remove newlines from individual entries to ensure
        # 1 list item = 1 visual line.
        clean_logs = [str(line).replace('\n', ' ').replace('\r', '') for line in log_lines]
        
        visible_lines = clean_logs[-max_lines:]
        
        # Pad with empty lines to maintain stable height
        if len(visible_lines) < max_lines:
            padding_needed = max_lines - len(visible_lines)
            # Add padding at the top so logs appear at the bottom
            visible_lines = [""] * padding_needed + visible_lines

        # Join lines, assuming they are markup strings
        # Align left to ensure clean look
        text_content = "\n".join(visible_lines)
        
        # Create text object and set properties separately for compatibility
        log_text = Text.from_markup(text_content)
        log_text.overflow = "ellipsis"
        log_text.no_wrap = True
        
        return Panel(
            log_text,
            title="[bold white]LOGS[/bold white]",
            border_style="white",
            box=box.ROUNDED,
            padding=(0, 1),
            style="white",
            expand=True
        )
