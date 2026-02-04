# debug_launcher.py - Launch the application in debug mode

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Launch the application with debug settings"""
    
    # Set debug environment variables
    os.environ['CHESS_DEBUG'] = '1'
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
    
    # Import after setting environment
    import pygame
    from src.core.config import Config
    from src.core.game_engine import ChessEducationEngine
    
    print("=" * 50)
    print("Chess Learning System - DEBUG MODE")
    print("=" * 50)
    
    # Override some config for debugging
    class DebugConfig(Config):
        def __init__(self):
            super().__init__()
            
            # Debug settings
            self.DEBUG_MODE = True
            self.SHOW_FPS = True
            self.SHOW_HITBOXES = True
            self.FAST_ANIMATIONS = True
            
            # Override some timings for faster testing
            self.EDUCATION['hint_delay'] = 2.0
            self.EDUCATION['celebration_threshold'] = 1
            self.EDUCATION['break_reminder_time'] = 300  # 5 minutes for testing
            
            # Window settings for development
            self.SCREEN_WIDTH = 1024
            self.SCREEN_HEIGHT = 768
            self.WINDOW_TITLE = "Chess Learning System [DEBUG]"
    
    # Initialize pygame
    pygame.init()
    
    # Create debug config
    config = DebugConfig()
    
    # Create engine with debug config
    engine = ChessEducationEngine(config)
    
    # Add debug overlay
    class DebugOverlay:
        def __init__(self, engine):
            self.engine = engine
            self.font = pygame.font.Font(None, 16)
            self.show_overlay = True
            
        def update(self, dt):
            # Toggle overlay with F3
            keys = pygame.key.get_pressed()
            if keys[pygame.K_F3]:
                self.show_overlay = not self.show_overlay
        
        def render(self, screen):
            if not self.show_overlay:
                return
                
            # FPS counter
            fps = int(self.engine.clock.get_fps())
            fps_text = self.font.render(f"FPS: {fps}", True, (255, 255, 0))
            screen.blit(fps_text, (10, 10))
            
            # Current state
            if self.engine.state_machine.current_state:
                state_name = self.engine.state_machine.current_state_id.name
                state_text = self.font.render(f"State: {state_name}", True, (255, 255, 0))
                screen.blit(state_text, (10, 30))
            
            # Memory usage
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_text = self.font.render(f"Memory: {memory_mb:.1f} MB", True, (255, 255, 0))
            screen.blit(memory_text, (10, 50))
            
            # Controls help
            help_text = [
                "F3: Toggle debug overlay",
                "F5: Quick save",
                "F9: Quick load",
                "ESC: Back/Menu"
            ]
            
            y = screen.get_height() - len(help_text) * 20 - 10
            for line in help_text:
                text = self.font.render(line, True, (200, 200, 200))
                screen.blit(text, (10, y))
                y += 20
    
    # Create debug overlay
    debug_overlay = DebugOverlay(engine)
    
    # Monkey patch the engine render method to include debug overlay
    original_render = engine._render
    
    def debug_render():
        original_render()
        debug_overlay.render(engine.screen)
    
    engine._render = debug_render
    
    # Monkey patch the engine update method
    original_update = engine.state_machine.update
    
    def debug_update(dt):
        original_update(dt)
        debug_overlay.update(dt)
    
    engine.state_machine.update = debug_update
    
    print("\nDebug Controls:")
    print("- F3: Toggle debug overlay")
    print("- F5: Quick save")
    print("- F9: Quick load")
    print("- ESC: Back/Menu")
    print("\nStarting in debug mode...\n")
    
    try:
        # Run the engine
        engine.run()
    except KeyboardInterrupt:
        print("\nShutting down (Ctrl+C)...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.cleanup()
        pygame.quit()

if __name__ == "__main__":
    # Check for psutil (optional dependency for memory monitoring)
    try:
        import psutil
    except ImportError:
        print("Warning: psutil not installed. Memory monitoring disabled.")
        print("Install with: pip install psutil")
        print()
    
    main()