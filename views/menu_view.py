"""Terminal menu view with Rich library for beautiful UI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
import sys


console = Console()


class MenuView:
    """Beautiful terminal menu interface."""
    
    @staticmethod
    def show_banner():
        """Display application banner."""
        banner = Text()
        banner.append("🎬 ", style="bold yellow")
        banner.append("EOS REUP VIDEO SERVER", style="bold cyan")
        banner.append(" 🎬", style="bold yellow")
        
        panel = Panel(
            banner,
            border_style="bright_blue",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        console.print(panel)
        console.print()
    
    @staticmethod
    def show_menu():
        """Display main menu options."""
        table = Table(
            show_header=False,
            box=box.ROUNDED,
            border_style="cyan",
            padding=(0, 2)
        )
        
        table.add_column("Option", style="bold magenta", width=8)
        table.add_column("Description", style="white")
        
        table.add_row("1", "Test Export - Thử xuất video từ test.mp4 và test.mp3")
        table.add_row("2", "Start Socket Server - Khởi chạy Server")
        table.add_row("3", "Settings - Cài đặt GPU và cấu hình")
        table.add_row("4", "Exit - Thoát chương trình")
        
        console.print(table)
        console.print()
    
    @staticmethod
    def get_choice():
        """Get user menu choice."""
        choice = console.input("[bold yellow]Chọn chức năng (1-4):[/bold yellow] ")
        return choice.strip()
    
    @staticmethod
    def show_success(message):
        """Display success message."""
        console.print(f"[bold green]✅ {message}[/bold green]")
    
    @staticmethod
    def show_error(message):
        """Display error message."""
        console.print(f"[bold red]❌ {message}[/bold red]")
    
    @staticmethod
    def show_info(message):
        """Display info message."""
        console.print(f"[cyan]ℹ️  {message}[/cyan]")
    
    @staticmethod
    def show_warning(message):
        """Display warning message."""
        console.print(f"[yellow]⚠️  {message}[/yellow]")
    
    @staticmethod
    def show_panel(title, content, style="cyan"):
        """Display a panel with title and content."""
        panel = Panel(
            content,
            title=f"[bold]{title}[/bold]",
            border_style=style,
            box=box.ROUNDED,
            padding=(1, 2)
        )
        console.print(panel)
    
    @staticmethod
    def clear_screen():
        """Clear the terminal screen."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def wait_for_enter():
        """Wait for user to press enter."""
        console.input("\n[dim]Press Enter to continue...[/dim]")
    
    @staticmethod
    def print_separator():
        """Print a visual separator."""
        console.print("─" * console.width, style="dim")
