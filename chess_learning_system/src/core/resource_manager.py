# src/core/resource_manager.py - Resource loading and caching system

import pygame
from pathlib import Path
from typing import Dict, Optional, Tuple
import json

class ResourceManager:
    """Manages loading and caching of game resources"""
    
    def __init__(self, config):
        self.config = config
        self.images: Dict[str, pygame.Surface] = {}
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.fonts: Dict[Tuple[str, int], pygame.font.Font] = {}
        self.json_data: Dict[str, dict] = {}
        
        # Preload common resources
        self._preload_resources()
    
    def _preload_resources(self):
        """Preload commonly used resources"""
        # Load default fonts
        self.load_font(None, self.config.FONTS['small_size'])
        self.load_font(None, self.config.FONTS['default_size'])
        self.load_font(None, self.config.FONTS['medium_size'])
        self.load_font(None, self.config.FONTS['large_size'])
        
        # Preload UI sounds
        ui_sounds = ['button_click', 'success', 'incorrect', 'hint']
        for sound_name in ui_sounds:
            if sound_name in self.config.SOUND_EFFECTS:
                self.load_sound(sound_name)
    
    def load_image(self, name: str, size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
        """Load and cache an image"""
        #print(f"Debug: Attempting to load image '{name}' with size {size}")
        cache_key = f"{name}_{size}" if size else name
        
        if cache_key in self.images:
            return self.images[cache_key]
        
        # Determine the path
        if name in self.config.PIECE_IMAGES.get('white', {}):
            path = self.config.IMAGES_DIR / self.config.PIECE_IMAGES['white'][name]
        elif name in self.config.PIECE_IMAGES.get('black', {}):
            path = self.config.IMAGES_DIR / self.config.PIECE_IMAGES['black'][name]
        else:
            # Try to load from various subdirectories
            possible_paths = [
                self.config.IMAGES_DIR / name,
                self.config.IMAGES_DIR / "ui" / name,
                self.config.IMAGES_DIR / "backgrounds" / name,
                self.config.IMAGES_DIR / "pieces" / name,
            ]
            #print(f"Debug: Searching for image '{possible_paths}' in possible paths.")
            path = None
            for p in possible_paths:
                if p.exists():
                    path = p
                    break
            
            if not path:
                print(f"Warning: Image '{name}' not found. Using placeholder.")
                return self._create_placeholder_image(size or (64, 64))
        
        try:
            # Load the image
            image = pygame.image.load(str(path))
            
            # Resize if size specified
            if size:
                image = pygame.transform.smoothscale(image, size)
            
            # Convert for better performance
            if image.get_alpha():
                image = image.convert_alpha()
            else:
                image = image.convert()
            
            # Cache it
            self.images[cache_key] = image
            return image
            
        except Exception as e:
            print(f"Error loading image '{name}': {e}")
            return self._create_placeholder_image(size or (64, 64))
    
    def load_piece_image(self, piece_type: str, color: str, size: Optional[Tuple[int, int]] = None) -> pygame.Surface:
        """Load a chess piece image"""
        if color not in self.config.PIECE_IMAGES:
            print(f"Warning: Color '{color}' not found in piece images")
            return self._create_placeholder_image(size or (64, 64))
            
        if piece_type not in self.config.PIECE_IMAGES[color]:
            print(f"Warning: Piece '{piece_type}' not found for color '{color}'")
            return self._create_placeholder_image(size or (64, 64))
        
        path = self.config.IMAGES_DIR / self.config.PIECE_IMAGES[color][piece_type]
        cache_key = f"{color}_{piece_type}_{size}" if size else f"{color}_{piece_type}"
        
        if cache_key in self.images:
            return self.images[cache_key]
        
        try:
            image = pygame.image.load(str(path))
            
            if size:
                image = pygame.transform.smoothscale(image, size)
            
            if image.get_alpha():
                image = image.convert_alpha()
            else:
                image = image.convert()
            
            self.images[cache_key] = image
            return image
            
        except Exception as e:
            print(f"Error loading piece image '{piece_type}' ({color}): {e}")
            return self._create_placeholder_piece(piece_type, color, size or (64, 64))
    
    def load_sound(self, name: str) -> Optional[pygame.mixer.Sound]:
        """Load and cache a sound effect"""
        if name in self.sounds:
            return self.sounds[name]
        
        if name not in self.config.SOUND_EFFECTS:
            print(f"Warning: Sound '{name}' not found in configuration")
            return None
        
        path = self.config.SOUNDS_DIR / self.config.SOUND_EFFECTS[name]
        
        if not path.exists():
            print(f"Warning: Sound file '{path}' not found")
            return None
        
        try:
            sound = pygame.mixer.Sound(str(path))
            self.sounds[name] = sound
            return sound
        except Exception as e:
            print(f"Error loading sound '{name}': {e}")
            return None
    
    def load_font(self, name: Optional[str], size: int) -> pygame.font.Font:
        """Load and cache a font"""
        cache_key = (name, size)
        
        if cache_key in self.fonts:
            return self.fonts[cache_key]
        
        try:
            if name:
                path = self.config.FONTS_DIR / name
                if path.exists():
                    font = pygame.font.Font(str(path), size)
                else:
                    print(f"Warning: Font '{name}' not found. Using default.")
                    font = pygame.font.Font(None, size)
            else:
                font = pygame.font.Font(None, size)
            
            self.fonts[cache_key] = font
            return font
            
        except Exception as e:
            print(f"Error loading font '{name}': {e}")
            return pygame.font.Font(None, size)
    
    def load_json(self, name: str) -> dict:
        """Load and cache JSON data"""
        if name in self.json_data:
            return self.json_data[name]
        
        path = self.config.DATA_DIR / name
        
        if not path.exists():
            print(f"Warning: JSON file '{name}' not found")
            return {}
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            self.json_data[name] = data
            return data
        except Exception as e:
            print(f"Error loading JSON '{name}': {e}")
            return {}
    
    def _create_placeholder_image(self, size: Tuple[int, int]) -> pygame.Surface:
        """Create a placeholder image when asset is missing"""
        surface = pygame.Surface(size)
        surface.fill((200, 200, 200))
        pygame.draw.rect(surface, (100, 100, 100), surface.get_rect(), 2)
        pygame.draw.line(surface, (100, 100, 100), (0, 0), size, 2)
        pygame.draw.line(surface, (100, 100, 100), (size[0], 0), (0, size[1]), 2)
        return surface
    
    def _create_placeholder_piece(self, piece_type: str, color: str, size: Tuple[int, int]) -> pygame.Surface:
        """Create a placeholder chess piece"""
        surface = pygame.Surface(size, pygame.SRCALPHA)
        
        # Draw a circle for the piece
        piece_color = (255, 255, 255) if color == 'white' else (50, 50, 50)
        outline_color = (0, 0, 0) if color == 'white' else (200, 200, 200)
        
        center = (size[0] // 2, size[1] // 2)
        radius = min(size[0], size[1]) // 3
        
        pygame.draw.circle(surface, piece_color, center, radius)
        pygame.draw.circle(surface, outline_color, center, radius, 2)
        
        # Draw piece initial
        font = pygame.font.Font(None, radius)
        initial = piece_type[0].upper() if piece_type != 'knight' else 'N'
        text = font.render(initial, True, outline_color)
        text_rect = text.get_rect(center=center)
        surface.blit(text, text_rect)
        
        return surface
    
    def cleanup(self):
        """Clean up resources"""
        self.images.clear()
        self.sounds.clear()
        self.fonts.clear()
        self.json_data.clear()