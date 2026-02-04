# src/states/main_menu_state.py - Main menu with module selection

import pygame
from src.core.state_machine import BaseState, GameState
from src.ui.components import Button

class MainMenuState(BaseState):
    """Main menu for selecting learning modules"""
    
    def __init__(self, engine):
        super().__init__(engine)
        
        # Menu title
        self.title_text = "Choose Your Adventure!"
        
        # Module information
        self.modules = [
            {
                'name': 'Identify Pieces',
                'description': 'Learn to recognize each chess piece',
                'state': GameState.IDENTIFY_PIECES,
                'icon': 'pawn',
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'Board Setup',
                'description': 'Learn how to set up the chess board',
                'state': GameState.BOARD_SETUP,
                'icon': 'rook',
                'unlocked': False,  # Locked until identify pieces completed
                'stars': 0
            },
            {
                'name': 'Pawn Movement',
                'description': 'Master how pawns move and capture',
                'state': GameState.PAWN_MOVEMENT,
                'icon': 'pawn',
                'unlocked': False,
                'stars': 0
            },
            {
                'name': 'Knight Movement',
                'description': 'Learn the knight\'s special L-shaped move',
                'state': GameState.KNIGHT_MOVEMENT,
                'icon': 'knight',
                'unlocked': False,
                'stars': 0
            },
            {
                'name': 'Special Moves',
                'description': 'Learn about castling, en passant, and promotion',
                'state': GameState.SPECIAL_MOVES,
                'icon': 'king',
                'unlocked': False,
                'stars': 0
            },

            # Add more modules as implemented
        ]
        
        # Create module buttons
        self.create_module_buttons()
        
        # Back button
        self.back_button = Button(
            text="Back",
            pos=(100, 50),
            size=(100, 50),
            callback=self.on_back_clicked,
            config=self.config
        )
        
        # Load fonts
        self.title_font = self.engine.resource_manager.load_font(None,
                                                                self.config.FONTS['large_size'])
        self.module_font = self.engine.resource_manager.load_font(None,
                                                                 self.config.FONTS['default_size'])
        self.desc_font = self.engine.resource_manager.load_font(None,
                                                               self.config.FONTS['small_size'])
    
    def create_module_buttons(self):
        """Create buttons for each module"""
        self.module_buttons = []
        
        # Grid layout
        columns = 3
        start_x = 200
        start_y = 200
        spacing_x = 250
        spacing_y = 200
        
        for i, module in enumerate(self.modules):
            col = i % columns
            row = i // columns
            
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            
            button = ModuleButton(
                module=module,
                pos=(x, y),
                size=(200, 150),
                callback=lambda m=module: self.on_module_clicked(m),
                config=self.config
            )
            
            self.module_buttons.append(button)
    
    def enter(self):
        """Called when entering the main menu"""
        super().enter()
        
        # Stop welcome music and play menu music
        self.engine.audio_manager.stop_music()
        self.engine.audio_manager.play_music('menu_theme.ogg', loops=-1)
        
        # TODO: Load user progress to update module unlock status
    
    def update(self, dt):
        """Update the main menu"""
        super().update(dt)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Update buttons
        self.back_button.update(dt, mouse_pos)
        
        for button in self.module_buttons:
            button.update(dt, mouse_pos)
    
    def render(self, screen):
        """Render the main menu"""
        # Clear screen
        screen.fill(self.config.COLORS['background'])
        
        # Draw title
        title_surface = self.title_font.render(self.title_text, True,
                                             self.config.COLORS['primary'])
        title_rect = title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 80))
        screen.blit(title_surface, title_rect)
        
        # Draw module buttons
        for button in self.module_buttons:
            button.render(screen)
        
        # Draw back button
        self.back_button.render(screen)
    
    def handle_event(self, event):
        """Handle events in the main menu"""
        self.back_button.handle_event(event)
        
        for button in self.module_buttons:
            button.handle_event(event)
    
    def on_module_clicked(self, module):
        """Handle module selection"""
        if module['unlocked']:
            self.engine.change_state(module['state'])
        else:
            # Show locked message
            print(f"{module['name']} is locked! Complete previous modules first.")
            self.engine.audio_manager.play_error_sound()
    
    def on_back_clicked(self):
        """Handle back button"""
        self.engine.change_state(GameState.WELCOME)


