"""
Main application entry point with terminal menu.
Beautiful terminal UI with MVC architecture.
"""

from views.menu_view import MenuView
from controllers.export_controller import ExportController
from controllers.server_controller import ServerController
from controllers.settings_controller import SettingsController
from models.settings import Settings
import sys


def main():
    """Main application loop."""
    # Load configuration
    Settings.load_config()
    
    # Ensure required directories exist
    Settings.ensure_directories()
    
    # Initialize components
    menu_view = MenuView()
    export_controller = ExportController()
    server_controller = ServerController()
    settings_controller = SettingsController()
    
    while True:
        # Clear screen and show menu
        menu_view.clear_screen()
        menu_view.show_banner()
        menu_view.show_menu()
        
        # Get user choice
        choice = menu_view.get_choice()
        
        # Handle choice
        if choice == '1':
            # Test Export
            export_controller.test_export()
            
        elif choice == '2':
            # Run Socket Server
            server_controller.start_server()
            
        elif choice == '3':
            # Settings
            settings_controller.show_settings()
            
        elif choice == '4':
            # Exit
            menu_view.clear_screen()
            menu_view.show_success("Goodbye! 👋")
            sys.exit(0)
            
        else:
            menu_view.show_error("Invalid choice. Please select 1, 2, 3, or 4.")
            menu_view.wait_for_enter()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
