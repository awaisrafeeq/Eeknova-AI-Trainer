import pygame
from src.core.state_machine import BaseState, GameState
from src.ui.components import Button

class MainMenuState(BaseState):
    """Main menu for selecting learning modules"""
    
    def __init__(self, engine):
        super().__init__(engine)
        
        # Menu title
        self.title_text = "Choose Your Adventure!"
        
        # Scroll variables
        self.scroll_y = 0  # Current scroll offset
        self.max_scroll = 0  # Maximum scrollable height (calculated later)
        self.scroll_speed = 20  # Pixels per scroll event
        
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
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'Pawn Movement',
                'description': 'Master how pawns move and capture',
                'state': GameState.PAWN_MOVEMENT,
                'icon': 'pawn',
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'Knight Movement',
                'description': 'Learn the knight\'s special L-shaped move',
                'state': GameState.KNIGHT_MOVEMENT,
                'icon': 'knight',
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'Rook Movement',
                'description': 'Learn the Rook Movement Drill movements',
                'state': GameState.ROOK_MOVEMENT,
                'icon': 'rook',
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'Bishop Movement ',
                'description': 'Learn the Bishop Movement Drill movements',
                'state': GameState.BISHOP_MOVEMENT,
                'icon': 'bishop',
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'Queen Movement ',
                'description': 'Learn the Queen Movement Drill movements',
                'state': GameState.QUEEN_MOVEMENT,
                'icon': 'queen',
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'King Movement',
                'description': 'Learn how to move the King and check',
                'state': GameState.KING_MOVEMENT,
                'icon': 'king',
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'Special Moves',
                'description': 'Learn about castling, en passant, and promotion',
                'state': GameState.SPECIAL_MOVES,
                'icon': 'pawn',
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'Checkmate and Stalemate',
                'description': 'Learn the basics of check, checkmate, and stalemate',
                'state': GameState.CHECK_CHECKMATE_STALEMATE,
                'icon': 'king',
                'unlocked': True,
                'stars': 0
            },
            {
                'name': 'Game Play',
                'description': 'Learn the basic opening principles in chess',
                'state': GameState.PlayWithAI,
                'icon': 'king',
                'unlocked': True,
                'stars': 0
            }
        ]
        
        # Create module buttons and calculate max scroll
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
        self.title_font = pygame.font.Font(None, self.config.FONTS['large_size'])
        self.module_font = pygame.font.Font(None, self.config.FONTS['default_size'])
        self.desc_font = pygame.font.Font(None, self.config.FONTS['small_size'])
    
    def create_module_buttons(self):
        """Create buttons for each module"""
        self.module_buttons = []
        
        # Grid layout
        columns = 3
        start_x = 200
        start_y = 200
        spacing_x = 250
        spacing_y = 200
        button_height = 150
        
        for i, module in enumerate(self.modules):
            col = i % columns
            row = i // columns
            
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y
            
            button = ModuleButton(
                module=module,
                pos=(x, y),
                size=(200, button_height),
                callback=lambda m=module: self.on_module_clicked(m),
                config=self.config,
                engine=self.engine
            )
            
            self.module_buttons.append(button)
        
        # Calculate max scroll (ensure last row is fully visible)
        rows = (len(self.modules) + columns - 1) // columns
        content_height = start_y + rows * spacing_y + button_height
        self.max_scroll = max(0, content_height - self.config.SCREEN_HEIGHT)
    
    def enter(self):
        """Called when entering the main menu"""
        super().enter()
        
        self.scroll_y = 0  # Reset scroll position
        self.engine.audio_manager.stop_music()
        try:
            self.engine.audio_manager.play_music('menu_theme.ogg', loops=-1)
        except Exception as e:
            print(f"Warning: Failed to play menu music: {e}")
    
    def update(self, dt):
        """Update the main menu"""
        super().update(dt)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Update buttons with scroll-adjusted positions
        for button in self.module_buttons:
            button.rect.y = button.original_y - self.scroll_y
            button.update(dt, mouse_pos)
        
        self.back_button.update(dt, mouse_pos)
    
    def render(self, screen):
        """Render the main menu"""
        #screen.fill(self.config.COLORS['background'])
        background_image = self.engine.resource_manager.load_image(
        "bg.jpg",  # <-- keep this simple; no hardcoded project root
        size=screen.get_size()
        )
       # print("[render] blitting background")
        screen.blit(background_image, (0, 0))
        # Draw title
        title_surface = self.title_font.render(self.title_text, True,
                                             self.config.COLORS['primary'])
        title_rect = title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 80))
        screen.blit(title_surface, title_rect)
        
        # Clip rendering to screen bounds
        clip_rect = pygame.Rect(0, 150, self.config.SCREEN_WIDTH, self.config.SCREEN_HEIGHT - 150)
        screen.set_clip(clip_rect)
        
        # Draw module buttons
        for button in self.module_buttons:
            if button.rect.top < self.config.SCREEN_HEIGHT and button.rect.bottom > 150:
                button.render(screen)
        
        screen.set_clip(None)
        
        # Draw back button (always visible, above scrollable area)
        self.back_button.render(screen)
    
    def handle_event(self, event):
        """Handle events in the main menu"""
        self.back_button.handle_event(event)
        
        # Handle scroll events
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * self.scroll_speed
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.scroll_y -= self.scroll_speed
            elif event.key == pygame.K_DOWN:
                self.scroll_y += self.scroll_speed
            self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
        
        # Handle button clicks with scroll-adjusted positions
        for button in self.module_buttons:
            button.handle_event(event)
    
    def on_module_clicked(self, module):
        """Handle module selection"""
        if module['unlocked']:
            self.engine.change_state(module['state'])
        else:
            print(f"{module['name']} is locked! Complete previous modules first.")
            try:
                self.engine.audio_manager.play_sound('error.wav')
            except Exception as e:
                print(f"Warning: Failed to play error sound: {e}")
    
    def on_back_clicked(self):
        """Handle back button"""
        self.engine.change_state(GameState.WELCOME)


