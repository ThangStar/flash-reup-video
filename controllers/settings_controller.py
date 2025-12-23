"""Controller for application settings."""

from views.menu_view import MenuView
from models.settings import Settings


class SettingsController:
    """Handles application settings management."""
    
    def __init__(self):
        self.view = MenuView()
    
    def show_settings(self):
        """Display and handle settings menu."""
        while True:
            self.view.clear_screen()
            self.view.show_panel(
                "⚙️ Application Settings",
                "Configure application preferences",
                "yellow"
            )
            print()
            
            # Display current settings
            self.view.show_info(f"Current GPU Type: {Settings.GPU_TYPE.upper()}")
            self.view.show_info(f"Server Port: {Settings.SERVER_PORT}")
            print()
            
            # Settings menu
            self.view.print_separator()
            print()
            self.view.show_info("[1] Change GPU Type")
            self.view.show_info("[2] Change Server Port")
            self.view.show_info("[0] Back to Main Menu")
            print()
            
            choice = self.view.get_choice()
            
            if choice == '1':
                self._change_gpu_type()
            elif choice == '2':
                self._change_server_port()
            elif choice == '0':
                break
            else:
                self.view.show_error("Invalid choice")
                self.view.wait_for_enter()
    
    def _change_gpu_type(self):
        """Change GPU type setting."""
        self.view.clear_screen()
        self.view.show_panel(
            "🎮 GPU Type Selection",
            "Select your graphics card type",
            "cyan"
        )
        print()
        
        self.view.show_info(f"Current: {Settings.GPU_TYPE.upper()}")
        print()
        self.view.show_info("[1] NVIDIA")
        self.view.show_info("[2] AMD")
        self.view.show_info("[0] Cancel")
        print()
        
        choice = self.view.get_choice()
        
        if choice == '1':
            Settings.set_gpu_type('nvidia')
            self.view.show_success("GPU type set to NVIDIA")
        elif choice == '2':
            Settings.set_gpu_type('amd')
            self.view.show_success("GPU type set to AMD")
        elif choice == '0':
            return
        else:
            self.view.show_error("Invalid choice")
        
        self.view.wait_for_enter()
    
    def _change_server_port(self):
        """Change server port setting."""
        self.view.clear_screen()
        self.view.show_panel(
            "🔌 Server Port",
            "Change the server port number",
            "cyan"
        )
        print()
        
        self.view.show_info(f"Current port: {Settings.SERVER_PORT}")
        print()
        
        try:
            port_input = input("Enter new port (or 0 to cancel): ").strip()
            if port_input == '0':
                return
            
            port = int(port_input)
            if 1024 <= port <= 65535:
                Settings.SERVER_PORT = port
                Settings.save_config()
                self.view.show_success(f"Server port set to {port}")
            else:
                self.view.show_error("Port must be between 1024 and 65535")
        except ValueError:
            self.view.show_error("Invalid port number")
        
        self.view.wait_for_enter()
