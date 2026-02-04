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

class CheckCheckmateStalemateState(BaseState):
    """Check, Checkmate, and Stalemate Training Module - Master Game Endings"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Enhanced module configuration with comprehensive progression
            self.exercises_per_type = 5  # Balanced practice for mastery
            self.scenario_types = [
                'check_recognition',        # Identify when king is in check
                'check_escape',            # Find ways to get out of check
                'checkmate_recognition',   # Identify checkmate positions
                'checkmate_delivery',      # Deliver checkmate in positions
                'stalemate_recognition',   # Identify stalemate positions
                'stalemate_avoidance',     # Avoid stalemate when winning
                'scenario_distinction'     # Distinguish between check/checkmate/stalemate
            ]
            
            # Comprehensive progress tracking
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            self.exercises_completed = {scenario_type: 0 for scenario_type in self.scenario_types}
            self.mastery_scores = {scenario_type: 0.0 for scenario_type in self.scenario_types}
            
            # Enhanced exercise state management
            self.selected_square = None
            self.show_feedback = False
            self.feedback_timer = 0
            self.feedback_message = ""
            self.exercise_type = None
            self.current_board_state = None
            
            # Progressive hint system
            self.hint_level = 0
            self.max_hint_levels = 4
            self.show_hints = False
            self.hint_progression = []
            self.hint_used_count = 0
            self.current_hint_text = ""
            
            # Visual learning aids
            self.show_escape_routes = False
            self.show_attack_lines = False
            self.show_safe_squares = False
            self.show_mate_threats = False
            self.animation_active = False
            self.animation_timer = 0
            
            # Game scenario state tracking
            self.target_squares = []
            self.valid_moves = []
            self.invalid_squares = []
            self.checking_pieces = []
            self.escape_squares = []
            self.blocking_squares = []
            self.capture_squares = []
            
            # Check/Checkmate/Stalemate specific state
            self.king_square = None
            self.king_color = None
            self.is_in_check = False
            self.is_checkmate = False
            self.is_stalemate = False
            self.scenario_answer = None  # 'check', 'checkmate', 'stalemate', 'none'
            self.escape_methods = []  # Available methods: 'move', 'block', 'capture'
            
            # Checkmate patterns recognition
            self.checkmate_pattern = None
            self.pattern_pieces = []
            
            # Educational content
            self.demonstration_mode = False
            self.auto_play_demo = False
            self.step_by_step_mode = False
            
            # Chess board with enhanced features
            try:
                self.chess_board = ChessBoard(
                    self.engine.screen,
                    self.engine.resource_manager,
                    board_size=500
                )
                self.chess_board.board_offset_x = (self.config.SCREEN_WIDTH - 500) // 2
                self.chess_board.board_offset_y = 160
            except Exception as e:
                logger.error(f"Failed to initialize chess board: {e}")
                raise
            
            # Create enhanced UI
            self.create_ui_elements()
            
            # Comprehensive instruction system
            self.instructions = {
                'check_recognition': {
                    'main': "Identify when the king is in check - under attack and must respond!",
                    'hints': [
                        "Look for pieces that can attack the king on this move",
                        "Check if any enemy piece has a clear path to the king",
                        "Remember: king is in check if it can be captured next move",
                        "Click 'Yes' if king is in check, 'No' if king is safe"
                    ]
                },
                'check_escape': {
                    'main': "Find the best way to escape from check - Move, Block, or Capture!",
                    'hints': [
                        "Three ways to escape check: move king, block attack, capture attacker",
                        "Moving the king to a safe square is often the simplest",
                        "Blocking with another piece can save the king",
                        "Capturing the attacking piece removes the threat"
                    ]
                },
                'checkmate_recognition': {
                    'main': "Recognize checkmate: King in check with NO way to escape!",
                    'hints': [
                        "King must be in check for it to be checkmate",
                        "Check if king can move to any safe square",
                        "See if the attack can be blocked by any piece",
                        "Verify that the attacking piece cannot be captured"
                    ]
                },
                'checkmate_delivery': {
                    'main': "Deliver checkmate! Find the move that ends the game!",
                    'hints': [
                        "Look for a move that puts the enemy king in check",
                        "Ensure the king cannot escape after your move",
                        "Check that the king has no safe squares",
                        "Verify that your attacking piece cannot be captured"
                    ]
                },
                'stalemate_recognition': {
                    'main': "Identify stalemate: King NOT in check but has NO legal moves!",
                    'hints': [
                        "Stalemate means no legal moves available for the side to move",
                        "The king must NOT be in check (that would be checkmate)",
                        "Check if any piece can make a legal move",
                        "Stalemate results in a draw, not a win"
                    ]
                },
                'stalemate_avoidance': {
                    'main': "Avoid stalemate! Find a move that maintains your winning advantage!",
                    'hints': [
                        "Give the opponent at least one legal move",
                        "Don't trap the king completely unless it's checkmate",
                        "Consider moves that maintain pressure without stalemate",
                        "Look for moves that keep the king in check or give it room"
                    ]
                },
                'scenario_distinction': {
                    'main': "Analyze the position: Is it Check, Checkmate, Stalemate, or None?",
                    'hints': [
                        "First, determine if the king is in check or not",
                        "If in check and can't escape: Checkmate",
                        "If not in check but no legal moves: Stalemate", 
                        "If king can move or attack can be stopped: just Check or normal position"
                    ]
                }
            }
            
            # Enhanced learning tips
            self.learning_tips = {
                'check_recognition': "Check = King in danger, must respond immediately!",
                'check_escape': "Remember: Move King, Block attack, or Capture attacker",
                'checkmate_recognition': "Checkmate = Check + No escape = Game Over!",
                'checkmate_delivery': "Look for forcing moves that leave the king trapped",
                'stalemate_recognition': "Stalemate = No check + No moves = Draw",
                'stalemate_avoidance': "When winning, always give opponent at least one move",
                'scenario_distinction': "Check the king's safety first, then count available moves"
            }
            
            # Common checkmate patterns for education
            self.checkmate_patterns = {
                'back_rank_mate': {
                    'name': 'Back Rank Mate',
                    'description': 'King trapped on back rank by own pawns',
                    'key_pieces': ['rook', 'queen']
                },
                'smothered_mate': {
                    'name': 'Smothered Mate', 
                    'description': 'Knight checkmates king surrounded by own pieces',
                    'key_pieces': ['knight']
                },
                'queen_mate': {
                    'name': 'Queen Mate',
                    'description': 'Queen delivers mate with king support',
                    'key_pieces': ['queen', 'king']
                },
                'rook_mate': {
                    'name': 'Rook Mate',
                    'description': 'Rook delivers mate with king support',
                    'key_pieces': ['rook', 'king']
                },
                'arabian_mate': {
                    'name': 'Arabian Mate',
                    'description': 'Rook and knight cooperate for corner mate',
                    'key_pieces': ['rook', 'knight']
                },
                'scholars_mate': {
                    'name': "Scholar's Mate",
                    'description': 'Quick attack on f7 square',
                    'key_pieces': ['queen', 'bishop']
                }
            }
            
            # Advanced feedback system
            self.feedback_history = []
            self.performance_metrics = {
                'accuracy': 0.0,
                'pattern_recognition': 0.0,
                'escape_success': 0.0,
                'mate_delivery': 0.0
            }
            
            # Font system
            try:
                self.title_font = pygame.font.Font(None, 48)
                self.subtitle_font = pygame.font.Font(None, 36)
                self.instruction_font = pygame.font.Font(None, 28)
                self.info_font = pygame.font.Font(None, 24)
                self.tip_font = pygame.font.Font(None, 20)
                self.hint_font = pygame.font.Font(None, 22)
            except Exception as e:
                logger.error(f"Failed to load fonts: {e}")
                # Fallback fonts
                self.title_font = pygame.font.SysFont('Arial', 48)
                self.subtitle_font = pygame.font.SysFont('Arial', 36)
                self.instruction_font = pygame.font.SysFont('Arial', 28)
                self.info_font = pygame.font.SysFont('Arial', 24)
                self.tip_font = pygame.font.SysFont('Arial', 20)
                self.hint_font = pygame.font.SysFont('Arial', 22)
            
            # Enhanced animation system
            self.animated_texts = []
            self.celebration_particles = []
            self.attack_line_particles = []
            self.visual_effects = {
                'check_pulse': 0,
                'mate_glow': 0,
                'stale_fade': 0,
                'escape_highlight': 0
            }
            
            # Module completion tracking
            self.module_completed = False
            self.completion_timer = 0
            self.final_score = 0.0
            
            # Session management
            self.session_timer = Timer()
            self.session_start_time = 0
            
            # Initialize first exercise
            self.reset_exercise_state()
            
        except Exception as e:
            logger.error(f"Failed to initialize CheckCheckmateStalemateState: {e}")
            raise
    
    def create_ui_elements(self):
        """Create comprehensive UI system"""
        try:
            total_exercises = len(self.scenario_types) * self.exercises_per_type
            
            # Enhanced progress bar
            #self.progress_bar = ProgressBar(
            #    pos=(self.config.SCREEN_WIDTH // 2 - 250, 25),
            #    size=(500, 30),
            #    max_value=total_exercises,
            #    config=self.config
            #)
            
            # Navigation buttons
            self.back_button = Button(
                text="← Back",
                pos=(50, 40),
                size=(120, 45),
                callback=self.on_back_clicked,
                config=self.config
            )
            
            # Learning aid buttons (left side)
            button_x = 50
            button_width = 140
            button_height = 35
            button_spacing = 45
            
            self.hint_button = Button(
                text="💡 Show Hints",
                pos=(button_x, 100),
                size=(button_width, button_height),
                callback=self.toggle_hints,
                config=self.config
            )
            
            self.escape_routes_button = Button(
                text="🚪 Escape Routes",
                pos=(button_x, 100 + button_spacing),
                size=(button_width, button_height),
                callback=self.toggle_escape_routes,
                config=self.config
            )
            
            self.attack_lines_button = Button(
                text="⚔️ Attack Lines",
                pos=(button_x, 100 + button_spacing * 2),
                size=(button_width, button_height),
                callback=self.toggle_attack_lines,
                config=self.config
            )
            
            self.safe_squares_button = Button(
                text="🛡️ Safe Squares",
                pos=(button_x, 100 + button_spacing * 3),
                size=(button_width, button_height),
                callback=self.toggle_safe_squares,
                config=self.config
            )
            
            self.demo_button = Button(
                text="▶️ Demo",
                pos=(button_x, 100 + button_spacing * 4),
                size=(button_width, button_height),
                callback=self.start_demonstration,
                config=self.config
            )
            
            # Control buttons (right side)
            control_x = self.config.SCREEN_WIDTH - 190
            
            self.reset_button = Button(
                text="🔄 Reset",
                pos=(control_x, 100),
                size=(button_width, button_height),
                callback=self.reset_exercise,
                config=self.config
            )
            
            self.skip_button = Button(
                text="⏭️ Skip",
                pos=(control_x, 100 + button_spacing),
                size=(button_width, button_height),
                callback=self.skip_exercise,
                config=self.config
            )
            
            self.analyze_button = Button(
                text="🔍 Analyze",
                pos=(control_x, 100 + button_spacing * 2),
                size=(button_width, button_height),
                callback=self.toggle_analysis_mode,
                config=self.config
            )
            
            # Answer buttons for recognition exercises (center)
            answer_y = 680
            answer_spacing = 180
            
            self.yes_button = Button(
                text="✅ YES",
                pos=(self.config.SCREEN_WIDTH // 2 - answer_spacing, answer_y),
                size=(120, 50),
                callback=lambda: self.handle_answer_button('yes'),
                config=self.config
            )
            
            self.no_button = Button(
                text="❌ NO", 
                pos=(self.config.SCREEN_WIDTH // 2 - 60, answer_y),
                size=(120, 50),
                callback=lambda: self.handle_answer_button('no'),
                config=self.config
            )
            
            self.check_button = Button(
                text="⚠️ CHECK",
                pos=(self.config.SCREEN_WIDTH // 2 - answer_spacing - 60, answer_y),
                size=(120, 50),
                callback=lambda: self.handle_answer_button('check'),
                config=self.config
            )
            
            self.checkmate_button = Button(
                text="💀 MATE",
                pos=(self.config.SCREEN_WIDTH // 2 - 60, answer_y),
                size=(120, 50),
                callback=lambda: self.handle_answer_button('checkmate'),
                config=self.config
            )
            
            self.stalemate_button = Button(
                text="🤝 STALEMATE",
                pos=(self.config.SCREEN_WIDTH // 2 + 60, answer_y),
                size=(120, 50),
                callback=lambda: self.handle_answer_button('stalemate'),
                config=self.config
            )
            
            self.none_button = Button(
                text="😐 NONE",
                pos=(self.config.SCREEN_WIDTH // 2 + answer_spacing, answer_y),
                size=(120, 50),
                callback=lambda: self.handle_answer_button('none'),
                config=self.config
            )
            
            # Main action button
            self.next_button = Button(
                text="Next Exercise →",
                pos=(self.config.SCREEN_WIDTH // 2 - 120, 680),
                size=(240, 50),
                callback=self.next_exercise,
                config=self.config
            )
            
            # Hint navigation buttons
            self.hint_prev_button = Button(
                text="← Prev Hint",
                pos=(self.config.SCREEN_WIDTH // 2 - 200, 630),
                size=(120, 35),
                callback=self.previous_hint,
                config=self.config
            )
            
            self.hint_next_button = Button(
                text="Next Hint →",
                pos=(self.config.SCREEN_WIDTH // 2 + 80, 630),
                size=(120, 35),
                callback=self.next_hint,
                config=self.config
            )
            
        except Exception as e:
            logger.error(f"Failed to create UI elements: {e}")
            raise
    
    def enter(self):
        """Enter the check/checkmate/stalemate training state"""
        try:
            super().enter()
            self.session_start_time = pygame.time.get_ticks()
            self.session_timer.reset()
            
            # Reset all progress
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            
            for scenario_type in self.scenario_types:
                self.exercises_completed[scenario_type] = 0
                self.mastery_scores[scenario_type] = 0.0
            
            #self.progress_bar.set_value(0)
            self.module_completed = False
            
            # Generate first exercise
            self.generate_exercise()
            
            # Start background music
            try:
                self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
            except Exception as e:
                logger.warning(f"Failed to play learning music: {e}")
                
        except Exception as e:
            logger.error(f"Failed to enter CheckCheckmateStalemateState: {e}")
            self.engine.change_state(GameState.MAIN_MENU)
    
    def reset_exercise_state(self):
        """Reset all exercise-specific state variables"""
        self.show_feedback = False
        self.selected_square = None
        self.hint_level = 0
        self.show_hints = False
        self.hint_progression = []
        self.hint_used_count = 0
        self.current_hint_text = ""
        self.show_escape_routes = False
        self.show_attack_lines = False
        self.show_safe_squares = False
        self.show_mate_threats = False
        self.animation_active = False
        self.animation_timer = 0
        self.demonstration_mode = False
        
        # Clear board highlights
        self.chess_board.clear_highlights()
        self.chess_board.select_square(None)
        
        # Reset game scenario state
        self.target_squares = []
        self.valid_moves = []
        self.invalid_squares = []
        self.checking_pieces = []
        self.escape_squares = []
        self.blocking_squares = []
        self.capture_squares = []
        self.king_square = None
        self.king_color = None
        self.is_in_check = False
        self.is_checkmate = False
        self.is_stalemate = False
        self.scenario_answer = None
        self.escape_methods = []
        self.checkmate_pattern = None
        self.pattern_pieces = []
    
    def generate_exercise(self):
        """Generate new exercise with enhanced setup and validation"""
        try:
            self.reset_exercise_state()
            
            if self.current_type_index < len(self.scenario_types):
                self.exercise_type = self.scenario_types[self.current_type_index]
            else:
                self.complete_module()
                return
            
            # Generate specific exercise type with validation
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    if self.exercise_type == 'check_recognition':
                        self._generate_check_recognition()
                    elif self.exercise_type == 'check_escape':
                        self._generate_check_escape()
                    elif self.exercise_type == 'checkmate_recognition':
                        self._generate_checkmate_recognition()
                    elif self.exercise_type == 'checkmate_delivery':
                        self._generate_checkmate_delivery()
                    elif self.exercise_type == 'stalemate_recognition':
                        self._generate_stalemate_recognition()
                    elif self.exercise_type == 'stalemate_avoidance':
                        self._generate_stalemate_avoidance()
                    elif self.exercise_type == 'scenario_distinction':
                        self._generate_scenario_distinction()
                    
                    # Validate the generated position
                    if self._validate_exercise():
                        break
                    else:
                        logger.warning(f"Invalid exercise generated, retrying ({attempt + 1}/{max_attempts})")
                        
                except Exception as e:
                    logger.error(f"Failed to generate {self.exercise_type} exercise: {e}")
                    if attempt == max_attempts - 1:
                        self.skip_exercise()
                        return
            
            # Setup hint progression for this exercise
            self._setup_hint_progression()
            
            # Store current board state for resets
            self.current_board_state = self.chess_board.board.copy()
            
            logger.info(f"Generated {self.exercise_type} exercise")
            
        except Exception as e:
            logger.error(f"Critical error in generate_exercise: {e}")
            self.skip_exercise()
    
    def _validate_exercise(self):
        """Validate that the generated exercise is proper and educational"""
        try:
            # Check basic requirements - must have both kings
            white_king_present = False
            black_king_present = False
            
            for square in chess.SQUARES:
                piece = self.chess_board.board.piece_at(square)
                if piece and piece.piece_type == chess.KING:
                    if piece.color == chess.WHITE:
                        white_king_present = True
                    else:
                        black_king_present = True
            
            if not (white_king_present and black_king_present):
                return False
            
            # Validate king square is set correctly
            if self.king_square is None:
                return False
                
            king_piece = self.chess_board.board.piece_at(self.king_square)
            if not king_piece or king_piece.piece_type != chess.KING:
                return False
                
            # Validate scenario-specific requirements
            if 'check' in self.exercise_type and not self.is_in_check:
                # Check exercises should have king in check
                return False
                
            if 'stalemate' in self.exercise_type and not self.is_stalemate:
                # Stalemate exercises should have stalemate position
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating exercise: {e}")
            return False
    
    def _generate_check_recognition(self):
        """Generate check recognition exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create scenarios where king may or may not be in check
            scenario = random.choice(['in_check', 'not_in_check'])
            
            # Always place both kings
            self.king_color = random.choice([chess.WHITE, chess.BLACK])
            
            if self.king_color == chess.WHITE:
                self.king_square = chess.E1
                other_king_square = chess.E8
            else:
                self.king_square = chess.E8
                other_king_square = chess.E1
                
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
            self.chess_board.board.set_piece_at(other_king_square, chess.Piece(chess.KING, not self.king_color))
            
            if scenario == 'in_check':
                # Place a piece that checks the king
                attacking_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
                attacking_piece_type = random.choice(attacking_pieces)
                
                # Find a square where this piece can check the king
                check_square = self._find_checking_square(attacking_piece_type, self.king_square, not self.king_color)
                if check_square:
                    self.chess_board.board.set_piece_at(check_square, chess.Piece(attacking_piece_type, not self.king_color))
                    self.checking_pieces = [check_square]
                    self.is_in_check = True
                    self.scenario_answer = 'yes'
                    
            else:
                # Place pieces that don't check the king
                safe_squares = self._find_safe_squares_for_pieces(self.king_square)
                piece_types = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]
                
                for _ in range(random.randint(2, 4)):
                    if safe_squares:
                        square = random.choice(safe_squares)
                        piece_type = random.choice(piece_types)
                        self.chess_board.board.set_piece_at(square, chess.Piece(piece_type, not self.king_color))
                        safe_squares.remove(square)
                        
                self.is_in_check = False
                self.scenario_answer = 'no'
            
            # Add some neutral pieces for context
            self._add_context_pieces()
            
            # Highlight the king being analyzed
            self.chess_board.highlight_square(self.king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate check recognition: {e}")
            raise
    
    def _generate_check_escape(self):
        """Generate check escape exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create a position where king is in check with escape options
            self.king_color = random.choice([chess.WHITE, chess.BLACK])
            
            if self.king_color == chess.WHITE:
                self.king_square = chess.E1
                other_king_square = chess.E8
            else:
                self.king_square = chess.E8
                other_king_square = chess.E1
                
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
            self.chess_board.board.set_piece_at(other_king_square, chess.Piece(chess.KING, not self.king_color))
            
            # Place attacking piece that checks the king
            attacking_piece_type = random.choice([chess.QUEEN, chess.ROOK, chess.BISHOP])
            check_square = self._find_checking_square(attacking_piece_type, self.king_square, not self.king_color)
            
            if check_square:
                self.chess_board.board.set_piece_at(check_square, chess.Piece(attacking_piece_type, not self.king_color))
                self.checking_pieces = [check_square]
                self.is_in_check = True
                
                # Determine available escape methods
                self.escape_methods = []
                
                # Check for king moves
                king_escapes = self._find_king_escape_squares(self.king_square)
                if king_escapes:
                    self.escape_methods.append('move')
                    self.escape_squares.extend(king_escapes)
                    self.target_squares.extend(king_escapes)
                
                # Check for blocking moves
                blocking_moves = self._find_blocking_squares(check_square, self.king_square)
                if blocking_moves:
                    self.escape_methods.append('block')
                    self.blocking_squares.extend(blocking_moves)
                    # Add friendly pieces that can block
                    for block_square in blocking_moves[:2]:  # Limit for clarity
                        friendly_piece = random.choice([chess.ROOK, chess.BISHOP, chess.KNIGHT])
                        piece_square = self._find_piece_that_can_reach(block_square, friendly_piece, self.king_color)
                        if piece_square:
                            self.chess_board.board.set_piece_at(piece_square, chess.Piece(friendly_piece, self.king_color))
                            self.target_squares.append(block_square)
                
                # Check for capture moves
                if self._can_capture_attacking_piece(check_square):
                    self.escape_methods.append('capture')
                    self.capture_squares = [check_square]
                    self.target_squares.append(check_square)
            
            # Add context pieces
            self._add_context_pieces()
            
            # Highlight the checked king
            self.chess_board.highlight_square(self.king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate check escape: {e}")
            raise
    
    def _generate_checkmate_recognition(self):
        """Generate checkmate recognition exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create checkmate or near-checkmate positions
            scenario = random.choice(['checkmate', 'not_checkmate'])
            
            self.king_color = random.choice([chess.WHITE, chess.BLACK])
            
            if scenario == 'checkmate':
                # Generate a basic checkmate pattern
                pattern = random.choice(['back_rank_mate', 'queen_mate', 'rook_mate'])
                self._create_checkmate_pattern(pattern)
                self.is_checkmate = True
                self.scenario_answer = 'yes'
            else:
                # Create a check position that looks like mate but isn't
                self._create_near_checkmate_position()
                self.is_checkmate = False
                self.scenario_answer = 'no'
            
            # Highlight the king being analyzed
            self.chess_board.highlight_square(self.king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate checkmate recognition: {e}")
            raise
    
    def _generate_checkmate_delivery(self):
        """Generate checkmate delivery exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create positions where player can deliver checkmate in one move
            pattern = random.choice(['back_rank_mate', 'queen_mate', 'smothered_mate'])
            
            self.king_color = chess.BLACK  # Player will checkmate black king
            self.king_square = chess.E8
            
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
            self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            
            if pattern == 'back_rank_mate':
                # Set up back rank mate scenario
                # Trapped king on back rank
                self.chess_board.board.set_piece_at(chess.F8, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.G8, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.H8, chess.Piece(chess.PAWN, chess.BLACK))
                
                # Rook that can deliver mate
                rook_square = chess.E2  # Will move to E8 for mate
                self.chess_board.board.set_piece_at(rook_square, chess.Piece(chess.ROOK, chess.WHITE))
                self.target_squares = [chess.E8]
                
            elif pattern == 'queen_mate':
                # Simple queen mate
                queen_square = chess.D7  # Will move to D8 for mate
                self.chess_board.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.WHITE))
                
                # Block escape squares
                self.chess_board.board.set_piece_at(chess.F8, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.F7, chess.Piece(chess.PAWN, chess.BLACK))
                
                self.target_squares = [chess.D8, chess.E7, chess.F7]  # Multiple mate options
                
            elif pattern == 'smothered_mate':
                # Knight smothered mate setup
                # Surround king with own pieces
                self.chess_board.board.set_piece_at(chess.D8, chess.Piece(chess.ROOK, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.F8, chess.Piece(chess.BISHOP, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.E7, chess.Piece(chess.PAWN, chess.BLACK))
                
                # Knight that can deliver mate
                knight_square = chess.D6
                self.chess_board.board.set_piece_at(knight_square, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.target_squares = [chess.F7]  # Knight to f7 is mate
            
            self.checkmate_pattern = pattern
            
            # Highlight attacking pieces
            for square in chess.SQUARES:
                piece = self.chess_board.board.piece_at(square)
                if piece and piece.color == chess.WHITE and piece.piece_type != chess.KING:
                    self.chess_board.highlight_square(square)
            
        except Exception as e:
            logger.error(f"Failed to generate checkmate delivery: {e}")
            raise
    
    def _generate_stalemate_recognition(self):
        """Generate stalemate recognition exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            scenario = random.choice(['stalemate', 'not_stalemate'])
            
            self.king_color = chess.BLACK  # Black to move
            
            if scenario == 'stalemate':
                # Create classic stalemate position
                self.king_square = chess.A8  # Black king trapped in corner
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.B6, chess.Piece(chess.KING, chess.WHITE))  # White king controls escape
                self.chess_board.board.set_piece_at(chess.C7, chess.Piece(chess.QUEEN, chess.WHITE))  # Queen blocks without checking
                
                self.is_stalemate = True
                self.scenario_answer = 'yes'
                
            else:
                # Create position that looks like stalemate but isn't
                self.king_square = chess.A8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.B6, chess.Piece(chess.KING, chess.WHITE))
                
                # Give black a legal move
                self.chess_board.board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, chess.BLACK))  # Pawn can move
                
                self.is_stalemate = False
                self.scenario_answer = 'no'
            
            # Add white king for valid position
            if not self.chess_board.board.piece_at(chess.B6):
                self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            
            # Highlight the potentially stalemated king
            self.chess_board.highlight_square(self.king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate stalemate recognition: {e}")
            raise
    
    def _generate_stalemate_avoidance(self):
        """Generate stalemate avoidance exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create winning position where player must avoid stalemate
            self.king_color = chess.BLACK  # Black king to avoid stalemating
            
            # Basic king and queen vs king endgame
            self.king_square = chess.A8  # Black king in corner
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.C6, chess.Piece(chess.KING, chess.WHITE))
            
            # Queen position where it can stalemate or give check
            queen_square = chess.B7
            self.chess_board.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.WHITE))
            
            # Target squares are moves that avoid stalemate
            # Good moves: Qb8+ (check), Qc7+ (check), King moves that give black room
            self.target_squares = [chess.B8, chess.C7, chess.C5, chess.D6]
            
            # Bad moves that cause stalemate
            self.invalid_squares = [chess.A7]  # This would be stalemate
            
            # Highlight the queen as the piece to move
            self.chess_board.highlight_square(queen_square)
            
        except Exception as e:
            logger.error(f"Failed to generate stalemate avoidance: {e}")
            raise
    
    def _generate_scenario_distinction(self):
        """Generate scenario distinction exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create various scenarios for analysis
            scenarios = ['check', 'checkmate', 'stalemate', 'none']
            scenario = random.choice(scenarios)
            
            self.king_color = random.choice([chess.WHITE, chess.BLACK])
            
            if scenario == 'check':
                self._create_check_position()
                self.scenario_answer = 'check'
            elif scenario == 'checkmate':
                self._create_checkmate_pattern('back_rank_mate')
                self.scenario_answer = 'checkmate'
            elif scenario == 'stalemate':
                self._create_stalemate_position()
                self.scenario_answer = 'stalemate'
            else:
                self._create_normal_position()
                self.scenario_answer = 'none'
            
            # Highlight the king being analyzed
            self.chess_board.highlight_square(self.king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate scenario distinction: {e}")
            raise
    
    # Helper methods for position creation
    def _find_checking_square(self, piece_type, king_square, attacking_color):
        """Find a square where a piece can check the king"""
        try:
            for square in chess.SQUARES:
                if square == king_square:
                    continue
                    
                # Check if this piece can attack the king from this square
                if self._can_piece_attack_square(piece_type, square, king_square, attacking_color):
                    # Make sure the square is empty or capturable
                    if not self.chess_board.board.piece_at(square):
                        return square
            return None
            
        except Exception as e:
            logger.error(f"Error finding checking square: {e}")
            return None
    
    def _can_piece_attack_square(self, piece_type, from_square, to_square, color):
        """Check if a piece can attack a target square"""
        try:
            if piece_type == chess.QUEEN:
                return self._queen_can_attack(from_square, to_square)
            elif piece_type == chess.ROOK:
                return self._rook_can_attack(from_square, to_square)
            elif piece_type == chess.BISHOP:
                return self._bishop_can_attack(from_square, to_square)
            elif piece_type == chess.KNIGHT:
                return self._knight_can_attack(from_square, to_square)
            elif piece_type == chess.PAWN:
                return self._pawn_can_attack(from_square, to_square, color)
            return False
            
        except Exception as e:
            logger.error(f"Error checking piece attack: {e}")
            return False
    
    def _queen_can_attack(self, from_square, to_square):
        """Check if queen can attack target"""
        return self._rook_can_attack(from_square, to_square) or self._bishop_can_attack(from_square, to_square)
    
    def _rook_can_attack(self, from_square, to_square):
        """Check if rook can attack target"""
        from_file = chess.square_file(from_square)
        from_rank = chess.square_rank(from_square)
        to_file = chess.square_file(to_square)
        to_rank = chess.square_rank(to_square)
        
        return (from_file == to_file or from_rank == to_rank) and self._is_path_clear(from_square, to_square)
    
    def _bishop_can_attack(self, from_square, to_square):
        """Check if bishop can attack target"""
        from_file = chess.square_file(from_square)
        from_rank = chess.square_rank(from_square)
        to_file = chess.square_file(to_square)
        to_rank = chess.square_rank(to_square)
        
        return abs(from_file - to_file) == abs(from_rank - to_rank) and self._is_path_clear(from_square, to_square)
    
    def _knight_can_attack(self, from_square, to_square):
        """Check if knight can attack target"""
        from_file = chess.square_file(from_square)
        from_rank = chess.square_rank(from_square)
        to_file = chess.square_file(to_square)
        to_rank = chess.square_rank(to_square)
        
        df = abs(from_file - to_file)
        dr = abs(from_rank - to_rank)
        
        return (df == 2 and dr == 1) or (df == 1 and dr == 2)
    
    def _pawn_can_attack(self, from_square, to_square, color):
        """Check if pawn can attack target"""
        from_file = chess.square_file(from_square)
        from_rank = chess.square_rank(from_square)
        to_file = chess.square_file(to_square)
        to_rank = chess.square_rank(to_square)
        
        direction = 1 if color == chess.WHITE else -1
        
        return abs(from_file - to_file) == 1 and (to_rank - from_rank) == direction
    
    def _is_path_clear(self, from_square, to_square):
        """Check if path between squares is clear"""
        try:
            from_file = chess.square_file(from_square)
            from_rank = chess.square_rank(from_square)
            to_file = chess.square_file(to_square)
            to_rank = chess.square_rank(to_square)
            
            df = to_file - from_file
            dr = to_rank - from_rank
            
            step_f = 0 if df == 0 else (1 if df > 0 else -1)
            step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
            
            current_file = from_file + step_f
            current_rank = from_rank + step_r
            
            while current_file != to_file or current_rank != to_rank:
                check_square = chess.square(current_file, current_rank)
                if self.chess_board.board.piece_at(check_square):
                    return False
                current_file += step_f
                current_rank += step_r
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking path clearance: {e}")
            return False
    
    def _find_safe_squares_for_pieces(self, king_square):
        """Find squares where pieces can be placed without checking the king"""
        safe_squares = []
        for square in chess.SQUARES:
            if square != king_square and not self.chess_board.board.piece_at(square):
                # Check if placing a piece here would check the king
                # Simplified check - just avoid obvious attacking squares
                if not self._square_attacks_king(square, king_square):
                    safe_squares.append(square)
        return safe_squares
    
    def _square_attacks_king(self, square, king_square):
        """Check if a square could attack the king"""
        # Simplified check for common pieces
        return (self._rook_can_attack(square, king_square) or 
                self._bishop_can_attack(square, king_square) or
                self._knight_can_attack(square, king_square))
    
    def _add_context_pieces(self):
        """Add neutral pieces to make position look realistic"""
        try:
            # Add some pawns and pieces that don't affect the main scenario
            context_pieces = [
                (chess.A2, chess.PAWN, chess.WHITE),
                (chess.B2, chess.PAWN, chess.WHITE),
                (chess.A7, chess.PAWN, chess.BLACK),
                (chess.B7, chess.PAWN, chess.BLACK),
            ]
            
            for square, piece_type, color in context_pieces:
                if not self.chess_board.board.piece_at(square):
                    self.chess_board.board.set_piece_at(square, chess.Piece(piece_type, color))
                    
        except Exception as e:
            logger.warning(f"Error adding context pieces: {e}")
    
    def _find_king_escape_squares(self, king_square):
        """Find squares where the king can escape"""
        escape_squares = []
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        # Check all adjacent squares
        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if df == 0 and dr == 0:
                    continue
                    
                new_file = king_file + df
                new_rank = king_rank + dr
                
                if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                    escape_square = chess.square(new_file, new_rank)
                    
                    # Check if square is empty or contains enemy piece
                    piece = self.chess_board.board.piece_at(escape_square)
                    if not piece or piece.color != self.king_color:
                        # Check if moving here would still be in check (simplified)
                        if not self._square_attacks_king(escape_square, escape_square):
                            escape_squares.append(escape_square)
        
        return escape_squares
    
    def _find_blocking_squares(self, attacker_square, king_square):
        """Find squares where pieces can block the attack"""
        blocking_squares = []
        
        # Find squares between attacker and king
        attacker_file = chess.square_file(attacker_square)
        attacker_rank = chess.square_rank(attacker_square)
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        df = king_file - attacker_file
        dr = king_rank - attacker_rank
        
        # Only works for straight lines (rook/queen/bishop attacks)
        if df != 0 and dr != 0 and abs(df) != abs(dr):
            return blocking_squares  # Not a straight line
        
        step_f = 0 if df == 0 else (1 if df > 0 else -1)
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        
        current_file = attacker_file + step_f
        current_rank = attacker_rank + step_r
        
        while current_file != king_file or current_rank != king_rank:
            blocking_square = chess.square(current_file, current_rank)
            blocking_squares.append(blocking_square)
            current_file += step_f
            current_rank += step_r
        
        return blocking_squares
    
    def _find_piece_that_can_reach(self, target_square, piece_type, color):
        """Find a square where a piece can be placed to reach the target"""
        # Simplified - place piece where it can reach target
        for square in chess.SQUARES:
            if not self.chess_board.board.piece_at(square):
                if self._can_piece_attack_square(piece_type, square, target_square, color):
                    return square
        return None
    
    def _can_capture_attacking_piece(self, attacker_square):
        """Check if the attacking piece can be captured"""
        # Add a friendly piece that can capture
        friendly_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
        piece_type = random.choice(friendly_pieces)
        
        capture_square = self._find_piece_that_can_reach(attacker_square, piece_type, self.king_color)
        if capture_square:
            self.chess_board.board.set_piece_at(capture_square, chess.Piece(piece_type, self.king_color))
            return True
        return False
    
    def _create_checkmate_pattern(self, pattern):
        """Create specific checkmate patterns"""
        try:
            if pattern == 'back_rank_mate':
                # Black king on back rank, trapped by own pawns
                self.king_square = chess.E8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
                self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, not self.king_color))
                
                # Pawns trapping king
                self.chess_board.board.set_piece_at(chess.F7, chess.Piece(chess.PAWN, self.king_color))
                self.chess_board.board.set_piece_at(chess.G7, chess.Piece(chess.PAWN, self.king_color))
                self.chess_board.board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, self.king_color))
                
                # Rook delivering checkmate
                self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.ROOK, not self.king_color))
                
                self.is_in_check = True
                self.is_checkmate = True
                self.checkmate_pattern = 'back_rank_mate'
                
            elif pattern == 'queen_mate':
                # Queen and king mate
                self.king_square = chess.H8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
                self.chess_board.board.set_piece_at(chess.F6, chess.Piece(chess.KING, not self.king_color))
                self.chess_board.board.set_piece_at(chess.G6, chess.Piece(chess.QUEEN, not self.king_color))
                
                self.is_in_check = True
                self.is_checkmate = True
                self.checkmate_pattern = 'queen_mate'
                
            elif pattern == 'rook_mate':
                # Rook and king mate
                self.king_square = chess.A8
                self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
                self.chess_board.board.set_piece_at(chess.B6, chess.Piece(chess.KING, not self.king_color))
                self.chess_board.board.set_piece_at(chess.A6, chess.Piece(chess.ROOK, not self.king_color))
                
                self.is_in_check = True
                self.is_checkmate = True
                self.checkmate_pattern = 'rook_mate'
                
        except Exception as e:
            logger.error(f"Error creating checkmate pattern: {e}")
    
    def _create_near_checkmate_position(self):
        """Create a position that looks like checkmate but has escape"""
        try:
            # Similar to checkmate but with one escape
            self.king_square = chess.E8
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
            self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, not self.king_color))
            
            # Rook checking, but king can escape
            self.chess_board.board.set_piece_at(chess.E2, chess.Piece(chess.ROOK, not self.king_color))
            
            # Only partially blocked - king can move to f8
            self.chess_board.board.set_piece_at(chess.G7, chess.Piece(chess.PAWN, self.king_color))
            self.chess_board.board.set_piece_at(chess.H7, chess.Piece(chess.PAWN, self.king_color))
            
            self.is_in_check = True
            self.is_checkmate = False
            
        except Exception as e:
            logger.error(f"Error creating near-checkmate: {e}")
    
    def _create_check_position(self):
        """Create a simple check position"""
        try:
            self.king_square = chess.E4
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
            self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, not self.king_color))
            
            # Rook checking with escape options
            self.chess_board.board.set_piece_at(chess.A4, chess.Piece(chess.ROOK, not self.king_color))
            
            self.is_in_check = True
            self.is_checkmate = False
            
        except Exception as e:
            logger.error(f"Error creating check position: {e}")
    
    def _create_stalemate_position(self):
        """Create a stalemate position"""
        try:
            # Classic stalemate
            self.king_square = chess.A8
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
            self.chess_board.board.set_piece_at(chess.B6, chess.Piece(chess.KING, not self.king_color))
            self.chess_board.board.set_piece_at(chess.C7, chess.Piece(chess.QUEEN, not self.king_color))
            
            self.is_in_check = False
            self.is_stalemate = True
            
        except Exception as e:
            logger.error(f"Error creating stalemate position: {e}")
    
    def _create_normal_position(self):
        """Create a normal position with no special conditions"""
        try:
            self.king_square = chess.E4
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, self.king_color))
            self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, not self.king_color))
            
            # Add some pieces that don't create special conditions
            self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, not self.king_color))
            self.chess_board.board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, not self.king_color))
            
            self.is_in_check = False
            self.is_checkmate = False
            self.is_stalemate = False
            
        except Exception as e:
            logger.error(f"Error creating normal position: {e}")
    
    def _setup_hint_progression(self):
        """Setup hint progression for current exercise"""
        try:
            if self.exercise_type in self.instructions:
                self.hint_progression = self.instructions[self.exercise_type]['hints'].copy()
            else:
                self.hint_progression = ["Analyze the position carefully", "Look for patterns", "Consider all possibilities"]
                
            self.hint_level = 0
            
            # Initialize first hint text
            if self.hint_progression:
                self.current_hint_text = self.hint_progression[0]
            else:
                self.current_hint_text = "Use the visual aids to help you"
            
        except Exception as e:
            logger.error(f"Error setting up hints: {e}")
            self.hint_progression = ["Look for patterns", "Analyze carefully"]
            self.current_hint_text = self.hint_progression[0]
    
    def handle_square_click(self, square):
        """Handle square click for move-based exercises"""
        try:
            if self.show_feedback or square is None or self.demonstration_mode:
                return
                
            # Only handle square clicks for exercises that require moves
            if self.exercise_type in ['check_escape', 'checkmate_delivery', 'stalemate_avoidance']:
                self.selected_square = square
                self.total_attempts += 1
                
                # Check if move is correct
                if square in self.target_squares:
                    self.on_correct_move()
                else:
                    self.on_incorrect_move()
                    
        except Exception as e:
            logger.error(f"Error handling square click: {e}")
    
    def handle_answer_button(self, answer):
        """Handle answer button clicks for recognition exercises"""
        try:
            if self.show_feedback or self.demonstration_mode:
                return
                
            # Only handle for recognition exercises
            if self.exercise_type in ['check_recognition', 'checkmate_recognition', 'stalemate_recognition', 'scenario_distinction']:
                self.total_attempts += 1
                
                # Check if answer is correct
                if answer == self.scenario_answer:
                    self.on_correct_move()
                else:
                    self.on_incorrect_move()
                    
        except Exception as e:
            logger.error(f"Error handling answer button: {e}")
    
    def on_correct_move(self):
        """Handle correct answer/move"""
        try:
            self.correct_moves += 1
            self.show_feedback = True
            self.feedback_timer = 0
            
            # Calculate score
            score_multiplier = max(0.3, 1.0 - (self.total_attempts - 1) * 0.2 - self.hint_used_count * 0.1)
            exercise_score = score_multiplier * 100
            
            # Update mastery score
            if self.exercise_type:
                current_mastery = self.mastery_scores[self.exercise_type]
                self.mastery_scores[self.exercise_type] = max(current_mastery, exercise_score)
            
            # Specific feedback messages
            feedback_messages = {
                'check_recognition': [
                    "Excellent! You correctly identified the check!",
                    "Perfect! You spotted the king in danger!",
                    "Outstanding recognition!"
                ],
                'check_escape': [
                    "Great escape! The king is now safe!",
                    "Perfect solution to get out of check!",
                    "Excellent defensive move!"
                ],
                'checkmate_recognition': [
                    "Perfect! You identified the checkmate correctly!",
                    "Excellent! The king truly has no escape!",
                    "Outstanding pattern recognition!"
                ],
                'checkmate_delivery': [
                    "Checkmate! Brilliantly executed!",
                    "Perfect! Game over for your opponent!",
                    "Excellent finishing move!"
                ],
                'stalemate_recognition': [
                    "Correct! You identified the stalemate!",
                    "Perfect! No legal moves but not in check!",
                    "Excellent understanding of stalemate!"
                ],
                'stalemate_avoidance': [
                    "Well done! You avoided the stalemate trap!",
                    "Perfect! Your opponent still has moves!",
                    "Excellent technique in winning positions!"
                ],
                'scenario_distinction': [
                    "Perfect analysis! You distinguished correctly!",
                    "Excellent! You identified the scenario properly!",
                    "Outstanding situational awareness!"
                ]
            }
            
            if self.exercise_type in feedback_messages:
                self.feedback_message = random.choice(feedback_messages[self.exercise_type])
            else:
                self.feedback_message = "Correct! Well done!"
            
            # Update progress
            if self.exercise_type:
                self.exercises_completed[self.exercise_type] += 1
                total_completed = sum(self.exercises_completed.values())
                #self.progress_bar.set_value(total_completed)
            
            # Audio and visual feedback
            try:
                success_sounds = ['success.wav', 'correct.wav', 'achievement.wav']
                sound = random.choice(success_sounds)
                self.engine.audio_manager.play_sound(sound)
            except Exception as e:
                logger.warning(f"Failed to play success sound: {e}")
            
            self.create_celebration_effect()
            
        except Exception as e:
            logger.error(f"Error in on_correct_move: {e}")
            self.feedback_message = "Correct! Great job!"
            self.show_feedback = True
    
    def on_incorrect_move(self):
        """Handle incorrect answer/move"""
        try:
            self.show_feedback = True
            self.feedback_timer = 0
            
            # Provide specific feedback
            feedback_messages = {
                'check_recognition': "Not quite! Look more carefully for pieces attacking the king.",
                'check_escape': "That doesn't solve the check! Try moving the king, blocking, or capturing.",
                'checkmate_recognition': "Not checkmate! The king still has escape options.",
                'checkmate_delivery': "That's not checkmate! Make sure the king has no escape.",
                'stalemate_recognition': "Not stalemate! Check if there are legal moves available.",
                'stalemate_avoidance': "That causes stalemate! Give your opponent at least one legal move.",
                'scenario_distinction': "Incorrect analysis! Check if the king is in check and count legal moves."
            }
            
            self.feedback_message = feedback_messages.get(self.exercise_type, "Not quite right. Try again!")
            
            # Audio feedback
            try:
                error_sounds = ['error.wav', 'wrong.wav', 'buzzer.wav']
                sound = random.choice(error_sounds)
                self.engine.audio_manager.play_sound(sound)
            except Exception as e:
                logger.warning(f"Failed to play error sound: {e}")
            
            # Suggest hint if multiple attempts
            if self.total_attempts >= 3 and not self.show_hints:
                self.feedback_message += " (Try using hints for guidance!)"
                
        except Exception as e:
            logger.error(f"Error in on_incorrect_move: {e}")
            self.feedback_message = "Not quite right. Try again!"
    
    def create_celebration_effect(self):
        """Create celebration particle effect"""
        try:
            particle_count = 30 if self.total_attempts == 1 else 20
            colors = [(255, 215, 0), (255, 255, 255), (0, 255, 0)]
            
            center_x = self.config.SCREEN_WIDTH // 2
            center_y = 350
            
            for _ in range(particle_count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(100, 300)
                
                self.celebration_particles.append({
                    'x': center_x,
                    'y': center_y,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle) - 50,
                    'color': random.choice(colors),
                    'life': random.uniform(2.0, 3.0),
                    'size': random.randint(4, 8),
                    'gravity': 200
                })
                
        except Exception as e:
            logger.warning(f"Failed to create celebration effect: {e}")
    
    # UI methods
    def toggle_hints(self):
        """Toggle hint display"""
        try:
            self.show_hints = not self.show_hints
            
            if self.show_hints:
                self.hint_used_count += 1
                if self.hint_progression and self.hint_level < len(self.hint_progression):
                    self.current_hint_text = self.hint_progression[self.hint_level]
            else:
                self.current_hint_text = ""
                
        except Exception as e:
            logger.error(f"Error toggling hints: {e}")
    
    def next_hint(self):
        """Show next hint"""
        try:
            if self.hint_level < len(self.hint_progression) - 1:
                self.hint_level += 1
                self.hint_used_count += 1
                if self.show_hints and self.hint_progression:
                    self.current_hint_text = self.hint_progression[self.hint_level]
                    
        except Exception as e:
            logger.error(f"Error showing next hint: {e}")
    
    def previous_hint(self):
        """Show previous hint"""
        try:
            if self.hint_level > 0:
                self.hint_level -= 1
                if self.show_hints and self.hint_progression:
                    self.current_hint_text = self.hint_progression[self.hint_level]
                    
        except Exception as e:
            logger.error(f"Error showing previous hint: {e}")
    
    def toggle_escape_routes(self):
        """Toggle escape route visualization"""
        self.show_escape_routes = not self.show_escape_routes
    
    def toggle_attack_lines(self):
        """Toggle attack line visualization"""
        self.show_attack_lines = not self.show_attack_lines
    
    def toggle_safe_squares(self):
        """Toggle safe square highlighting"""
        self.show_safe_squares = not self.show_safe_squares
    
    def toggle_analysis_mode(self):
        """Toggle analysis mode"""
        # Show additional information about the position
        self.show_escape_routes = True
        self.show_attack_lines = True
        self.show_safe_squares = True
    
    def start_demonstration(self):
        """Start demonstration mode"""
        try:
            self.demonstration_mode = True
            
            demo_messages = {
                'check_recognition': "Demo: Look for pieces that can capture the king!",
                'check_escape': "Demo: Three ways to escape - Move, Block, Capture!",
                'checkmate_recognition': "Demo: King in check with NO escape = Checkmate!",
                'checkmate_delivery': "Demo: Force the king into an inescapable trap!",
                'stalemate_recognition': "Demo: No legal moves but NOT in check = Stalemate!",
                'stalemate_avoidance': "Demo: Always give opponent a legal move when winning!",
                'scenario_distinction': "Demo: Analyze step by step - Check? Moves available?"
            }
            
            demo_text = demo_messages.get(self.exercise_type, "Watch the demonstration!")
            
            try:
                animated_text = AnimatedText(
                    demo_text,
                    (self.config.SCREEN_WIDTH // 2, 230),
                    32,
                    self.config.COLORS['accent'],
                    4.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create demo text: {e}")
            
            # Auto-disable after duration
            pygame.time.set_timer(pygame.USEREVENT + 7, 4000)
            
        except Exception as e:
            logger.error(f"Error starting demonstration: {e}")
            self.demonstration_mode = False
    
    def reset_exercise(self):
        """Reset current exercise"""
        try:
            if self.current_board_state:
                self.chess_board.board = self.current_board_state.copy()
                self.chess_board.clear_highlights()
                self.chess_board.select_square(None)
                
            self.show_feedback = False
            self.selected_square = None
            self.total_attempts = 0
            self.hint_level = 0
            self.show_hints = False
            self.hint_used_count = 0
            self.current_hint_text = ""
            
            # Re-setup hints
            self._setup_hint_progression()
            
            # Re-highlight key squares
            if self.king_square:
                self.chess_board.highlight_square(self.king_square)
                
        except Exception as e:
            logger.error(f"Error resetting exercise: {e}")
    
    def skip_exercise(self):
        """Skip current exercise"""
        try:
            if self.exercise_type:
                self.exercises_completed[self.exercise_type] += 1
                self.mastery_scores[self.exercise_type] = max(
                    self.mastery_scores[self.exercise_type], 30.0
                )
                
            self.next_exercise()
            
        except Exception as e:
            logger.error(f"Error skipping exercise: {e}")
            self.next_exercise()
    
    def next_exercise(self):
        """Move to next exercise"""
        try:
            self.current_exercise += 1
            
            # Check if current type is complete
            if self.exercise_type and self.exercises_completed[self.exercise_type] >= self.exercises_per_type:
                self.current_type_index += 1
                
                # Show completion message
                if self.current_type_index < len(self.scenario_types):
                    mastery = self.mastery_scores[self.exercise_type]
                    if mastery >= 80:
                        completion_msg = f"🎉 {self.exercise_type.replace('_', ' ').title()} MASTERED!"
                    elif mastery >= 60:
                        completion_msg = f"✅ {self.exercise_type.replace('_', ' ').title()} completed!"
                    else:
                        completion_msg = f"📚 {self.exercise_type.replace('_', ' ').title()} finished - review recommended"
                    
                    try:
                        animated_text = AnimatedText(
                            completion_msg,
                            (self.config.SCREEN_WIDTH // 2, 200),
                            36,
                            self.config.COLORS['secondary'],
                            3.0,
                            self.config
                        )
                        self.animated_texts.append(animated_text)
                    except Exception as e:
                        logger.warning(f"Failed to create completion text: {e}")
            
            # Check if module is complete
            if self.current_type_index >= len(self.scenario_types):
                self.complete_module()
            else:
                self.generate_exercise()
                
        except Exception as e:
            logger.error(f"Error moving to next exercise: {e}")
            self.complete_module()
    
    def complete_module(self):
        """Complete the module"""
        try:
            self.module_completed = True
            self.completion_timer = 0
            
            # Calculate final metrics
            total_exercises = sum(self.exercises_completed.values())
            accuracy = (self.correct_moves / max(self.total_attempts, 1)) * 100
            avg_mastery = sum(self.mastery_scores.values()) / len(self.mastery_scores)
            
            self.performance_metrics.update({
                'accuracy': accuracy,
                'pattern_recognition': avg_mastery,
                'escape_success': self.mastery_scores.get('check_escape', 0),
                'mate_delivery': self.mastery_scores.get('checkmate_delivery', 0)
            })
            
            self.final_score = accuracy * 0.6 + avg_mastery * 0.4
            
            # Epic celebration
            for _ in range(100):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(200, 500)
                colors = [(255, 215, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0)]
                
                self.celebration_particles.append({
                    'x': self.config.SCREEN_WIDTH // 2,
                    'y': self.config.SCREEN_HEIGHT // 2,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle),
                    'color': random.choice(colors),
                    'life': random.uniform(3.0, 5.0),
                    'size': random.randint(5, 15),
                    'gravity': 200
                })
            
            # Play completion sound
            try:
                self.engine.audio_manager.play_sound('victory.wav')
            except Exception as e:
                logger.warning(f"Failed to play completion sound: {e}")
                
        except Exception as e:
            logger.error(f"Error completing module: {e}")
            self.module_completed = True
    
    def on_back_clicked(self):
        """Handle back button click"""
        try:
            self.engine.change_state(GameState.MAIN_MENU)
        except Exception as e:
            logger.error(f"Error returning to main menu: {e}")
    
    def handle_event(self, event):
        """Handle events"""
        try:
            # UI button events
            self.back_button.handle_event(event)
            self.hint_button.handle_event(event)
            self.escape_routes_button.handle_event(event)
            self.attack_lines_button.handle_event(event)
            self.safe_squares_button.handle_event(event)
            self.reset_button.handle_event(event)
            self.analyze_button.handle_event(event)
            
            if not self.show_feedback:
                self.demo_button.handle_event(event)
                if self.total_attempts > 1:
                    self.skip_button.handle_event(event)
            
            # Answer buttons for recognition exercises
            if self.exercise_type in ['check_recognition', 'checkmate_recognition', 'stalemate_recognition']:
                if not self.show_feedback:
                    self.yes_button.handle_event(event)
                    self.no_button.handle_event(event)
            elif self.exercise_type == 'scenario_distinction':
                if not self.show_feedback:
                    self.check_button.handle_event(event)
                    self.checkmate_button.handle_event(event)
                    self.stalemate_button.handle_event(event)
                    self.none_button.handle_event(event)
            
            if self.show_feedback:
                self.next_button.handle_event(event)
            
            if self.show_hints:
                self.hint_prev_button.handle_event(event)
                self.hint_next_button.handle_event(event)
            
            # Mouse clicks on chess board for move-based exercises
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.exercise_type in ['check_escape', 'checkmate_delivery', 'stalemate_avoidance']:
                    try:
                        square = self.chess_board.get_square_from_pos(event.pos)
                        if square is not None:
                            self.handle_square_click(square)
                    except Exception as e:
                        logger.error(f"Error getting square from position: {e}")
            
            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.show_feedback:
                    self.next_exercise()
                elif event.key == pygame.K_h:
                    self.toggle_hints()
                elif event.key == pygame.K_r and not self.show_feedback:
                    self.reset_exercise()
                elif event.key == pygame.K_e:
                    self.toggle_escape_routes()
                elif event.key == pygame.K_a:
                    self.toggle_attack_lines()
                elif event.key == pygame.K_s:
                    self.toggle_safe_squares()
                elif event.key == pygame.K_d and not self.show_feedback:
                    self.start_demonstration()
                elif event.key == pygame.K_LEFT and self.show_hints:
                    self.previous_hint()
                elif event.key == pygame.K_RIGHT and self.show_hints:
                    self.next_hint()
                # Answer shortcuts for recognition exercises
                elif not self.show_feedback:
                    if event.key == pygame.K_y:
                        self.handle_answer_button('yes')
                    elif event.key == pygame.K_n:
                        self.handle_answer_button('no')
                    elif event.key == pygame.K_1:
                        self.handle_answer_button('check')
                    elif event.key == pygame.K_2:
                        self.handle_answer_button('checkmate')
                    elif event.key == pygame.K_3:
                        self.handle_answer_button('stalemate')
                    elif event.key == pygame.K_4:
                        self.handle_answer_button('none')
            
            # Timer events
            if event.type == pygame.USEREVENT + 7:
                self.demonstration_mode = False
                pygame.time.set_timer(pygame.USEREVENT + 7, 0)
                
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def update(self, dt):
        """Update game state"""
        try:
            super().update(dt)
            
            mouse_pos = pygame.mouse.get_pos()
            
            # Update UI elements
            self.back_button.update(dt, mouse_pos)
            self.hint_button.update(dt, mouse_pos)
            self.escape_routes_button.update(dt, mouse_pos)
            self.attack_lines_button.update(dt, mouse_pos)
            self.safe_squares_button.update(dt, mouse_pos)
            self.reset_button.update(dt, mouse_pos)
            self.analyze_button.update(dt, mouse_pos)
            
            if not self.show_feedback:
                self.demo_button.update(dt, mouse_pos)
                if self.total_attempts > 1:
                    self.skip_button.update(dt, mouse_pos)
            
            # Update answer buttons based on exercise type
            if self.exercise_type in ['check_recognition', 'checkmate_recognition', 'stalemate_recognition']:
                if not self.show_feedback:
                    self.yes_button.update(dt, mouse_pos)
                    self.no_button.update(dt, mouse_pos)
            elif self.exercise_type == 'scenario_distinction':
                if not self.show_feedback:
                    self.check_button.update(dt, mouse_pos)
                    self.checkmate_button.update(dt, mouse_pos)
                    self.stalemate_button.update(dt, mouse_pos)
                    self.none_button.update(dt, mouse_pos)
            
            if self.show_feedback:
                self.next_button.update(dt, mouse_pos)
            
            if self.show_hints:
                self.hint_prev_button.update(dt, mouse_pos)
                self.hint_next_button.update(dt, mouse_pos)
            
            # Update visual effects
            for effect_name in self.visual_effects:
                self.visual_effects[effect_name] += dt
                if self.visual_effects[effect_name] > 2 * math.pi:
                    self.visual_effects[effect_name] = 0
            
            # Update animated texts
            for text in self.animated_texts[:]:
                try:
                    text.update(dt)
                    if text.is_finished():
                        self.animated_texts.remove(text)
                except Exception as e:
                    logger.warning(f"Error updating animated text: {e}")
                    self.animated_texts.remove(text)
            
            # Update particles
            for particle in self.celebration_particles[:]:
                try:
                    particle['x'] += particle['vx'] * dt
                    particle['y'] += particle['vy'] * dt
                    particle['vy'] += particle.get('gravity', 200) * dt
                    particle['life'] -= dt
                    particle['size'] = max(1, particle['size'] - dt * 1.5)
                    
                    if particle['life'] <= 0:
                        self.celebration_particles.remove(particle)
                except Exception as e:
                    logger.warning(f"Error updating particle: {e}")
                    self.celebration_particles.remove(particle)
            
            # Update feedback timer
            if self.show_feedback and not self.module_completed:
                self.feedback_timer += dt
            
            # Auto-advance after module completion
            if self.module_completed:
                self.completion_timer += dt
                if self.completion_timer > 8.0:
                    self.engine.change_state(GameState.MAIN_MENU)
                    
        except Exception as e:
            logger.error(f"Error in update: {e}")
    
    def render(self, screen):
        """Render the game state"""
        try:
            # Fill background
            screen.fill(self.config.COLORS['background'])
            
            # Render title
            title_surface = self.title_font.render(
                "Master Chess Endings - Check, Checkmate & Stalemate", 
                True, self.config.COLORS['text_dark']
            )
            screen.blit(title_surface, title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 50)))
            
            # Render progress bar
            # self.progress_bar.render(screen)
            
            # Render current exercise info
            if not self.module_completed and self.exercise_type:
                # Exercise type and progress
                type_text = f"Exercise: {self.exercise_type.replace('_', ' ').title()}"
                progress_text = f"({self.exercises_completed[self.exercise_type] + 1}/{self.exercises_per_type})"
                
                type_surface = self.subtitle_font.render(type_text, True, self.config.COLORS['primary'])
                progress_surface = self.info_font.render(progress_text, True, self.config.COLORS['text_dark'])
                
                screen.blit(type_surface, type_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2 - 80, 90)))
                screen.blit(progress_surface, (self.config.SCREEN_WIDTH // 2 + 150, 85))
                
                # Main instruction
                main_instruction = self.instructions[self.exercise_type]['main']
                inst_surface = self.instruction_font.render(main_instruction, True, self.config.COLORS['text_dark'])
                screen.blit(inst_surface, inst_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 120)))
                
                # Learning tip
                tip = self.learning_tips.get(self.exercise_type, "")
                if tip:
                    tip_surface = self.tip_font.render(tip, True, self.config.COLORS['accent'])
                    screen.blit(tip_surface, tip_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 145)))
            
            # Render chess board
            try:
                self.chess_board.draw()
                
                # Render visual aids
                if self.show_escape_routes:
                    self._render_escape_routes(screen)
                if self.show_attack_lines:
                    self._render_attack_lines(screen)
                if self.show_safe_squares:
                    self._render_safe_squares(screen)
                    
            except Exception as e:
                logger.error(f"Error drawing chess board: {e}")
                error_surface = self.instruction_font.render(
                    "Error displaying board", True, self.config.COLORS.get('error', (255, 0, 0))
                )
                screen.blit(error_surface, error_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400)))
            
            # Render hint system
            if self.show_hints and self.current_hint_text:
                self._render_hint_system(screen)
            
            # Render feedback
            if self.feedback_message and not self.module_completed:
                color = (
                    self.config.COLORS['secondary'] 
                    if any(word in self.feedback_message for word in ["Perfect", "Excellent", "Great", "Outstanding", "Correct"])
                    else self.config.COLORS.get('error', (255, 0, 0))
                )
                feedback_surface = self.instruction_font.render(self.feedback_message, True, color)
                screen.blit(feedback_surface, feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 600)))
            
            # Render UI buttons
            self.back_button.render(screen)
            self.hint_button.render(screen)
            self.escape_routes_button.render(screen)
            self.attack_lines_button.render(screen)
            self.safe_squares_button.render(screen)
            self.reset_button.render(screen)
            self.analyze_button.render(screen)
            
            if not self.show_feedback:
                self.demo_button.render(screen)
                if self.total_attempts > 1:
                    self.skip_button.render(screen)
            
            # Render answer buttons based on exercise type
            if self.exercise_type in ['check_recognition', 'checkmate_recognition', 'stalemate_recognition']:
                if not self.show_feedback:
                    self.yes_button.render(screen)
                    self.no_button.render(screen)
            elif self.exercise_type == 'scenario_distinction':
                if not self.show_feedback:
                    self.check_button.render(screen)
                    self.checkmate_button.render(screen)
                    self.stalemate_button.render(screen)
                    self.none_button.render(screen)
            
            if self.show_feedback:
                self.next_button.render(screen)
            
            if self.show_hints:
                self.hint_prev_button.render(screen)
                self.hint_next_button.render(screen)
            
            # Render particles
            for particle in self.celebration_particles:
                try:
                    pygame.draw.circle(
                        screen, particle['color'],
                        (int(particle['x']), int(particle['y'])),
                        int(particle['size'])
                    )
                except Exception as e:
                    logger.warning(f"Error rendering particle: {e}")
            
            # Render animated texts
            for text in self.animated_texts:
                try:
                    text.render(screen)
                except Exception as e:
                    logger.warning(f"Error rendering animated text: {e}")
            
            # Render completion screen
            if self.module_completed:
                self._render_completion_screen(screen)
                
        except Exception as e:
            logger.error(f"Critical error in render: {e}")
            try:
                screen.fill((50, 50, 50))
                font = pygame.font.SysFont('Arial', 24)
                error_text = font.render("Rendering Error - Press Back", True, (255, 255, 255))
                screen.blit(error_text, (50, 50))
            except:
                pass
    
    def _render_escape_routes(self, screen):
        """Render king escape route visualization"""
        try:
            if not self.escape_squares:
                return
                
            alpha = int(100 + 50 * math.sin(self.visual_effects['escape_highlight'] * 3))
            
            for square in self.escape_squares:
                square_rect = self.chess_board.get_square_rect(square)
                if square_rect:
                    overlay = pygame.Surface((square_rect.width, square_rect.height))
                    overlay.set_alpha(alpha)
                    overlay.fill((0, 255, 0))  # Green for escape squares
                    screen.blit(overlay, square_rect.topleft)
                    
        except Exception as e:
            logger.warning(f"Error rendering escape routes: {e}")
    
    def _render_attack_lines(self, screen):
        """Render attack line visualization"""
        try:
            if not self.checking_pieces or not self.king_square:
                return
                
            for attacker_square in self.checking_pieces:
                king_rect = self.chess_board.get_square_rect(self.king_square)
                attacker_rect = self.chess_board.get_square_rect(attacker_square)
                
                if king_rect and attacker_rect:
                    # Draw attack line
                    pygame.draw.line(
                        screen, (255, 0, 0),
                        attacker_rect.center, king_rect.center, 4
                    )
                    
                    # Draw arrowhead
                    angle = math.atan2(
                        king_rect.centery - attacker_rect.centery,
                        king_rect.centerx - attacker_rect.centerx
                    )
                    arrow_length = 15
                    arrow_angle = 0.5
                    
                    end_pos = king_rect.center
                    arrow_p1 = (
                        end_pos[0] - arrow_length * math.cos(angle - arrow_angle),
                        end_pos[1] - arrow_length * math.sin(angle - arrow_angle)
                    )
                    arrow_p2 = (
                        end_pos[0] - arrow_length * math.cos(angle + arrow_angle),
                        end_pos[1] - arrow_length * math.sin(angle + arrow_angle)
                    )
                    
                    pygame.draw.polygon(screen, (255, 0, 0), [end_pos, arrow_p1, arrow_p2])
                    
        except Exception as e:
            logger.warning(f"Error rendering attack lines: {e}")
    
    def _render_safe_squares(self, screen):
        """Render safe square visualization"""
        try:
            if not self.target_squares:
                return
                
            alpha = int(80 + 40 * math.sin(self.visual_effects['check_pulse'] * 4))
            
            for square in self.target_squares:
                square_rect = self.chess_board.get_square_rect(square)
                if square_rect:
                    overlay = pygame.Surface((square_rect.width, square_rect.height))
                    overlay.set_alpha(alpha)
                    overlay.fill((0, 0, 255))  # Blue for safe/target squares
                    screen.blit(overlay, square_rect.topleft)
                    
        except Exception as e:
            logger.warning(f"Error rendering safe squares: {e}")
    
    def _render_hint_system(self, screen):
        """Render progressive hint system"""
        try:
            if not self.current_hint_text:
                return
            
            # Hint panel background
            panel_width = 600
            panel_height = 100
            panel_x = (self.config.SCREEN_WIDTH - panel_width) // 2
            panel_y = 520
            
            # Semi-transparent background
            hint_surface = pygame.Surface((panel_width, panel_height))
            hint_surface.set_alpha(220)
            hint_surface.fill((40, 40, 60))
            screen.blit(hint_surface, (panel_x, panel_y))
            
            # Border
            pygame.draw.rect(screen, self.config.COLORS['accent'], 
                           (panel_x, panel_y, panel_width, panel_height), 3)
            
            # Hint title
            hint_title = f"Hint {self.hint_level + 1}/{len(self.hint_progression)}"
            title_surface = self.info_font.render(hint_title, True, self.config.COLORS['accent'])
            screen.blit(title_surface, (panel_x + 20, panel_y + 10))
            
            # Current hint text
            hint_surface = self.hint_font.render(self.current_hint_text, True, (255, 255, 255))
            screen.blit(hint_surface, (panel_x + 20, panel_y + 35))
            
            # Hint navigation indicators
            if self.hint_level > 0:
                prev_text = "← Previous"
                prev_surface = self.tip_font.render(prev_text, True, (200, 200, 200))
                screen.blit(prev_surface, (panel_x + 20, panel_y + 65))
            
            if self.hint_level < len(self.hint_progression) - 1:
                next_text = "Next →"
                next_surface = self.tip_font.render(next_text, True, (200, 200, 200))
                next_rect = next_surface.get_rect()
                screen.blit(next_surface, (panel_x + panel_width - next_rect.width - 20, panel_y + 65))
                
        except Exception as e:
            logger.warning(f"Error rendering hint system: {e}")
    
    def _render_completion_screen(self, screen):
        """Render comprehensive module completion screen"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Main celebration message
            if self.final_score >= 90:
                main_message = "🏆 CHESS MASTER! 🏆"
                subtitle = "You've conquered Check, Checkmate & Stalemate!"
                color = (255, 215, 0)  # Gold
            elif self.final_score >= 75:
                main_message = "⭐ CHESS EXPERT! ⭐"
                subtitle = "Excellent mastery of chess endings!"
                color = (255, 255, 255)  # Silver
            elif self.final_score >= 60:
                main_message = "🎯 CHESS SCHOLAR! 🎯"
                subtitle = "Good understanding of game endings!"
                color = (205, 127, 50)  # Bronze
            else:
                main_message = "📚 CHESS STUDENT 📚"
                subtitle = "Keep practicing to master these concepts!"
                color = (100, 149, 237)  # Cornflower blue
            
            success_font = pygame.font.Font(None, 64)
            success_surface = success_font.render(main_message, True, color)
            screen.blit(success_surface, success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 140)))
            
            # Subtitle
            subtitle_surface = self.title_font.render(subtitle, True, (255, 255, 255))
            screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 200)))
            
            # Performance metrics
            metrics_y = 260
            metrics = [
                f"Final Score: {self.final_score:.1f}%",
                f"Overall Accuracy: {self.performance_metrics['accuracy']:.1f}%",
                f"Pattern Recognition: {self.performance_metrics['pattern_recognition']:.1f}%",
                f"Check Escape Skill: {self.performance_metrics['escape_success']:.1f}%",
                f"Checkmate Delivery: {self.performance_metrics['mate_delivery']:.1f}%",
                f"Total Time: {(pygame.time.get_ticks() - self.session_start_time) / 1000:.1f}s"
            ]
            
            for i, metric in enumerate(metrics):
                metric_surface = self.instruction_font.render(metric, True, (255, 255, 255))
                screen.blit(metric_surface, metric_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, metrics_y + i * 25)))
            
            # Individual mastery scores
            mastery_y = 420
            mastery_title = self.info_font.render("Mastery by Scenario:", True, (255, 255, 100))
            screen.blit(mastery_title, mastery_title.get_rect(center=(self.config.SCREEN_WIDTH // 2, mastery_y)))
            
            scenario_display_names = {
                'check_recognition': 'Check Recognition',
                'check_escape': 'Escaping Check',
                'checkmate_recognition': 'Checkmate Recognition',
                'checkmate_delivery': 'Delivering Checkmate',
                'stalemate_recognition': 'Stalemate Recognition',
                'stalemate_avoidance': 'Avoiding Stalemate',
                'scenario_distinction': 'Scenario Analysis'
            }
            
            col1_x = self.config.SCREEN_WIDTH // 2 - 150
            col2_x = self.config.SCREEN_WIDTH // 2 + 150
            
            for i, (scenario, score) in enumerate(self.mastery_scores.items()):
                if score > 0:
                    display_name = scenario_display_names.get(scenario, scenario.replace('_', ' ').title())
                    mastery_text = f"{display_name}: {score:.0f}%"
                    
                    # Color based on mastery level
                    if score >= 80:
                        scenario_color = (0, 255, 0)  # Green
                    elif score >= 60:
                        scenario_color = (255, 255, 0)  # Yellow
                    else:
                        scenario_color = (255, 165, 0)  # Orange
                    
                    mastery_surface = self.tip_font.render(mastery_text, True, scenario_color)
                    
                    # Alternate columns for better layout
                    x_pos = col1_x if i % 2 == 0 else col2_x
                    y_pos = mastery_y + 30 + (i // 2) * 18
                    
                    screen.blit(mastery_surface, mastery_surface.get_rect(center=(x_pos, y_pos)))
            
            # Key learning achievements
            achievements_y = 540
            achievement_title = self.info_font.render("Key Chess Concepts Mastered:", True, (255, 215, 0))
            screen.blit(achievement_title, achievement_title.get_rect(center=(self.config.SCREEN_WIDTH // 2, achievements_y)))
            
            achievements = [
                "✓ Check: Recognizing when the king is under attack",
                "✓ Escaping Check: Move, Block, or Capture strategies",
                "✓ Checkmate: Understanding when the game ends",
                "✓ Delivering Mate: Forcing decisive victories",
                "✓ Stalemate: Recognizing draw conditions",
                "✓ Endgame Technique: Avoiding stalemate traps",
                "✓ Position Analysis: Distinguishing game states"
            ]
            
            for i, achievement in enumerate(achievements):
                achievement_surface = self.tip_font.render(achievement, True, (200, 255, 200))
                screen.blit(achievement_surface, achievement_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, achievements_y + 25 + i * 16)))
            
            # Motivational message based on performance
            motivation_y = 680
            if self.final_score >= 90:
                motivation = "OUTSTANDING! You're ready for advanced chess tactics and strategy!"
            elif self.final_score >= 75:
                motivation = "EXCELLENT! You have solid mastery of fundamental chess endings!"
            elif self.final_score >= 60:
                motivation = "GOOD WORK! Continue practicing to perfect your endgame skills!"
            else:
                motivation = "KEEP LEARNING! These concepts are fundamental to chess success!"
            
            motivation_surface = self.info_font.render(motivation, True, self.config.COLORS['accent'])
            screen.blit(motivation_surface, motivation_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, motivation_y)))
            
            # Next steps recommendation
            next_steps_y = 710
            if self.final_score >= 80:
                next_steps = "Ready for: Advanced Tactics, Opening Principles, and Strategic Planning"
            elif self.final_score >= 60:
                next_steps = "Recommended: Review weak areas, then practice Basic Tactics"
            else:
                next_steps = "Suggested: Repeat this module and focus on piece movement fundamentals"
            
            next_steps_surface = self.tip_font.render(next_steps, True, (150, 200, 255))
            screen.blit(next_steps_surface, next_steps_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, next_steps_y)))
            
            # Auto-return message
            auto_return_surface = self.tip_font.render(
                "Returning to main menu automatically...", 
                True, (150, 150, 150)
            )
            screen.blit(auto_return_surface, auto_return_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 740)))
            
        except Exception as e:
            logger.error(f"Error rendering completion screen: {e}")
            # Fallback completion screen
            try:
                screen.fill((0, 0, 50))
                fallback_font = pygame.font.SysFont('Arial', 36)
                fallback_text = fallback_font.render("Check, Checkmate & Stalemate Module Complete!", True, (255, 255, 255))
                screen.blit(fallback_text, fallback_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2)))
            except:
                pass