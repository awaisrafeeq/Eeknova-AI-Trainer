# src/states/welcome_state.py - Welcome screen state

import pygame
from src.core.state_machine import BaseState, GameState
from src.ui.components import Button, AnimatedText

class WelcomeState(BaseState):
    """Welcome screen shown when the game starts"""
    
    def __init__(self, engine):
        super().__init__(engine)
        
        # Create UI elements
        self.title_text = "Chess Learning Adventure"
        self.subtitle_text = "Learn chess the fun way!"
        
        # Buttons
        center_x = self.config.SCREEN_WIDTH // 2
        self.start_button = Button(
            text="Start Learning",
            pos=(center_x, 400),
            size=(250, 80),
            callback=self.on_start_clicked,
            config=self.config
        )
        
        self.settings_button = Button(
            text="Settings",
            pos=(center_x - 150, 500),
            size=(120, 60),
            callback=self.on_settings_clicked,
            config=self.config
        )
        
        self.quit_button = Button(
            text="Quit",
            pos=(center_x + 150, 500),
            size=(120, 60),
            callback=self.on_quit_clicked,
            config=self.config
        )
        
        self.buttons = [self.start_button, self.settings_button, self.quit_button]
        
        # Animation
        self.title_y = -100
        self.title_target_y = 150
        self.animation_speed = 300
        
        # Load fonts
        self.title_font = self.engine.resource_manager.load_font(None, 
                                                                self.config.FONTS['large_size'])
        self.subtitle_font = self.engine.resource_manager.load_font(None,
                                                                   self.config.FONTS['medium_size'])
        
        # Animated chess pieces
        self.piece_animations = []
        self.create_piece_animations()
        
    def create_piece_animations(self):
        """Create floating chess piece animations"""
        piece_types = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
        colors = ['white', 'black']
        
        import random
        for i in range(6):
            piece_type = random.choice(piece_types)
            color = random.choice(colors)
            
            self.piece_animations.append({
                'type': piece_type,
                'color': color,
                'x': random.randint(100, self.config.SCREEN_WIDTH - 100),
                'y': random.randint(550, self.config.SCREEN_HEIGHT - 100),
                'float_offset': random.random() * 3.14,
                'float_speed': random.uniform(0.5, 1.5),
                'scale': random.uniform(0.5, 0.8)
            })
    
    def enter(self):
        """Called when entering the welcome state"""
        super().enter()
        
        # Play welcome music
        self.engine.audio_manager.play_music('welcome_theme.ogg', loops=-1)
        
        # Reset animations
        self.title_y = -100
    
    def update(self, dt):
        """Update the welcome state"""
        super().update(dt)
        
        # Update title animation
        if self.title_y < self.title_target_y:
            self.title_y = min(self.title_target_y, 
                             self.title_y + self.animation_speed * dt)
        
        # Update buttons
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(dt, mouse_pos)
        
        # Update floating pieces
        import math
        for piece in self.piece_animations:
            piece['float_offset'] += piece['float_speed'] * dt
            
    def render(self, screen):
        """Render the welcome state"""
        # Clear screen
        screen.fill(self.config.COLORS['background'])
        
        # Draw floating chess pieces
        for piece in self.piece_animations:
            image = self.engine.resource_manager.load_piece_image(
                piece['type'], piece['color'], 
                (int(64 * piece['scale']), int(64 * piece['scale']))
            )
            
            # Apply floating animation
            import math
            y_offset = math.sin(piece['float_offset']) * 10
            
            pos = (piece['x'], piece['y'] + y_offset)
            screen.blit(image, pos)
        
        # Draw title
        title_surface = self.title_font.render(self.title_text, True, 
                                             self.config.COLORS['primary'])
        title_rect = title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 
                                                   self.title_y))
        screen.blit(title_surface, title_rect)
        
        # Draw subtitle
        if self.title_y >= self.title_target_y:
            subtitle_surface = self.subtitle_font.render(self.subtitle_text, True,
                                                       self.config.COLORS['text_dark'])
            subtitle_rect = subtitle_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2,
                                                            self.title_y + 60))
            screen.blit(subtitle_surface, subtitle_rect)
        
        # Draw buttons
        if self.title_y >= self.title_target_y - 50:
            for button in self.buttons:
                button.render(screen)
    
    def handle_event(self, event):
        """Handle events in the welcome state"""
        for button in self.buttons:
            button.handle_event(event)
    
    def on_start_clicked(self):
        """Handle start button click"""
        self.engine.change_state(GameState.MAIN_MENU)
    
    def on_settings_clicked(self):
        """Handle settings button click"""
        # TODO: Implement settings state
        print("Settings clicked - not implemented yet")
    
    def on_quit_clicked(self):
        """Handle quit button click"""
        self.engine.running = False