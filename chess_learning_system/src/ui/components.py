# src/ui/components.py - Reusable UI components for child-friendly interface

import pygame
from typing import Callable, Optional, Tuple
from src.utils.math_helpers import ease_in_out, point_in_rect


class Button:
    """Child-friendly button component"""
    
    def __init__(self, text: str, pos: Tuple[int, int], size: Tuple[int, int],
                 callback: Callable, config=None, font=None):
        self.text = text
        self.pos = pos
        self.size = size
        self.callback = callback
        self.config = config
        
        # Create rect for collision detection
        self.rect = pygame.Rect(pos[0] - size[0]//2, pos[1] - size[1]//2, size[0], size[1])
        
        # Visual properties
        self.base_color = config.COLORS['primary'] if config else (52, 152, 219)
        self.hover_color = self._brighten_color(self.base_color)
        self.text_color = config.COLORS['text_light'] if config else (255, 255, 255)
        self.border_radius = config.UI['border_radius'] if config else 10
        
        # State
        self.is_hovered = False
        self.is_pressed = False
        self.hover_scale = 1.0
        self.press_offset = 0
        
        # Animation
        self.animation_time = 0
        
        # Font
        self.font = font if font else pygame.font.SysFont("arial", 24)  # Use Arial as default
    
    def _brighten_color(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Make a color brighter for hover effect"""
        return tuple(min(255, c + 30) for c in color)
    
    def update(self, dt: float, mouse_pos: Tuple[int, int]):
        """Update button state"""
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Skip hover sound since no sound files exist
        if self.is_hovered:
            self.hover_scale = min(1.1, self.hover_scale + dt * 3)
        else:
            self.hover_scale = max(1.0, self.hover_scale - dt * 3)
        
        if self.is_pressed:
            self.press_offset = 3
        else:
            self.press_offset = max(0, self.press_offset - dt * 20)
        
        self.animation_time += dt
    
    def handle_event(self, event: pygame.event.Event):
        """Handle mouse events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                was_pressed = self.is_pressed
                self.is_pressed = False
                if was_pressed and self.is_hovered:
                    self.on_click()
    
    def on_click(self):
        """Handle button click"""
        # Skip click sound since no sound files exist
        if self.callback:
            self.callback()
    
    def render(self, screen: pygame.Surface):
        """Render the button"""
        scale = self.hover_scale
        width = int(self.size[0] * scale)
        height = int(self.size[1] * scale)
        x = self.pos[0] - width // 2
        y = self.pos[1] - height // 2 + self.press_offset
        
        shadow_offset = 5
        shadow_rect = pygame.Rect(x + shadow_offset, y + shadow_offset, width, height)
        shadow_color = (0, 0, 0, 50)
        
        shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, shadow_color, shadow_surf.get_rect(), 
                        border_radius=self.border_radius)
        screen.blit(shadow_surf, (x + shadow_offset, y + shadow_offset))
        
        button_rect = pygame.Rect(x, y, width, height)
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, button_rect, border_radius=self.border_radius)
        
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.pos[0], self.pos[1] + self.press_offset))
        screen.blit(text_surface, text_rect)

class AnimatedText:
    """Animated text for celebrations and feedback"""
    
    def __init__(self, text: str, pos: Tuple[int, int], font_size: int,
                 color: Tuple[int, int, int], duration: float = 2.0, config=None, font=None):
        self.text = text
        self.start_pos = pos
        self.pos = list(pos)
        self.font_size = font_size
        self.color = color
        self.duration = duration
        self.config = config
        
        # Animation state
        self.time = 0
        self.alpha = 255
        self.scale = 1.0
        self.is_complete = False
        
        # Load font
        self.font = font if font else pygame.font.SysFont("arial", font_size)  # Use Arial as default
    
    def update(self, dt: float):
        """Update animation"""
        self.time += dt
        if self.time >= self.duration:
            self.is_complete = True
            return
        
        progress = self.time / self.duration
        self.alpha = int(255 * (1 - progress))
        self.scale = 1.0 + progress * 0.5
        self.pos[1] = self.start_pos[1] - progress * 50
    
    def render(self, screen: pygame.Surface):
        """Render animated text"""
        if self.is_complete:
            return
        
        text_surface = self.font.render(self.text, True, self.color)
        if self.scale != 1.0:
            width = int(text_surface.get_width() * self.scale)
            height = int(text_surface.get_height() * self.scale)
            text_surface = pygame.transform.smoothscale(text_surface, (width, height))
        
        text_surface.set_alpha(self.alpha)
        text_rect = text_surface.get_rect(center=(self.pos[0], self.pos[1]))
        screen.blit(text_surface, text_rect)

