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

class KingCheckState(BaseState):
    """Module for teaching king movement and check concepts - the heart of chess"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Module configuration based on fundamental chess concepts
            self.exercises_per_type = 4  # Multiple exercises for each critical concept
            self.movement_types = ['king_movement', 'check_recognition', 'check_responses', 'illegal_moves', 'checkmate_basics']
            
            # Progress tracking
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            self.exercises_completed = {move_type: 0 for move_type in self.movement_types}
            
            # Current exercise data
            self.current_king_square = None
            self.target_squares = []
            self.invalid_squares = []
            self.selected_square = None
            self.show_feedback = False
            self.feedback_timer = 0
            self.feedback_message = ""
            self.exercise_type = None
            self.show_hint = False
            
            # King and check specific learning aids
            self.show_king_safety = False
            self.show_attack_lines = False
            self.highlight_checks = False
            self.demonstration_mode = False
            self.checking_piece_square = None
            self.is_in_check = False
            
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
            
            # Instructions based on check fundamentals
            self.instructions = {
                'king_movement': "Kings move one square in any direction. Click a legal king move.",
                'check_recognition': "Identify when the king is in CHECK! Click the attacking piece.",
                'check_responses': "Get out of check: move king, block, or capture. Find the solution!",
                'illegal_moves': "Kings cannot move into check! Click only SAFE squares.",
                'checkmate_basics': "Checkmate = king in check with no escape. Find checkmate!"
            }
            
            # Learning tips for each type
            self.learning_tips = {
                'king_movement': "King moves 1 square in 8 directions - but never into danger!",
                'check_recognition': "Check = king under attack. You MUST respond immediately!",
                'check_responses': "3 ways out: 1) Move king 2) Block attack 3) Capture attacker",
                'illegal_moves': "Rule #1: King can NEVER move into check - it's illegal!",
                'checkmate_basics': "Checkmate ends the game - king in check with no legal moves"
            }
            
            # Fonts
            try:
                self.title_font = pygame.font.Font(None, 48)
                self.instruction_font = pygame.font.Font(None, 32)
                self.info_font = pygame.font.Font(None, 24)
                self.tip_font = pygame.font.Font(None, 20)
                self.warning_font = pygame.font.Font(None, 36)
            except Exception as e:
                logger.error(f"Failed to load fonts: {e}")
                self.title_font = pygame.font.SysFont('Arial', 48)
                self.instruction_font = pygame.font.SysFont('Arial', 32)
                self.info_font = pygame.font.SysFont('Arial', 24)
                self.tip_font = pygame.font.SysFont('Arial', 20)
                self.warning_font = pygame.font.SysFont('Arial', 36)
            
            # Animation elements
            self.animated_texts = []
            self.celebration_particles = []
            self.danger_animation = 0
            self.check_pulse = 0
            
            # Module completion
            self.module_completed = False
            self.completion_timer = 0
            
            # Session timer
            self.session_timer = Timer()
            
            # King movement directions (8 directions)
            self.king_directions = [(0, 1), (0, -1), (1, 0), (-1, 0),
                                  (1, 1), (1, -1), (-1, 1), (-1, -1)]
            
        except Exception as e:
            logger.error(f"Failed to initialize KingCheckState: {e}")
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
                pos=(self.config.SCREEN_WIDTH - 180, 150),
                size=(150, 40),
                callback=self.toggle_hint,
                config=self.config
            )
            
            #self.safety_button = Button(
            #    text="King Safety",
            #    pos=(self.config.SCREEN_WIDTH - 180, 100),
            #    size=(150, 40),
            #    callback=self.toggle_king_safety,
            #    config=self.config
            #)
            
            #self.attack_lines_button = Button(
            #    text="Attack Lines",
            #    pos=(self.config.SCREEN_WIDTH - 180, 150),
            #    size=(150, 40),
            #    callback=self.toggle_attack_lines,
            #    config=self.config
            #)
            
            #self.check_button = Button(
            #    text="Highlight Check",
            #    pos=(self.config.SCREEN_WIDTH - 180, 200),
            #    size=(150, 40),
            #    callback=self.toggle_highlight_checks,
            #    config=self.config
            #)
            
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
            #self.progress_bar.set_value(0)
            self.module_completed = False
            self.session_timer.reset()
            self.generate_exercise()
            
            try:
                self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
            except Exception as e:
                logger.warning(f"Failed to play learning music: {e}")
                
        except Exception as e:
            logger.error(f"Failed to enter KingCheckState: {e}")
            self.engine.change_state(GameState.MAIN_MENU)
    
    def get_king_moves(self, square, board=None):
        """Get all possible king moves from a square (not checking for safety)"""
        try:
            if square is None or not (0 <= square <= 63):
                return []
            
            if board is None:
                board = self.chess_board.board
            
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            moves = []
            
            # Check all 8 directions
            for df, dr in self.king_directions:
                new_file = file + df
                new_rank = rank + dr
                
                # Check if still on board
                if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                    new_square = chess.square(new_file, new_rank)
                    piece = board.piece_at(new_square)
                    
                    # Can move to empty square or capture enemy piece
                    if piece is None:
                        moves.append(new_square)
                    else:
                        king_piece = board.piece_at(square)
                        if king_piece and piece.color != king_piece.color:
                            moves.append(new_square)
            
            return moves
        except Exception as e:
            logger.error(f"Error calculating king moves: {e}")
            return []
    
    def is_square_attacked_by_color(self, square, attacking_color, board=None):
        """Check if a square is attacked by pieces of given color"""
        try:
            if board is None:
                board = self.chess_board.board
            
            # Check all squares for pieces of attacking_color
            for sq in range(64):
                piece = board.piece_at(sq)
                if piece and piece.color == attacking_color:
                    # Check if this piece can attack the target square
                    if self._piece_attacks_square(sq, square, piece, board):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking square attack: {e}")
            return False
    
    def _piece_attacks_square(self, from_square, to_square, piece, board):
        """Check if a piece can attack a specific square"""
        try:
            if from_square == to_square:
                return False
            
            from_file = chess.square_file(from_square)
            from_rank = chess.square_rank(from_square)
            to_file = chess.square_file(to_square)
            to_rank = chess.square_rank(to_square)
            
            df = to_file - from_file
            dr = to_rank - from_rank
            
            if piece.piece_type == chess.PAWN:
                # Pawn attacks diagonally
                direction = 1 if piece.color == chess.WHITE else -1
                return dr == direction and abs(df) == 1
            
            elif piece.piece_type == chess.KING:
                # King attacks adjacent squares
                return abs(df) <= 1 and abs(dr) <= 1
            
            elif piece.piece_type == chess.KNIGHT:
                # Knight attacks in L-shape
                return (abs(df) == 2 and abs(dr) == 1) or (abs(df) == 1 and abs(dr) == 2)
            
            elif piece.piece_type == chess.ROOK:
                # Rook attacks along ranks and files
                if df != 0 and dr != 0:
                    return False  # Not on same rank or file
                return self._is_path_clear(from_square, to_square, board)
            
            elif piece.piece_type == chess.BISHOP:
                # Bishop attacks along diagonals
                if abs(df) != abs(dr):
                    return False  # Not on same diagonal
                return self._is_path_clear(from_square, to_square, board)
            
            elif piece.piece_type == chess.QUEEN:
                # Queen combines rook and bishop
                if df == 0 or dr == 0 or abs(df) == abs(dr):
                    return self._is_path_clear(from_square, to_square, board)
                return False
            
            return False
        except Exception as e:
            logger.error(f"Error checking piece attack: {e}")
            return False
    
    def _is_path_clear(self, from_square, to_square, board):
        """Check if path between squares is clear"""
        try:
            from_file = chess.square_file(from_square)
            from_rank = chess.square_rank(from_square)
            to_file = chess.square_file(to_square)
            to_rank = chess.square_rank(to_square)
            
            df = to_file - from_file
            dr = to_rank - from_rank
            
            # Normalize direction
            step_f = 0 if df == 0 else (1 if df > 0 else -1)
            step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
            
            current_file = from_file + step_f
            current_rank = from_rank + step_r
            
            # Check each square along the path
            while current_file != to_file or current_rank != to_rank:
                check_square = chess.square(current_file, current_rank)
                if board.piece_at(check_square):
                    return False  # Path blocked
                current_file += step_f
                current_rank += step_r
            
            return True
        except Exception as e:
            logger.error(f"Error checking path clearance: {e}")
            return False
    
    def is_king_in_check(self, king_color, board=None):
        """Check if king of given color is in check"""
        try:
            if board is None:
                board = self.chess_board.board
            
            # Find the king
            king_square = None
            for sq in range(64):
                piece = board.piece_at(sq)
                if piece and piece.piece_type == chess.KING and piece.color == king_color:
                    king_square = sq
                    break
            
            if king_square is None:
                return False
            
            # Check if king is attacked by opposite color
            enemy_color = chess.BLACK if king_color == chess.WHITE else chess.WHITE
            return self.is_square_attacked_by_color(king_square, enemy_color, board)
        except Exception as e:
            logger.error(f"Error checking if king in check: {e}")
            return False
    
    def get_checking_pieces(self, king_color, board=None):
        """Get list of pieces that are checking the king"""
        try:
            if board is None:
                board = self.chess_board.board
            
            # Find the king
            king_square = None
            for sq in range(64):
                piece = board.piece_at(sq)
                if piece and piece.piece_type == chess.KING and piece.color == king_color:
                    king_square = sq
                    break
            
            if king_square is None:
                return []
            
            checking_pieces = []
            enemy_color = chess.BLACK if king_color == chess.WHITE else chess.WHITE
            
            # Check all enemy pieces
            for sq in range(64):
                piece = board.piece_at(sq)
                if piece and piece.color == enemy_color:
                    if self._piece_attacks_square(sq, king_square, piece, board):
                        checking_pieces.append(sq)
            
            return checking_pieces
        except Exception as e:
            logger.error(f"Error getting checking pieces: {e}")
            return []
    
    def generate_exercise(self):
        """Generate a new exercise"""
        try:
            self.show_feedback = False
            self.selected_square = None
            self.show_hint = False
            self.show_king_safety = False
            self.show_attack_lines = False
            self.highlight_checks = False
            self.demonstration_mode = False
            self.target_squares = []
            self.invalid_squares = []
            self.checking_piece_square = None
            self.is_in_check = False
            self.chess_board.clear_highlights()
            self.chess_board.select_square(None)
            
            if self.current_type_index < len(self.movement_types):
                self.exercise_type = self.movement_types[self.current_type_index]
            else:
                self.complete_module()
                return
                
            try:
                if self.exercise_type == 'king_movement':
                    self._generate_king_movement()
                elif self.exercise_type == 'check_recognition':
                    self._generate_check_recognition()
                elif self.exercise_type == 'check_responses':
                    self._generate_check_responses()
                elif self.exercise_type == 'illegal_moves':
                    self._generate_illegal_moves()
                elif self.exercise_type == 'checkmate_basics':
                    self._generate_checkmate_basics()
            except Exception as e:
                logger.error(f"Failed to generate {self.exercise_type} exercise: {e}")
                self.next_exercise()
                
        except Exception as e:
            logger.error(f"Failed to generate exercise: {e}")
            self.feedback_message = "Error generating exercise. Skipping..."
            self.next_exercise()
    
    def _generate_king_movement(self):
        """Generate basic king movement exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place king in center area for maximum mobility
            king_file = random.randint(2, 5)
            king_rank = random.randint(2, 5)
            king_square = chess.square(king_file, king_rank)
            
            self.chess_board.board.set_piece_at(king_square, chess.Piece(chess.KING, chess.WHITE))
            self.current_king_square = king_square
            
            # Get all possible king moves
            self.target_squares = self.get_king_moves(king_square)
            
            # Add some invalid squares (not adjacent)
            self.invalid_squares = []
            for _ in range(6):
                while True:
                    invalid_square = random.randint(0, 63)
                    if (invalid_square not in self.target_squares and 
                        invalid_square != king_square):
                        # Ensure it's not adjacent to king
                        inv_file = chess.square_file(invalid_square)
                        inv_rank = chess.square_rank(invalid_square)
                        if (abs(inv_file - king_file) > 1 or 
                            abs(inv_rank - king_rank) > 1):
                            self.invalid_squares.append(invalid_square)
                            break
            
            self.chess_board.highlight_square(king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate king movement exercise: {e}")
            raise
    
    def _generate_check_recognition(self):
        """Generate check recognition exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place white king
            king_square = chess.square(random.randint(2, 5), random.randint(2, 5))
            self.chess_board.board.set_piece_at(king_square, chess.Piece(chess.KING, chess.WHITE))
            self.current_king_square = king_square
            
            # Place a piece that checks the king
            checking_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
            checking_piece_type = random.choice(checking_pieces)
            
            # Find a position for the checking piece
            placed = False
            for _ in range(20):  # Try multiple positions
                check_square = chess.square(random.randint(0, 7), random.randint(0, 7))
                if check_square != king_square and not self.chess_board.board.piece_at(check_square):
                    # Test if this piece would check the king
                    test_piece = chess.Piece(checking_piece_type, chess.BLACK)
                    if self._piece_attacks_square(check_square, king_square, test_piece, self.chess_board.board):
                        self.chess_board.board.set_piece_at(check_square, test_piece)
                        self.checking_piece_square = check_square
                        placed = True
                        break
            
            if not placed:
                # Fallback: place queen next to king
                king_file = chess.square_file(king_square)
                king_rank = chess.square_rank(king_square)
                check_square = chess.square(min(7, king_file + 2), king_rank)
                self.chess_board.board.set_piece_at(check_square, chess.Piece(chess.QUEEN, chess.BLACK))
                self.checking_piece_square = check_square
            
            # Add some non-checking pieces as distractors
            distractor_squares = []
            for _ in range(3):
                distractor_square = chess.square(random.randint(0, 7), random.randint(0, 7))
                if (not self.chess_board.board.piece_at(distractor_square) and
                    distractor_square != king_square):
                    distractor_pieces = [chess.KNIGHT, chess.BISHOP, chess.ROOK]
                    distractor_piece = chess.Piece(random.choice(distractor_pieces), chess.BLACK)
                    # Only place if it doesn't check the king
                    if not self._piece_attacks_square(distractor_square, king_square, distractor_piece, self.chess_board.board):
                        self.chess_board.board.set_piece_at(distractor_square, distractor_piece)
                        distractor_squares.append(distractor_square)
            
            self.target_squares = [self.checking_piece_square] if self.checking_piece_square else []
            self.invalid_squares = distractor_squares
            self.is_in_check = True
            
            self.chess_board.highlight_square(king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate check recognition exercise: {e}")
            raise
    
    def _generate_check_responses(self):
        """Generate check response exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place white king in check
            king_square = chess.square(random.randint(1, 6), random.randint(1, 6))
            self.chess_board.board.set_piece_at(king_square, chess.Piece(chess.KING, chess.WHITE))
            self.current_king_square = king_square
            
            # Place checking piece
            king_file = chess.square_file(king_square)
            king_rank = chess.square_rank(king_square)
            
            # Place a rook checking from distance (easy to block/capture)
            check_square = chess.square(king_file, 0)  # Same file, different rank
            self.chess_board.board.set_piece_at(check_square, chess.Piece(chess.ROOK, chess.BLACK))
            self.checking_piece_square = check_square
            
            # Add friendly pieces that can help
            # Place a piece that can capture the checking piece
            capture_square = chess.square(0, 0)  # Corner square
            if not self.chess_board.board.piece_at(capture_square):
                self.chess_board.board.set_piece_at(capture_square, chess.Piece(chess.QUEEN, chess.WHITE))
            
            # Find valid responses to check
            response_squares = []
            
            # 1. King moves to safety
            king_moves = self.get_king_moves(king_square)
            for move_square in king_moves:
                if not self.is_square_attacked_by_color(move_square, chess.BLACK):
                    response_squares.append(move_square)
            
            # 2. Blocking squares
            block_squares = []
            for rank in range(1, king_rank):
                block_square = chess.square(king_file, rank)
                if not self.chess_board.board.piece_at(block_square):
                    block_squares.append(block_square)
            response_squares.extend(block_squares[:2])  # Add some blocking squares
            
            # 3. Capture the checking piece
            response_squares.append(check_square)
            
            self.target_squares = response_squares
            self.invalid_squares = [sq for sq in range(64) 
                                  if sq not in response_squares 
                                  and sq != king_square 
                                  and not self.chess_board.board.piece_at(sq)][:5]
            self.is_in_check = True
            
            self.chess_board.highlight_square(king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate check responses exercise: {e}")
            raise
    
    def _generate_illegal_moves(self):
        """Generate illegal moves exercise (king cannot move into check)"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place white king
            king_square = chess.square(random.randint(2, 5), random.randint(2, 5))
            self.chess_board.board.set_piece_at(king_square, chess.Piece(chess.KING, chess.WHITE))
            self.current_king_square = king_square
            
            # Place enemy pieces that control some squares around the king
            king_file = chess.square_file(king_square)
            king_rank = chess.square_rank(king_square)
            
            # Place enemy queen that controls some adjacent squares
            enemy_square = chess.square(min(7, king_file + 3), king_rank)
            self.chess_board.board.set_piece_at(enemy_square, chess.Piece(chess.QUEEN, chess.BLACK))
            
            # Place enemy bishop that controls diagonal squares
            bishop_square = chess.square(max(0, king_file - 3), max(0, king_rank - 3))
            if not self.chess_board.board.piece_at(bishop_square):
                self.chess_board.board.set_piece_at(bishop_square, chess.Piece(chess.BISHOP, chess.BLACK))
            
            # Find safe vs unsafe squares for king
            all_king_moves = self.get_king_moves(king_square)
            safe_squares = []
            unsafe_squares = []
            
            for move_square in all_king_moves:
                if self.is_square_attacked_by_color(move_square, chess.BLACK):
                    unsafe_squares.append(move_square)
                else:
                    safe_squares.append(move_square)
            
            self.target_squares = safe_squares
            self.invalid_squares = unsafe_squares
            
            self.chess_board.highlight_square(king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate illegal moves exercise: {e}")
            raise
    
    def _generate_checkmate_basics(self):
        """Generate basic checkmate recognition exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create a simple checkmate position
            # Back rank mate with queen and king
            king_square = chess.square(7, 0)  # Corner
            self.chess_board.board.set_piece_at(king_square, chess.Piece(chess.KING, chess.WHITE))
            self.current_king_square = king_square
            
            # Blocking pieces
            self.chess_board.board.set_piece_at(chess.square(6, 1), chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.square(7, 1), chess.Piece(chess.PAWN, chess.WHITE))
            
            # Enemy queen delivering checkmate
            queen_square = chess.square(7, 7)
            self.chess_board.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.BLACK))
            self.checking_piece_square = queen_square
            
            # This is checkmate - no legal moves
            self.target_squares = []  # No valid moves in checkmate
            self.invalid_squares = [chess.square(6, 0)]  # Show why this move is illegal
            self.is_in_check = True
            
            self.chess_board.highlight_square(king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate checkmate basics exercise: {e}")
            raise
    
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
            if self.exercise_type == 'king_movement':
                self.feedback_message = "Perfect! Kings move one square in any direction!"
            elif self.exercise_type == 'check_recognition':
                self.feedback_message = "Excellent! You found the piece giving check!"
            elif self.exercise_type == 'check_responses':
                self.feedback_message = "Great! That's a valid way to get out of check!"
            elif self.exercise_type == 'illegal_moves':
                self.feedback_message = "Smart! That square is safe for the king!"
            elif self.exercise_type == 'checkmate_basics':
                self.feedback_message = "Correct! This is checkmate - no legal moves!"
            
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
                points = 200 if self.exercise_type == 'checkmate_basics' else 120
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
            
            if self.selected_square == self.current_king_square:
                self.feedback_message = "Click where the king can move, not the king itself."
            elif self.exercise_type == 'king_movement':
                self.feedback_message = "Kings can only move one square adjacent! Try again."
            elif self.exercise_type == 'check_recognition':
                self.feedback_message = "That piece is not giving check. Look for the attacker!"
            elif self.exercise_type == 'check_responses':
                self.feedback_message = "That doesn't get out of check. Try moving king, blocking, or capturing!"
            elif self.exercise_type == 'illegal_moves':
                self.feedback_message = "DANGER! That square is attacked - kings cannot move into check!"
            elif self.exercise_type == 'checkmate_basics':
                if len(self.target_squares) == 0:
                    self.feedback_message = "This is checkmate! The king has no legal moves."
                else:
                    self.feedback_message = "Look for the checkmate move!"
            else:
                self.feedback_message = "Invalid move. Remember the king's safety rules!"
            
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
                if self.current_king_square is not None:
                    self.chess_board.highlight_square(self.current_king_square)
        except Exception as e:
            logger.error(f"Error toggling hint: {e}")
    
    def toggle_king_safety(self):
        """Toggle king safety visualization"""
        try:
            self.show_king_safety = not self.show_king_safety
        except Exception as e:
            logger.error(f"Error toggling king safety: {e}")
    
    def toggle_attack_lines(self):
        """Toggle attack line visualization"""
        try:
            self.show_attack_lines = not self.show_attack_lines
        except Exception as e:
            logger.error(f"Error toggling attack lines: {e}")
    
    def toggle_highlight_checks(self):
        """Toggle check highlighting"""
        try:
            self.highlight_checks = not self.highlight_checks
        except Exception as e:
            logger.error(f"Error toggling check highlighting: {e}")
    
    def start_demonstration(self):
        """Start movement demonstration"""
        try:
            if self.demonstration_mode:
                return
            
            self.demonstration_mode = True
            
            # Create demonstration based on exercise type
            if self.exercise_type == 'king_movement':
                demo_text = "Watch: King moves one square in any direction!"
            elif self.exercise_type == 'check_recognition':
                demo_text = "See: The red piece is attacking the king!"
            elif self.exercise_type == 'check_responses':
                demo_text = "Learn: 3 ways to escape check!"
            elif self.exercise_type == 'illegal_moves':
                demo_text = "Warning: Kings cannot move into danger!"
            else:
                demo_text = "Observe the king safety rules!"
            
            try:
                animated_text = AnimatedText(
                    demo_text,
                    (self.config.SCREEN_WIDTH // 2, 250),
                    32,
                    self.config.COLORS['accent'],
                    3.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create demo text: {e}")
            
            # Reset after delay
            pygame.time.set_timer(pygame.USEREVENT + 4, 3000)
            
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
        """Complete the king and check module"""
        try:
            self.module_completed = True
            self.completion_timer = 0
            
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            
            # Create royal completion celebration
            for _ in range(60):
                try:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(200, 500)
                    colors = [(255, 215, 0), (255, 255, 255), (255, 0, 0),  # Gold, White, Red
                             self.config.COLORS.get('accent', (155, 89, 182)),
                             self.config.COLORS.get('secondary', (46, 204, 113))]
                    self.celebration_particles.append({
                        'x': self.config.SCREEN_WIDTH // 2,
                        'y': self.config.SCREEN_HEIGHT // 2,
                        'vx': speed * math.cos(angle),
                        'vy': speed * math.sin(angle),
                        'color': random.choice(colors),
                        'life': 4.0,
                        'size': random.randint(5, 18)
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
            particle_count = 25 if self.exercise_type == 'checkmate_basics' else 18
            
            for _ in range(particle_count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(120, 350)
                colors = [self.config.COLORS.get('accent', (155, 89, 182)), 
                         self.config.COLORS.get('secondary', (46, 204, 113)), 
                         (255, 215, 0), (255, 255, 255)]
                
                self.celebration_particles.append({
                    'x': self.config.SCREEN_WIDTH // 2,
                    'y': 350,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle),
                    'color': random.choice(colors),
                    'life': 2.5,
                    'size': random.randint(4, 11)
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
            #self.safety_button.handle_event(event)
            #self.attack_lines_button.handle_event(event)
            #self.check_button.handle_event(event)
            
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
                elif event.key == pygame.K_k:
                    self.toggle_king_safety()
                elif event.key == pygame.K_a:
                    self.toggle_attack_lines()
                elif event.key == pygame.K_c:
                    self.toggle_highlight_checks()
                elif event.key == pygame.K_d and not self.show_feedback:
                    self.start_demonstration()
                elif event.key == pygame.K_s and self.total_attempts > 2:
                    self.skip_exercise()
            
            # Handle demonstration timer
            if event.type == pygame.USEREVENT + 4:
                self.demonstration_mode = False
                pygame.time.set_timer(pygame.USEREVENT + 4, 0)  # Cancel timer
                
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
            #self.safety_button.update(dt, mouse_pos)
            #self.attack_lines_button.update(dt, mouse_pos)
            #self.check_button.update(dt, mouse_pos)
            
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
            self.danger_animation += dt * 5
            if self.danger_animation > 2 * math.pi:
                self.danger_animation = 0
            
            self.check_pulse += dt * 6
            if self.check_pulse > 2 * math.pi:
                self.check_pulse = 0
            
            # Auto-advance after module completion
            if self.module_completed:
                self.completion_timer += dt
                if self.completion_timer > 6.0:
                    self.engine.change_state(GameState.MAIN_MENU)
                    
        except Exception as e:
            logger.error(f"Error in update: {e}")
    
    def render(self, screen):
        """Render the king and check training interface"""
        try:
            # Fill background
            screen.fill(self.config.COLORS['background'])
            
            # Render title
            title_surface = self.title_font.render("Learn King & Check - Chess Fundamentals", True, self.config.COLORS['text_dark'])
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
            
            # Render check warning if applicable
            if self.is_in_check:
                warning_surface = self.warning_font.render("⚠️ KING IN CHECK! ⚠️", True, (255, 0, 0))
                screen.blit(warning_surface, warning_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 175)))
            
            # Render chess board
            try:
                self.chess_board.draw()
                
                # Render special visualizations
                if self.current_king_square is not None:
                    if self.show_king_safety:
                        self.render_king_safety_overlay(screen)
                    if self.show_attack_lines and self.checking_piece_square:
                        self.render_attack_lines_overlay(screen)
                    if self.highlight_checks and self.is_in_check:
                        self.render_check_overlay(screen)
                    
            except Exception as e:
                logger.error(f"Error drawing chess board: {e}")
                error_surface = self.instruction_font.render("Error displaying board", True, 
                                                           self.config.COLORS.get('error', (255, 0, 0)))
                screen.blit(error_surface, error_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400)))
            
            # Render hint text
            if self.show_hint and not self.show_feedback:
                if self.exercise_type == 'check_recognition':
                    hint_text = "The checking piece is highlighted in yellow"
                elif self.exercise_type == 'illegal_moves':
                    hint_text = "Green squares are safe, avoid red squares!"
                else:
                    hint_text = "Valid moves highlighted in yellow"
                
                hint_surface = self.info_font.render(hint_text, True, self.config.COLORS['secondary'])
                screen.blit(hint_surface, hint_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 680)))
            
            # Render feedback message
            if self.feedback_message and not self.module_completed:
                color = (self.config.COLORS['secondary'] if any(word in self.feedback_message for word in 
                        ["Perfect", "Excellent", "Great", "Smart", "Correct"]) 
                        else self.config.COLORS.get('error', (255, 0, 0)))
                feedback_surface = self.instruction_font.render(self.feedback_message, True, color)
                screen.blit(feedback_surface, feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 620)))
            
            # Render UI buttons
            self.back_button.render(screen)
            self.hint_button.render(screen)
            #self.safety_button.render(screen)
            #self.attack_lines_button.render(screen)
            #self.check_button.render(screen)
            
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
    
    def render_king_safety_overlay(self, screen):
        """Render king safety zone visualization"""
        try:
            if self.current_king_square is None:
                return
            
            king_pos = self.chess_board.get_square_center(self.current_king_square)
            if king_pos is None:
                return
            
            # Draw safety zone around king
            alpha = int(60 + 30 * math.sin(self.danger_animation))
            
            # Show king's movement range
            for direction in self.king_directions:
                df, dr = direction
                king_file = chess.square_file(self.current_king_square)
                king_rank = chess.square_rank(self.current_king_square)
                new_file = king_file + df
                new_rank = king_rank + dr
                
                if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                    adj_square = chess.square(new_file, new_rank)
                    square_rect = self.chess_board.get_square_rect(adj_square)
                    if square_rect:
                        overlay = pygame.Surface((square_rect.width, square_rect.height))
                        overlay.set_alpha(alpha)
                        
                        # Green for safe, red for danger
                        if adj_square in self.invalid_squares:
                            overlay.fill((255, 0, 0))  # Red for danger
                        else:
                            overlay.fill((0, 255, 0))  # Green for safe
                        
                        screen.blit(overlay, square_rect.topleft)
                    
        except Exception as e:
            logger.error(f"Error rendering king safety overlay: {e}")
    
    def render_attack_lines_overlay(self, screen):
        """Render attack lines from checking piece to king"""
        try:
            if self.current_king_square is None or self.checking_piece_square is None:
                return
            
            king_pos = self.chess_board.get_square_center(self.current_king_square)
            checker_pos = self.chess_board.get_square_center(self.checking_piece_square)
            
            if king_pos is None or checker_pos is None:
                return
            
            # Draw animated attack line
            alpha = int(150 + 105 * math.sin(self.check_pulse))
            line_width = int(6 + 4 * math.sin(self.check_pulse))
            
            # Draw pulsing red line showing the attack
            pygame.draw.line(screen, (255, 0, 0, alpha), checker_pos, king_pos, line_width)
            
            # Draw arrow pointing to king
            angle = math.atan2(king_pos[1] - checker_pos[1], king_pos[0] - checker_pos[0])
            arrow_size = 15
            arrow_offset = 30
            
            arrow_tip_x = king_pos[0] - arrow_offset * math.cos(angle)
            arrow_tip_y = king_pos[1] - arrow_offset * math.sin(angle)
            
            arrow_p1 = (arrow_tip_x - arrow_size * math.cos(angle - 0.5),
                       arrow_tip_y - arrow_size * math.sin(angle - 0.5))
            arrow_p2 = (arrow_tip_x - arrow_size * math.cos(angle + 0.5),
                       arrow_tip_y - arrow_size * math.sin(angle + 0.5))
            
            pygame.draw.polygon(screen, (255, 0, 0, alpha), 
                              [(arrow_tip_x, arrow_tip_y), arrow_p1, arrow_p2])
                    
        except Exception as e:
            logger.error(f"Error rendering attack lines overlay: {e}")
    
    def render_check_overlay(self, screen):
        """Render check highlighting overlay"""
        try:
            if not self.is_in_check or self.current_king_square is None:
                return
            
            # Pulsing red overlay on king square
            alpha = int(100 + 80 * math.sin(self.check_pulse))
            king_rect = self.chess_board.get_square_rect(self.current_king_square)
            
            if king_rect:
                overlay = pygame.Surface((king_rect.width, king_rect.height))
                overlay.set_alpha(alpha)
                overlay.fill((255, 0, 0))
                screen.blit(overlay, king_rect.topleft)
            
            # Highlight checking piece
            if self.checking_piece_square is not None:
                checker_rect = self.chess_board.get_square_rect(self.checking_piece_square)
                if checker_rect:
                    overlay = pygame.Surface((checker_rect.width, checker_rect.height))
                    overlay.set_alpha(alpha // 2)
                    overlay.fill((255, 100, 0))  # Orange for checking piece
                    screen.blit(overlay, checker_rect.topleft)
                    
        except Exception as e:
            logger.error(f"Error rendering check overlay: {e}")
    
    def render_completion_screen(self, screen):
        """Render module completion screen"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            overlay.set_alpha(170)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Congratulations message
            success_font = pygame.font.Font(None, 72)
            success_surface = success_font.render("Chess Royalty!", True, (255, 215, 0))
            screen.blit(success_surface, success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 180)))
            
            # Completion message
            complete_surface = self.title_font.render("You've mastered the king and check!", 
                                                    True, (255, 255, 255))
            screen.blit(complete_surface, complete_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 250)))
            
            # Statistics
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            stats = [
                f"Accuracy: {accuracy:.1f}%",
                f"Correct Moves: {self.correct_moves}/{self.total_attempts}",
                f"Chess Fundamentals: {sum(self.exercises_completed.values())} exercises mastered"
            ]
            
            for i, stat in enumerate(stats):
                stat_surface = self.instruction_font.render(stat, True, (255, 255, 255))
                screen.blit(stat_surface, stat_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 320 + i * 40)))
            
            # Achievement message
            if accuracy >= 90:
                achievement = "Outstanding! You understand the heart of chess!"
            elif accuracy >= 75:
                achievement = "Excellent! The king's secrets are yours!"
            else:
                achievement = "Great progress! You're learning chess fundamentals!"
            
            achievement_surface = self.info_font.render(achievement, True, self.config.COLORS['accent'])
            screen.blit(achievement_surface, achievement_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 460)))
            
            # King and check summary
            summary_lines = [
                "King & Check Mastery Summary:",
                "• King moves 1 square in any direction",
                "• Check = king under attack, must respond!", 
                "• 3 ways out: move king, block, capture",
                "• Kings cannot move into check (illegal)",
                "• Checkmate = check with no escape",
                "• Protecting the king is chess goal #1!"
            ]
            
            for i, line in enumerate(summary_lines):
                color = (255, 215, 0) if i == 0 else (200, 200, 200)
                font = self.info_font if i == 0 else self.tip_font
                line_surface = font.render(line, True, color)
                screen.blit(line_surface, line_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 500 + i * 22)))
            
        except Exception as e:
            logger.error(f"Error rendering completion screen: {e}")