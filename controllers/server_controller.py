"""Controller for socket server management."""

from views.server_view import ServerView
from views.menu_view import MenuView
from services.socket_server import SocketServer
from models.settings import Settings


class ServerController:
    """Manages socket server operations."""
    
    def __init__(self):
        self.server_view = ServerView()
        self.menu_view = MenuView()
        self.socket_server = None
    
    def start_server(self):
        """Start the Flask socket server."""
        self.menu_view.clear_screen()
        self.menu_view.show_panel(
            "🌐 Socket Server",
            "Starting Flask server for video processing...",
            "green"
        )
        print()
        
        # Ensure directories exist
        Settings.ensure_directories()
        
        # Show server info
        self.server_view.show_server_info(Settings.SERVER_HOST, Settings.SERVER_PORT)
        self.server_view.show_server_instructions()
        
        # Create and start server
        try:
            self.socket_server = SocketServer(
                host=Settings.SERVER_HOST,
                port=Settings.SERVER_PORT
            )
            
            self.menu_view.show_info("Server is starting...")
            print()
            
            # This will block until Ctrl+C
            self.socket_server.run()
            
        except KeyboardInterrupt:
            print()
            self.menu_view.show_info("Server stopped by user")
        except Exception as e:
            print()
            self.menu_view.show_error(f"Server error: {str(e)}")
        
        print()
        self.menu_view.wait_for_enter()
