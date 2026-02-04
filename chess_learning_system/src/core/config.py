# src/core/config.py - Configuration settings for the chess learning system

import pygame
from pathlib import Path

class Config:
    """Central configuration for the chess education system"""
    
    # Display settings
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 768
    FPS = 30  # Child-friendly frame rate
    WINDOW_TITLE = "Chess Learning Adventure"
    
    # Colors (child-friendly palette)
    COLORS = {
        'background': (240, 248, 255),      # Alice blue
        'primary': (52, 152, 219),          # Bright blue
        'secondary': (46, 204, 113),        # Emerald green
        'accent': (241, 196, 15),           # Sunflower yellow
        'danger': (231, 76, 60),            # Soft red
        'text_dark': (44, 62, 80),          # Dark blue-gray
        'text_light': (236, 240, 241),      # Cloud white
        'board_light': (240, 217, 181),     # Cream
        'board_dark': (181, 136, 99),       # Brown
        'highlight': (255, 255, 0, 128),    # Semi-transparent yellow
        'valid_move': (0, 255, 0, 64),      # Semi-transparent green
        'invalid_move': (255, 0, 0, 64),    # Semi-transparent red
    }
    
    # Font settings
    FONTS = {
        'default_size': 24,
        'large_size': 48,
        'medium_size': 32,
        'small_size': 18,
        'default_name': None,  # Will use pygame default
    }
    
    # Audio settings
    AUDIO = {
        'master_volume': 0.8,
        'music_volume': 0.6,
        'effects_volume': 0.7,
        'voice_volume': 0.8,
        'frequency': 44100,
        'size': -16,
        'channels': 2,
        'buffer': 512,
    }
    
    # Board settings
    BOARD = {
        'size': 8,
        'square_size': 80,
        'board_offset_x': 100,
        'board_offset_y': 100,
    }
    
    # Animation settings
    ANIMATION = {
        'piece_move_speed': 300,  # pixels per second
        'fade_speed': 2.0,        # seconds
        'celebration_duration': 3.0,
        'hint_pulse_speed': 1.0,
    }
    
    # Educational settings
    EDUCATION = {
        'hint_delay': 5.0,              # seconds before showing hint
        'celebration_threshold': 3,      # correct answers for celebration
        'break_reminder_time': 900,     # 15 minutes
        'min_session_length': 300,      # 5 minutes
        'max_session_length': 1800,     # 30 minutes
        'difficulty_adjustment_rate': 0.1,
    }
    
    # Module settings
    MODULES = {
        'identify_pieces': {
            'min_age': 4,
            'max_age': 8,
            'base_duration': 10,  # minutes
            'questions_per_session': 10,
            'hint_after_attempts': 2,
        },
        'board_setup': {
            'min_age': 5,
            'max_age': 10,
            'base_duration': 15,
        },
        # Add more modules as implemented
    }
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    ASSETS_DIR = BASE_DIR / "assets"
    IMAGES_DIR = ASSETS_DIR / "images"
    SOUNDS_DIR = ASSETS_DIR / "sounds"
    FONTS_DIR = ASSETS_DIR / "fonts"
    DATA_DIR = BASE_DIR / "data"
    PROFILES_DIR = DATA_DIR / "profiles"
    
    # Piece images configuration
    PIECE_IMAGES = {
        'white': {
            'king': 'pieces/white_king.png',
            'queen': 'pieces/white_queen.png',
            'rook': 'pieces/white_rook.png',
            'bishop': 'pieces/white_bishop.png',
            'knight': 'pieces/white_knight.png',
            'pawn': 'pieces/white_pawn.png',
        },
        'black': {
            'king': 'pieces/black_king.png',
            'queen': 'pieces/black_queen.png',
            'rook': 'pieces/black_rook.png',
            'bishop': 'pieces/black_bishop.png',
            'knight': 'pieces/black_knight.png',
            'pawn': 'pieces/black_pawn.png',
        }
    }
    
    # Sound effects configuration
    SOUND_EFFECTS = {
        'success': 'feedback/success.mp3',
        'incorrect': 'feedback/incorrect.wav',
        'hint': 'feedback/hint.wav',
        'move_piece': 'feedback/move.wav',
        'celebration': 'feedback/celebration.wav',
        'button_click': 'feedback/click.wav',
    }
    
    # UI settings
    UI = {
        'button_padding': 20,
        'button_min_width': 150,
        'button_min_height': 60,
        'border_radius': 10,
        'transition_speed': 0.3,
        'tooltip_delay': 1.0,
    }
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories = [
            cls.DATA_DIR,
            cls.PROFILES_DIR,
            cls.ASSETS_DIR,
            cls.IMAGES_DIR,
            cls.SOUNDS_DIR,
            cls.FONTS_DIR,
            cls.IMAGES_DIR / "pieces",
            cls.IMAGES_DIR / "backgrounds",
            cls.IMAGES_DIR / "ui",
            cls.SOUNDS_DIR / "feedback",
            cls.SOUNDS_DIR / "music",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def __init__(self):
        """Initialize configuration and ensure directories exist"""
        self.ensure_directories()