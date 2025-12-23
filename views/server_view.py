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