class ModuleButton(Button):
    """Special button for module selection"""
    
    def __init__(self, module, pos, size, callback, config, engine):
        super().__init__(module['name'], pos, size, callback, config)
        self.module = module
        self.config = config
        self.engine = engine
        self.original_y = pos[1]  # Store original y-position for scrolling
        
        # Load icon
        self.icon = None
        if module['icon'] and module['unlocked']:
            try:
                self.icon = self.engine.resource_manager.load_piece_image(
                    self.module['icon'], 'white', (48, 48)
                )
            except Exception as e:
                print(f"Warning: Failed to load icon for {module['name']}: {e}")
        
        # Colors based on unlock status
        if module['unlocked']:
            self.base_color = config.COLORS['primary']
        else:
            self.base_color = (150, 150, 150)
            
        self.hover_color = self._brighten_color(self.base_color)
        
        self.desc_font = pygame.font.Font(None, 16)
    
    def _brighten_color(self, color):
        """Make a color brighter"""
        return tuple(min(255, c + 50) for c in color)
    
    def render(self, screen):
        """Render the module button"""
        shadow_rect = pygame.Rect(self.rect.x + 5, self.rect.y + 5, 
                                 self.rect.width, self.rect.height)
        pygame.draw.rect(screen, (0, 0, 0, 50), shadow_rect, border_radius=10)
        
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=10)
        
        if not self.module['unlocked']:
            lock_text = "🔒"
            lock_font = pygame.font.Font(None, 48)
            lock_surface = lock_font.render(lock_text, True, (255, 255, 255))
            lock_rect = lock_surface.get_rect(center=self.rect.center)
            screen.blit(lock_surface, lock_rect)
        else:
            if self.icon:
                icon_rect = self.icon.get_rect(center=(self.rect.centerx, self.rect.centery - 20))
                screen.blit(self.icon, icon_rect)
            
            title_surface = self.font.render(self.module['name'], True, self.text_color)
            title_rect = title_surface.get_rect(center=(self.rect.centerx, self.rect.centery + 20))
            screen.blit(title_surface, title_rect)
            
            desc_surface = self.desc_font.render(self.module['description'], True, self.text_color)
            desc_rect = desc_surface.get_rect(center=(self.rect.centerx, self.rect.centery + 45))
            screen.blit(desc_surface, desc_rect)
            
            if self.module['stars'] > 0:
                self.draw_stars(screen, self.module['stars'], 
                              (self.rect.centerx, self.rect.centery + 65))
    
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
            radius = size if i % 2 == 0 else size * 0.5
            x = pos[0] + radius * math.cos(angle - math.pi / 2)
            y = pos[1] + radius * math.sin(angle - math.pi / 2)
            points.append((x, y))
        
        pygame.draw.polygon(screen, color, points)