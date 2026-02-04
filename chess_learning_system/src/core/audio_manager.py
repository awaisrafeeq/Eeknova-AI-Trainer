# src/core/audio_manager.py - Audio management system

import pygame
from typing import Optional, Dict
from src.utils.singleton import Singleton

class AudioManager(metaclass=Singleton):
    """Manages all audio playback in the game"""
    
    def __init__(self, config):
        self.config = config
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.current_music = None
        self.music_volume = config.AUDIO['music_volume']
        self.effects_volume = config.AUDIO['effects_volume']
        self.master_volume = config.AUDIO['master_volume']
        
        # Set initial volumes
        self._update_volumes()
        
        # Track playing sounds for management
        self.active_channels = []
        
    def _update_volumes(self):
        """Update all volume levels"""
        pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
    
    def play_sound(self, sound_name: str, volume: Optional[float] = None):
        """Play a sound effect"""
        # Get the sound from resource manager
        from src.core.game_engine import ChessEducationEngine
        engine = ChessEducationEngine()
        sound = engine.resource_manager.load_sound(sound_name)
        
        if not sound:
            return
        
        # Set volume
        if volume is None:
            volume = self.effects_volume
        
        sound.set_volume(volume * self.master_volume)
        
        # Play the sound
        channel = sound.play()
        
        if channel:
            self.active_channels.append(channel)
            # Clean up finished channels
            self.active_channels = [ch for ch in self.active_channels if ch.get_busy()]
    
    def play_music(self, music_file: str, loops: int = -1, fade_in: int = 1000):
        """Play background music"""
        music_path = self.config.SOUNDS_DIR / "music" / music_file
        
        if not music_path.exists():
            print(f"Warning: Music file '{music_file}' not found")
            return
        
        try:
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
            pygame.mixer.music.play(loops, fade_ms=fade_in)
            self.current_music = music_file
        except Exception as e:
            print(f"Error playing music '{music_file}': {e}")
    
    def stop_music(self, fade_out: int = 1000):
        """Stop the current music"""
        pygame.mixer.music.fadeout(fade_out)
        self.current_music = None
    
    def pause_music(self):
        """Pause the current music"""
        pygame.mixer.music.pause()
    
    def unpause_music(self):
        """Unpause the music"""
        pygame.mixer.music.unpause()
    
    def set_music_volume(self, volume: float):
        """Set the music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        self._update_volumes()
    
    def set_effects_volume(self, volume: float):
        """Set the effects volume (0.0 to 1.0)"""
        self.effects_volume = max(0.0, min(1.0, volume))
    
    def set_master_volume(self, volume: float):
        """Set the master volume (0.0 to 1.0)"""
        self.master_volume = max(0.0, min(1.0, volume))
        self._update_volumes()
    
    def play_success_sound(self):
        """Play a success/correct answer sound"""
        self.play_sound('success')
    
    def play_error_sound(self):
        """Play an error/incorrect answer sound"""
        self.play_sound('incorrect', volume=0.5)  # Softer for children
    
    def play_hint_sound(self):
        """Play a hint notification sound"""
        self.play_sound('hint')
    
    def play_click_sound(self):
        """Play a button click sound"""
        self.play_sound('button_click', volume=0.7)
    
    def play_celebration_sound(self):
        """Play a celebration/achievement sound"""
        self.play_sound('celebration')
    
    def stop_all_sounds(self):
        """Stop all currently playing sounds"""
        pygame.mixer.stop()
        self.active_channels.clear()
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_all_sounds()
        self.stop_music(fade_out=100)
        pygame.mixer.quit()