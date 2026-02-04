# src/states/board_setup_state.py - Board Setup Learning Module

import pygame
import chess
import random
from pathlib import Path
from src.core.state_machine import BaseState, GameState
from src.ui.components import Button, ProgressBar
from src.utils.timer import Timer

class BoardSetupState(BaseState):
    """Module for teaching proper chess board setup"""
    
    def __init__(self, engine):
        super().__init__(engine)
        
        # Module configuration
        self.total_pieces = 32  # All pieces on the board
        self.pieces_placed_correctly = 0
        self.mistakes_allowed = 10
        self.current_mistakes = 0
        self.session_timer = Timer()
        
        # Board dimensions
        self.board_size = 480
        self.square_size = self.board_size // 8
        self.board_offset_x = 50
        self.board_offset_y = 120
        
        # Piece tray dimensions (wider for more pieces)
        self.tray_x = 580
        self.tray_y = 120
        self.tray_width = 200
        self.tray_height = 500
        self.tray_padding = 10
        
        # Drag and drop state
        self.dragging = False
        self.dragged_piece = None
        self.drag_offset = (0, 0)
        self.original_position = None
        
        # Board state
        self.board_state = [[None for _ in range(8)] for _ in range(8)]
        self.pieces_inventory = {}  # Track piece counts
        self.piece_buttons = []  # Clickable piece type buttons
        self.selected_piece_type = None
        self.hint_squares = []
        
        # Visual feedback
        self.show_feedback = False
        self.feedback_message = ""
        self.feedback_timer = 0
        self.error_shake = 0
        
        # UI elements
        self.create_ui_elements()
        
        # Load fonts
        self.title_font = pygame.font.Font(None, 36)
        self.instruction_font = pygame.font.Font(None, 24)
        self.feedback_font = pygame.font.Font(None, 28)
        self.count_font = pygame.font.Font(None, 20)
        
        # Initialize the module
        self.setup_pieces_inventory()
        
        # Completion state
        self.module_completed = False
        self.completion_timer = 0
        
    def create_ui_elements(self):
        """Create UI elements for the module"""
        # Progress bar
        #self.progress_bar = ProgressBar(
        #    pos=(self.config.SCREEN_WIDTH // 2 - 150, 30),
        #    size=(300, 25),
        #    max_value=self.total_pieces,
        #    config=self.config
        #)
        
        # Mistakes indicator with correct color
        #self.mistakes_bar = ProgressBar(
        #    pos=(self.config.SCREEN_WIDTH // 2 - 150, 65),
        #    size=(300, 20),
        #    max_value=self.mistakes_allowed,
        #    config=self.config
        #)
        # Use error color for mistakes
        #if hasattr(self.config.COLORS, 'error'):
            #self.mistakes_bar.fill_color = self.config.COLORS['error']
        #else:
            #self.mistakes_bar.fill_color = (231, 76, 60)  # Red color
            
        
        # Navigation buttons
        self.back_button = Button(
            text="Back",
            pos=(60, 50),
            size=(100, 40),
            callback=self.on_back_clicked,
            config=self.config
        )
        
        self.hint_button = Button(
            text="Show Hint",
            pos=(self.config.SCREEN_WIDTH - 100, 50),
            size=(120, 40),
            callback=self.on_hint_clicked,
            config=self.config
        )
        
        self.reset_button = Button(
            text="Reset",
            pos=(self.config.SCREEN_WIDTH - 100, 100),
            size=(120, 40),
            callback=self.reset_board,
            config=self.config
        )
    
    def setup_pieces_inventory(self):
        """Set up the inventory of all pieces to be placed"""
        # Define all pieces and their counts
        self.pieces_inventory = {
            'white_pawn': {'count': 8, 'total': 8, 'positions': [(i, 1) for i in range(8)]},
            'white_rook': {'count': 2, 'total': 2, 'positions': [(0, 0), (7, 0)]},
            'white_knight': {'count': 2, 'total': 2, 'positions': [(1, 0), (6, 0)]},
            'white_bishop': {'count': 2, 'total': 2, 'positions': [(2, 0), (5, 0)]},
            'white_queen': {'count': 1, 'total': 1, 'positions': [(3, 0)]},
            'white_king': {'count': 1, 'total': 1, 'positions': [(4, 0)]},
            'black_pawn': {'count': 8, 'total': 8, 'positions': [(i, 6) for i in range(8)]},
            'black_rook': {'count': 2, 'total': 2, 'positions': [(0, 7), (7, 7)]},
            'black_knight': {'count': 2, 'total': 2, 'positions': [(1, 7), (6, 7)]},
            'black_bishop': {'count': 2, 'total': 2, 'positions': [(2, 7), (5, 7)]},
            'black_queen': {'count': 1, 'total': 1, 'positions': [(3, 7)]},
            'black_king': {'count': 1, 'total': 1, 'positions': [(4, 7)]}
        }
        
        # Create piece type buttons
        self.create_piece_buttons()
        
    def create_piece_buttons(self):
        """Create clickable buttons for each piece type"""
        self.piece_buttons = []
        
        button_height = 35
        spacing = 5
        start_y = self.tray_y + 40
        
        piece_order = [
            ('white_king', '♔'), ('white_queen', '♕'), ('white_rook', '♖'),
            ('white_bishop', '♗'), ('white_knight', '♘'), ('white_pawn', '♙'),
            ('black_king', '♚'), ('black_queen', '♛'), ('black_rook', '♜'),
            ('black_bishop', '♝'), ('black_knight', '♞'), ('black_pawn', '♟')
        ]
        
        for i, (piece_key, symbol) in enumerate(piece_order):
            y = start_y + i * (button_height + spacing)
            
            button = PieceInventoryButton(
                piece_key=piece_key,
                symbol=symbol,
                inventory=self.pieces_inventory[piece_key],
                pos=(self.tray_x + self.tray_padding, y),
                size=(self.tray_width - 2 * self.tray_padding, button_height),
                callback=lambda pk=piece_key: self.select_piece_type(pk),
                config=self.config
            )
            self.piece_buttons.append(button)
    
    def select_piece_type(self, piece_key):
        """Select a piece type to place"""
        if self.pieces_inventory[piece_key]['count'] > 0:
            self.selected_piece_type = piece_key
            self.hint_squares = []  # Clear hints when selecting new piece
            
            # Play selection sound
            self.engine.audio_manager.play_sound('click.wav')
    
    def get_piece_color_and_type(self, piece_key):
        """Extract color and type from piece key"""
        parts = piece_key.split('_')
        return parts[0], parts[1]
    
    def square_to_pixels(self, file, rank):
        """Convert board square to pixel coordinates"""
        x = self.board_offset_x + file * self.square_size
        y = self.board_offset_y + (7 - rank) * self.square_size
        return (x, y)
    
    def pixels_to_square(self, x, y):
        """Convert pixel coordinates to board square"""
        file = (x - self.board_offset_x) // self.square_size
        rank = 7 - ((y - self.board_offset_y) // self.square_size)
        
        if 0 <= file <= 7 and 0 <= rank <= 7:
            return (file, rank)
        return None
    
    def is_correct_position(self, piece_key, file, rank):
        """Check if piece is placed in correct position"""
        positions = self.pieces_inventory[piece_key]['positions']
        return (file, rank) in positions
    
    def enter(self):
        """Called when entering the board setup state"""
        super().enter()
        
        # Reset session
        self.reset_board()
        self.module_completed = False
        
        # Play learning music
        self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
    
    def handle_event(self, event):
        """Handle events"""
        # Handle button events
        self.back_button.handle_event(event)
        self.hint_button.handle_event(event)
        self.reset_button.handle_event(event)
        
        # Handle piece buttons
        for button in self.piece_buttons:
            button.handle_event(event)
        
        # Handle board clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = pygame.mouse.get_pos()
                square = self.pixels_to_square(mouse_pos[0], mouse_pos[1])
                
                if square and self.selected_piece_type:
                    self.try_place_piece(square)
    
    def try_place_piece(self, square):
        """Try to place the selected piece type at the given square"""
        file, rank = square
        
        # Check if square is empty
        if self.board_state[rank][file] is not None:
            self.show_feedback = True
            self.feedback_message = "Square already occupied!"
            self.feedback_timer = 0
            self.engine.audio_manager.play_sound('error.wav')
            return
        
        # Check if correct position
        if self.is_correct_position(self.selected_piece_type, file, rank):
            # Correct placement
            self.place_piece_correctly(file, rank)
        else:
            # Wrong placement
            self.place_piece_incorrectly()
    
    def place_piece_correctly(self, file, rank):
        """Handle correct piece placement"""
        # Place piece on board
        self.board_state[rank][file] = self.selected_piece_type
        
        # Update inventory
        self.pieces_inventory[self.selected_piece_type]['count'] -= 1
        
        # Update progress
        self.pieces_placed_correctly += 1
        #self.progress_bar.set_value(self.pieces_placed_correctly)
        
        # Clear selection if no more pieces of this type
        if self.pieces_inventory[self.selected_piece_type]['count'] == 0:
            self.selected_piece_type = None
        
        # Update piece buttons
        for button in self.piece_buttons:
            button.update_count()
        
        # Feedback
        self.show_feedback = True
        self.feedback_message = "Correct! Well placed!"
        self.feedback_timer = 0
        
        # Clear hints
        self.hint_squares = []
        
        # Sound effect
        self.engine.audio_manager.play_sound('success.wav')
        
        # Check for completion
        if self.pieces_placed_correctly >= self.total_pieces:
            self.complete_module()
    
    def place_piece_incorrectly(self):
        """Handle incorrect piece placement"""
        # Update mistakes
        self.current_mistakes += 1
        #self.mistakes_bar.set_value(self.current_mistakes)
        
        # Feedback
        self.show_feedback = True
        self.feedback_message = "Wrong position! Try again!"
        self.feedback_timer = 0
        self.error_shake = 0.5
        
        # Sound effect
        self.engine.audio_manager.play_sound('error.wav')
        
        # Auto-show hint after too many mistakes
        if self.current_mistakes >= self.mistakes_allowed:
            self.show_feedback = True
            self.feedback_message = "Too many mistakes! Here's a hint..."
            self.on_hint_clicked()
    
    def on_hint_clicked(self):
        """Show hint for selected piece"""
        if self.selected_piece_type:
            # Show all valid positions for selected piece
            self.hint_squares = self.pieces_inventory[self.selected_piece_type]['positions'].copy()
            
            # Remove already placed positions
            self.hint_squares = [(f, r) for f, r in self.hint_squares 
                               if self.board_state[r][f] is None]
        else:
            self.show_feedback = True
            self.feedback_message = "Select a piece first!"
            self.feedback_timer = 0
    
    def reset_board(self):
        """Reset the board to start over"""
        # Clear board
        self.board_state = [[None for _ in range(8)] for _ in range(8)]
        
        # Reset inventory
        for piece_key in self.pieces_inventory:
            self.pieces_inventory[piece_key]['count'] = self.pieces_inventory[piece_key]['total']
        
        # Reset counters
        self.pieces_placed_correctly = 0
        self.current_mistakes = 0
        #self.progress_bar.set_value(0)
        #self.mistakes_bar.set_value(0)
        
        # Clear selection and feedback
        self.selected_piece_type = None
        self.show_feedback = False
        self.hint_squares = []
        
        # Update buttons
        for button in self.piece_buttons:
            button.update_count()
        
        # Reset timer
        self.session_timer.reset()
    
    def complete_module(self):
        """Complete the module"""
        self.module_completed = True
        self.completion_timer = 0
        self.show_feedback = True
        self.feedback_message = "Excellent! You've mastered board setup!"
        
        # Play completion sound
        self.engine.audio_manager.play_sound('complete.wav')
        
        # TODO: Unlock next module in progress tracking
    
    def on_back_clicked(self):
        """Return to main menu"""
        self.engine.change_state(GameState.MAIN_MENU)
    
    def update(self, dt):
        """Update the board setup state"""
        super().update(dt)
        
        # Update UI elements
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.update(dt, mouse_pos)
        self.hint_button.update(dt, mouse_pos)
        self.reset_button.update(dt, mouse_pos)
        
        for button in self.piece_buttons:
            button.update(dt, mouse_pos)
        
        # Update feedback timer
        if self.show_feedback:
            self.feedback_timer += dt
            if self.feedback_timer > 2.0 and not self.module_completed:
                self.show_feedback = False
                self.feedback_message = ""
        
        # Update error shake
        if self.error_shake > 0:
            self.error_shake = max(0, self.error_shake - dt * 2)
        
        # Update completion
        if self.module_completed:
            self.completion_timer += dt
            if self.completion_timer > 4.0:
                self.engine.change_state(GameState.MAIN_MENU)
    
    def _resource_base():
        """Support running from source or PyInstaller bundle."""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(__file__).resolve().parent

    def _resolve_image_path(filename_or_path: str) -> Path:
        """
        Resolve an image path given either:
        - 'backgrounds/gradient_bg.jpg'
        - 'assets/images/backgrounds/gradient_bg.jpg'
        - absolute or relative OS path
        """
        candidate = Path(filename_or_path)

        # If it's already absolute or exists as given, try it first.
        if candidate.is_absolute() and candidate.exists():
            return candidate

        base = _resource_base()

        # If the provided path already contains 'assets', don't double-prepend.
        if "assets" in str(candidate).replace("\\", "/"):
            p = (base / candidate).resolve()
            if p.exists():
                return p

        # Default: look under assets/images/<filename>
        p = (base / "assets" / "images" / candidate).resolve()
        return p

    def load_image(self, filename_or_path: str, *, target_size=None):
        """
        Bulletproof image loader:
        - Accepts 'backgrounds/gradient_bg.jpg', 'assets/images/...', or any absolute/relative path.
        - Tries several candidate paths without raising.
        - Only calls convert/convert_alpha if a display Surface exists.
        - Returns a valid fallback Surface on any error.
        """
        try:
            print(f"[load_image] requested: {filename_or_path}")

            # Normalize separators
            incoming = filename_or_path.replace("\\", "/").lstrip("./")

            # Build candidate search list
            cwd = os.getcwd()
            candidates = []

            # 1) If caller gave absolute or relative path as-is
            candidates.append(incoming)
            candidates.append(os.path.join(cwd, incoming))

            # 2) If path already contains 'assets', try from CWD
            if "assets/" in incoming:
                candidates.append(os.path.join(cwd, incoming))

            # 3) Default convention: assets/images/<incoming>
            candidates.append(os.path.join(cwd, "assets", "images", incoming))

            # Deduplicate while preserving order
            seen = set()
            uniq_candidates = []
            for c in candidates:
                c = os.path.abspath(c)
                if c not in seen:
                    uniq_candidates.append(c)
                    seen.add(c)

            # Pick the first that exists
            chosen = None
            for c in uniq_candidates:
                if os.path.isfile(c):
                    chosen = c
                    break

            print(f"[load_image] candidates:\n  " + "\n  ".join(uniq_candidates))
            if not chosen:
                logging.warning(f"[load_image] file not found; using fallback. requested={incoming}")
                # fallback
                surf = pygame.Surface(target_size or (1, 1))
                # surf.fill((255, 0, 255))  # uncomment to visualize missing asset
                return surf

            # Safe load
            image = pygame.image.load(chosen)

            # Only convert if display is initialized
            display_ready = pygame.display.get_surface() is not None
            if display_ready:
                if image.get_alpha() is not None:
                    image = image.convert_alpha()
                else:
                    image = image.convert()

            # Optional scaling
            if target_size:
                image = pygame.transform.smoothscale(image, target_size)

            print(f"[load_image] loaded OK: {chosen}")
            return image

        except Exception as e:
            logging.exception(f"[load_image] error: {e}")
            # Never propagate: always return a blit-safe fallback
            surf = pygame.Surface(target_size or (1, 1))
            # surf.fill((255, 0, 255))
            return surf
    def render(self, screen):
        """Render the board setup state"""
        # Clear screen
        # screen.fill(self.config.COLORS['background'])
        #print("[render] loading background image")
        background_image = self.engine.resource_manager.load_image(
        "gradient_bg.jpg",  # <-- keep this simple; no hardcoded project root
        size=screen.get_size()
        )
       # print("[render] blitting background")
        screen.blit(background_image, (0, 0))
        # Draw title
        title_text = "Learn Board Setup"
        title_surface = self.title_font.render(title_text, True, self.config.COLORS['text_dark'])
        title_rect = title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 40))
        screen.blit(title_surface, title_rect)
        
        # Draw progress bars
        #self.progress_bar.render(screen)
        
        # Draw mistakes label and bar
        #mistakes_label = self.instruction_font.render("Mistakes:", True, self.config.COLORS['text_dark'])
        #screen.blit(mistakes_label, (self.config.SCREEN_WIDTH // 2 - 220, 65))
        #self.mistakes_bar.render(screen)
        
        # Draw instruction
        if not self.module_completed:
            if self.selected_piece_type:
                color, piece_type = self.get_piece_color_and_type(self.selected_piece_type)
                instruction = f"Place the {color} {piece_type} on the board"
            else:
                instruction = "Select a piece from the right panel"
            
            inst_surface = self.instruction_font.render(instruction, True, self.config.COLORS['text_dark'])
            inst_rect = inst_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 100))
            screen.blit(inst_surface, inst_rect)
        
        # Draw chess board
        self.draw_board(screen)
        
        # Draw piece inventory panel
        self.draw_piece_inventory(screen)
        
        # Draw feedback
        if self.show_feedback:
            color = self.config.COLORS['secondary'] if "Correct" in self.feedback_message else (231, 76, 60)
            feedback_surface = self.feedback_font.render(self.feedback_message, True, color)
            feedback_rect = feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 650))
            
            # Add shake effect for errors
            if self.error_shake > 0:
                import math
                feedback_rect.x += int(math.sin(self.error_shake * 20) * 5)
            
            screen.blit(feedback_surface, feedback_rect)
        
        # Draw navigation buttons
        self.back_button.render(screen)
        self.hint_button.render(screen)
        self.reset_button.render(screen)
        
        # Draw completion overlay
        if self.module_completed:
            self.draw_completion_overlay(screen)
    
    def draw_board(self, screen):
        """Draw the chess board"""
        # Draw board background
        board_rect = pygame.Rect(
            self.board_offset_x - 5,
            self.board_offset_y - 5,
            self.board_size + 10,
            self.board_size + 10
        )
        pygame.draw.rect(screen, (0, 0, 0), board_rect)
        
        # Draw squares
        for file in range(8):
            for rank in range(8):
                x = self.board_offset_x + file * self.square_size
                y = self.board_offset_y + (7 - rank) * self.square_size
                
                # Determine square color
                if (file + rank) % 2 == 0:
                    color = (240, 217, 181)  # Light squares
                else:
                    color = (181, 136, 99)   # Dark squares
                
                # Highlight hint squares
                if (file, rank) in self.hint_squares:
                    color = (255, 255, 100)  # Yellow highlight
                
                rect = pygame.Rect(x, y, self.square_size, self.square_size)
                pygame.draw.rect(screen, color, rect)
                
                # Draw placed pieces
                if self.board_state[rank][file]:
                    piece_key = self.board_state[rank][file]
                    color, piece_type = self.get_piece_color_and_type(piece_key)
                    
                    # Load and draw piece image
                    piece_image = self.engine.resource_manager.load_piece_image(
                        piece_type, color, (self.square_size - 10, self.square_size - 10)
                    )
                    screen.blit(piece_image, (x + 5, y + 5))
                
                # Draw file labels (a-h)
                if rank == 0:
                    label = chr(ord('a') + file)
                    label_surface = self.instruction_font.render(label, True, self.config.COLORS['text_dark'])
                    label_rect = label_surface.get_rect(center=(x + self.square_size // 2, y + self.square_size + 15))
                    screen.blit(label_surface, label_rect)
                
                # Draw rank labels (1-8)
                if file == 0:
                    label = str(rank + 1)
                    label_surface = self.instruction_font.render(label, True, self.config.COLORS['text_dark'])
                    label_rect = label_surface.get_rect(center=(x - 15, y + self.square_size // 2))
                    screen.blit(label_surface, label_rect)
    
    def draw_piece_inventory(self, screen):
        """Draw the piece inventory panel"""
        # Draw panel background
        panel_rect = pygame.Rect(self.tray_x, self.tray_y, self.tray_width, self.tray_height)
        pygame.draw.rect(screen, (220, 220, 220), panel_rect)
        pygame.draw.rect(screen, (100, 100, 100), panel_rect, 3)
        
        # Draw panel title
        title = "Pieces to Place"
        title_surface = self.instruction_font.render(title, True, self.config.COLORS['text_dark'])
        title_rect = title_surface.get_rect(center=(self.tray_x + self.tray_width // 2, self.tray_y - 20))
        screen.blit(title_surface, title_rect)
        
        # Draw piece buttons
        for button in self.piece_buttons:
            button.render(screen)
    
    def draw_completion_overlay(self, screen):
        """Draw completion celebration overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((screen.get_width(), screen.get_height()))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Success message
        success_font = pygame.font.Font(None, 72)
        success_text = "Perfect Setup!"
        success_surface = success_font.render(success_text, True, (255, 215, 0))
        success_rect = success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 200))
        screen.blit(success_surface, success_rect)
        
        # Stats
        stats_text = f"Completed with {self.current_mistakes} mistakes"
        stats_surface = self.instruction_font.render(stats_text, True, (255, 255, 255))
        stats_rect = stats_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 300))
        screen.blit(stats_surface, stats_rect)


class PieceInventoryButton(Button):
    """Button showing piece type and remaining count"""
    
    def __init__(self, piece_key, symbol, inventory, pos, size, callback, config):
        # Extract piece name for display
        color, piece_type = piece_key.split('_')
        display_text = f"{symbol} {piece_type.title()}"
        
        super().__init__(display_text, pos, size, callback, config)
        
        self.piece_key = piece_key
        self.symbol = symbol
        self.inventory = inventory
        self.base_rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.rect = self.base_rect.copy()
        
        # Fonts
        self.symbol_font = pygame.font.Font(None, 28)
        self.count_font = pygame.font.Font(None, 24)
        
    def update_count(self):
        """Update the visual state based on remaining pieces"""
        if self.inventory['count'] == 0:
            self.base_color = (200, 200, 200)  # Gray out when empty
        else:
            self.base_color = self.config.COLORS['primary']
        self.hover_color = self._brighten_color(self.base_color)
    
    def render(self, screen):
        """Render the piece inventory button"""
        # Update color based on count
        self.update_count()
        
        # Draw button background
        color = self.hover_color if self.is_hovered else self.base_color
        if self.is_pressed:
            color = tuple(int(c * 0.8) for c in color)
        
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=5)
        
        # Draw symbol
        symbol_surface = self.symbol_font.render(self.symbol, True, self.text_color)
        symbol_rect = symbol_surface.get_rect(midleft=(self.rect.left + 10, self.rect.centery))
        screen.blit(symbol_surface, symbol_rect)
        
        # Draw piece name
        color, piece_type = self.piece_key.split('_')
        name_text = f"{piece_type.title()}"
        name_surface = self.font.render(name_text, True, self.text_color)
        name_rect = name_surface.get_rect(center=(self.rect.centerx, self.rect.centery))
        screen.blit(name_surface, name_rect)
        
        # Draw count
        count_text = f"{self.inventory['count']}/{self.inventory['total']}"
        count_color = (0, 200, 0) if self.inventory['count'] > 0 else (200, 0, 0)
        count_surface = self.count_font.render(count_text, True, count_color)
        count_rect = count_surface.get_rect(midright=(self.rect.right - 10, self.rect.centery))
        screen.blit(count_surface, count_rect)
        
        # Strike through if all placed
        if self.inventory['count'] == 0:
            pygame.draw.line(screen, (100, 100, 100), 
                           (self.rect.left + 5, self.rect.centery),
                           (self.rect.right - 5, self.rect.centery), 2)