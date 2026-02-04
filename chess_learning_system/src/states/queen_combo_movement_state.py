import pygame
import chess
import random
from src.core.state_machine import BaseState, GameState
from src.chess.chess_board import ChessBoard
from src.ui.components import Button, ProgressBar, AnimatedText
from src.utils.timer import Timer
import math
import logging

# Set up logging
logger = logging.getLogger(__name__)

class QueenMovementState(BaseState):
    """Module for teaching queen movement - the ultimate combo piece combining rook and bishop power"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Module configuration based on queen's complex nature
            self.exercises_per_type = 4  # Multiple exercises for each concept
            self.movement_types = ['basic_combo', 'straight_lines', 'diagonal_paths', 'tactical_patterns', 'positioning_strategy']
            
            # Progress tracking
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            self.exercises_completed = {move_type: 0 for move_type in self.movement_types}
            
            # Current exercise data
            self.current_queen_square = None
            self.target_squares = []
            self.invalid_squares = []
            self.selected_square = None
            self.show_feedback = False
            self.feedback_timer = 0
            self.feedback_message = ""
            self.exercise_type = None
            self.show_hint = False
            
            # Queen-specific learning aids
            self.show_rook_lines = False
            self.show_bishop_lines = False
            self.show_combo_power = False
            self.demonstration_mode = False
            self.highlight_danger_squares = False
            
            # Chess board
            try:
                self.chess_board = ChessBoard(
                    self.engine.screen,
                    self.engine.resource_manager,
                    board_size=480
                )
                self.chess_board.board_offset_x = (self.config.SCREEN_WIDTH - 480) // 2
                self.chess_board.board_offset_y = 180
            except Exception as e:
                logger.error(f"Failed to initialize chess board: {e}")
                raise
            
            # UI elements
            self.create_ui_elements()
            
            # Instructions based on queen mastery research
            self.instructions = {
                'basic_combo': "Queens combine rook + bishop power! Move in any direction. Click a valid square.",
                'straight_lines': "Queens move like rooks: horizontally and vertically. Click a straight line move.",
                'diagonal_paths': "Queens move like bishops: diagonally any distance. Click a diagonal move.",
                'tactical_patterns': "Queens excel at forks, pins, and skewers! Find the tactical shot.",
                'positioning_strategy': "Position queens for maximum power while staying safe. Find the best square."
            }
            
            # Learning tips for each type
            self.learning_tips = {
                'basic_combo': "Queen = Rook + Bishop combined! Can move 8 directions from center",
                'straight_lines': "Horizontal/vertical like rook - great for back rank attacks",
                'diagonal_paths': "Diagonal movement like bishop - powerful for pins and skewers", 
                'tactical_patterns': "Queens are tactical monsters - look for multi-piece attacks",
                'positioning_strategy': "Keep queen safe but active - avoid early development"
            }
            
            # Fonts
            try:
                self.title_font = pygame.font.Font(None, 48)
                self.instruction_font = pygame.font.Font(None, 32)
                self.info_font = pygame.font.Font(None, 24)
                self.tip_font = pygame.font.Font(None, 20)
            except Exception as e:
                logger.error(f"Failed to load fonts: {e}")
                self.title_font = pygame.font.SysFont('Arial', 48)
                self.instruction_font = pygame.font.SysFont('Arial', 32)
                self.info_font = pygame.font.SysFont('Arial', 24)
                self.tip_font = pygame.font.SysFont('Arial', 20)
            
            # Animation elements
            self.animated_texts = []
            self.celebration_particles = []
            self.power_animation = 0
            self.combo_pulse = 0
            
            # Module completion
            self.module_completed = False
            self.completion_timer = 0
            
            # Session timer
            self.session_timer = Timer()
            
            # Queen movement patterns - combines rook and bishop
            self.rook_directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Horizontal/Vertical
            self.bishop_directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]  # Diagonal
            self.queen_directions = self.rook_directions + self.bishop_directions  # All 8 directions
            
        except Exception as e:
            logger.error(f"Failed to initialize QueenMovementState: {e}")
            raise
    
    def create_ui_elements(self):
        """Create UI elements"""
        try:
            total_exercises = len(self.movement_types) * self.exercises_per_type
            self.progress_bar = ProgressBar(
                pos=(self.config.SCREEN_WIDTH // 2 - 200, 30),
                size=(400, 25),
                max_value=total_exercises,
                config=self.config
            )
            
            self.back_button = Button(
                text="Back",
                pos=(60, 50),
                size=(100, 40),
                callback=self.on_back_clicked,
                config=self.config
            )
            
            self.hint_button = Button(
                text="Show Hint",
                pos=(self.config.SCREEN_WIDTH - 180, 50),
                size=(150, 40),
                callback=self.toggle_hint,
                config=self.config
            )
            
            self.rook_lines_button = Button(
                text="Rook Lines",
                pos=(self.config.SCREEN_WIDTH - 180, 100),
                size=(150, 40),
                callback=self.toggle_rook_lines,
                config=self.config
            )
            
            self.bishop_lines_button = Button(
                text="Bishop Lines",
                pos=(self.config.SCREEN_WIDTH - 180, 150),
                size=(150, 40),
                callback=self.toggle_bishop_lines,
                config=self.config
            )
            
            self.combo_button = Button(
                text="Show Combo",
                pos=(self.config.SCREEN_WIDTH - 180, 200),
                size=(150, 40),
                callback=self.toggle_combo_power,
                config=self.config
            )
            
            self.demo_button = Button(
                text="Demo Move",
                pos=(self.config.SCREEN_WIDTH - 180, 250),
                size=(150, 40),
                callback=self.start_demonstration,
                config=self.config
            )
            
            self.skip_button = Button(
                text="Skip",
                pos=(self.config.SCREEN_WIDTH - 180, 300),
                size=(150, 40),
                callback=self.skip_exercise,
                config=self.config
            )
            
            self.next_button = Button(
                text="Next Exercise",
                pos=(self.config.SCREEN_WIDTH // 2 - 100, 650),
                size=(200, 50),
                callback=self.next_exercise,
                config=self.config
            )
        except Exception as e:
            logger.error(f"Failed to create UI elements: {e}")
            raise
    
    def enter(self):
        """Enter the state"""
        try:
            super().enter()
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            for move_type in self.movement_types:
                self.exercises_completed[move_type] = 0
            self.progress_bar.set_value(0)
            self.module_completed = False
            self.session_timer.reset()
            self.generate_exercise()
            
            try:
                self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
            except Exception as e:
                logger.warning(f"Failed to play learning music: {e}")
                
        except Exception as e:
            logger.error(f"Failed to enter QueenMovementState: {e}")
            self.engine.change_state(GameState.MAIN_MENU)
    
    def get_queen_moves(self, square, board=None, directions=None):
        """Get all valid queen moves from a square in specified directions"""
        try:
            if square is None or not (0 <= square <= 63):
                return []
            
            if board is None:
                board = self.chess_board.board
            
            if directions is None:
                directions = self.queen_directions
            
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            moves = []
            
            # Check all specified directions
            for df, dr in directions:
                for distance in range(1, 8):
                    new_file = file + df * distance
                    new_rank = rank + dr * distance
                    
                    # Check if still on board
                    if not (0 <= new_file <= 7 and 0 <= new_rank <= 7):
                        break
                    
                    new_square = chess.square(new_file, new_rank)
                    piece = board.piece_at(new_square)
                    
                    if piece is None:
                        # Empty square - can move here
                        moves.append(new_square)
                    else:
                        # Occupied square - can capture if enemy, then stop
                        queen_piece = board.piece_at(square)
                        if queen_piece and piece.color != queen_piece.color:
                            moves.append(new_square)
                        break
            
            return moves
        except Exception as e:
            logger.error(f"Error calculating queen moves: {e}")
            return []
    
    def get_line_between(self, from_square, to_square):
        """Get all squares on the line between two squares"""
        try:
            if from_square is None or to_square is None:
                return []
            
            from_file = chess.square_file(from_square)
            from_rank = chess.square_rank(from_square)
            to_file = chess.square_file(to_square)
            to_rank = chess.square_rank(to_square)
            
            # Check if squares are on same line (horizontal, vertical, or diagonal)
            df = to_file - from_file
            dr = to_rank - from_rank
            
            # Must be on same rank, file, or diagonal
            if df != 0 and dr != 0 and abs(df) != abs(dr):
                return []
            
            path = []
            if df == 0 and dr == 0:
                return []  # Same square
            
            # Normalize direction
            step_f = 0 if df == 0 else (1 if df > 0 else -1)
            step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
            
            current_file = from_file + step_f
            current_rank = from_rank + step_r
            
            while current_file != to_file or current_rank != to_rank:
                path.append(chess.square(current_file, current_rank))
                current_file += step_f
                current_rank += step_r
            
            return path
        except Exception as e:
            logger.error(f"Error calculating line between squares: {e}")
            return []
    
    def generate_exercise(self):
        """Generate a new exercise"""
        try:
            self.show_feedback = False
            self.selected_square = None
            self.show_hint = False
            self.show_rook_lines = False
            self.show_bishop_lines = False
            self.show_combo_power = False
            self.highlight_danger_squares = False
            self.demonstration_mode = False
            self.target_squares = []
            self.invalid_squares = []
            self.chess_board.clear_highlights()
            self.chess_board.select_square(None)
            
            if self.current_type_index < len(self.movement_types):
                self.exercise_type = self.movement_types[self.current_type_index]
            else:
                self.complete_module()
                return
                
            try:
                if self.exercise_type == 'basic_combo':
                    self._generate_basic_combo()
                elif self.exercise_type == 'straight_lines':
                    self._generate_straight_lines()
                elif self.exercise_type == 'diagonal_paths':
                    self._generate_diagonal_paths()
                elif self.exercise_type == 'tactical_patterns':
                    self._generate_tactical_patterns()
                elif self.exercise_type == 'positioning_strategy':
                    self._generate_positioning_strategy()
            except Exception as e:
                logger.error(f"Failed to generate {self.exercise_type} exercise: {e}")
                self.next_exercise()
                
        except Exception as e:
            logger.error(f"Failed to generate exercise: {e}")
            self.feedback_message = "Error generating exercise. Skipping..."
            self.next_exercise()
    
    def _generate_basic_combo(self):
        """Generate basic combo movement exercise showing queen's versatility"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place queen in center area to show maximum power
            queen_file = random.randint(3, 4)
            queen_rank = random.randint(3, 4)
            queen_square = chess.square(queen_file, queen_rank)
            
            self.chess_board.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.WHITE))
            self.current_queen_square = queen_square
            
            # Get all valid queen moves (rook + bishop combined)
            self.target_squares = self.get_queen_moves(queen_square)
            
            # Add some invalid squares (knight moves and other impossible moves)
            self.invalid_squares = []
            knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
            for df, dr in knight_moves:
                new_file = queen_file + df
                new_rank = queen_rank + dr
                if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                    invalid_square = chess.square(new_file, new_rank)
                    if invalid_square not in self.target_squares:
                        self.invalid_squares.append(invalid_square)
            
            self.chess_board.highlight_square(queen_square)
            
        except Exception as e:
            logger.error(f"Failed to generate basic combo exercise: {e}")
            raise
    
    def _generate_straight_lines(self):
        """Generate straight line movement exercise (rook-like moves)"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place queen on edge to emphasize straight line movement
            queen_file = random.choice([0, 7])
            queen_rank = random.randint(2, 5)
            queen_square = chess.square(queen_file, queen_rank)
            
            self.chess_board.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.WHITE))
            self.current_queen_square = queen_square
            
            # Get only horizontal and vertical moves (rook-like)
            self.target_squares = self.get_queen_moves(queen_square, directions=self.rook_directions)
            
            # Add diagonal moves as invalid options
            diagonal_moves = self.get_queen_moves(queen_square, directions=self.bishop_directions)
            self.invalid_squares = diagonal_moves[:6]  # Take some diagonal moves as wrong answers
            
            self.chess_board.highlight_square(queen_square)
            
        except Exception as e:
            logger.error(f"Failed to generate straight lines exercise: {e}")
            raise
    
    def _generate_diagonal_paths(self):
        """Generate diagonal movement exercise (bishop-like moves)"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place queen in corner to emphasize diagonal movement
            queen_file = random.choice([1, 6])
            queen_rank = random.choice([1, 6])
            queen_square = chess.square(queen_file, queen_rank)
            
            self.chess_board.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.WHITE))
            self.current_queen_square = queen_square
            
            # Get only diagonal moves (bishop-like)
            self.target_squares = self.get_queen_moves(queen_square, directions=self.bishop_directions)
            
            # Add straight line moves as invalid options
            straight_moves = self.get_queen_moves(queen_square, directions=self.rook_directions)
            self.invalid_squares = straight_moves[:6]  # Take some straight moves as wrong answers
            
            self.chess_board.highlight_square(queen_square)
            
        except Exception as e:
            logger.error(f"Failed to generate diagonal paths exercise: {e}")
            raise
    
    def _generate_tactical_patterns(self):
        """Generate tactical pattern exercise (forks, pins, skewers)"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place white queen
            queen_file = random.randint(1, 6)
            queen_rank = random.randint(1, 6)
            queen_square = chess.square(queen_file, queen_rank)
            
            self.chess_board.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.WHITE))
            self.current_queen_square = queen_square
            
            # Create tactical opportunities
            self._setup_tactical_position(queen_square)
            
            # Find squares where queen can create forks, pins, or skewers
            tactical_squares = []
            all_moves = self.get_queen_moves(queen_square)
            
            for move_square in all_moves:
                if self._creates_tactical_pattern(queen_square, move_square):
                    tactical_squares.append(move_square)
            
            self.target_squares = tactical_squares if tactical_squares else all_moves[:3]
            
            # Invalid squares are non-tactical moves
            self.invalid_squares = [sq for sq in all_moves 
                                  if sq not in self.target_squares][:5]
            
            self.chess_board.highlight_square(queen_square)
            
        except Exception as e:
            logger.error(f"Failed to generate tactical patterns exercise: {e}")
            raise
    
    def _generate_positioning_strategy(self):
        """Generate strategic positioning exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create a position with pieces that could attack queen if poorly placed
            queen_square = chess.square(random.randint(0, 7), random.randint(0, 7))
            self.chess_board.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.WHITE))
            self.current_queen_square = queen_square
            
            # Add enemy pieces that could threaten the queen
            enemy_pieces = [
                (chess.KNIGHT, chess.BLACK),
                (chess.BISHOP, chess.BLACK),
                (chess.ROOK, chess.BLACK)
            ]
            
            placed_enemies = 0
            for piece_type, color in enemy_pieces:
                if placed_enemies >= 3:
                    break
                for _ in range(5):  # Try to place enemy piece
                    enemy_square = chess.square(random.randint(0, 7), random.randint(0, 7))
                    if (not self.chess_board.board.piece_at(enemy_square) and 
                        enemy_square != queen_square):
                        self.chess_board.board.set_piece_at(enemy_square, chess.Piece(piece_type, color))
                        placed_enemies += 1
                        break
            
            # Find safe, active squares for queen
            all_moves = self.get_queen_moves(queen_square)
            safe_squares = []
            dangerous_squares = []
            
            for move_square in all_moves:
                if self._is_square_safe(move_square, chess.BLACK):
                    safe_squares.append(move_square)
                else:
                    dangerous_squares.append(move_square)
            
            self.target_squares = safe_squares if safe_squares else all_moves[:3]
            self.invalid_squares = dangerous_squares[:5]
            self.highlight_danger_squares = True
            
            self.chess_board.highlight_square(queen_square)
            
        except Exception as e:
            logger.error(f"Failed to generate positioning strategy exercise: {e}")
            raise
    
    def _setup_tactical_position(self, queen_square):
        """Setup pieces for tactical exercises"""
        try:
            # Place enemy pieces in positions where queen can create tactics
            enemy_squares = []
            
            # Try to place pieces on same lines as queen for pins/skewers
            for direction in self.queen_directions:
                df, dr = direction
                for distance in range(2, 6):
                    new_file = chess.square_file(queen_square) + df * distance
                    new_rank = chess.square_rank(queen_square) + dr * distance
                    
                    if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                        enemy_square = chess.square(new_file, new_rank)
                        if len(enemy_squares) < 4:
                            enemy_squares.append(enemy_square)
            
            # Place enemy pieces
            piece_types = [chess.KING, chess.ROOK, chess.BISHOP, chess.KNIGHT]
            for i, enemy_square in enumerate(enemy_squares[:4]):
                piece_type = piece_types[i]
                self.chess_board.board.set_piece_at(enemy_square, chess.Piece(piece_type, chess.BLACK))
                
        except Exception as e:
            logger.error(f"Error setting up tactical position: {e}")
    
    def _creates_tactical_pattern(self, from_square, to_square):
        """Check if moving queen creates a tactical pattern"""
        try:
            # Simple tactical detection
            attacked_squares = self.get_queen_moves(to_square)
            enemy_pieces_attacked = []
            
            for attacked_square in attacked_squares:
                piece = self.chess_board.board.piece_at(attacked_square)
                if piece and piece.color == chess.BLACK:
                    enemy_pieces_attacked.append((piece, attacked_square))
            
            # Fork: attacking 2+ pieces
            if len(enemy_pieces_attacked) >= 2:
                return True
            
            # Pin/Skewer: check for pieces in line
            for direction in self.queen_directions:
                pieces_in_line = []
                df, dr = direction
                to_file = chess.square_file(to_square)
                to_rank = chess.square_rank(to_square)
                
                for distance in range(1, 8):
                    check_file = to_file + df * distance
                    check_rank = to_rank + dr * distance
                    
                    if not (0 <= check_file <= 7 and 0 <= check_rank <= 7):
                        break
                    
                    check_square = chess.square(check_file, check_rank)
                    piece = self.chess_board.board.piece_at(check_square)
                    
                    if piece:
                        pieces_in_line.append((piece, check_square))
                        if len(pieces_in_line) >= 2:
                            # Check for pin/skewer pattern
                            first_piece = pieces_in_line[0][0]
                            second_piece = pieces_in_line[1][0]
                            if (first_piece.color == chess.BLACK and 
                                second_piece.color == chess.BLACK and
                                second_piece.piece_type > first_piece.piece_type):
                                return True
                            break
            
            return False
        except Exception as e:
            logger.error(f"Error checking tactical pattern: {e}")
            return False
    
    def _is_square_safe(self, square, enemy_color):
        """Check if a square is safe from enemy attacks"""
        try:
            # Simple safety check - see if any enemy piece can attack this square
            for sq in range(64):
                piece = self.chess_board.board.piece_at(sq)
                if piece and piece.color == enemy_color:
                    if piece.piece_type == chess.KNIGHT:
                        # Check knight moves
                        knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), 
                                      (1, 2), (1, -2), (-1, 2), (-1, -2)]
                        sq_file = chess.square_file(sq)
                        sq_rank = chess.square_rank(sq)
                        for df, dr in knight_moves:
                            attack_file = sq_file + df
                            attack_rank = sq_rank + dr
                            if (0 <= attack_file <= 7 and 0 <= attack_rank <= 7 and
                                chess.square(attack_file, attack_rank) == square):
                                return False
                    elif piece.piece_type in [chess.ROOK, chess.BISHOP, chess.QUEEN]:
                        # Check if piece can attack the square
                        if piece.piece_type == chess.ROOK:
                            directions = self.rook_directions
                        elif piece.piece_type == chess.BISHOP:
                            directions = self.bishop_directions
                        else:  # QUEEN
                            directions = self.queen_directions
                        
                        attacked_squares = self.get_queen_moves(sq, directions=directions)
                        if square in attacked_squares:
                            return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking square safety: {e}")
            return True
    
    def handle_square_click(self, square):
        """Handle square click"""
        try:
            if self.show_feedback or square is None or self.demonstration_mode:
                return
            
            self.selected_square = square
            self.total_attempts += 1
            
            if square in self.target_squares:
                self.on_correct_move()
            else:
                self.on_incorrect_move()
                
        except Exception as e:
            logger.error(f"Error handling square click: {e}")
            self.feedback_message = "Error processing move."
            self.show_feedback = True
    
    def on_correct_move(self):
        """Handle correct move"""
        try:
            self.correct_moves += 1
            self.show_feedback = True
            self.feedback_timer = 0
            
            # Specific feedback based on exercise type
            if self.exercise_type == 'basic_combo':
                self.feedback_message = "Perfect! The queen combines rook and bishop power!"
            elif self.exercise_type == 'straight_lines':
                self.feedback_message = "Excellent straight line move! Queens dominate ranks and files!"
            elif self.exercise_type == 'diagonal_paths':
                self.feedback_message = "Great diagonal move! Queens control powerful diagonals!"
            elif self.exercise_type == 'tactical_patterns':
                self.feedback_message = "Brilliant tactic! Queens are tactical powerhouses!"
            elif self.exercise_type == 'positioning_strategy':
                self.feedback_message = "Smart positioning! Keep the queen safe but active!"
            
            if self.selected_square is not None:
                self.chess_board.select_square(self.selected_square)
            
            if self.exercise_type:
                # Check if we've already completed max exercises for this type
                if self.exercises_completed[self.exercise_type] < self.exercises_per_type:
                    self.exercises_completed[self.exercise_type] += 1
                total_completed = sum(self.exercises_completed.values())
                # Only update progress bar if not exceeding max
                max_exercises = len(self.movement_types) * self.exercises_per_type
                if total_completed <= max_exercises:
                    self.progress_bar.set_value(total_completed)
            
            try:
                self.engine.audio_manager.play_sound('success.wav')
            except Exception as e:
                logger.warning(f"Failed to play success sound: {e}")
            
            self.create_celebration()
            
            try:
                points = 150 if self.exercise_type == 'tactical_patterns' else 120
                animated_text = AnimatedText(
                    f"+{points} points!",
                    (self.config.SCREEN_WIDTH // 2, 300),
                    48,
                    self.config.COLORS['secondary'],
                    2.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create animated text: {e}")
                
        except Exception as e:
            logger.error(f"Error in on_correct_move: {e}")
            self.feedback_message = "Move registered correctly!"
            self.show_feedback = True
    
    def on_incorrect_move(self):
        """Handle incorrect move"""
        try:
            self.show_feedback = True
            self.feedback_timer = 0
            
            if self.selected_square == self.current_queen_square:
                self.feedback_message = "Click where the queen can move, not the queen itself."
            elif self.exercise_type == 'straight_lines' and self.selected_square in self.invalid_squares:
                self.feedback_message = "That's a diagonal move! Try horizontal or vertical lines."
            elif self.exercise_type == 'diagonal_paths' and self.selected_square in self.invalid_squares:
                self.feedback_message = "That's a straight line! Try diagonal movement."
            elif self.exercise_type == 'tactical_patterns':
                self.feedback_message = "Look for moves that attack multiple pieces or create pins!"
            elif self.exercise_type == 'positioning_strategy':
                self.feedback_message = "That square looks dangerous! Find a safer but active square."
            elif self.exercise_type == 'basic_combo':
                self.feedback_message = "Queens can't move like knights! Try straight or diagonal lines."
            else:
                self.feedback_message = "Invalid queen move. Remember: straight lines and diagonals only!"
            
            try:
                self.engine.audio_manager.play_sound('error.wav')
            except Exception as e:
                logger.warning(f"Failed to play error sound: {e}")
                
        except Exception as e:
            logger.error(f"Error in on_incorrect_move: {e}")
            self.feedback_message = "Invalid move. Try again!"
    
    def toggle_hint(self):
        """Toggle hint display"""
        try:
            self.show_hint = not self.show_hint
            if self.show_hint:
                for square in self.target_squares:
                    if 0 <= square <= 63:
                        self.chess_board.highlight_square(square)
            else:
                self.chess_board.clear_highlights()
                if self.current_queen_square is not None:
                    self.chess_board.highlight_square(self.current_queen_square)
        except Exception as e:
            logger.error(f"Error toggling hint: {e}")
    
    def toggle_rook_lines(self):
        """Toggle rook-style movement visualization"""
        try:
            self.show_rook_lines = not self.show_rook_lines
            if self.show_bishop_lines and self.show_rook_lines:
                self.show_combo_power = True
        except Exception as e:
            logger.error(f"Error toggling rook lines: {e}")
    
    def toggle_bishop_lines(self):
        """Toggle bishop-style movement visualization"""
        try:
            self.show_bishop_lines = not self.show_bishop_lines
            if self.show_bishop_lines and self.show_rook_lines:
                self.show_combo_power = True
        except Exception as e:
            logger.error(f"Error toggling bishop lines: {e}")
    
    def toggle_combo_power(self):
        """Toggle full combo power visualization"""
        try:
            self.show_combo_power = not self.show_combo_power
            if self.show_combo_power:
                self.show_rook_lines = True
                self.show_bishop_lines = True
            else:
                self.show_rook_lines = False
                self.show_bishop_lines = False
        except Exception as e:
            logger.error(f"Error toggling combo power: {e}")
    
    def start_demonstration(self):
        """Start movement demonstration"""
        try:
            if not self.target_squares or self.demonstration_mode:
                return
            
            self.demonstration_mode = True
            demo_square = random.choice(self.target_squares)
            
            # Animate movement
            try:
                animated_text = AnimatedText(
                    "Watch the queen's ultimate power!",
                    (self.config.SCREEN_WIDTH // 2, 250),
                    32,
                    self.config.COLORS['accent'],
                    3.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create demo text: {e}")
            
            # Highlight the path
            self.chess_board.select_square(demo_square)
            
            # Reset after delay
            pygame.time.set_timer(pygame.USEREVENT + 3, 3000)
            
        except Exception as e:
            logger.error(f"Error starting demonstration: {e}")
            self.demonstration_mode = False
    
    def skip_exercise(self):
        """Skip current exercise"""
        try:
            if not self.show_feedback and self.exercise_type:
                self.exercises_completed[self.exercise_type] += 1
                self.next_exercise()
        except Exception as e:
            logger.error(f"Error skipping exercise: {e}")
            self.next_exercise()
    
    def next_exercise(self):
        """Move to next exercise"""
        try:
            self.current_exercise += 1
            
            if self.exercise_type and self.exercises_completed[self.exercise_type] >= self.exercises_per_type:
                self.current_type_index += 1
                
            # Prevent going beyond total exercises
            total_completed = sum(self.exercises_completed.values())
            max_exercises = len(self.movement_types) * self.exercises_per_type
            
            if self.current_type_index >= len(self.movement_types) or total_completed >= max_exercises:
                self.complete_module()
            else:
                self.generate_exercise()
                
        except Exception as e:
            logger.error(f"Error moving to next exercise: {e}")
            self.current_type_index += 1
            total_completed = sum(self.exercises_completed.values())
            max_exercises = len(self.movement_types) * self.exercises_per_type
            if self.current_type_index >= len(self.movement_types) or total_completed >= max_exercises:
                self.complete_module()
            else:
                self.generate_exercise()
    
    def complete_module(self):
        """Complete the queen movement module"""
        try:
            self.module_completed = True
            self.completion_timer = 0
            
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            
            # Create massive completion celebration (queen is the most powerful!)
            for _ in range(75):
                try:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(250, 600)
                    self.celebration_particles.append({
                        'x': self.config.SCREEN_WIDTH // 2,
                        'y': self.config.SCREEN_HEIGHT // 2,
                        'vx': speed * math.cos(angle),
                        'vy': speed * math.sin(angle),
                        'color': random.choice([(255, 215, 0), (255, 255, 255), (255, 0, 255),
                                              self.config.COLORS.get('accent', (155, 89, 182)),
                                              self.config.COLORS.get('secondary', (46, 204, 113)),
                                              (255, 100, 100)]),
                        'life': 4.5,
                        'size': random.randint(6, 20)
                    })
                except Exception as e:
                    logger.warning(f"Failed to create celebration particle: {e}")
            
            try:
                self.engine.audio_manager.play_sound('complete.wav')
            except Exception as e:
                logger.warning(f"Failed to play completion sound: {e}")
                
        except Exception as e:
            logger.error(f"Error completing module: {e}")
            self.module_completed = True
    
    def create_celebration(self):
        """Create celebration effect for correct moves"""
        try:
            particle_count = 30 if self.exercise_type == 'tactical_patterns' else 20
            
            for _ in range(particle_count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(150, 400)
                colors = [self.config.COLORS.get('accent', (155, 89, 182)), 
                         self.config.COLORS.get('secondary', (46, 204, 113)), 
                         (255, 255, 255), (255, 215, 0), (255, 0, 255)]
                
                self.celebration_particles.append({
                    'x': self.config.SCREEN_WIDTH // 2,
                    'y': 350,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle),
                    'color': random.choice(colors),
                    'life': 2.5,
                    'size': random.randint(4, 12)
                })
        except Exception as e:
            logger.warning(f"Failed to create celebration effect: {e}")
    
    def on_back_clicked(self):
        """Handle back button click"""
        try:
            self.engine.change_state(GameState.MAIN_MENU)
        except Exception as e:
            logger.error(f"Error returning to main menu: {e}")
            try:
                self.engine.running = False
            except:
                pass
    
    def handle_event(self, event):
        """Handle pygame events"""
        try:
            # Handle UI button events
            self.back_button.handle_event(event)
            self.hint_button.handle_event(event)
            #self.rook_lines_button.handle_event(event)
            #self.bishop_lines_button.handle_event(event)
            #self.combo_button.handle_event(event)
            
            if not self.show_feedback:
                self.demo_button.handle_event(event)
                if self.total_attempts > 2:
                    self.skip_button.handle_event(event)
            
            if self.show_feedback:
                self.next_button.handle_event(event)
            
            # Handle mouse clicks on chess board
            if event.type == pygame.MOUSEBUTTONDOWN:
                try:
                    square = self.chess_board.get_square_from_pos(event.pos)
                    self.handle_square_click(square)
                except Exception as e:
                    logger.error(f"Error getting square from position: {e}")
            
            # Handle keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.show_feedback:
                    self.next_exercise()
                elif event.key == pygame.K_h:
                    self.toggle_hint()
                elif event.key == pygame.K_r:
                    self.toggle_rook_lines()
                elif event.key == pygame.K_b:
                    self.toggle_bishop_lines()
                elif event.key == pygame.K_c:
                    self.toggle_combo_power()
                elif event.key == pygame.K_m and not self.show_feedback:
                    self.start_demonstration()
                elif event.key == pygame.K_s and self.total_attempts > 2:
                    self.skip_exercise()
            
            # Handle demonstration timer
            if event.type == pygame.USEREVENT + 3:
                self.demonstration_mode = False
                pygame.time.set_timer(pygame.USEREVENT + 3, 0)  # Cancel timer
                
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def update(self, dt):
        """Update game state"""
        try:
            super().update(dt)
            
            # Update mouse position for UI elements
            mouse_pos = pygame.mouse.get_pos()
            
            # Update UI elements
            self.back_button.update(dt, mouse_pos)
            self.hint_button.update(dt, mouse_pos)
            #self.rook_lines_button.update(dt, mouse_pos)
            #self.bishop_lines_button.update(dt, mouse_pos)
            #self.combo_button.update(dt, mouse_pos)
            
            if not self.show_feedback:
                self.demo_button.update(dt, mouse_pos)
                if self.total_attempts > 2:
                    self.skip_button.update(dt, mouse_pos)
            
            if self.show_feedback:
                self.next_button.update(dt, mouse_pos)
            
            # Update feedback timer
            if self.show_feedback and not self.module_completed:
                self.feedback_timer += dt
            
            # Update animated texts
            for text in self.animated_texts[:]:
                try:
                    text.update(dt)
                    if text.is_finished():
                        self.animated_texts.remove(text)
                except Exception as e:
                    logger.warning(f"Error updating animated text: {e}")
                    self.animated_texts.remove(text)
            
            # Update celebration particles
            for particle in self.celebration_particles[:]:
                try:
                    particle['x'] += particle['vx'] * dt
                    particle['y'] += particle['vy'] * dt
                    particle['vy'] += 500 * dt  # Gravity
                    particle['life'] -= dt
                    particle['size'] = max(1, particle['size'] - dt * 2.5)
                    if particle['life'] <= 0:
                        self.celebration_particles.remove(particle)
                except Exception as e:
                    logger.warning(f"Error updating particle: {e}")
                    self.celebration_particles.remove(particle)
            
            # Update animations
            self.power_animation += dt * 3
            if self.power_animation > 2 * math.pi:
                self.power_animation = 0
            
            self.combo_pulse += dt * 4
            if self.combo_pulse > 2 * math.pi:
                self.combo_pulse = 0
            
            # Auto-advance after module completion
            if self.module_completed:
                self.completion_timer += dt
                if self.completion_timer > 7.0:
                    self.engine.change_state(GameState.MAIN_MENU)
                    
        except Exception as e:
            logger.error(f"Error in update: {e}")
    
    def render(self, screen):
        """Render the queen movement training interface"""
        try:
            # Fill background
            screen.fill(self.config.COLORS['background'])
            
            # Render title
            title_surface = self.title_font.render("Learn Queen Movement - Ultimate Power!", True, self.config.COLORS['text_dark'])
            screen.blit(title_surface, title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 40)))
            
            # Render progress bar
            #self.progress_bar.render(screen)
            
            # Render current exercise info
            if not self.module_completed and self.exercise_type:
                # Exercise type
                type_surface = self.instruction_font.render(
                    f"Exercise: {self.exercise_type.replace('_', ' ').title()}", 
                    True, self.config.COLORS['primary']
                )
                screen.blit(type_surface, type_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 90)))
                
                # Instructions
                inst_surface = self.info_font.render(
                    self.instructions.get(self.exercise_type, ""), 
                    True, self.config.COLORS['text_dark']
                )
                screen.blit(inst_surface, inst_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 120)))
                
                # Learning tip
                tip_surface = self.tip_font.render(
                    self.learning_tips.get(self.exercise_type, ""), 
                    True, self.config.COLORS['accent']
                )
                screen.blit(tip_surface, tip_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 150)))
            
            # Render chess board
            try:
                self.chess_board.draw()
                
                # Render queen power visualizations
                if self.current_queen_square is not None:
                    if self.show_rook_lines:
                        self.render_rook_lines_overlay(screen)
                    if self.show_bishop_lines:
                        self.render_bishop_lines_overlay(screen)
                    if self.show_combo_power:
                        self.render_combo_power_overlay(screen)
                    
            except Exception as e:
                logger.error(f"Error drawing chess board: {e}")
                error_surface = self.instruction_font.render("Error displaying board", True, 
                                                           self.config.COLORS.get('error', (255, 0, 0)))
                screen.blit(error_surface, error_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400)))
            
            # Render hint text
            if self.show_hint and not self.show_feedback:
                hint_surface = self.info_font.render("Valid queen moves highlighted in yellow", 
                                                   True, self.config.COLORS['secondary'])
                screen.blit(hint_surface, hint_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 680)))
            
            # Render feedback message
            if self.feedback_message and not self.module_completed:
                color = (self.config.COLORS['secondary'] if any(word in self.feedback_message for word in 
                        ["Perfect", "Excellent", "Great", "Brilliant", "Smart"]) 
                        else self.config.COLORS.get('error', (255, 0, 0)))
                feedback_surface = self.instruction_font.render(self.feedback_message, True, color)
                screen.blit(feedback_surface, feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 620)))
            
            # Render UI buttons
            self.back_button.render(screen)
            self.hint_button.render(screen)
            #self.rook_lines_button.render(screen)
            #self.bishop_lines_button.render(screen)
            #self.combo_button.render(screen)
            
            if not self.show_feedback:
                self.demo_button.render(screen)
                if self.total_attempts > 2:
                    self.skip_button.render(screen)
            
            if self.show_feedback:
                self.next_button.render(screen)
            
            # Render animated texts
            for text in self.animated_texts:
                try:
                    text.render(screen)
                except Exception as e:
                    logger.warning(f"Error rendering animated text: {e}")
            
            # Render celebration particles
            for particle in self.celebration_particles:
                try:
                    pygame.draw.circle(screen, particle['color'], 
                                     (int(particle['x']), int(particle['y'])), 
                                     int(particle['size']))
                except Exception as e:
                    logger.warning(f"Error rendering particle: {e}")
            
            # Render completion screen
            if self.module_completed:
                self.render_completion_screen(screen)
                
        except Exception as e:
            logger.error(f"Critical error in render: {e}")
            try:
                screen.fill((200, 200, 200))
                font = pygame.font.SysFont('Arial', 24)
                error_text = font.render("Error: Unable to render. Press Back to return.", True, (255, 0, 0))
                screen.blit(error_text, (50, 50))
            except:
                pass
    
    def render_rook_lines_overlay(self, screen):
        """Render rook-style movement lines"""
        try:
            if self.current_queen_square is None:
                return
            
            queen_pos = self.chess_board.get_square_center(self.current_queen_square)
            if queen_pos is None:
                return
            
            # Draw animated horizontal and vertical lines
            alpha = int(128 + 64 * math.sin(self.power_animation))
            
            for df, dr in self.rook_directions:
                try:
                    square_size = self.chess_board.square_size
                    line_length = 4  # Draw lines extending 4 squares
                    
                    end_x = queen_pos[0] + df * line_length * square_size
                    end_y = queen_pos[1] + dr * line_length * square_size
                    
                    # Ensure line stays on board
                    board_left = self.chess_board.board_offset_x
                    board_top = self.chess_board.board_offset_y
                    board_right = board_left + 8 * square_size
                    board_bottom = board_top + 8 * square_size
                    
                    end_x = max(board_left, min(board_right, end_x))
                    end_y = max(board_top, min(board_bottom, end_y))
                    
                    # Draw straight line (rook-style)
                    pygame.draw.line(screen, (0, 255, 0, alpha), queen_pos, (end_x, end_y), 5)
                        
                except Exception as e:
                    logger.warning(f"Error drawing rook line: {e}")
                    
        except Exception as e:
            logger.error(f"Error rendering rook lines overlay: {e}")
    
    def render_bishop_lines_overlay(self, screen):
        """Render bishop-style movement lines"""
        try:
            if self.current_queen_square is None:
                return
            
            queen_pos = self.chess_board.get_square_center(self.current_queen_square)
            if queen_pos is None:
                return
            
            # Draw animated diagonal lines
            alpha = int(128 + 64 * math.sin(self.power_animation + 1))
            
            for df, dr in self.bishop_directions:
                try:
                    square_size = self.chess_board.square_size
                    line_length = 4  # Draw lines extending 4 squares
                    
                    end_x = queen_pos[0] + df * line_length * square_size
                    end_y = queen_pos[1] + dr * line_length * square_size
                    
                    # Ensure line stays on board
                    board_left = self.chess_board.board_offset_x
                    board_top = self.chess_board.board_offset_y
                    board_right = board_left + 8 * square_size
                    board_bottom = board_top + 8 * square_size
                    
                    end_x = max(board_left, min(board_right, end_x))
                    end_y = max(board_top, min(board_bottom, end_y))
                    
                    # Draw diagonal line (bishop-style)
                    pygame.draw.line(screen, (255, 0, 255, alpha), queen_pos, (end_x, end_y), 5)
                        
                except Exception as e:
                    logger.warning(f"Error drawing bishop line: {e}")
                    
        except Exception as e:
            logger.error(f"Error rendering bishop lines overlay: {e}")
    
    def render_combo_power_overlay(self, screen):
        """Render combined queen power visualization"""
        try:
            if self.current_queen_square is None:
                return
            
            queen_pos = self.chess_board.get_square_center(self.current_queen_square)
            if queen_pos is None:
                return
            
            # Draw pulsing circle showing queen's complete range
            alpha = int(100 + 50 * math.sin(self.combo_pulse))
            radius = int(60 + 20 * math.sin(self.combo_pulse))
            
            # Create surface for alpha blending
            overlay = pygame.Surface((radius * 2, radius * 2))
            overlay.set_alpha(alpha)
            overlay.fill((255, 215, 0))  # Golden color for queen power
            
            circle_rect = overlay.get_rect(center=queen_pos)
            screen.blit(overlay, circle_rect)
            
            # Draw power text
            if hasattr(self, 'combo_text_timer'):
                self.combo_text_timer += 0.016  # Approximate dt
            else:
                self.combo_text_timer = 0
            
            if self.combo_text_timer < 3.0:  # Show for 3 seconds
                power_surface = self.info_font.render("ULTIMATE POWER!", True, (255, 215, 0))
                text_rect = power_surface.get_rect(center=(queen_pos[0], queen_pos[1] - 80))
                screen.blit(power_surface, text_rect)
                    
        except Exception as e:
            logger.error(f"Error rendering combo power overlay: {e}")
    
    def render_completion_screen(self, screen):
        """Render module completion screen"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Congratulations message
            success_font = pygame.font.Font(None, 72)
            success_surface = success_font.render("Queen Master!", True, (255, 215, 0))
            screen.blit(success_surface, success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 180)))
            
            # Completion message
            complete_surface = self.title_font.render("You've mastered the most powerful piece!", 
                                                    True, (255, 255, 255))
            screen.blit(complete_surface, complete_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 250)))
            
            # Statistics
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            stats = [
                f"Accuracy: {accuracy:.1f}%",
                f"Correct Moves: {self.correct_moves}/{self.total_attempts}",
                f"Combo Mastery: {sum(self.exercises_completed.values())} exercises completed"
            ]
            
            for i, stat in enumerate(stats):
                stat_surface = self.instruction_font.render(stat, True, (255, 255, 255))
                screen.blit(stat_surface, stat_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 320 + i * 40)))
            
            # Achievement message
            if accuracy >= 90:
                achievement = "Outstanding! You wield the queen's ultimate power!"
            elif accuracy >= 75:
                achievement = "Excellent! The queen's secrets are yours to command!"
            else:
                achievement = "Good progress! Keep practicing the queen's mighty moves!"
            
            achievement_surface = self.info_font.render(achievement, True, self.config.COLORS['accent'])
            screen.blit(achievement_surface, achievement_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 460)))
            
            # Queen power summary
            power_lines = [
                "Queen Power Summary:",
                "• Combines rook + bishop movements",
                "• Controls up to 27 squares from center", 
                "• Perfect for tactics: forks, pins, skewers",
                "• Worth 9 points - most valuable piece",
                "• Keep safe but active in games!"
            ]
            
            for i, line in enumerate(power_lines):
                color = (255, 215, 0) if i == 0 else (200, 200, 200)
                font = self.info_font if i == 0 else self.tip_font
                line_surface = font.render(line, True, color)
                screen.blit(line_surface, line_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 510 + i * 25)))
            
        except Exception as e:
            logger.error(f"Error rendering completion screen: {e}")