class ModuleButton(Button):
    """Special button for module selection"""
    
    def __init__(self, module, pos, size, callback, config):
        super().__init__(module['name'], pos, size, callback, config)
        self.module = module
        self.config = config
        # Load icon
        self.icon = None
        if module['icon']:
            self.icon = self.get_icon_image()
        
        # Colors based on unlock status
        if module['unlocked']:
            self.base_color = config.COLORS['primary']
        else:
            self.base_color = (150, 150, 150)  # Gray for locked
            
        self.hover_color = self._brighten_color(self.base_color)
        
        # Font for description
        self.desc_font = pygame.font.Font(None, 16)
    
    def get_icon_image(self):
        """Get the icon image for the module"""
        # Don't create a new engine instance!
        # Instead, get the existing engine instance through the state
        
        # Option 1: If MainMenuState has access to the engine
        # (You need to store self.engine = engine in MainMenuState.__init__)
        if hasattr(self, 'parent_state') and hasattr(self.parent_state, 'engine'):
            engine = self.parent_state.engine
        
        # Option 2: Get the singleton instance if it already exists
        elif hasattr(ChessEducationEngine, '_instances') and ChessEducationEngine in ChessEducationEngine._instances:
            engine = ChessEducationEngine._instances[ChessEducationEngine]
        
        # Option 3: Pass the resource manager directly to the button
        # This is the cleanest solution - modify the ModuleButton constructor
        else:
            # This should not happen if you implement one of the above
            raise RuntimeError("Cannot access engine or resource manager")
        
        # Use a chess piece as icon
        return engine.resource_manager.load_piece_image(
            self.module['icon'], 'white', (48, 48)
        )
    
    def render(self, screen):
        """Render the module button"""
        # Draw background
        scale = self.hover_scale
        width = int(self.size[0] * scale)
        height = int(self.size[1] * scale)
        x = self.pos[0] - width // 2
        y = self.pos[1] - height // 2 + self.press_offset
        
        # Shadow
        shadow_rect = pygame.Rect(x + 5, y + 5, width, height)
        shadow_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        shadow_color = (0, 0, 0, 50)
        pygame.draw.rect(shadow_surf, shadow_color, shadow_surf.get_rect(),
                        border_radius=self.border_radius)
        screen.blit(shadow_surf, (x + 5, y + 5))
        
        # Button background
        button_rect = pygame.Rect(x, y, width, height)
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, button_rect, border_radius=self.border_radius)
        
        # Draw lock overlay if locked
        if not self.module['unlocked']:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (x, y))
            
            # Draw lock icon
            lock_text = "🔒"
            lock_surface = self.font.render(lock_text, True, (255, 255, 255))
            lock_rect = lock_surface.get_rect(center=(self.pos[0], self.pos[1]))
            screen.blit(lock_surface, lock_rect)
        else:
            # Draw icon if available
            if self.icon:
                icon_rect = self.icon.get_rect(center=(self.pos[0], self.pos[1] - 20))
                screen.blit(self.icon, icon_rect)
            
            # Draw title
            title_surface = self.font.render(self.module['name'], True, self.text_color)
            title_rect = title_surface.get_rect(center=(self.pos[0], self.pos[1] + 20))
            screen.blit(title_surface, title_rect)
            
            # Draw description
            desc_surface = self.desc_font.render(self.module['description'], True, 
                                               self.text_color)
            desc_rect = desc_surface.get_rect(center=(self.pos[0], self.pos[1] + 45))
            screen.blit(desc_surface, desc_rect)
            
            # Draw stars if earned
            if self.module['stars'] > 0:
                self.draw_stars(screen, self.module['stars'], 
                              (self.pos[0], self.pos[1] + 65))
    
    def draw_stars(self, screen, count, pos):
        """Draw achievement stars"""
        star_size = 16
        spacing = 20
        start_x = pos[0] - (count * spacing) // 2
        
        for i in range(count):
            x = start_x + i * spacing
            self._draw_star(screen, (x, pos[1]), star_size, (255, 215, 0))
    
    def _draw_star(self, screen, pos, size, color):
        """Draw a simple star"""
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