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

class BishopMovementState(BaseState):
    """Module for teaching bishop movement rules - diagonal paths and color restriction"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Module configuration based on bishop learning challenges
            self.exercises_per_type = 4  # Multiple exercises for each concept
            self.movement_types = ['basic_diagonal', 'color_restriction', 'pin_tactics', 'strategic_positioning']
            
            # Progress tracking
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            self.exercises_completed = {move_type: 0 for move_type in self.movement_types}
            
            # Current exercise data
            self.current_bishop_square = None
            self.target_squares = []
            self.invalid_squares = []
            self.selected_square = None
            self.show_feedback = False
            self.feedback_timer = 0
            self.feedback_message = ""
            self.exercise_type = None
            self.show_hint = False
            
            # Bishop-specific learning aids
            self.show_diagonal_paths = False
            self.show_color_restriction = False
            self.current_square_color = None
            self.demonstration_mode = False
            self.highlight_unreachable = False
            
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
            
            # Instructions based on diagonal movement research
            self.instructions = {
                'basic_diagonal': "Bishops move diagonally any number of squares. Click a valid diagonal square.",
                'color_restriction': "Bishops stay on the same color squares forever! Click a reachable square.",
                'pin_tactics': "Bishops can pin pieces to more valuable pieces behind them. Find the pin!",
                'strategic_positioning': "Position bishops on strong diagonals. Find the best square."
            }
            
            # Learning tips for each type
            self.learning_tips = {
                'basic_diagonal': "Think of bishops as traveling on 'X' shaped highways",
                'color_restriction': "Light-squared bishops never reach dark squares (and vice versa)",
                'pin_tactics': "A pinned piece cannot move because it would expose a more valuable piece",
                'strategic_positioning': "Bishops are strongest on long, open diagonals"
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
            self.diagonal_animation = 0
            self.color_pulse = 0
            
            # Module completion
            self.module_completed = False
            self.completion_timer = 0
            
            # Session timer
            self.session_timer = Timer()
            
            # Bishop movement patterns for validation
            self.diagonal_directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            
        except Exception as e:
            logger.error(f"Failed to initialize BishopMovementState: {e}")
            raise
    
    def create_ui_elements(self):
        """Create UI elements"""
        try:
            total_exercises = len(self.movement_types) * self.exercises_per_type
            #self.progress_bar = ProgressBar(
            #    pos=(self.config.SCREEN_WIDTH // 2 - 200, 30),
            #    size=(400, 25),
            #    max_value=total_exercises,
            #    config=self.config
            #)
            
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
            
            #self.diagonal_button = Button(
            #    text="Show Diagonals",
            #    pos=(self.config.SCREEN_WIDTH - 180, 100),
            #    size=(150, 40),
            #    callback=self.toggle_diagonal_paths,
            #    config=self.config
            #)
            
            #self.color_button = Button(
            #    text="Show Colors",
            #    pos=(self.config.SCREEN_WIDTH - 180, 150),
            #    size=(150, 40),
            #    callback=self.toggle_color_restriction,
            #    config=self.config
            #)
            
            self.demo_button = Button(
                text="Demo Move",
                pos=(self.config.SCREEN_WIDTH - 180, 200),
                size=(150, 40),
                callback=self.start_demonstration,
                config=self.config
            )
            
            self.skip_button = Button(
                text="Skip",
                pos=(self.config.SCREEN_WIDTH - 180, 250),
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
            #self.progress_bar.set_value(0)
            self.module_completed = False
            self.session_timer.reset()
            self.generate_exercise()
            
            try:
                self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
            except Exception as e:
                logger.warning(f"Failed to play learning music: {e}")
                
        except Exception as e:
            logger.error(f"Failed to enter BishopMovementState: {e}")
            self.engine.change_state(GameState.MAIN_MENU)
    
    def is_light_square(self, square):
        """Check if square is light colored"""
        try:
            if square is None or not (0 <= square <= 63):
                return False
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            return (file + rank) % 2 == 1
        except Exception as e:
            logger.error(f"Error checking square color: {e}")
            return False
    
    def get_bishop_moves(self, square, board=None):
        """Get all valid bishop moves from a square"""
        try:
            if square is None or not (0 <= square <= 63):
                return []
            
            if board is None:
                board = self.chess_board.board
            
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            moves = []
            
            # Check all four diagonal directions
            for df, dr in self.diagonal_directions:
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
                        bishop_piece = board.piece_at(square)
                        if bishop_piece and piece.color != bishop_piece.color:
                            moves.append(new_square)
                        break
            
            return moves
        except Exception as e:
            logger.error(f"Error calculating bishop moves: {e}")
            return []
    
    def get_diagonal_path(self, from_square, to_square):
        """Get all squares on diagonal path between two squares"""
        try:
            if from_square is None or to_square is None:
                return []
            
            from_file = chess.square_file(from_square)
            from_rank = chess.square_rank(from_square)
            to_file = chess.square_file(to_square)
            to_rank = chess.square_rank(to_square)
            
            # Check if squares are on same diagonal
            if abs(from_file - to_file) != abs(from_rank - to_rank):
                return []
            
            path = []
            df = 1 if to_file > from_file else -1
            dr = 1 if to_rank > from_rank else -1
            
            current_file = from_file + df
            current_rank = from_rank + dr
            
            while current_file != to_file and current_rank != to_rank:
                path.append(chess.square(current_file, current_rank))
                current_file += df
                current_rank += dr
            
            return path
        except Exception as e:
            logger.error(f"Error calculating diagonal path: {e}")
            return []
    
    def generate_exercise(self):
        """Generate a new exercise"""
        try:
            self.show_feedback = False
            self.selected_square = None
            self.show_hint = False
            self.show_diagonal_paths = False
            self.show_color_restriction = False
            self.highlight_unreachable = False
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
                if self.exercise_type == 'basic_diagonal':
                    self._generate_basic_diagonal()
                elif self.exercise_type == 'color_restriction':
                    self._generate_color_restriction()
                elif self.exercise_type == 'pin_tactics':
                    self._generate_pin_tactics()
                elif self.exercise_type == 'strategic_positioning':
                    self._generate_strategic_positioning()
            except Exception as e:
                logger.error(f"Failed to generate {self.exercise_type} exercise: {e}")
                self.next_exercise()
                
        except Exception as e:
            logger.error(f"Failed to generate exercise: {e}")
            self.feedback_message = "Error generating exercise. Skipping..."
            self.next_exercise()
    
    def _generate_basic_diagonal(self):
        """Generate basic diagonal movement exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place bishop in varied positions to show different diagonal patterns
            bishop_file = random.randint(1, 6)
            bishop_rank = random.randint(1, 6)
            bishop_square = chess.square(bishop_file, bishop_rank)
            
            self.chess_board.board.set_piece_at(bishop_square, chess.Piece(chess.BISHOP, chess.WHITE))
            self.current_bishop_square = bishop_square
            self.current_square_color = self.is_light_square(bishop_square)
            
            # Get all valid diagonal moves
            self.target_squares = self.get_bishop_moves(bishop_square)
            
            # Add some invalid squares (non-diagonal)
            self.invalid_squares = []
            for _ in range(6):
                while True:
                    invalid_square = random.randint(0, 63)
                    if (invalid_square not in self.target_squares and 
                        invalid_square != bishop_square):
                        # Ensure it's not on the same diagonal
                        if not self._is_diagonal_from(bishop_square, invalid_square):
                            self.invalid_squares.append(invalid_square)
                            break
            
            self.chess_board.highlight_square(bishop_square)
            
        except Exception as e:
            logger.error(f"Failed to generate basic diagonal exercise: {e}")
            raise
    
    def _generate_color_restriction(self):
        """Generate color restriction exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place bishop on specific color
            is_light_bishop = random.choice([True, False])
            
            # Find a square of the chosen color
            while True:
                bishop_file = random.randint(2, 5)
                bishop_rank = random.randint(2, 5)
                bishop_square = chess.square(bishop_file, bishop_rank)
                if self.is_light_square(bishop_square) == is_light_bishop:
                    break
            
            self.chess_board.board.set_piece_at(bishop_square, chess.Piece(chess.BISHOP, chess.WHITE))
            self.current_bishop_square = bishop_square
            self.current_square_color = is_light_bishop
            self.show_color_restriction = True
            
            # Get valid moves (all same color)
            self.target_squares = self.get_bishop_moves(bishop_square)
            
            # Add opposite color squares as invalid options
            self.invalid_squares = []
            opposite_color_squares = [sq for sq in range(64) 
                                    if self.is_light_square(sq) != is_light_bishop 
                                    and sq != bishop_square]
            self.invalid_squares = random.sample(opposite_color_squares, 
                                               min(8, len(opposite_color_squares)))
            
            self.chess_board.highlight_square(bishop_square)
            
        except Exception as e:
            logger.error(f"Failed to generate color restriction exercise: {e}")
            raise
    
    def _generate_pin_tactics(self):
        """Generate pin tactics exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place white bishop
            bishop_file = random.randint(0, 3)
            bishop_rank = random.randint(0, 3)
            bishop_square = chess.square(bishop_file, bishop_rank)
            
            self.chess_board.board.set_piece_at(bishop_square, chess.Piece(chess.BISHOP, chess.WHITE))
            self.current_bishop_square = bishop_square
            
            # Find a diagonal to create a pin
            possible_diagonals = []
            for df, dr in self.diagonal_directions:
                diagonal_squares = []
                for distance in range(1, 8):
                    new_file = bishop_file + df * distance
                    new_rank = bishop_rank + dr * distance
                    if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                        diagonal_squares.append(chess.square(new_file, new_rank))
                    else:
                        break
                
                if len(diagonal_squares) >= 2:
                    possible_diagonals.append(diagonal_squares)
            
            if possible_diagonals:
                chosen_diagonal = random.choice(possible_diagonals)
                
                # Place a piece to be pinned and a valuable piece behind it
                if len(chosen_diagonal) >= 2:
                    pinned_square = chosen_diagonal[0]
                    valuable_square = chosen_diagonal[1]
                    
                    # Place pieces
                    self.chess_board.board.set_piece_at(pinned_square, 
                                                       chess.Piece(chess.KNIGHT, chess.BLACK))
                    self.chess_board.board.set_piece_at(valuable_square, 
                                                       chess.Piece(chess.QUEEN, chess.BLACK))
            
            # Target squares are moves that create or maintain pins
            self.target_squares = self.get_bishop_moves(bishop_square)
            
            # Filter to only moves that create pins
            pin_moves = []
            for move_square in self.target_squares:
                if self._creates_pin(bishop_square, move_square):
                    pin_moves.append(move_square)
            
            if pin_moves:
                self.target_squares = pin_moves
            
            # Invalid squares are non-pinning moves
            self.invalid_squares = [sq for sq in range(64) 
                                  if sq not in self.target_squares 
                                  and sq != bishop_square 
                                  and not self.chess_board.board.piece_at(sq)][:5]
            
            self.chess_board.highlight_square(bishop_square)
            
        except Exception as e:
            logger.error(f"Failed to generate pin tactics exercise: {e}")
            raise
    
    def _generate_strategic_positioning(self):
        """Generate strategic positioning exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create a position with pawn structure
            bishop_square = chess.square(random.randint(0, 7), random.randint(0, 7))
            self.chess_board.board.set_piece_at(bishop_square, chess.Piece(chess.BISHOP, chess.WHITE))
            self.current_bishop_square = bishop_square
            
            # Add some pawn structure
            for _ in range(random.randint(3, 6)):
                pawn_square = chess.square(random.randint(0, 7), random.randint(1, 6))
                if not self.chess_board.board.piece_at(pawn_square):
                    color = random.choice([chess.WHITE, chess.BLACK])
                    self.chess_board.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, color))
            
            # Find good squares for bishop (long diagonals, few obstructions)
            all_moves = self.get_bishop_moves(bishop_square)
            good_squares = []
            
            for move_square in all_moves:
                # Evaluate square quality based on diagonal length and obstacles
                diagonal_length = self._evaluate_diagonal_strength(move_square)
                if diagonal_length >= 4:  # Prefer long diagonals
                    good_squares.append(move_square)
            
            self.target_squares = good_squares if good_squares else all_moves[:3]
            
            # Invalid squares are poor positioning choices
            self.invalid_squares = [sq for sq in all_moves 
                                  if sq not in self.target_squares][:4]
            
            self.chess_board.highlight_square(bishop_square)
            
        except Exception as e:
            logger.error(f"Failed to generate strategic positioning exercise: {e}")
            raise
    
    def _is_diagonal_from(self, from_square, to_square):
        """Check if two squares are on the same diagonal"""
        try:
            from_file = chess.square_file(from_square)
            from_rank = chess.square_rank(from_square)
            to_file = chess.square_file(to_square)
            to_rank = chess.square_rank(to_square)
            
            return abs(from_file - to_file) == abs(from_rank - to_rank)
        except Exception as e:
            logger.error(f"Error checking diagonal relationship: {e}")
            return False
    
    def _creates_pin(self, bishop_square, target_square):
        """Check if moving bishop to target square creates a pin"""
        try:
            # Simple pin detection - check if there are enemy pieces on the diagonal
            diagonal_squares = []
            target_file = chess.square_file(target_square)
            target_rank = chess.square_rank(target_square)
            
            # Check each diagonal direction from target square
            for df, dr in self.diagonal_directions:
                pieces_on_diagonal = []
                for distance in range(1, 8):
                    new_file = target_file + df * distance
                    new_rank = target_rank + dr * distance
                    if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                        check_square = chess.square(new_file, new_rank)
                        piece = self.chess_board.board.piece_at(check_square)
                        if piece:
                            pieces_on_diagonal.append((piece, check_square))
                            if len(pieces_on_diagonal) >= 2:
                                break
                    else:
                        break
                
                # Check if we have a potential pin (2+ enemy pieces on diagonal)
                if len(pieces_on_diagonal) >= 2:
                    first_piece, _ = pieces_on_diagonal[0]
                    second_piece, _ = pieces_on_diagonal[1]
                    if (first_piece.color == chess.BLACK and 
                        second_piece.color == chess.BLACK and
                        second_piece.piece_type > first_piece.piece_type):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking pin creation: {e}")
            return False
    
    def _evaluate_diagonal_strength(self, square):
        """Evaluate the strength of a diagonal from given square"""
        try:
            max_length = 0
            square_file = chess.square_file(square)
            square_rank = chess.square_rank(square)
            
            # Check all four diagonal directions
            for df, dr in self.diagonal_directions:
                length = 0
                for distance in range(1, 8):
                    new_file = square_file + df * distance
                    new_rank = square_rank + dr * distance
                    if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                        check_square = chess.square(new_file, new_rank)
                        if self.chess_board.board.piece_at(check_square):
                            break  # Blocked by piece
                        length += 1
                    else:
                        break  # Edge of board
                
                max_length = max(max_length, length)
            
            return max_length
        except Exception as e:
            logger.error(f"Error evaluating diagonal strength: {e}")
            return 0
    
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
            if self.exercise_type == 'basic_diagonal':
                self.feedback_message = "Perfect diagonal move! Bishops travel on X-shaped paths!"
            elif self.exercise_type == 'color_restriction':
                color_name = "light" if self.current_square_color else "dark"
                self.feedback_message = f"Excellent! The bishop stayed on {color_name} squares!"
            elif self.exercise_type == 'pin_tactics':
                self.feedback_message = "Great pin! The piece cannot move without exposing the piece behind!"
            elif self.exercise_type == 'strategic_positioning':
                self.feedback_message = "Smart positioning! Long diagonals give bishops maximum power!"
            
            if self.selected_square is not None:
                self.chess_board.select_square(self.selected_square)
            
            if self.exercise_type:
                # Check if we've already completed max exercises for this type
                if self.exercises_completed[self.exercise_type] < self.exercises_per_type:
                    self.exercises_completed[self.exercise_type] += 1
                total_completed = sum(self.exercises_completed.values())
                #self.progress_bar.set_value(total_completed)
            
            try:
                self.engine.audio_manager.play_sound('success.wav')
            except Exception as e:
                logger.warning(f"Failed to play success sound: {e}")
            
            self.create_celebration()
            
            try:
                points = 120 if self.exercise_type == 'pin_tactics' else 100
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
            
            if self.selected_square == self.current_bishop_square:
                self.feedback_message = "Click where the bishop can move, not the bishop itself."
            elif self.exercise_type == 'color_restriction' and self.selected_square in self.invalid_squares:
                current_color = "light" if self.current_square_color else "dark"
                opposite_color = "dark" if self.current_square_color else "light"
                self.feedback_message = f"Wrong color! This bishop can never reach {opposite_color} squares."
            elif self.exercise_type == 'basic_diagonal':
                self.feedback_message = "Bishops only move diagonally! Look for X-shaped paths."
            elif self.exercise_type == 'pin_tactics':
                self.feedback_message = "That move doesn't create a pin. Look for pieces lined up on diagonals."
            elif self.exercise_type == 'strategic_positioning':
                self.feedback_message = "Try to find squares with longer, clearer diagonal paths."
            else:
                self.feedback_message = "Invalid bishop move. Remember: only diagonal movement!"
            
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
                if self.current_bishop_square is not None:
                    self.chess_board.highlight_square(self.current_bishop_square)
        except Exception as e:
            logger.error(f"Error toggling hint: {e}")
    
    def toggle_diagonal_paths(self):
        """Toggle diagonal path visualization"""
        try:
            self.show_diagonal_paths = not self.show_diagonal_paths
        except Exception as e:
            logger.error(f"Error toggling diagonal paths: {e}")
    
    def toggle_color_restriction(self):
        """Toggle color restriction visualization"""
        try:
            self.show_color_restriction = not self.show_color_restriction
        except Exception as e:
            logger.error(f"Error toggling color restriction: {e}")
    
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
                    "Watch the diagonal movement!",
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
            pygame.time.set_timer(pygame.USEREVENT + 2, 2500)
            
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
        """Complete the bishop movement module"""
        try:
            self.module_completed = True
            self.completion_timer = 0
            
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            
            # Create completion celebration
            for _ in range(50):
                try:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(200, 450)
                    self.celebration_particles.append({
                        'x': self.config.SCREEN_WIDTH // 2,
                        'y': self.config.SCREEN_HEIGHT // 2,
                        'vx': speed * math.cos(angle),
                        'vy': speed * math.sin(angle),
                        'color': random.choice([(255, 215, 0), (255, 255, 255), 
                                              self.config.COLORS.get('accent', (155, 89, 182)),
                                              self.config.COLORS.get('secondary', (46, 204, 113))]),
                        'life': 3.5,
                        'size': random.randint(4, 16)
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
            particle_count = 20 if self.exercise_type == 'pin_tactics' else 15
            
            for _ in range(particle_count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(120, 320)
                colors = [self.config.COLORS.get('accent', (155, 89, 182)), 
                         self.config.COLORS.get('secondary', (46, 204, 113)), 
                         (255, 255, 255), (255, 215, 0)]
                
                self.celebration_particles.append({
                    'x': self.config.SCREEN_WIDTH // 2,
                    'y': 350,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle),
                    'color': random.choice(colors),
                    'life': 2.0,
                    'size': random.randint(3, 9)
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
            #self.diagonal_button.handle_event(event)
            #self.color_button.handle_event(event)
            
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
                elif event.key == pygame.K_d:
                    self.toggle_diagonal_paths()
                elif event.key == pygame.K_c:
                    self.toggle_color_restriction()
                elif event.key == pygame.K_m and not self.show_feedback:
                    self.start_demonstration()
                elif event.key == pygame.K_s and self.total_attempts > 2:
                    self.skip_exercise()
            
            # Handle demonstration timer
            if event.type == pygame.USEREVENT + 2:
                self.demonstration_mode = False
                pygame.time.set_timer(pygame.USEREVENT + 2, 0)  # Cancel timer
                
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
            #self.diagonal_button.update(dt, mouse_pos)
            ##self.color_button.update(dt, mouse_pos)
            
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
                    particle['vy'] += 550 * dt  # Gravity
                    particle['life'] -= dt
                    particle['size'] = max(1, particle['size'] - dt * 2)
                    if particle['life'] <= 0:
                        self.celebration_particles.remove(particle)
                except Exception as e:
                    logger.warning(f"Error updating particle: {e}")
                    self.celebration_particles.remove(particle)
            
            # Update animations
            self.diagonal_animation += dt * 2.5
            if self.diagonal_animation > 2 * math.pi:
                self.diagonal_animation = 0
            
            self.color_pulse += dt * 3
            if self.color_pulse > 2 * math.pi:
                self.color_pulse = 0
            
            # Auto-advance after module completion
            if self.module_completed:
                self.completion_timer += dt
                if self.completion_timer > 6.0:
                    self.engine.change_state(GameState.MAIN_MENU)
                    
        except Exception as e:
            logger.error(f"Error in update: {e}")
    
    def render(self, screen):
        """Render the bishop movement training interface"""
        try:
            # Fill background
            screen.fill(self.config.COLORS['background'])
            
            # Render title
            title_surface = self.title_font.render("Learn Bishop Movement", True, self.config.COLORS['text_dark'])
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
                
                # Render diagonal path visualization if enabled
                if self.show_diagonal_paths and self.current_bishop_square is not None:
                    self.render_diagonal_overlay(screen)
                
                # Render color restriction visualization
                if self.show_color_restriction:
                    self.render_color_overlay(screen)
                    
            except Exception as e:
                logger.error(f"Error drawing chess board: {e}")
                error_surface = self.instruction_font.render("Error displaying board", True, 
                                                           self.config.COLORS.get('error', (255, 0, 0)))
                screen.blit(error_surface, error_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400)))
            
            # Render hint text
            if self.show_hint and not self.show_feedback:
                hint_surface = self.info_font.render("Valid bishop moves highlighted in yellow", 
                                                   True, self.config.COLORS['secondary'])
                screen.blit(hint_surface, hint_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 680)))
            
            # Render feedback message
            if self.feedback_message and not self.module_completed:
                color = (self.config.COLORS['secondary'] if any(word in self.feedback_message for word in 
                        ["Perfect", "Excellent", "Great", "Strong", "Correct"]) 
                        else self.config.COLORS.get('error', (255, 0, 0)))
                feedback_surface = self.instruction_font.render(self.feedback_message, True, color)
                screen.blit(feedback_surface, feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 620)))
            
            # Render UI buttons
            self.back_button.render(screen)
            self.hint_button.render(screen)
            #self.diagonal_button.render(screen)
            #self.color_button.render(screen)
            
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
    
    def render_diagonal_overlay(self, screen):
        """Render diagonal path visualization overlay"""
        try:
            if self.current_bishop_square is None:
                return
            
            bishop_pos = self.chess_board.get_square_center(self.current_bishop_square)
            if bishop_pos is None:
                return
            
            # Draw animated diagonal lines
            alpha = int(128 + 64 * math.sin(self.diagonal_animation))
            
            # Draw lines along all four diagonal directions
            for df, dr in self.diagonal_directions:
                try:
                    square_size = self.chess_board.square_size
                    line_length = min(4, 8 - max(abs(chess.square_file(self.current_bishop_square) + df * 4),
                                                 abs(chess.square_rank(self.current_bishop_square) + dr * 4)))
                    
                    end_x = bishop_pos[0] + df * line_length * square_size
                    end_y = bishop_pos[1] + dr * line_length * square_size
                    
                    # Draw diagonal line
                    pygame.draw.line(screen, (255, 255, 0, alpha), bishop_pos, (end_x, end_y), 4)
                    
                    # Draw arrow head
                    arrow_size = 10
                    angle = math.atan2(dr, df)
                    arrow_p1 = (end_x - arrow_size * math.cos(angle - 0.5),
                               end_y - arrow_size * math.sin(angle - 0.5))
                    arrow_p2 = (end_x - arrow_size * math.cos(angle + 0.5),
                               end_y - arrow_size * math.sin(angle + 0.5))
                    
                    pygame.draw.polygon(screen, (255, 255, 0, alpha), 
                                      [(end_x, end_y), arrow_p1, arrow_p2])
                        
                except Exception as e:
                    logger.warning(f"Error drawing diagonal line: {e}")
                    
        except Exception as e:
            logger.error(f"Error rendering diagonal overlay: {e}")
    
    def render_color_overlay(self, screen):
        """Render color restriction visualization"""
        try:
            alpha = int(80 + 40 * math.sin(self.color_pulse))
            
            # Highlight squares of the same color as bishop can reach
            if self.current_square_color is not None:
                for square in range(64):
                    if self.is_light_square(square) == self.current_square_color:
                        square_rect = self.chess_board.get_square_rect(square)
                        if square_rect:
                            overlay = pygame.Surface((square_rect.width, square_rect.height))
                            overlay.set_alpha(alpha)
                            overlay.fill((0, 255, 0))  # Green for reachable color
                            screen.blit(overlay, square_rect.topleft)
                    else:
                        # Show unreachable squares in red if highlighting is enabled
                        if self.highlight_unreachable:
                            square_rect = self.chess_board.get_square_rect(square)
                            if square_rect:
                                overlay = pygame.Surface((square_rect.width, square_rect.height))
                                overlay.set_alpha(alpha // 2)
                                overlay.fill((255, 0, 0))  # Red for unreachable color
                                screen.blit(overlay, square_rect.topleft)
                        
        except Exception as e:
            logger.error(f"Error rendering color overlay: {e}")
    
    def render_completion_screen(self, screen):
        """Render module completion screen"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            overlay.set_alpha(160)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Congratulations message
            success_font = pygame.font.Font(None, 72)
            success_surface = success_font.render("Bishop Master!", True, (255, 215, 0))
            screen.blit(success_surface, success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 200)))
            
            # Completion message
            complete_surface = self.title_font.render("You've mastered diagonal movement!", 
                                                    True, (255, 255, 255))
            screen.blit(complete_surface, complete_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 280)))
            
            # Statistics
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            stats = [
                f"Accuracy: {accuracy:.1f}%",
                f"Correct Moves: {self.correct_moves}/{self.total_attempts}",
                f"Diagonal Mastery: {sum(self.exercises_completed.values())} exercises completed"
            ]
            
            for i, stat in enumerate(stats):
                stat_surface = self.instruction_font.render(stat, True, (255, 255, 255))
                screen.blit(stat_surface, stat_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 350 + i * 40)))
            
            # Achievement message
            if accuracy >= 90:
                achievement = "Outstanding! You understand the power of the diagonal!"
            elif accuracy >= 75:
                achievement = "Excellent work! Bishops hold no more secrets!"
            else:
                achievement = "Good progress! Keep practicing diagonal patterns!"
            
            achievement_surface = self.info_font.render(achievement, True, self.config.COLORS['accent'])
            screen.blit(achievement_surface, achievement_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 500)))
            
            # Color restriction reminder
            color_reminder = "Remember: Bishops are forever bound to their starting square color!"
            reminder_surface = self.tip_font.render(color_reminder, True, (200, 200, 200))
            screen.blit(reminder_surface, reminder_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 540)))
            
        except Exception as e:
            logger.error(f"Error rendering completion screen: {e}")