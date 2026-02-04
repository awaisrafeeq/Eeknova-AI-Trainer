# main.py - Entry point for the Chess Learning System

import pygame
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from src.core.game_engine import ChessEducationEngine
from src.core.config import Config

def main():
    """Main entry point for the chess education system"""
    pygame.init()
    
    # Load configuration
    config = Config()
    # Create and run the game engine
    engine = ChessEducationEngine(config)
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
    finally:
        engine.cleanup()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()