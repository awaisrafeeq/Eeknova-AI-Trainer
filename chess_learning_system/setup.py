# setup.py - Setup script for the Chess Learning System

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    return True

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    dependencies = [
        "pygame==2.5.2",
        "numpy==1.24.3",
        "Pillow==10.0.0"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
    
    print("\nDependencies installed successfully!")

def create_directory_structure():
    """Create the required directory structure"""
    print("\nCreating directory structure...")
    
    base_dir = Path(__file__).parent
    
    directories = [
        "assets/images/pieces",
        "assets/images/backgrounds",
        "assets/images/ui",
        "assets/sounds/feedback",
        "assets/sounds/music",
        "assets/fonts",
        "data/profiles",
        "src/core",
        "src/modules/identify_pieces",
        "src/modules/board_setup",
        "src/modules/pawn_movement",
        "src/modules/rook_movement",
        "src/modules/knight_movement",
        "src/modules/bishop_movement",
        "src/modules/queen_movement",
        "src/modules/king_movement",
        "src/modules/mini_matches",
        "src/modules/capture_game",
        "src/states",
        "src/ui",
        "src/education",
        "src/chess",
        "src/audio",
        "src/utils"
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files for Python packages
        if directory.startswith("src"):
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("Directory structure created!")

def generate_placeholder_assets():
    """Generate placeholder assets"""
    print("\nGenerating placeholder assets...")
    
    try:
        from generate_assets import AssetGenerator
        generator = AssetGenerator()
        generator.generate_all_assets()
    except ImportError:
        print("Warning: Could not import asset generator.")
        print("Please run 'python generate_assets.py' manually after setup.")

def create_config_file():
    """Create a default configuration file"""
    print("\nCreating configuration file...")
    
    config_content = '''# config.ini - Chess Learning System Configuration

[Display]
width = 1024
height = 768
fullscreen = false
fps = 30

[Audio]
master_volume = 0.8
music_volume = 0.6
effects_volume = 0.7

[Education]
hint_delay = 5.0
break_reminder_minutes = 15
min_session_minutes = 5
max_session_minutes = 30

[Development]
debug_mode = false
show_fps = false
'''
    
    config_path = Path(__file__).parent / "config.ini"
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    print("Configuration file created!")

def test_installation():
    """Test if everything is set up correctly"""
    print("\nTesting installation...")
    
    try:
        import pygame
        import numpy
        from PIL import Image
        
        pygame.init()
        print("✓ Pygame initialized successfully")
        
        test_array = numpy.array([1, 2, 3])
        print("✓ NumPy working correctly")
        
        print("✓ PIL/Pillow available")
        
        # Check if main.py exists
        main_file = Path(__file__).parent / "main.py"
        if main_file.exists():
            print("✓ main.py found")
        else:
            print("✗ main.py not found - please ensure all files are present")
            return False
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 50)
    print("Chess Learning System - Setup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"\nError installing dependencies: {e}")
        print("Please install manually using: pip install pygame==2.5.2 numpy==1.24.3 Pillow==10.0.0")
        return
    
    # Create directory structure
    create_directory_structure()
    
    # Create config file
    create_config_file()
    
    # Generate assets
    generate_placeholder_assets()
    
    # Test installation
    print("\n" + "=" * 50)
    if test_installation():
        print("\n✅ Setup completed successfully!")
        print("\nTo start the Chess Learning System, run:")
        print("  python main.py")
        print("\nFor development mode with debug output:")
        print("  python main.py --debug")
        print("\nEnjoy teaching chess to children! 🎮♟️")
    else:
        print("\n⚠️  Setup completed with warnings.")
        print("Please check the errors above and fix any issues.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()