# ProgressBar class remains unchanged since it doesn't use fonts or sounds

class ProgressBar:
    """Visual progress indicator for children"""
    
    def __init__(self, pos: Tuple[int, int], size: Tuple[int, int], 
                 max_value: float, config=None):
        self.pos = pos
        self.size = size
        self.max_value = max_value
        self.current_value = 0
        self.target_value = 0
        self.config = config
        
        # Visual properties
        self.bg_color = (200, 200, 200)
        self.fill_color = config.COLORS['secondary'] if config else (46, 204, 113)
        self.border_color = (100, 100, 100)
        self.border_radius = 5
        
        # Animation
        self.fill_animation_speed = 2.0
        
    def set_value(self, value: float):
        """Set the progress value"""
        self.target_value = min(self.max_value, max(0, value))
        # Also immediately cap current_value to prevent overflow
        self.current_value = min(self.current_value, self.max_value)
    
    def update(self, dt: float):
        """Update progress bar animation"""
        if self.current_value < self.target_value:
            self.current_value = min(self.target_value, 
                                   self.current_value + self.max_value * dt * self.fill_animation_speed)
        elif self.current_value > self.target_value:
            self.current_value = max(self.target_value,
                                   self.current_value - self.max_value * dt * self.fill_animation_speed)
    
    def render(self, screen: pygame.Surface):
        """Render the progress bar"""
        # Background
        bg_rect = pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
        pygame.draw.rect(screen, self.bg_color, bg_rect, 
                        border_radius=self.border_radius)
        
        # Fill
        if self.current_value > 0:
            fill_width = int((self.current_value / self.max_value) * self.size[0])
            fill_rect = pygame.Rect(self.pos[0], self.pos[1], fill_width, self.size[1])
            pygame.draw.rect(screen, self.fill_color, fill_rect,
                           border_radius=self.border_radius)
        
        # Border
        pygame.draw.rect(screen, self.border_color, bg_rect, 2,
                        border_radius=self.border_radius)
        
        # Add milestone stars if configured
        if hasattr(self, 'milestones'):
            for milestone in self.milestones:
                if self.current_value >= milestone['value']:
                    star_x = int(self.pos[0] + (milestone['value'] / self.max_value) * self.size[0])
                    star_y = self.pos[1] - 10
                    self._draw_star(screen, (star_x, star_y), 8, (255, 215, 0))
    
    def _draw_star(self, screen: pygame.Surface, pos: Tuple[int, int], size: int, color):
        """Draw a simple star shape"""
        # Simple star with 5 points
        import math
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
        
        pygame.draw.polygon(screen, color, points)


class AnimatedText:
    """Animated text for celebrations and feedback"""
    
    def __init__(self, text: str, pos: Tuple[int, int], font_size: int,
                 color: Tuple[int, int, int], duration: float = 2.0, config=None):
        self.text = text
        self.start_pos = pos
        self.pos = list(pos)
        self.font_size = font_size
        self.color = color
        self.duration = duration
        self.config = config
        
        # Animation state
        self.time = 0
        self.alpha = 255
        self.scale = 1.0
        self.is_complete = False
        
        # Load font
        if config:
            from src.core.game_engine import ChessEducationEngine
            engine = ChessEducationEngine()
            self.font = engine.resource_manager.load_font(None, font_size)
        else:
            self.font = pygame.font.Font(None, font_size)
    
    def update(self, dt: float):
        """Update animation"""
        self.time += dt
        
        if self.time >= self.duration:
            self.is_complete = True
            return
        
        # Calculate animation progress
        progress = self.time / self.duration
        
        # Fade out
        self.alpha = int(255 * (1 - progress))
        
        # Scale up and move up
        self.scale = 1.0 + progress * 0.5
        self.pos[1] = self.start_pos[1] - progress * 50
    
    def render(self, screen: pygame.Surface):
        """Render animated text"""
        if self.is_complete:
            return
        
        # Render text with alpha
        text_surface = self.font.render(self.text, True, self.color)
        
        # Scale if needed
        if self.scale != 1.0:
            width = int(text_surface.get_width() * self.scale)
            height = int(text_surface.get_height() * self.scale)
            text_surface = pygame.transform.smoothscale(text_surface, (width, height))
        
        # Apply alpha
        text_surface.set_alpha(self.alpha)
        
        # Center and blit
        text_rect = text_surface.get_rect(center=(self.pos[0], self.pos[1]))
        screen.blit(text_surface, text_rect)

    def is_finished(self):
        return self.time >= self.duration  # True if animation is done