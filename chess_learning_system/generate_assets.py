# generate_assets.py - Generate placeholder assets for development

import pygame
import os
from pathlib import Path
import math
import numpy as np

class AssetGenerator:
    """Generate placeholder chess assets for development"""
    
    def __init__(self):
        pygame.init()
        self.base_dir = Path(__file__).parent
        self.assets_dir = self.base_dir / "assets"
        
        # Ensure directories exist
        self.create_directories()
        
        # Color schemes
        self.colors = {
            'white': (240, 240, 240),
            'black': (60, 60, 60),
            'outline': (100, 100, 100),
            'background': (200, 200, 200)
        }
    
    def create_directories(self):
        """Create all required directories"""
        directories = [
            self.assets_dir / "images" / "pieces",
            self.assets_dir / "images" / "backgrounds",
            self.assets_dir / "images" / "ui",
            self.assets_dir / "sounds" / "feedback",
            self.assets_dir / "sounds" / "music",
            self.assets_dir / "fonts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_all_assets(self):
        """Generate all placeholder assets"""
        print("Generating placeholder assets...")
        
        # Generate chess pieces
        self.generate_chess_pieces()
        
        # Generate backgrounds
        self.generate_backgrounds()
        
        # Generate UI elements
        self.generate_ui_elements()
        
        # Generate placeholder sounds
        self.generate_sound_placeholders()
        
        print("Asset generation complete!")
    
    def generate_chess_pieces(self):
        """Generate placeholder chess piece images"""
        pieces = {
            'king': self.draw_king,
            'queen': self.draw_queen,
            'rook': self.draw_rook,
            'bishop': self.draw_bishop,
            'knight': self.draw_knight,
            'pawn': self.draw_pawn
        }
        
        for color in ['white', 'black']:
            for piece_name, draw_func in pieces.items():
                # Create surface
                surface = pygame.Surface((128, 128), pygame.SRCALPHA)
                
                # Draw piece
                draw_func(surface, self.colors[color])
                
                # Save image
                filename = f"{color}_{piece_name}.png"
                filepath = self.assets_dir / "images" / "pieces" / filename
                pygame.image.save(surface, str(filepath))
                print(f"Generated: {filename}")
    
    def draw_king(self, surface, color):
        """Draw a king piece"""
        center = (64, 64)
        
        # Base
        pygame.draw.circle(surface, color, (center[0], center[1] + 20), 30)
        pygame.draw.rect(surface, color, (center[0] - 20, center[1], 40, 30))
        
        # Crown
        points = [
            (center[0] - 20, center[1] - 10),
            (center[0] - 20, center[1] - 30),
            (center[0] - 10, center[1] - 20),
            (center[0], center[1] - 35),
            (center[0] + 10, center[1] - 20),
            (center[0] + 20, center[1] - 30),
            (center[0] + 20, center[1] - 10)
        ]
        pygame.draw.polygon(surface, color, points)
        
        # Cross on top
        pygame.draw.rect(surface, color, (center[0] - 2, center[1] - 45, 4, 15))
        pygame.draw.rect(surface, color, (center[0] - 7, center[1] - 40, 14, 4))
        
        # Outline
        pygame.draw.circle(surface, self.colors['outline'], (center[0], center[1] + 20), 30, 2)
    
    def draw_queen(self, surface, color):
        """Draw a queen piece"""
        center = (64, 64)
        
        # Base
        pygame.draw.circle(surface, color, (center[0], center[1] + 20), 30)
        pygame.draw.rect(surface, color, (center[0] - 20, center[1], 40, 30))
        
        # Crown with points
        for angle in range(0, 360, 72):
            x = center[0] + 20 * math.cos(math.radians(angle))
            y = center[1] - 20 + 20 * math.sin(math.radians(angle))
            pygame.draw.circle(surface, color, (int(x), int(y)), 8)
        
        # Center circle
        pygame.draw.circle(surface, color, (center[0], center[1] - 20), 15)
        
        # Outline
        pygame.draw.circle(surface, self.colors['outline'], (center[0], center[1] + 20), 30, 2)
    
    def draw_rook(self, surface, color):
        """Draw a rook piece"""
        center = (64, 64)
        
        # Base
        pygame.draw.rect(surface, color, (center[0] - 25, center[1] + 10, 50, 30))
        
        # Tower body
        pygame.draw.rect(surface, color, (center[0] - 20, center[1] - 20, 40, 40))
        
        # Battlements
        for i in range(3):
            x = center[0] - 20 + i * 20
            pygame.draw.rect(surface, color, (x, center[1] - 35, 10, 20))
        
        # Outline
        pygame.draw.rect(surface, self.colors['outline'], 
                        (center[0] - 25, center[1] + 10, 50, 30), 2)
        pygame.draw.rect(surface, self.colors['outline'],
                        (center[0] - 20, center[1] - 20, 40, 40), 2)
    
    def draw_bishop(self, surface, color):
        """Draw a bishop piece"""
        center = (64, 64)
        
        # Base
        pygame.draw.circle(surface, color, (center[0], center[1] + 20), 25)
        
        # Body
        pygame.draw.polygon(surface, color, [
            (center[0] - 15, center[1] + 10),
            (center[0] - 10, center[1] - 20),
            (center[0] + 10, center[1] - 20),
            (center[0] + 15, center[1] + 10)
        ])
        
        # Hat/Mitre
        pygame.draw.polygon(surface, color, [
            (center[0] - 10, center[1] - 20),
            (center[0], center[1] - 40),
            (center[0] + 10, center[1] - 20)
        ])
        
        # Slit in hat
        pygame.draw.line(surface, self.colors['outline'],
                        (center[0], center[1] - 35), (center[0], center[1] - 25), 2)
        
        # Outline
        pygame.draw.circle(surface, self.colors['outline'], (center[0], center[1] + 20), 25, 2)
    
    def draw_knight(self, surface, color):
        """Draw a knight piece"""
        center = (64, 64)
        
        # Base
        pygame.draw.ellipse(surface, color, (center[0] - 20, center[1] + 10, 40, 30))
        
        # Horse head shape
        points = [
            (center[0] - 15, center[1] + 10),
            (center[0] - 20, center[1] - 10),
            (center[0] - 15, center[1] - 25),
            (center[0], center[1] - 30),
            (center[0] + 10, center[1] - 25),
            (center[0] + 15, center[1] - 10),
            (center[0] + 10, center[1]),
            (center[0] + 15, center[1] + 10)
        ]
        pygame.draw.polygon(surface, color, points)
        
        # Eye
        pygame.draw.circle(surface, self.colors['outline'], 
                          (center[0] + 5, center[1] - 15), 3)
        
        # Outline
        pygame.draw.polygon(surface, self.colors['outline'], points, 2)
    
    def draw_pawn(self, surface, color):
        """Draw a pawn piece"""
        center = (64, 64)
        
        # Base
        pygame.draw.circle(surface, color, (center[0], center[1] + 20), 20)
        
        # Neck
        pygame.draw.rect(surface, color, (center[0] - 8, center[1], 16, 20))
        
        # Head
        pygame.draw.circle(surface, color, (center[0], center[1] - 10), 12)
        
        # Outline
        pygame.draw.circle(surface, self.colors['outline'], (center[0], center[1] + 20), 20, 2)
        pygame.draw.circle(surface, self.colors['outline'], (center[0], center[1] - 10), 12, 2)
    
    def generate_backgrounds(self):
        """Generate background images"""
        # Chess board pattern
        board_surface = pygame.Surface((640, 640))
        square_size = 80
        
        for row in range(8):
            for col in range(8):
                color = (240, 217, 181) if (row + col) % 2 == 0 else (181, 136, 99)
                rect = pygame.Rect(col * square_size, row * square_size, 
                                 square_size, square_size)
                pygame.draw.rect(board_surface, color, rect)
        
        pygame.image.save(board_surface, 
                         str(self.assets_dir / "images" / "backgrounds" / "chess_board.png"))
        
        # Gradient background
        gradient_surface = pygame.Surface((1024, 768))
        for y in range(768):
            color_value = int(200 + (55 * y / 768))
            color = (color_value, color_value, 255)
            pygame.draw.line(gradient_surface, color, (0, y), (1024, y))
        
        pygame.image.save(gradient_surface,
                         str(self.assets_dir / "images" / "backgrounds" / "gradient_bg.png"))
        
        print("Generated background images")
    
    def generate_ui_elements(self):
        """Generate UI element images"""
        # Star icon
        star_surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        self.draw_star(star_surface, (32, 32), 30, (255, 215, 0))
        pygame.image.save(star_surface,
                         str(self.assets_dir / "images" / "ui" / "star.png"))
        
        # Lock icon
        lock_surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        # Lock body
        pygame.draw.rect(lock_surface, (100, 100, 100), (20, 30, 24, 30))
        pygame.draw.rect(lock_surface, (80, 80, 80), (20, 30, 24, 30), 2)
        # Lock shackle
        pygame.draw.arc(lock_surface, (100, 100, 100), (22, 15, 20, 25), 0, math.pi, 8)
        
        pygame.image.save(lock_surface,
                         str(self.assets_dir / "images" / "ui" / "lock.png"))
        
        print("Generated UI elements")
    
    def draw_star(self, surface, pos, size, color):
        """Draw a star shape"""
        points = []
        for i in range(10):
            angle = math.pi * i / 5
            if i % 2 == 0:
                radius = size
            else:
                radius = size * 0.5
            x = pos[0] + radius * math.cos(angle - math.pi / 2)
            y = pos[1] + radius * math.sin(angle - math.pi / 2)
            points.append((x, y))
        
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, (200, 200, 0), points, 2)
    
    def generate_sound_placeholders(self):
        """Create placeholder text files for sounds"""
        sounds = {
            'feedback': [
                'success.wav',
                'incorrect.wav',
                'hint.wav',
                'move.wav',
                'celebration.wav',
                'click.wav'
            ],
            'music': [
                'welcome_theme.ogg',
                'menu_theme.ogg',
                'learning_theme.ogg'
            ]
        }
        
        for category, files in sounds.items():
            for filename in files:
                filepath = self.assets_dir / "sounds" / category / filename
                with open(filepath, 'w') as f:
                    f.write(f"Placeholder for {filename}")
                print(f"Created placeholder: sounds/{category}/{filename}")
    
    def generate_sample_audio(self):
        """Generate actual audio files using pygame (optional)"""
        try:
            # This requires numpy
            sample_rate = 22050
            duration = 0.5
            
            # Success sound (ascending tone)
            t = np.linspace(0, duration, int(sample_rate * duration))
            frequency = 440 * (1 + 0.5 * t / duration)  # 440Hz to 660Hz
            wave = np.sin(frequency * 2 * np.pi * t) * 0.3
            wave = (wave * 32767).astype(np.int16)
            
            sound = pygame.sndarray.make_sound(wave)
            # Note: Pygame doesn't have built-in save functionality for sounds
            
            print("Sample audio generation would require additional libraries")
        except ImportError:
            print("NumPy not available for audio generation")


def main():
    """Run the asset generator"""
    generator = AssetGenerator()
    generator.generate_all_assets()
    
    print("\nAsset generation complete!")
    print("You can now run the chess learning system.")
    print("\nNote: The generated sounds are placeholder files.")
    print("For actual audio, you'll need to add real sound files.")

if __name__ == "__main__":
    main()