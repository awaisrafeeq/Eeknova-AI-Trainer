import pygame
import chess
import random
import math
import logging
import os
from typing import Optional, List, Tuple, Dict

# Set up logging
logger = logging.getLogger(__name__)

# Try to import your base state class
try:
    from src.core.state_machine import BaseState, GameState as ProjectGameState
except ImportError:
    # Fallback minimal base state
    class BaseState:
        def __init__(self, engine):
            self.engine = engine
            self.config = getattr(engine, 'config', None)
        def enter(self): pass
        def update(self, dt): pass
        def render(self, screen): pass
        def handle_event(self, event): pass
        def exit(self): pass
    
    class ProjectGameState:
        MAIN_MENU = 'main_menu'


class SimpleButton:
    """Simple, reliable button class - KEEPING YOUR ORIGINAL STYLE"""
    
    def __init__(self, text: str, pos: Tuple[int, int], size: Tuple[int, int], callback, config=None, button_type='primary'):
        self.text = text
        self.pos = pos
        self.size = size
        self.callback = callback
        self.config = config
        self.button_type = button_type
        
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.is_hovered = False
        self.is_pressed = False
        
        # Your original color schemes
        if button_type == 'primary':
            self.base_color = (52, 152, 219)  # Blue
            self.hover_color = (41, 128, 185)
            self.text_color = (255, 255, 255)
        elif button_type == 'secondary':
            self.base_color = (46, 204, 113)  # Green
            self.hover_color = (39, 174, 96)
            self.text_color = (255, 255, 255)
        elif button_type == 'danger':
            self.base_color = (231, 76, 60)  # Red
            self.hover_color = (192, 57, 43)
            self.text_color = (255, 255, 255)
        elif button_type == 'warning':
            self.base_color = (241, 196, 15)  # Yellow
            self.hover_color = (243, 156, 18)
            self.text_color = (0, 0, 0)
        else:
            self.base_color = (149, 165, 166)  # Gray
            self.hover_color = (127, 140, 141)
            self.text_color = (255, 255, 255)
        
        self.font = pygame.font.Font(None, 24)
        self.enabled = True
    
    def update(self, dt: float, mouse_pos: Tuple[int, int]):
        if self.enabled:
            self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def handle_event(self, event):
        if not self.enabled:
            return
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.is_pressed = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_pressed and self.is_hovered:
                if self.callback:
                    self.callback()
            self.is_pressed = False
    
    def render(self, screen):
        if not self.enabled:
            color = (100, 100, 100)
            text_color = (150, 150, 150)
        else:
            color = self.hover_color if self.is_hovered else self.base_color
            text_color = self.text_color
        
        if self.is_pressed and self.enabled:
            color = tuple(int(c * 0.8) for c in color)
        
        # Draw button - YOUR ORIGINAL STYLE
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=8)
        
        # Draw text
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class ManualChessBoard:
    """Manual chess board - KEEPING YOUR IMPLEMENTATION with piece images"""
    
    def __init__(self, screen, board_size=500, offset_x=200, offset_y=120):
        self.screen = screen
        self.board_size = board_size
        self.square_size = board_size // 8
        self.offset_x = offset_x
        self.offset_y = offset_y
        
        # Board colors matching other modules - YOUR COLORS
        self.light_square_color = (240, 217, 181)
        self.dark_square_color = (181, 136, 99)
        self.highlight_color = (255, 255, 100)  # Yellow highlight
        self.target_color = (144, 238, 144)     # Light green
        self.danger_color = (255, 100, 100)     # Light red
        self.selected_color = (100, 149, 237)   # Blue
        self.legal_move_color = (173, 216, 230) # Light blue for legal moves
        
        # Chess board state
        self.board = chess.Board()
        
        # Visual state
        self.highlighted_squares = set()
        self.target_squares = set()
        self.danger_squares = set()
        self.legal_move_squares = set()  # New: for visual hints
        self.selected_square = None
        
        # Load piece images - YOUR IMPLEMENTATION
        self.piece_images = {}
        self.load_piece_images()
    
    def load_piece_images(self):
        """Load piece images from the assets folder - YOUR CODE"""
        try:
            piece_mapping = {
                'black_bishop.png': (chess.BISHOP, chess.BLACK),
                'black_king.png': (chess.KING, chess.BLACK),
                'black_knight.png': (chess.KNIGHT, chess.BLACK),
                'black_pawn.png': (chess.PAWN, chess.BLACK),
                'black_queen.png': (chess.QUEEN, chess.BLACK),
                'black_rook.png': (chess.ROOK, chess.BLACK),
                'white_bishop.png': (chess.BISHOP, chess.WHITE),
                'white_king.png': (chess.KING, chess.WHITE),
                'white_knight.png': (chess.KNIGHT, chess.WHITE),
                'white_pawn.png': (chess.PAWN, chess.WHITE),
                'white_queen.png': (chess.QUEEN, chess.WHITE),
                'white_rook.png': (chess.ROOK, chess.WHITE)
            }
            
            possible_paths = [
                os.path.join('chess_learning_system', 'assets', 'images', 'pieces'),
                os.path.join('assets', 'images', 'pieces'),
                os.path.join('src', 'assets', 'images', 'pieces'),
                'pieces'
            ]
            
            pieces_dir = None
            for path in possible_paths:
                if os.path.exists(path):
                    pieces_dir = path
                    break
            
            if pieces_dir:
                for filename, (piece_type, color) in piece_mapping.items():
                    filepath = os.path.join(pieces_dir, filename)
                    if os.path.exists(filepath):
                        try:
                            image = pygame.image.load(filepath)
                            scaled_image = pygame.transform.scale(image, (self.square_size - 10, self.square_size - 10))
                            self.piece_images[(piece_type, color)] = scaled_image
                        except Exception as e:
                            logger.warning(f"Failed to load {filename}: {e}")
                            self.piece_images[(piece_type, color)] = self.create_text_piece(piece_type, color)
                    else:
                        self.piece_images[(piece_type, color)] = self.create_text_piece(piece_type, color)
            else:
                for filename, (piece_type, color) in piece_mapping.items():
                    self.piece_images[(piece_type, color)] = self.create_text_piece(piece_type, color)
            
        except Exception as e:
            logger.error(f"Error loading piece images: {e}")
            piece_types = [chess.PAWN, chess.ROOK, chess.KNIGHT, chess.BISHOP, chess.QUEEN, chess.KING]
            colors = [chess.WHITE, chess.BLACK]
            for piece_type in piece_types:
                for color in colors:
                    self.piece_images[(piece_type, color)] = self.create_text_piece(piece_type, color)
    
    def create_text_piece(self, piece_type: int, color: bool) -> pygame.Surface:
        """Create text piece - YOUR IMPLEMENTATION"""
        surface = pygame.Surface((self.square_size - 10, self.square_size - 10), pygame.SRCALPHA)
        
        symbols = {
            chess.PAWN: '♙' if color == chess.WHITE else '♟',
            chess.ROOK: '♖' if color == chess.WHITE else '♜',
            chess.KNIGHT: '♘' if color == chess.WHITE else '♞',
            chess.BISHOP: '♗' if color == chess.WHITE else '♝',
            chess.QUEEN: '♕' if color == chess.WHITE else '♛',
            chess.KING: '♔' if color == chess.WHITE else '♚'
        }
        
        symbol = symbols.get(piece_type, '?')
        font = pygame.font.Font(None, int((self.square_size - 10) * 0.8))
        
        text_color = (255, 255, 255) if color == chess.WHITE else (50, 50, 50)
        shadow_color = (100, 100, 100)
        
        shadow_surface = font.render(symbol, True, shadow_color)
        text_surface = font.render(symbol, True, text_color)
        
        shadow_rect = shadow_surface.get_rect(center=(surface.get_width() // 2 + 2, surface.get_height() // 2 + 2))
        text_rect = text_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        
        surface.blit(shadow_surface, shadow_rect)
        surface.blit(text_surface, text_rect)
        
        return surface
    
    def clear_highlights(self):
        """Clear all visual highlights"""
        self.highlighted_squares.clear()
        self.target_squares.clear()
        self.danger_squares.clear()
        self.legal_move_squares.clear()  # Clear legal move hints
        self.selected_square = None
    
    def highlight_square(self, square: int, color_type='highlight'):
        """Highlight a square with specified color"""
        if color_type == 'target':
            self.target_squares.add(square)
        elif color_type == 'danger':
            self.danger_squares.add(square)
        elif color_type == 'legal_move':  # New: for visual hints
            self.legal_move_squares.add(square)
        else:
            self.highlighted_squares.add(square)
    
    def select_square(self, square: Optional[int]):
        """Select a square"""
        self.selected_square = square
    
    def get_square_from_pos(self, pos: Tuple[int, int]) -> Optional[int]:
        """Get chess square from pixel position"""
        x, y = pos
        
        if (x < self.offset_x or x >= self.offset_x + self.board_size or
            y < self.offset_y or y >= self.offset_y + self.board_size):
            return None
        
        file = (x - self.offset_x) // self.square_size
        rank = 7 - ((y - self.offset_y) // self.square_size)
        
        if 0 <= file <= 7 and 0 <= rank <= 7:
            return chess.square(file, rank)
        return None
    
    def get_square_rect(self, square: int) -> pygame.Rect:
        """Get pixel rectangle for a chess square"""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        x = self.offset_x + file * self.square_size
        y = self.offset_y + (7 - rank) * self.square_size
        
        return pygame.Rect(x, y, self.square_size, self.square_size)
    
    def draw(self):
        """Draw the chess board and pieces - YOUR IMPLEMENTATION"""
        # Draw board background
        board_bg = pygame.Rect(
            self.offset_x - 5, self.offset_y - 5,
            self.board_size + 10, self.board_size + 10
        )
        pygame.draw.rect(self.screen, (60, 60, 60), board_bg, border_radius=8)
        pygame.draw.rect(self.screen, (40, 40, 40), board_bg, 3, border_radius=8)
        
        # Draw squares
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, rank)
                
                # Base square color
                if (rank + file) % 2 == 0:
                    color = self.light_square_color
                else:
                    color = self.dark_square_color
                
                # Apply special colors
                if square in self.target_squares:
                    color = self.target_color
                elif square in self.danger_squares:
                    color = self.danger_color
                elif square in self.legal_move_squares:  # Visual hint highlighting
                    color = self.legal_move_color
                elif square in self.highlighted_squares:
                    color = self.highlight_color
                elif square == self.selected_square:
                    color = self.selected_color
                
                # Draw square
                x = self.offset_x + file * self.square_size
                y = self.offset_y + (7 - rank) * self.square_size
                square_rect = pygame.Rect(x, y, self.square_size, self.square_size)
                pygame.draw.rect(self.screen, color, square_rect)
                
                # Draw border for special squares
                if (square in self.target_squares or square in self.danger_squares or 
                    square in self.highlighted_squares or square == self.selected_square or
                    square in self.legal_move_squares):
                    pygame.draw.rect(self.screen, (0, 0, 0), square_rect, 2)
        
        # Draw pieces
        self._draw_pieces()
        
        # Draw coordinate labels
        self._draw_coordinates()
    
    def _draw_pieces(self):
        """Draw chess pieces on the board"""
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                file = chess.square_file(square)
                rank = chess.square_rank(square)
                
                piece_key = (piece.piece_type, piece.color)
                if piece_key in self.piece_images:
                    piece_image = self.piece_images[piece_key]
                    x = self.offset_x + file * self.square_size + 5
                    y = self.offset_y + (7 - rank) * self.square_size + 5
                    self.screen.blit(piece_image, (x, y))
    
    def _draw_coordinates(self):
        """Draw file and rank labels"""
        coord_font = pygame.font.Font(None, 20)
        coord_color = (100, 100, 100)
        
        # Files (a-h)
        for file in range(8):
            letter = chr(ord('a') + file)
            text_surface = coord_font.render(letter, True, coord_color)
            x = self.offset_x + file * self.square_size + self.square_size // 2
            y = self.offset_y + self.board_size + 5
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
        
        # Ranks (1-8)
        for rank in range(8):
            number = str(rank + 1)
            text_surface = coord_font.render(number, True, coord_color)
            x = self.offset_x - 15
            y = self.offset_y + (7 - rank) * self.square_size + self.square_size // 2
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)


class CheckCheckmateStalemateState(BaseState):
    """Enhanced Chess Endgame Training - Keeping Your Structure"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Enhanced exercise system with MORE CASES as you requested
            self.exercise_types = [
                'check_recognition',        # Basic check detection
                'complex_check',           # NEW: Discovered checks, double checks
                'check_escape',            # Ways to escape check  
                'advanced_escape',         # NEW: Complex escape scenarios
                'checkmate_recognition',   # Basic checkmate patterns
                'famous_checkmates',       # NEW: Famous checkmate patterns
                'checkmate_delivery',      # Deliver checkmate
                'mate_in_two',            # NEW: More complex mates
                'stalemate_recognition',   # Basic stalemate
                'stalemate_tricks',       # NEW: Tricky stalemate positions
                'endgame_patterns'        # NEW: Advanced endgame knowledge
            ]
            
            self.exercises_per_type = 4  # More exercises per type
            
            # Current state - KEEPING YOUR STRUCTURE
            self.current_exercise = 0
            self.current_type_index = 0
            self.exercise_type = None
            self.correct_moves = 0
            self.total_attempts = 0
            
            # Exercise progress tracking
            self.exercises_completed = {ex_type: 0 for ex_type in self.exercise_types}
            
            # Visual and interaction state
            self.show_feedback = False
            self.feedback_message = ""
            self.feedback_timer = 0
            self.show_hints = False
            self.show_visual_hints = False  # NEW: Visual move highlights
            self.current_hint = ""
            self.hint_level = 0
            self.max_hints = 3
            
            # Chess board - YOUR IMPLEMENTATION
            self.chess_board = ManualChessBoard(
                self.engine.screen,
                board_size=450,
                offset_x=(self.config.SCREEN_WIDTH - 450) // 2 if self.config else 200,
                offset_y=150
            )
            
            # Exercise-specific data
            self.target_squares = []
            self.legal_escape_squares = []  # NEW: For visual hints
            self.blocking_squares = []      # NEW: For visual hints
            self.capture_squares = []       # NEW: For visual hints
            self.scenario_answer = None
            self.selected_square = None
            
            # Create UI elements - YOUR BUTTON STYLE
            self.create_ui_elements()
            self.init_fonts()
            
            # Enhanced learning content - MORE EDUCATIONAL
            self.init_comprehensive_content()
            
            # Module completion
            self.module_completed = False
            self.completion_timer = 0
            
        except Exception as e:
            logger.error(f"Failed to initialize CheckCheckmateStalemateState: {e}")
            raise
    
    def init_fonts(self):
        """Initialize fonts - YOUR ORIGINAL IMPLEMENTATION"""
        try:
            self.title_font = pygame.font.Font(None, 40)
            self.subtitle_font = pygame.font.Font(None, 32)
            self.instruction_font = pygame.font.Font(None, 24)
            self.info_font = pygame.font.Font(None, 20)
            self.hint_font = pygame.font.Font(None, 22)
        except:
            self.title_font = pygame.font.SysFont('Arial', 40, bold=True)
            self.subtitle_font = pygame.font.SysFont('Arial', 32)
            self.instruction_font = pygame.font.SysFont('Arial', 24)
            self.info_font = pygame.font.SysFont('Arial', 20)
            self.hint_font = pygame.font.SysFont('Arial', 22)
    
    def create_ui_elements(self):
        """Create UI elements - KEEPING YOUR BUTTON STYLE"""
        try:
            # Main navigation
            self.back_button = SimpleButton(
                "← Back to Menu", (20, 20), (150, 40), self.on_back_clicked, self.config
            )
            
            # Hint system - ENHANCED
            self.hint_button = SimpleButton(
                "💡 Show Hint", (20, 80), (120, 35), self.toggle_hints, self.config, 'secondary'
            )
            
            self.visual_hint_button = SimpleButton(  # NEW: Visual hints for moves
                "👁️ Visual Hints", (150, 80), (130, 35), self.toggle_visual_hints, self.config, 'warning'
            )
            
            self.next_hint_button = SimpleButton(
                "Next Hint →", (20, 125), (120, 35), self.next_hint, self.config, 'secondary'
            )
            
            # Exercise controls
            self.reset_button = SimpleButton(
                "🔄 Reset", (self.config.SCREEN_WIDTH - 140, 80), (120, 35), self.reset_exercise, self.config, 'warning'
            )
            
            self.skip_button = SimpleButton(
                "Skip →", (self.config.SCREEN_WIDTH - 140, 125), (120, 35), self.skip_exercise, self.config, 'danger'
            )
            
            # Answer buttons - YOUR ORIGINAL STYLE
            button_width, button_height = 110, 45
            center_x = self.config.SCREEN_WIDTH // 2
            answer_y = 660
            
            self.yes_button = SimpleButton(
                "✅ YES", (center_x - 160, answer_y), (button_width, button_height),
                lambda: self.handle_answer('yes'), self.config, 'secondary'
            )
            
            self.no_button = SimpleButton(
                "❌ NO", (center_x - 40, answer_y), (button_width, button_height),
                lambda: self.handle_answer('no'), self.config, 'danger'
            )
            
            self.maybe_button = SimpleButton(
                "❓ UNCLEAR", (center_x + 80, answer_y), (button_width, button_height),
                lambda: self.handle_answer('unclear'), self.config, 'warning'
            )
            
            # Next exercise button
            self.next_button = SimpleButton(
                "Continue →", (center_x - 60, answer_y), (120, button_height),
                self.advance_exercise, self.config, 'primary'
            )
            
        except Exception as e:
            logger.error(f"Failed to create UI elements: {e}")
    
    def init_comprehensive_content(self):
        """Initialize comprehensive learning content - MORE EDUCATIONAL"""
        self.learning_content = {
            'check_recognition': {
                'title': 'Basic Check Recognition',
                'hints': [
                    'A king is in check when an enemy piece can capture it next move',
                    'Look for direct attacks from all enemy pieces',
                    'Remember: pawns attack diagonally, not forward'
                ]
            },
            'complex_check': {
                'title': 'Advanced Check Patterns',
                'hints': [
                    'Discovered check: A piece moves revealing an attack behind it',
                    'Double check: Two pieces attack the king simultaneously', 
                    'Only moving the king can escape double check'
                ]
            },
            'check_escape': {
                'title': 'Escaping Check',
                'hints': [
                    'Three ways to escape: Move king, Block attack, Capture attacker',
                    'King must move to a safe square (not under attack)',
                    'Blocking works only against sliding pieces (queen/rook/bishop)'
                ]
            },
            'advanced_escape': {
                'title': 'Complex Escape Scenarios', 
                'hints': [
                    'In double check, only king moves work - no blocking or capturing',
                    'Look for squares where the king can escape multiple threats',
                    'Sometimes sacrificing material is the only escape'
                ]
            },
            'checkmate_recognition': {
                'title': 'Basic Checkmate Patterns',
                'hints': [
                    'Checkmate = King in check + No legal moves to escape',
                    'Check if king can move to any safe adjacent square',
                    'Check if the attack can be blocked or attacker captured'
                ]
            },
            'famous_checkmates': {
                'title': 'Famous Checkmate Patterns',
                'hints': [
                    'Back-rank mate: King trapped by own pawns on back rank',
                    'Smothered mate: Knight delivers mate to king surrounded by own pieces',
                    'Arabian mate: Rook and knight coordinate for corner checkmate'
                ]
            },
            'checkmate_delivery': {
                'title': 'Delivering Checkmate',
                'hints': [
                    'Find moves that put enemy king in check with no escape',
                    'Ensure the king has no safe squares to move to',
                    'Make sure your attacking piece cannot be captured'
                ]
            },
            'mate_in_two': {
                'title': 'Multi-Move Checkmates',
                'hints': [
                    'Look for forcing moves that set up inevitable mate',
                    'Consider sacrifices that strip away the king\'s defenders',
                    'Force the enemy king into a mating net'
                ]
            },
            'stalemate_recognition': {
                'title': 'Stalemate Recognition',
                'hints': [
                    'Stalemate = King NOT in check + No legal moves = DRAW',
                    'Check if ANY piece (not just king) has legal moves',
                    'Stalemate is different from checkmate - king is safe but trapped'
                ]
            },
            'stalemate_tricks': {
                'title': 'Tricky Stalemate Positions',
                'hints': [
                    'Look carefully for hidden pawn moves or piece movements',
                    'Sometimes a piece seems trapped but has an escape square',
                    'Count all possible moves for the side to move, not just obvious ones'
                ]
            },
            'endgame_patterns': {
                'title': 'Advanced Endgame Knowledge',
                'hints': [
                    'Opposition: Kings facing each other with one square between',
                    'Key squares: Critical squares for pawn promotion',
                    'Fortress: Defensive setup that prevents breakthrough'
                ]
            }
        }
    
    def enter(self):
        """Enter the training state - YOUR ORIGINAL LOGIC"""
        try:
            super().enter()
            
            # Reset progress
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            self.module_completed = False
            
            for ex_type in self.exercise_types:
                self.exercises_completed[ex_type] = 0
            
            # Start first exercise
            self.generate_exercise()
            
            # Play background music if available
            try:
                self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
            except Exception as e:
                logger.warning(f"Failed to play music: {e}")
                
        except Exception as e:
            logger.error(f"Failed to enter state: {e}")
    
    def generate_exercise(self):
        """Generate exercises - ENHANCED WITH MORE CASES"""
        try:
            # Clear previous state
            self.chess_board.clear_highlights()
            self.show_feedback = False
            self.show_hints = False
            self.show_visual_hints = False  # Clear visual hints
            self.hint_level = 0
            self.current_hint = ""
            self.selected_square = None
            self.target_squares = []
            self.legal_escape_squares = []
            self.blocking_squares = []
            self.capture_squares = []
            
            # Determine exercise type
            if self.current_type_index < len(self.exercise_types):
                self.exercise_type = self.exercise_types[self.current_type_index]
            else:
                self.complete_module()
                return
            
            # Generate specific exercise with MORE CASES
            if self.exercise_type == 'check_recognition':
                self.generate_check_recognition()
            elif self.exercise_type == 'complex_check':  # NEW
                self.generate_complex_check()
            elif self.exercise_type == 'check_escape':
                self.generate_check_escape()
            elif self.exercise_type == 'advanced_escape':  # NEW
                self.generate_advanced_escape()
            elif self.exercise_type == 'checkmate_recognition':
                self.generate_checkmate_recognition()
            elif self.exercise_type == 'famous_checkmates':  # NEW
                self.generate_famous_checkmates()
            elif self.exercise_type == 'checkmate_delivery':
                self.generate_checkmate_delivery()
            elif self.exercise_type == 'mate_in_two':  # NEW
                self.generate_mate_in_two()
            elif self.exercise_type == 'stalemate_recognition':
                self.generate_stalemate_recognition()
            elif self.exercise_type == 'stalemate_tricks':  # NEW
                self.generate_stalemate_tricks()
            elif self.exercise_type == 'endgame_patterns':  # NEW
                self.generate_endgame_patterns()
            
            logger.info(f"Generated {self.exercise_type} exercise")
            
        except Exception as e:
            logger.error(f"Error generating exercise: {e}")
            self.skip_exercise()
    
    def generate_check_recognition(self):
        """Generate basic check recognition - YOUR ORIGINAL"""
        try:
            self.chess_board.board.clear()
            
            is_check = random.choice([True, False])
            
            if is_check:
                self.king_square = chess.E4
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.WHITE))
                
                attacker_square = chess.E7
                self.chess_board.board.set_piece_at(attacker_square, chess.Piece(chess.ROOK, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.highlight_square(self.king_square, 'danger')
                self.chess_board.highlight_square(attacker_square, 'highlight')
                
                self.scenario_answer = 'yes'
            else:
                self.king_square = chess.E4
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.WHITE))
                
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.H1, chess.Piece(chess.BISHOP, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.highlight_square(self.king_square, 'target')
                self.scenario_answer = 'no'
                
        except Exception as e:
            logger.error(f"Error generating check recognition: {e}")
    
    def generate_complex_check(self):
        """NEW: Generate complex check scenarios"""
        try:
            self.chess_board.board.clear()
            
            scenario = random.choice(['discovered_check', 'double_check', 'pin_check'])
            
            if scenario == 'discovered_check':
                # Piece moves revealing check behind it
                self.king_square = chess.E4
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.WHITE))
                
                # Rook that will be revealed
                self.chess_board.board.set_piece_at(chess.E7, chess.Piece(chess.ROOK, chess.BLACK))
                # Piece that moved away
                self.chess_board.board.set_piece_at(chess.D6, chess.Piece(chess.KNIGHT, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.highlight_square(self.king_square, 'danger')
                self.chess_board.highlight_square(chess.E7, 'highlight')
                
                self.scenario_answer = 'yes'
                
            elif scenario == 'double_check':
                # Two pieces checking simultaneously
                self.king_square = chess.E4
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.WHITE))
                
                # Two attackers
                self.chess_board.board.set_piece_at(chess.E7, chess.Piece(chess.ROOK, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.C2, chess.Piece(chess.BISHOP, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.highlight_square(self.king_square, 'danger')
                self.chess_board.highlight_square(chess.E7, 'highlight')
                self.chess_board.highlight_square(chess.C2, 'highlight')
                
                self.scenario_answer = 'yes'
            
            else:  # pin_check
                # Check through a pinned piece
                self.king_square = chess.E4
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.WHITE))
                
                # Attacking queen
                self.chess_board.board.set_piece_at(chess.E7, chess.Piece(chess.QUEEN, chess.BLACK))
                # Own piece that can't move (pinned)
                self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.ROOK, chess.WHITE))
                
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.highlight_square(self.king_square, 'danger')
                self.chess_board.highlight_square(chess.E7, 'highlight')
                
                self.scenario_answer = 'yes'
                
        except Exception as e:
            logger.error(f"Error generating complex check: {e}")
    
    def generate_check_escape(self):
        """Generate check escape - ENHANCED WITH VISUAL HINTS"""
        try:
            self.chess_board.board.clear()
            
            self.king_square = chess.E4
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.WHITE))
            
            attacker_square = chess.E7
            self.chess_board.board.set_piece_at(attacker_square, chess.Piece(chess.ROOK, chess.BLACK))
            
            self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.BLACK))
            
            # Calculate all escape options for visual hints
            # King escape squares
            king_escapes = [chess.D4, chess.D3, chess.D5, chess.F4, chess.F3, chess.F5]
            for square in king_escapes:
                if not self.chess_board.board.piece_at(square):
                    self.target_squares.append(square)
                    self.legal_escape_squares.append(square)
            
            # Blocking squares (between attacker and king)
            self.blocking_squares = [chess.E5, chess.E6]  # Squares that can block
            
            # Capture option (if pieces can capture the attacker)
            # Add a piece that can capture
            self.chess_board.board.set_piece_at(chess.C7, chess.Piece(chess.BISHOP, chess.WHITE))
            self.capture_squares = [chess.E7]  # Can capture the rook
            self.target_squares.extend(self.blocking_squares)
            self.target_squares.extend(self.capture_squares)
            
            self.chess_board.highlight_square(self.king_square, 'danger')
            self.chess_board.highlight_square(attacker_square, 'highlight')
            
        except Exception as e:
            logger.error(f"Error generating check escape: {e}")
    
    def generate_advanced_escape(self):
        """NEW: Generate advanced escape scenarios"""
        try:
            self.chess_board.board.clear()
            
            # Double check scenario - only king moves work
            self.king_square = chess.E4
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.WHITE))
            
            # Two attackers - double check
            self.chess_board.board.set_piece_at(chess.E7, chess.Piece(chess.ROOK, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.B1, chess.Piece(chess.BISHOP, chess.BLACK))
            
            self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.BLACK))
            
            # Only king moves work in double check
            self.legal_escape_squares = [chess.D3, chess.F3, chess.F5]  # Safe king moves
            self.target_squares = self.legal_escape_squares[:]
            
            self.chess_board.highlight_square(self.king_square, 'danger')
            self.chess_board.highlight_square(chess.E7, 'highlight')
            self.chess_board.highlight_square(chess.B1, 'highlight')
            
        except Exception as e:
            logger.error(f"Error generating advanced escape: {e}")
    
    def generate_checkmate_recognition(self):
        """Generate checkmate recognition - YOUR ORIGINAL"""
        try:
            self.chess_board.board.clear()
            
            is_checkmate = random.choice([True, False])
            
            if is_checkmate:
                self.king_square = chess.E8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.F7, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.G7, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, chess.BLACK))
                
                attacker_square = chess.E1
                self.chess_board.board.set_piece_at(attacker_square, chess.Piece(chess.ROOK, chess.WHITE))
                
                self.chess_board.board.set_piece_at(chess.E2, chess.Piece(chess.KING, chess.WHITE))
                
                self.chess_board.highlight_square(self.king_square, 'danger')
                self.chess_board.highlight_square(attacker_square, 'highlight')
                
                self.scenario_answer = 'yes'
            else:
                self.king_square = chess.E8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.G7, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, chess.BLACK))
                
                attacker_square = chess.E1
                self.chess_board.board.set_piece_at(attacker_square, chess.Piece(chess.ROOK, chess.WHITE))
                
                self.chess_board.board.set_piece_at(chess.E2, chess.Piece(chess.KING, chess.WHITE))
                
                self.chess_board.highlight_square(chess.F8, 'target')  # Escape square
                
                self.chess_board.highlight_square(self.king_square, 'danger')
                self.chess_board.highlight_square(attacker_square, 'highlight')
                
                self.scenario_answer = 'no'
                
        except Exception as e:
            logger.error(f"Error generating checkmate recognition: {e}")
    
    def generate_famous_checkmates(self):
        """NEW: Generate famous checkmate patterns"""
        try:
            self.chess_board.board.clear()
            
            pattern = random.choice(['smothered_mate', 'arabian_mate', 'legal_mate'])
            
            if pattern == 'smothered_mate':
                # Knight delivers mate to king surrounded by own pieces
                self.king_square = chess.E8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                # Surrounding pieces
                self.chess_board.board.set_piece_at(chess.D8, chess.Piece(chess.ROOK, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.F8, chess.Piece(chess.BISHOP, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.E7, chess.Piece(chess.PAWN, chess.BLACK))
                
                # Knight delivering mate
                self.chess_board.board.set_piece_at(chess.F6, chess.Piece(chess.KNIGHT, chess.WHITE))
                
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
                
                self.chess_board.highlight_square(self.king_square, 'danger')
                self.chess_board.highlight_square(chess.F6, 'highlight')
                
                self.scenario_answer = 'yes'
                
            elif pattern == 'arabian_mate':
                # Rook and knight mate in corner
                self.king_square = chess.H8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                # Mating pieces
                self.chess_board.board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.F7, chess.Piece(chess.KNIGHT, chess.WHITE))
                
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
                
                self.chess_board.highlight_square(self.king_square, 'danger')
                self.chess_board.highlight_square(chess.H1, 'highlight')
                self.chess_board.highlight_square(chess.F7, 'highlight')
                
                self.scenario_answer = 'yes'
                
            else:  # legal_mate - not actually mate, escape available
                self.king_square = chess.E8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                # Looks like mate but king has escape
                self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.ROOK, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.F7, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.G7, chess.Piece(chess.PAWN, chess.BLACK))
                
                # King can escape to F8
                self.chess_board.highlight_square(chess.F8, 'target')
                
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.WHITE))
                
                self.chess_board.highlight_square(self.king_square, 'danger')
                self.chess_board.highlight_square(chess.E1, 'highlight')
                
                self.scenario_answer = 'no'
                
        except Exception as e:
            logger.error(f"Error generating famous checkmates: {e}")
    
    def generate_checkmate_delivery(self):
        """Generate checkmate delivery - YOUR ORIGINAL"""
        try:
            self.chess_board.board.clear()
            
            self.king_square = chess.H8
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
            
            self.chess_board.board.set_piece_at(chess.G6, chess.Piece(chess.KING, chess.WHITE))
            queen_square = chess.F7
            self.chess_board.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.WHITE))
            
            mate_squares = [chess.H7, chess.G7, chess.G8]
            for square in mate_squares:
                self.target_squares.append(square)
            
            self.chess_board.highlight_square(self.king_square, 'danger')
            self.chess_board.highlight_square(queen_square, 'highlight')
            
        except Exception as e:
            logger.error(f"Error generating checkmate delivery: {e}")
    
    def generate_mate_in_two(self):
        """NEW: Generate mate in two scenarios"""
        try:
            self.chess_board.board.clear()
            
            # More complex mating scenarios requiring multiple moves
            self.king_square = chess.G8
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
            
            # Set up position where queen sacrifice leads to mate
            self.chess_board.board.set_piece_at(chess.G7, chess.Piece(chess.PAWN, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.F7, chess.Piece(chess.PAWN, chess.BLACK))
            
            # White pieces for the attack
            self.chess_board.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.B1, chess.Piece(chess.BISHOP, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.G1, chess.Piece(chess.KING, chess.WHITE))
            
            # Target is the forcing move
            self.target_squares = [chess.D8]  # Queen sacrifice forces mate
            
            self.chess_board.highlight_square(self.king_square, 'danger')
            self.chess_board.highlight_square(chess.D1, 'highlight')
            
        except Exception as e:
            logger.error(f"Error generating mate in two: {e}")
    
    def generate_stalemate_recognition(self):
        """Generate stalemate recognition - YOUR ORIGINAL"""
        try:
            self.chess_board.board.clear()
            
            is_stalemate = random.choice([True, False])
            
            if is_stalemate:
                self.king_square = chess.A8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.B6, chess.Piece(chess.KING, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.C7, chess.Piece(chess.QUEEN, chess.WHITE))
                
                self.chess_board.highlight_square(self.king_square, 'highlight')
                
                self.scenario_answer = 'yes'
            else:
                self.king_square = chess.A8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.B6, chess.Piece(chess.KING, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.C7, chess.Piece(chess.QUEEN, chess.WHITE))
                
                self.chess_board.highlight_square(chess.H6, 'target')
                self.chess_board.highlight_square(chess.H7, 'highlight')
                
                self.scenario_answer = 'no'
                
        except Exception as e:
            logger.error(f"Error generating stalemate recognition: {e}")
    
    def generate_stalemate_tricks(self):
        """NEW: Generate tricky stalemate positions"""
        try:
            self.chess_board.board.clear()
            
            trick = random.choice(['hidden_pawn_move', 'trapped_piece_escape', 'king_has_move'])
            
            if trick == 'hidden_pawn_move':
                # Looks like stalemate but pawn can move
                self.king_square = chess.A8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                # Hidden pawn that can move
                self.chess_board.board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.BLACK))  # Can move to A6
                
                self.chess_board.board.set_piece_at(chess.B6, chess.Piece(chess.KING, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.C7, chess.Piece(chess.QUEEN, chess.WHITE))
                
                self.chess_board.highlight_square(chess.A6, 'target')  # Pawn move
                
                self.scenario_answer = 'no'  # Not stalemate
                
            elif trick == 'trapped_piece_escape':
                # Piece looks trapped but has escape
                self.king_square = chess.H8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                # Bishop that looks trapped but can move
                self.chess_board.board.set_piece_at(chess.F8, chess.Piece(chess.BISHOP, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.F6, chess.Piece(chess.KING, chess.WHITE))
                
                self.chess_board.highlight_square(chess.E7, 'target')  # Bishop can move
                
                self.scenario_answer = 'no'  # Not stalemate
                
            else:  # True stalemate
                self.king_square = chess.A8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                
                self.chess_board.board.set_piece_at(chess.B6, chess.Piece(chess.KING, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.A7, chess.Piece(chess.QUEEN, chess.WHITE))
                
                self.scenario_answer = 'yes'  # Is stalemate
                
        except Exception as e:
            logger.error(f"Error generating stalemate tricks: {e}")
    
    def generate_endgame_patterns(self):
        """NEW: Generate advanced endgame patterns"""
        try:
            self.chess_board.board.clear()
            
            pattern = random.choice(['opposition', 'key_squares', 'fortress'])
            
            if pattern == 'opposition':
                # Kings in opposition
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.KING, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.E6, chess.Piece(chess.KING, chess.BLACK))  # Opposition
                
                # Add pawn
                self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.WHITE))
                
                self.chess_board.highlight_square(chess.E4, 'highlight')
                self.chess_board.highlight_square(chess.E6, 'danger')
                
                self.scenario_answer = 'yes'  # This demonstrates opposition
                
            elif pattern == 'key_squares':
                # Key squares for pawn promotion
                self.chess_board.board.set_piece_at(chess.A6, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.C4, chess.Piece(chess.KING, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.C8, chess.Piece(chess.KING, chess.BLACK))
                
                # Key squares marked
                key_squares = [chess.A7, chess.B7, chess.B8]
                for square in key_squares:
                    self.chess_board.highlight_square(square, 'target')
                
                self.scenario_answer = 'yes'
                
            else:  # fortress
                # Fortress drawing setup
                self.chess_board.board.set_piece_at(chess.A8, chess.Piece(chess.KING, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.B8, chess.Piece(chess.BISHOP, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.A7, chess.Piece(chess.PAWN, chess.BLACK))
                
                # White trying to break through
                self.chess_board.board.set_piece_at(chess.D6, chess.Piece(chess.KING, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.C6, chess.Piece(chess.PAWN, chess.WHITE))
                
                self.scenario_answer = 'yes'  # This is a fortress draw
                
        except Exception as e:
            logger.error(f"Error generating endgame patterns: {e}")
    
    # Visual hints system - NEW FEATURE YOU REQUESTED
    def toggle_visual_hints(self):
        """Toggle visual move hints on the board"""
        self.show_visual_hints = not self.show_visual_hints
        
        if self.show_visual_hints:
            # Show move highlights based on exercise type
            if 'escape' in self.exercise_type:
                # Highlight escape moves
                for square in self.legal_escape_squares:
                    self.chess_board.highlight_square(square, 'legal_move')
                for square in self.blocking_squares:
                    self.chess_board.highlight_square(square, 'legal_move')
                for square in self.capture_squares:
                    self.chess_board.highlight_square(square, 'legal_move')
            elif 'delivery' in self.exercise_type or 'mate' in self.exercise_type:
                # Highlight mating moves
                for square in self.target_squares:
                    self.chess_board.highlight_square(square, 'legal_move')
        else:
            # Clear visual hints
            self.chess_board.legal_move_squares.clear()
    
    def toggle_hints(self):
        """Toggle textual hints - YOUR ORIGINAL"""
        self.show_hints = not self.show_hints
        if self.show_hints and self.exercise_type in self.learning_content:
            hints = self.learning_content[self.exercise_type]['hints']
            if hints and self.hint_level < len(hints):
                self.current_hint = hints[self.hint_level]
        else:
            self.current_hint = ""
    
    def next_hint(self):
        """Show next hint - YOUR ORIGINAL"""
        if self.exercise_type in self.learning_content:
            hints = self.learning_content[self.exercise_type]['hints']
            if self.hint_level < len(hints) - 1:
                self.hint_level += 1
                self.current_hint = hints[self.hint_level]
                self.show_hints = True
    
    def handle_square_click(self, square: int):
        """Handle square clicks - YOUR ORIGINAL"""
        try:
            if self.show_feedback:
                return
            
            self.selected_square = square
            self.total_attempts += 1
            
            if self.exercise_type in ['check_escape', 'advanced_escape', 'checkmate_delivery', 'mate_in_two']:
                if square in self.target_squares:
                    self.on_correct_move()
                else:
                    self.on_incorrect_move()
            else:
                self.chess_board.select_square(square)
                
        except Exception as e:
            logger.error(f"Error handling square click: {e}")
    
    def handle_answer(self, answer: str):
        """Handle answer button clicks - YOUR ORIGINAL"""
        try:
            if self.show_feedback:
                return
                
            self.total_attempts += 1
            
            if answer == 'unclear':
                self.show_feedback = True
                self.feedback_message = "🤔 Take your time to analyze. Use hints if you need guidance!"
            elif answer == self.scenario_answer:
                self.on_correct_move()
            else:
                self.on_incorrect_move()
                
        except Exception as e:
            logger.error(f"Error handling answer: {e}")
    
    def on_correct_move(self):
        """Handle correct answer - YOUR ORIGINAL WITH BETTER FEEDBACK"""
        try:
            self.correct_moves += 1
            self.show_feedback = True
            self.feedback_timer = 0
            
            # Enhanced feedback for different exercise types
            feedback_by_type = {
                'check_recognition': ["🎉 Excellent! You correctly spotted the check!", "👏 Perfect check detection!", "⭐ Great pattern recognition!"],
                'complex_check': ["🏆 Outstanding! You identified the complex check pattern!", "⚡ Brilliant analysis of the position!", "🎯 Expert-level recognition!"],
                'check_escape': ["✅ Perfect escape! The king is now safe!", "🛡️ Excellent defensive move!", "👍 Great problem solving!"],
                'advanced_escape': ["🌟 Masterful! You handled the complex escape!", "🎖️ Expert-level defensive play!", "💫 Brilliant calculation!"],
                'checkmate_recognition': ["💀 Correct! You spotted the checkmate!", "🎯 Perfect mate recognition!", "👑 Excellent endgame vision!"],
                'famous_checkmates': ["📚 Outstanding! You know your chess history!", "🏛️ Classic pattern mastery!", "🎓 Excellent theoretical knowledge!"],
                'checkmate_delivery': ["⚔️ Checkmate delivered! Game over!", "👑 Royal execution!", "🗡️ Perfect finishing move!"],
                'mate_in_two': ["🧠 Brilliant! Complex mate calculation!", "💎 Diamond-level tactical vision!", "🔥 Spectacular combination!"],
                'stalemate_recognition': ["🤝 Correct! You identified the stalemate!", "⚖️ Perfect draw recognition!", "📐 Excellent position evaluation!"],
                'stalemate_tricks': ["🕵️ Great detective work! You found the hidden move!", "🔍 Sharp eye for details!", "🎭 You weren't fooled by the trick!"],
                'endgame_patterns': ["🎓 Excellent! You understand advanced endgames!", "📖 Masterful theoretical knowledge!", "🏅 Professional-level understanding!"]
            }
            
            if self.exercise_type in feedback_by_type:
                self.feedback_message = random.choice(feedback_by_type[self.exercise_type])
            else:
                self.feedback_message = "🎉 Excellent! You got it right!"
            
            # Update progress
            if self.exercise_type:
                self.exercises_completed[self.exercise_type] += 1
            
            # Play success sound
            try:
                self.engine.audio_manager.play_sound('success.wav')
            except Exception as e:
                logger.warning(f"Failed to play success sound: {e}")
                
        except Exception as e:
            logger.error(f"Error in on_correct_move: {e}")
    
    def on_incorrect_move(self):
        """Handle incorrect answer - YOUR ORIGINAL WITH BETTER FEEDBACK"""
        try:
            self.show_feedback = True
            self.feedback_timer = 0
            
            # Enhanced feedback for different exercise types
            error_feedback = {
                'check_recognition': "❌ Not quite. Look carefully for pieces attacking the king.",
                'complex_check': "❌ This is a tricky position. Consider discovered or double checks.",
                'check_escape': "❌ That doesn't escape the check. Try moving the king to safety.",
                'advanced_escape': "❌ In double check, only king moves work. Find a safe square.",
                'checkmate_recognition': "❌ Check if the king has any escape squares or if pieces can help.",
                'famous_checkmates': "❌ Study this classic pattern. It's important for chess mastery.",
                'checkmate_delivery': "❌ Not quite mate yet. Make sure the king has no escape.",
                'mate_in_two': "❌ Look for forcing moves that set up inevitable mate.",
                'stalemate_recognition': "❌ Check if ANY piece (not just king) can make a legal move.",
                'stalemate_tricks': "❌ Look more carefully! There might be a hidden legal move.",
                'endgame_patterns': "❌ This requires advanced knowledge. Study endgame theory."
            }
            
            self.feedback_message = error_feedback.get(self.exercise_type, "❌ Not quite right. Try analyzing more carefully.")
            
            # Add hint suggestion after multiple attempts
            if self.total_attempts >= 2:
                self.feedback_message += " 💡 Try using the hint buttons for guidance!"
            
            # Play error sound
            try:
                self.engine.audio_manager.play_sound('error.wav')
            except Exception as e:
                logger.warning(f"Failed to play error sound: {e}")
                
        except Exception as e:
            logger.error(f"Error in on_incorrect_move: {e}")
    
    def reset_exercise(self):
        """Reset current exercise - YOUR ORIGINAL"""
        try:
            self.show_feedback = False
            self.show_hints = False
            self.show_visual_hints = False
            self.hint_level = 0
            self.current_hint = ""
            self.total_attempts = 0
            self.selected_square = None
            
            # Regenerate same exercise type
            if self.exercise_type == 'check_recognition':
                self.generate_check_recognition()
            elif self.exercise_type == 'complex_check':
                self.generate_complex_check()
            elif self.exercise_type == 'check_escape':
                self.generate_check_escape()
            elif self.exercise_type == 'advanced_escape':
                self.generate_advanced_escape()
            elif self.exercise_type == 'checkmate_recognition':
                self.generate_checkmate_recognition()
            elif self.exercise_type == 'famous_checkmates':
                self.generate_famous_checkmates()
            elif self.exercise_type == 'checkmate_delivery':
                self.generate_checkmate_delivery()
            elif self.exercise_type == 'mate_in_two':
                self.generate_mate_in_two()
            elif self.exercise_type == 'stalemate_recognition':
                self.generate_stalemate_recognition()
            elif self.exercise_type == 'stalemate_tricks':
                self.generate_stalemate_tricks()
            elif self.exercise_type == 'endgame_patterns':
                self.generate_endgame_patterns()
                
        except Exception as e:
            logger.error(f"Error resetting exercise: {e}")
    
    def skip_exercise(self):
        """Skip current exercise - YOUR ORIGINAL"""
        try:
            if self.exercise_type:
                self.exercises_completed[self.exercise_type] += 1
            self.advance_exercise()
        except Exception as e:
            logger.error(f"Error skipping exercise: {e}")
    
    def advance_exercise(self):
        """Move to next exercise - YOUR ORIGINAL"""
        try:
            self.current_exercise += 1
            
            if (self.exercise_type and 
                self.exercises_completed[self.exercise_type] >= self.exercises_per_type):
                self.current_type_index += 1
            
            if self.current_type_index >= len(self.exercise_types):
                self.complete_module()
            else:
                self.generate_exercise()
                
        except Exception as e:
            logger.error(f"Error moving to next exercise: {e}")
    
    def complete_module(self):
        """Complete the module - YOUR ORIGINAL"""
        try:
            self.module_completed = True
            self.completion_timer = 0
            
            if self.total_attempts > 0:
                accuracy = (self.correct_moves / self.total_attempts) * 100
            else:
                accuracy = 0
            
            try:
                self.engine.audio_manager.play_sound('victory.wav')
            except Exception as e:
                logger.warning(f"Failed to play completion sound: {e}")
                
        except Exception as e:
            logger.error(f"Error completing module: {e}")
    
    def on_back_clicked(self):
        """Handle back button click - YOUR ORIGINAL"""
        try:
            self.engine.change_state(ProjectGameState.MAIN_MENU)
        except Exception as e:
            logger.error(f"Error returning to main menu: {e}")
    
    def handle_event(self, event):
        """Handle events - YOUR ORIGINAL WITH VISUAL HINTS"""
        try:
            # Update all buttons
            self.back_button.handle_event(event)
            
            if not self.module_completed:
                self.hint_button.handle_event(event)
                self.visual_hint_button.handle_event(event)  # NEW
                self.reset_button.handle_event(event)
                
                if self.show_hints:
                    self.next_hint_button.handle_event(event)
                
                if self.total_attempts > 0:
                    self.skip_button.handle_event(event)
                
                if not self.show_feedback:
                    if self.exercise_type in ['check_recognition', 'complex_check', 'checkmate_recognition', 
                                             'famous_checkmates', 'stalemate_recognition', 'stalemate_tricks', 'endgame_patterns']:
                        self.yes_button.handle_event(event)
                        self.no_button.handle_event(event)
                        self.maybe_button.handle_event(event)
                else:
                    self.next_button.handle_event(event)
            
            # Handle board clicks for move-based exercises
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and 
                not self.show_feedback and not self.module_completed):
                
                if self.exercise_type in ['check_escape', 'advanced_escape', 'checkmate_delivery', 'mate_in_two']:
                    square = self.chess_board.get_square_from_pos(event.pos)
                    if square is not None:
                        self.handle_square_click(square)
            
            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h and not self.module_completed:
                    self.toggle_hints()
                elif event.key == pygame.K_v and not self.module_completed:  # NEW: V for visual hints
                    self.toggle_visual_hints()
                elif event.key == pygame.K_r and not self.show_feedback and not self.module_completed:
                    self.reset_exercise()
                elif event.key == pygame.K_SPACE and self.show_feedback:
                    self.advance_exercise()
                elif event.key == pygame.K_y and not self.show_feedback:
                    self.handle_answer('yes')
                elif event.key == pygame.K_n and not self.show_feedback:
                    self.handle_answer('no')
                elif event.key == pygame.K_u and not self.show_feedback:
                    self.handle_answer('unclear')
                    
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def update(self, dt: float):
        """Update game state - YOUR ORIGINAL"""
        try:
            super().update(dt)
            
            mouse_pos = pygame.mouse.get_pos()
            
            # Update all buttons
            self.back_button.update(dt, mouse_pos)
            
            if not self.module_completed:
                self.hint_button.update(dt, mouse_pos)
                self.visual_hint_button.update(dt, mouse_pos)  # NEW
                self.reset_button.update(dt, mouse_pos)
                
                if self.show_hints:
                    self.next_hint_button.update(dt, mouse_pos)
                
                if self.total_attempts > 0:
                    self.skip_button.update(dt, mouse_pos)
                
                if not self.show_feedback:
                    if self.exercise_type in ['check_recognition', 'complex_check', 'checkmate_recognition',
                                             'famous_checkmates', 'stalemate_recognition', 'stalemate_tricks', 'endgame_patterns']:
                        self.yes_button.update(dt, mouse_pos)
                        self.no_button.update(dt, mouse_pos)
                        self.maybe_button.update(dt, mouse_pos)
                else:
                    self.next_button.update(dt, mouse_pos)
            
            # Update feedback timer
            if self.show_feedback:
                self.feedback_timer += dt
            
            # Auto-advance after module completion
            if self.module_completed:
                self.completion_timer += dt
                if self.completion_timer > 5.0:
                    self.engine.change_state(ProjectGameState.MAIN_MENU)
                    
        except Exception as e:
            logger.error(f"Error in update: {e}")
    
    def render(self, screen):
        """Render the game state - YOUR ORIGINAL STYLE"""
        try:
            # Clear screen
            bg_color = getattr(self.config, 'COLORS', {}).get('background', (248, 249, 250))
            screen.fill(bg_color)
            
            if self.module_completed:
                self.render_completion_screen(screen)
                return
            
            # Title
            title_text = "Enhanced Chess Endings: Check, Checkmate & Stalemate"
            title_surface = self.title_font.render(title_text, True, (44, 62, 80))
            title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 30))
            screen.blit(title_surface, title_rect)
            
            # Exercise info
            if self.exercise_type and self.exercise_type in self.learning_content:
                content = self.learning_content[self.exercise_type]
                
                # Exercise title and progress
                progress_text = f"{content['title']} - Exercise {self.exercises_completed[self.exercise_type] + 1}/{self.exercises_per_type}"
                progress_surface = self.subtitle_font.render(progress_text, True, (52, 152, 219))
                progress_rect = progress_surface.get_rect(center=(screen.get_width() // 2, 70))
                screen.blit(progress_surface, progress_rect)
                
                # Basic instruction
                if self.exercise_type in ['check_recognition', 'complex_check', 'checkmate_recognition',
                                         'famous_checkmates', 'stalemate_recognition', 'stalemate_tricks', 'endgame_patterns']:
                    instruction = "Analyze the position and click your answer"
                elif self.exercise_type in ['check_escape', 'advanced_escape', 'checkmate_delivery', 'mate_in_two']:
                    instruction = "Click on the board to make your move"
                else:
                    instruction = "Follow the exercise instructions"
                
                instruction_surface = self.instruction_font.render(instruction, True, (44, 62, 80))
                instruction_rect = instruction_surface.get_rect(center=(screen.get_width() // 2, 100))
                screen.blit(instruction_surface, instruction_rect)
            
            # Draw chess board
            self.chess_board.draw()
            
            # Render hint system - ONLY when user requests
            if self.show_hints and self.current_hint:
                self.render_hint_panel(screen)
            
            # Render feedback
            if self.show_feedback and self.feedback_message:
                feedback_color = (46, 204, 113) if "🎉" in self.feedback_message or "👏" in self.feedback_message else (231, 76, 60)
                feedback_surface = self.instruction_font.render(self.feedback_message, True, feedback_color)
                feedback_rect = feedback_surface.get_rect(center=(screen.get_width() // 2, 620))
                screen.blit(feedback_surface, feedback_rect)
            
            # Render buttons - YOUR ORIGINAL STYLE
            self.back_button.render(screen)
            self.hint_button.render(screen)
            self.visual_hint_button.render(screen)  # NEW
            self.reset_button.render(screen)
            
            if self.show_hints:
                self.next_hint_button.render(screen)
            
            if self.total_attempts > 0:
                self.skip_button.render(screen)
            
            # Render appropriate answer buttons
            if not self.show_feedback:
                if self.exercise_type in ['check_recognition', 'complex_check', 'checkmate_recognition',
                                         'famous_checkmates', 'stalemate_recognition', 'stalemate_tricks', 'endgame_patterns']:
                    self.yes_button.render(screen)
                    self.no_button.render(screen)
                    self.maybe_button.render(screen)
            else:
                self.next_button.render(screen)
            
            # Instructions for user interaction
            if not self.show_feedback:
                if self.exercise_type in ['check_escape', 'advanced_escape', 'checkmate_delivery', 'mate_in_two']:
                    help_text = "Click on squares to make moves. Use 'Visual Hints' (V key) to see legal moves."
                elif self.exercise_type in ['check_recognition', 'complex_check', 'checkmate_recognition',
                                           'famous_checkmates', 'stalemate_recognition', 'stalemate_tricks', 'endgame_patterns']:
                    help_text = "Analyze and answer: Y = Yes, N = No, U = Unclear. Use 'H' for hints, 'V' for visual hints."
                else:
                    help_text = "Use H for hints, V for visual move hints"
                
                help_surface = self.info_font.render(help_text, True, (100, 100, 100))
                help_rect = help_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() - 30))
                screen.blit(help_surface, help_rect)
                
        except Exception as e:
            logger.error(f"Error in render: {e}")
            screen.fill((50, 50, 50))
            error_font = pygame.font.SysFont('Arial', 24)
            error_text = error_font.render("Error in rendering - Press Back", True, (255, 255, 255))
            screen.blit(error_text, (50, 50))
    
    def render_hint_panel(self, screen):
        """Render hint panel - YOUR ORIGINAL"""
        try:
            panel_width = 500
            panel_height = 80
            panel_x = (screen.get_width() - panel_width) // 2
            panel_y = 450
            
            # Background
            hint_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            hint_bg.fill((40, 60, 80, 200))
            screen.blit(hint_bg, (panel_x, panel_y))
            
            # Border
            pygame.draw.rect(screen, (52, 152, 219), (panel_x, panel_y, panel_width, panel_height), 2, border_radius=8)
            
            # Title
            hint_title = f"💡 Hint {self.hint_level + 1}"
            title_surface = self.info_font.render(hint_title, True, (100, 200, 255))
            screen.blit(title_surface, (panel_x + 15, panel_y + 10))
            
            # Hint text
            hint_surface = self.hint_font.render(self.current_hint, True, (255, 255, 255))
            screen.blit(hint_surface, (panel_x + 15, panel_y + 35))
            
        except Exception as e:
            logger.warning(f"Error rendering hint panel: {e}")
    
    def render_completion_screen(self, screen):
        """Render module completion screen - YOUR ORIGINAL"""
        try:
            screen.fill((40, 50, 60))
            
            if self.total_attempts > 0:
                accuracy = (self.correct_moves / self.total_attempts) * 100
            else:
                accuracy = 100
            
            # Title based on performance
            if accuracy >= 90:
                title = "🏆 CHESS MASTER! 🏆"
                subtitle = "You've mastered advanced chess endings!"
                color = (255, 215, 0)
            elif accuracy >= 75:
                title = "⭐ EXCELLENT WORK! ⭐"
                subtitle = "Great understanding of chess endings!"
                color = (255, 255, 255)
            elif accuracy >= 60:
                title = "👍 WELL DONE! 👍"
                subtitle = "Good progress in chess endings!"
                color = (100, 149, 237)
            else:
                title = "📚 KEEP LEARNING! 📚"
                subtitle = "Practice makes perfect!"
                color = (100, 149, 237)
            
            # Render title
            title_surface = pygame.font.Font(None, 64).render(title, True, color)
            title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 150))
            screen.blit(title_surface, title_rect)
            
            # Render subtitle
            subtitle_surface = self.title_font.render(subtitle, True, (255, 255, 255))
            subtitle_rect = subtitle_surface.get_rect(center=(screen.get_width() // 2, 200))
            screen.blit(subtitle_surface, subtitle_rect)
            
            # Stats
            stats = [
                f"Final Accuracy: {accuracy:.1f}%",
                f"Correct Answers: {self.correct_moves}/{self.total_attempts}",
                f"Exercise Types Completed: {len([t for t in self.exercise_types if self.exercises_completed[t] > 0])}/{len(self.exercise_types)}"
            ]
            
            for i, stat in enumerate(stats):
                stat_surface = self.instruction_font.render(stat, True, (200, 200, 200))
                stat_rect = stat_surface.get_rect(center=(screen.get_width() // 2, 280 + i * 30))
                screen.blit(stat_surface, stat_rect)
            
            # Key concepts learned
            concepts_title = self.subtitle_font.render("Advanced Concepts Mastered:", True, (255, 215, 0))
            concepts_rect = concepts_title.get_rect(center=(screen.get_width() // 2, 400))
            screen.blit(concepts_title, concepts_rect)
            
            concepts = [
                "✅ Advanced check patterns and recognition",
                "✅ Complex escape techniques and tactics", 
                "✅ Famous checkmate patterns and delivery",
                "✅ Tricky stalemate positions and avoidance",
                "✅ Professional endgame pattern knowledge"
            ]
            
            for i, concept in enumerate(concepts):
                concept_surface = self.info_font.render(concept, True, (150, 255, 150))
                concept_rect = concept_surface.get_rect(center=(screen.get_width() // 2, 440 + i * 25))
                screen.blit(concept_surface, concept_rect)
            
            # Return message
            return_text = "Returning to main menu..."
            return_surface = self.info_font.render(return_text, True, (150, 150, 150))
            return_rect = return_surface.get_rect(center=(screen.get_width() // 2, 600))
            screen.blit(return_surface, return_rect)
            
        except Exception as e:
            logger.error(f"Error rendering completion screen: {e}")