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

class SpecialMovesState(BaseState):
    """Advanced Special Moves Training Module - En Passant & Castling Mastery"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Enhanced module configuration with progressive learning
            self.exercises_per_type = 5  # Balanced practice for mastery
            self.movement_types = [
                'castling_basics',
                'castling_requirements', 
                'castling_obstacles',
                'en_passant_recognition',
                'en_passant_execution',
                'special_moves_integration'
            ]
            
            # Comprehensive progress tracking
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            self.exercises_completed = {move_type: 0 for move_type in self.movement_types}
            self.mastery_scores = {move_type: 0.0 for move_type in self.movement_types}
            
            # Enhanced exercise state management
            self.selected_square = None
            self.show_feedback = False
            self.feedback_timer = 0
            self.feedback_message = ""
            self.exercise_type = None
            self.current_board_state = None
            
            # Fixed progressive hint system
            self.hint_level = 0
            self.max_hint_levels = 4
            self.show_hints = False
            self.hint_progression = []
            self.hint_used_count = 0
            self.current_hint_text = ""
            
            # Visual learning aids
            self.show_conditions = False
            self.show_move_paths = False
            self.show_legal_moves = False
            self.show_danger_zones = False
            self.animation_active = False
            self.animation_timer = 0
            self.animation_sequence = []
            
            # Special moves state tracking
            self.target_squares = []
            self.valid_moves = []
            self.invalid_squares = []
            self.blocked_squares = []
            
            # Castling specific state
            self.king_square = None
            self.rook_squares = []
            self.castling_side = None
            self.castling_legal = {'kingside': False, 'queenside': False}
            self.castling_blocked_reasons = []
            
            # En passant specific state (fixed variable name)
            self.en_passant_pawn = None
            self.capturing_pawn = None  # Fixed: was "capturing_pahn"
            self.en_passant_target = None
            self.en_passant_legal = False
            self.last_move_simulation = None
            
            # Enhanced UI elements
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
            
            # Comprehensive instruction system with better hints
            self.instructions = {
                'castling_basics': {
                    'main': "Learn castling fundamentals: King moves 2 squares toward rook, rook jumps over!",
                    'hints': [
                        "Click on the king to see where it can castle",
                        "Castling moves both king and rook in one special move",
                        "King moves exactly 2 squares toward the chosen rook",
                        "The rook 'jumps over' to the square the king crossed"
                    ]
                },
                'castling_requirements': {
                    'main': "Master castling rules: Check all conditions before castling!",
                    'hints': [
                        "Both king and rook must never have moved before",
                        "All squares between king and rook must be empty", 
                        "King cannot be in check when castling starts",
                        "King cannot pass through or land on an attacked square"
                    ]
                },
                'castling_obstacles': {
                    'main': "Identify what prevents castling in this position",
                    'hints': [
                        "Look carefully for pieces blocking the castling path",
                        "Check if any pieces have moved from their starting squares",
                        "See if the king is currently in check",
                        "Verify no enemy pieces attack the castling path"
                    ]
                },
                'en_passant_recognition': {
                    'main': "Spot en passant opportunities: Enemy pawn just moved 2 squares!",
                    'hints': [
                        "Look for enemy pawns that just moved 2 squares forward",
                        "Your pawn must be on the 5th rank adjacent to enemy pawn",
                        "En passant captures the pawn 'as it passes by'",
                        "Click the diagonal square the enemy pawn jumped over"
                    ]
                },
                'en_passant_execution': {
                    'main': "Execute en passant: Capture 'in passing' - it's your only chance!",
                    'hints': [
                        "Move your pawn diagonally to the empty square behind the enemy pawn",
                        "The enemy pawn will be removed from the board automatically",
                        "This special capture must be done immediately - can't wait!",
                        "Remember: you're capturing the pawn 'as it passes'"
                    ]
                },
                'special_moves_integration': {
                    'main': "Master both moves: Evaluate and choose the best special move!",
                    'hints': [
                        "Consider both castling and en passant possibilities",
                        "Think about king safety, piece development, and tactics",
                        "Evaluate which move gives you the biggest advantage",
                        "Sometimes multiple special moves are legal - choose wisely!"
                    ]
                }
            }
            
            # Enhanced learning tips with memory aids
            self.learning_tips = {
                'castling_basics': "Memory aid: 'King moves 2, Rook jumps through'",
                'castling_requirements': "Remember: K.I.N.G - King safe, In place, No blocks, Good squares",
                'castling_obstacles': "Common obstacles: pieces moved, path blocked, king in danger",
                'en_passant_recognition': "Key: Enemy pawn just moved 2 squares, now vulnerable!",
                'en_passant_execution': "Critical: Must capture immediately - next move or never!",
                'special_moves_integration': "Strategy: Which move improves your position most?"
            }
            
            # Advanced feedback system
            self.feedback_history = []
            self.performance_metrics = {
                'accuracy': 0.0,
                'hint_dependency': 0.0,
                'time_per_exercise': 0.0,
                'improvement_trend': 0.0
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
            self.move_trail_particles = []
            self.visual_effects = {
                'pulse_timer': 0,
                'glow_timer': 0,
                'highlight_timer': 0,
                'warning_timer': 0
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
            logger.error(f"Failed to initialize SpecialMovesState: {e}")
            raise
    
    def create_ui_elements(self):
        """Create comprehensive UI system"""
        try:
            total_exercises = len(self.movement_types) * self.exercises_per_type
            
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
            
            self.conditions_button = Button(
                text="📋 Rules",
                pos=(button_x, 100 + button_spacing),
                size=(button_width, button_height),
                callback=self.toggle_conditions,
                config=self.config
            )
            
            # self.paths_button = Button(
            #     text="🎯 Move Paths",
            #     pos=(button_x, 100 + button_spacing * 2),
            #     size=(button_width, button_height),
            #     callback=self.toggle_move_paths,
            #     config=self.config
            # )
            
            # self.legal_moves_button = Button(
            #     text="✅ Legal Moves",
            #     pos=(button_x, 100 + button_spacing * 3),
            #     size=(button_width, button_height),
            #     callback=self.toggle_legal_moves,
            #     config=self.config
            # )
            
            # self.demo_button = Button(
            #     text="▶️ Demo",
            #     pos=(button_x, 100 + button_spacing * 4),
            #     size=(button_width, button_height),
            #     callback=self.start_demonstration,
            #     config=self.config
            # )
            
            # Control buttons (right side)
            control_x = self.config.SCREEN_WIDTH - 190
            
            # self.reset_button = Button(
            #     text="🔄 Reset",
            #     pos=(control_x, 100),
            #     size=(button_width, button_height),
            #     callback=self.reset_exercise,
            #     config=self.config
            # )
            
            self.skip_button = Button(
                text="⏭️ Skip",
                pos=(control_x, 100 + button_spacing),
                size=(button_width, button_height),
                callback=self.skip_exercise,
                config=self.config
            )
            
            # self.step_mode_button = Button(
            #     text="👣 Step Mode",
            #     pos=(control_x, 100 + button_spacing * 2),
            #     size=(button_width, button_height),
            #     callback=self.toggle_step_mode,
            #     config=self.config
            # )
            
            # Main action button (center bottom)
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
        """Enter the special moves training state"""
        try:
            super().enter()
            self.session_start_time = pygame.time.get_ticks()
            self.session_timer.reset()
            
            # Reset all progress
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            
            for move_type in self.movement_types:
                self.exercises_completed[move_type] = 0
                self.mastery_scores[move_type] = 0.0
            
            # self.progress_bar.set_value(0)
            self.module_completed = False
            
            # Generate first exercise
            self.generate_exercise()
            
            # Start background music
            try:
                self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
            except Exception as e:
                logger.warning(f"Failed to play learning music: {e}")
                
        except Exception as e:
            logger.error(f"Failed to enter SpecialMovesState: {e}")
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
        self.show_conditions = False
        self.show_move_paths = False
        self.show_legal_moves = False
        self.show_danger_zones = False
        self.animation_active = False
        self.animation_timer = 0
        self.animation_sequence = []
        self.demonstration_mode = False
        self.step_by_step_mode = False
        
        # Clear board highlights
        self.chess_board.clear_highlights()
        self.chess_board.select_square(None)
        
        # Reset special moves state
        self.target_squares = []
        self.valid_moves = []
        self.invalid_squares = []
        self.blocked_squares = []
        self.king_square = None
        self.rook_squares = []
        self.castling_side = None
        self.castling_legal = {'kingside': False, 'queenside': False}
        self.castling_blocked_reasons = []
        self.en_passant_pawn = None
        self.capturing_pawn = None  # Fixed variable name
        self.en_passant_target = None
        self.en_passant_legal = False
        self.last_move_simulation = None
    
    def generate_exercise(self):
        """Generate new exercise with enhanced setup and validation"""
        try:
            self.reset_exercise_state()
            
            if self.current_type_index < len(self.movement_types):
                self.exercise_type = self.movement_types[self.current_type_index]
            else:
                self.complete_module()
                return
            
            # Generate specific exercise type with validation
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    if self.exercise_type == 'castling_basics':
                        self._generate_castling_basics()
                    elif self.exercise_type == 'castling_requirements':
                        self._generate_castling_requirements()
                    elif self.exercise_type == 'castling_obstacles':
                        self._generate_castling_obstacles()
                    elif self.exercise_type == 'en_passant_recognition':
                        self._generate_en_passant_recognition()
                    elif self.exercise_type == 'en_passant_execution':
                        self._generate_en_passant_execution()
                    elif self.exercise_type == 'special_moves_integration':
                        self._generate_special_moves_integration()
                    
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
            
            logger.info(f"Generated {self.exercise_type} exercise with {len(self.target_squares)} targets")
            
        except Exception as e:
            logger.error(f"Critical error in generate_exercise: {e}")
            self.skip_exercise()
    
    def _validate_exercise(self):
        """Validate that the generated exercise is proper and educational"""
        try:
            # Check basic requirements
            if not self.target_squares and self.exercise_type != 'castling_obstacles':
                return False
            
            # Ensure kings are present (required for valid chess position)
            white_king_present = False
            black_king_present = False
            
            for square in chess.SQUARES:
                piece = self.chess_board.board.piece_at(square)
                if piece:
                    if piece.piece_type == chess.KING:
                        if piece.color == chess.WHITE:
                            white_king_present = True
                        else:
                            black_king_present = True
            
            if not (white_king_present and black_king_present):
                return False
            
            # Validate castling exercises
            if 'castling' in self.exercise_type:
                if not self.king_square or not self.rook_squares:
                    return False
                    
                # Verify king is actually on king_square
                king_piece = self.chess_board.board.piece_at(self.king_square)
                if not king_piece or king_piece.piece_type != chess.KING:
                    return False
            
            # Validate en passant exercises
            if 'en_passant' in self.exercise_type:
                if not self.capturing_pawn or not self.en_passant_pawn:
                    return False
                    
                # Verify pawns are properly positioned
                capturing_piece = self.chess_board.board.piece_at(self.capturing_pawn)
                enemy_piece = self.chess_board.board.piece_at(self.en_passant_pawn)
                
                if not capturing_piece or capturing_piece.piece_type != chess.PAWN:
                    return False
                if not enemy_piece or enemy_piece.piece_type != chess.PAWN:
                    return False
                    
                # Check they're on the same rank
                if chess.square_rank(self.capturing_pawn) != chess.square_rank(self.en_passant_pawn):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating exercise: {e}")
            return False
    
    def _generate_castling_basics(self):
        """Generate basic castling exercise with proper setup"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Set up perfect castling position
            color = chess.WHITE
            
            # Always place both kings for valid position
            self.king_square = chess.E1
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, color))
            self.chess_board.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
            
            # Place rooks
            kingside_rook = chess.H1
            queenside_rook = chess.A1
            self.chess_board.board.set_piece_at(kingside_rook, chess.Piece(chess.ROOK, color))
            self.chess_board.board.set_piece_at(queenside_rook, chess.Piece(chess.ROOK, color))
            
            # Choose castling side
            self.castling_side = random.choice(['kingside', 'queenside'])
            self.castling_legal[self.castling_side] = True
            
            # Set target squares
            if self.castling_side == 'kingside':
                king_target = chess.G1
                rook_source = kingside_rook
                rook_target = chess.F1
                self.rook_squares = [kingside_rook]
            else:
                king_target = chess.C1
                rook_source = queenside_rook  
                rook_target = chess.D1
                self.rook_squares = [queenside_rook]
            
            # Valid moves include king target
            self.target_squares = [king_target]
            self.valid_moves = [
                chess.Move(self.king_square, king_target),
                chess.Move(rook_source, rook_target)
            ]
            
            # Add some reasonable distractors
            all_squares = list(range(64))
            occupied = [self.king_square, kingside_rook, queenside_rook, chess.E8]
            available = [sq for sq in all_squares if sq not in occupied + self.target_squares]
            self.invalid_squares = random.sample(available, min(6, len(available)))
            
            # Highlight king to guide player
            self.chess_board.highlight_square(self.king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate castling basics: {e}")
            raise
    
    def _generate_castling_requirements(self):
        """Generate castling requirements checking exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create various scenarios to test requirements
            scenarios = [
                'legal_both_sides',
                'pieces_blocking',
                'king_in_check',
                'through_check'
            ]
            
            scenario = random.choice(scenarios)
            color = chess.WHITE
            
            # Base position - always include both kings
            self.king_square = chess.E1
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, color))
            self.chess_board.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
            
            kingside_rook = chess.H1
            queenside_rook = chess.A1
            self.chess_board.board.set_piece_at(kingside_rook, chess.Piece(chess.ROOK, color))
            self.chess_board.board.set_piece_at(queenside_rook, chess.Piece(chess.ROOK, color))
            
            self.target_squares = []
            self.invalid_squares = []
            self.castling_blocked_reasons = []
            
            if scenario == 'legal_both_sides':
                # Both castling moves are legal
                self.castling_legal['kingside'] = True
                self.castling_legal['queenside'] = True
                self.target_squares = [chess.G1, chess.C1]
                
            elif scenario == 'pieces_blocking':
                # Add pieces blocking castling paths
                if random.choice([True, False]):
                    # Block kingside
                    self.chess_board.board.set_piece_at(chess.F1, chess.Piece(chess.BISHOP, color))
                    self.castling_blocked_reasons.append("Bishop blocks kingside castling")
                    self.blocked_squares = [chess.F1]
                    self.castling_legal['queenside'] = True
                    self.target_squares = [chess.C1]
                else:
                    # Block queenside
                    self.chess_board.board.set_piece_at(chess.D1, chess.Piece(chess.KNIGHT, color))
                    self.castling_blocked_reasons.append("Knight blocks queenside castling")
                    self.blocked_squares = [chess.D1]
                    self.castling_legal['kingside'] = True
                    self.target_squares = [chess.G1]
                    
            elif scenario == 'king_in_check':
                # King in check - no castling allowed
                self.chess_board.board.set_piece_at(chess.E3, chess.Piece(chess.ROOK, chess.BLACK))
                self.castling_blocked_reasons.append("King in check - cannot castle")
                self.invalid_squares = [chess.G1, chess.C1]
                
            elif scenario == 'through_check':
                # King would pass through check
                side = random.choice(['kingside', 'queenside'])
                if side == 'kingside':
                    self.chess_board.board.set_piece_at(chess.F3, chess.Piece(chess.ROOK, chess.BLACK))
                    self.castling_blocked_reasons.append("King would pass through check on f1")
                    self.invalid_squares = [chess.G1]
                    self.castling_legal['queenside'] = True
                    self.target_squares = [chess.C1]
                else:
                    self.chess_board.board.set_piece_at(chess.D3, chess.Piece(chess.ROOK, chess.BLACK))
                    self.castling_blocked_reasons.append("King would pass through check on d1")
                    self.invalid_squares = [chess.C1]
                    self.castling_legal['kingside'] = True
                    self.target_squares = [chess.G1]
            
            # Add reasonable distractors
            all_squares = list(range(64))
            occupied = [sq for sq in all_squares if self.chess_board.board.piece_at(sq)]
            available = [sq for sq in all_squares if sq not in occupied + self.target_squares + self.invalid_squares]
            additional_invalid = random.sample(available, min(4, len(available)))
            self.invalid_squares.extend(additional_invalid)
            
            self.rook_squares = [kingside_rook, queenside_rook]
            self.chess_board.highlight_square(self.king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate castling requirements: {e}")
            raise
    
    def _generate_castling_obstacles(self):
        """Generate exercise identifying castling obstacles"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create position with clear obstacles
            color = chess.WHITE
            self.king_square = chess.E1
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, color))
            self.chess_board.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
            
            kingside_rook = chess.H1
            queenside_rook = chess.A1
            self.chess_board.board.set_piece_at(kingside_rook, chess.Piece(chess.ROOK, color))
            self.chess_board.board.set_piece_at(queenside_rook, chess.Piece(chess.ROOK, color))
            
            # Add specific obstacles
            obstacles = []
            obstacle_type = random.choice(['blocking_piece', 'king_in_check', 'path_attacked'])
            
            if obstacle_type == 'blocking_piece':
                # Add a piece that blocks castling
                if random.choice([True, False]):
                    # Block kingside
                    block_square = random.choice([chess.F1, chess.G1])
                    self.chess_board.board.set_piece_at(block_square, chess.Piece(chess.BISHOP, color))
                    obstacles.append(f"Piece blocking {chess.square_name(block_square)}")
                    self.blocked_squares = [block_square]
                    self.invalid_squares = [chess.G1]
                    self.target_squares = [chess.C1]  # Queenside still legal
                else:
                    # Block queenside
                    block_square = random.choice([chess.B1, chess.C1, chess.D1])
                    self.chess_board.board.set_piece_at(block_square, chess.Piece(chess.KNIGHT, color))
                    obstacles.append(f"Piece blocking {chess.square_name(block_square)}")
                    self.blocked_squares = [block_square]
                    self.invalid_squares = [chess.C1]
                    self.target_squares = [chess.G1]  # Kingside still legal
                    
            elif obstacle_type == 'king_in_check':
                # King is in check
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.ROOK, chess.BLACK))
                obstacles.append("King is in check")
                self.invalid_squares = [chess.G1, chess.C1]  # No castling allowed
                self.target_squares = []
                
            elif obstacle_type == 'path_attacked':
                # Castling path is attacked
                if random.choice([True, False]):
                    # Attack kingside path
                    self.chess_board.board.set_piece_at(chess.F4, chess.Piece(chess.ROOK, chess.BLACK))
                    obstacles.append("Kingside path is under attack")
                    self.invalid_squares = [chess.G1]
                    self.target_squares = [chess.C1]  # Queenside still legal
                else:
                    # Attack queenside path
                    self.chess_board.board.set_piece_at(chess.D4, chess.Piece(chess.ROOK, chess.BLACK))
                    obstacles.append("Queenside path is under attack")
                    self.invalid_squares = [chess.C1]
                    self.target_squares = [chess.G1]  # Kingside still legal
            
            self.castling_blocked_reasons = obstacles
            self.rook_squares = [kingside_rook, queenside_rook]
            self.chess_board.highlight_square(self.king_square)
            
        except Exception as e:
            logger.error(f"Failed to generate castling obstacles: {e}")
            raise
    
    def _generate_en_passant_recognition(self):
        """Generate en passant recognition exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Set up en passant opportunity with complete position
            # Place kings first
            self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
            
            # White pawn on 5th rank (index 4)
            capturing_file = random.randint(1, 6)  # b-g files to avoid edges
            self.capturing_pawn = chess.square(capturing_file, 4)  # 5th rank
            self.chess_board.board.set_piece_at(self.capturing_pawn, chess.Piece(chess.PAWN, chess.WHITE))
            
            # Black pawn that "just moved" 2 squares (now on 5th rank)
            enemy_file = capturing_file + random.choice([-1, 1])  # Adjacent file
            if enemy_file < 0 or enemy_file > 7:  # Safety check
                enemy_file = capturing_file + (1 if capturing_file > 3 else -1)
                
            self.en_passant_pawn = chess.square(enemy_file, 4)  # Same rank as capturing pawn
            self.chess_board.board.set_piece_at(self.en_passant_pawn, chess.Piece(chess.PAWN, chess.BLACK))
            
            # En passant target square (6th rank for White)
            self.en_passant_target = chess.square(enemy_file, 5)  # 6th rank
            self.en_passant_legal = True
            
            # Simulate that this was the last move (2-square pawn advance)
            self.last_move_simulation = chess.Move(chess.square(enemy_file, 6), self.en_passant_pawn)
            
            # Target is the en passant capture square
            self.target_squares = [self.en_passant_target]
            self.valid_moves = [chess.Move(self.capturing_pawn, self.en_passant_target)]
            
            # Add educational distractors
            normal_pawn_move = chess.square(capturing_file, 5)  # Normal forward move
            if not self.chess_board.board.piece_at(normal_pawn_move):
                self.invalid_squares = [normal_pawn_move]
            
            # Can't capture pawn directly
            self.invalid_squares.append(self.en_passant_pawn)
            
            # Add some other pawns for context
            context_pawns = [
                (chess.square(2, 1), chess.PAWN, chess.WHITE),  # c2
                (chess.square(5, 1), chess.PAWN, chess.WHITE),  # f2
                (chess.square(3, 6), chess.PAWN, chess.BLACK),  # d7
                (chess.square(4, 6), chess.PAWN, chess.BLACK),  # e7
            ]
            
            for square, piece_type, color in context_pawns:
                if not self.chess_board.board.piece_at(square) and square != self.capturing_pawn and square != self.en_passant_pawn:
                    self.chess_board.board.set_piece_at(square, chess.Piece(piece_type, color))
            
            # Add more distractors from empty squares
            all_squares = list(range(64))
            occupied = [sq for sq in all_squares if self.chess_board.board.piece_at(sq)]
            available = [sq for sq in all_squares if sq not in occupied + self.target_squares + self.invalid_squares]
            additional_invalid = random.sample(available, min(4, len(available)))
            self.invalid_squares.extend(additional_invalid)
            
            self.chess_board.highlight_square(self.capturing_pawn)
            
        except Exception as e:
            logger.error(f"Failed to generate en passant recognition: {e}")
            raise
    
    def _generate_en_passant_execution(self):
        """Generate en passant execution exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Similar setup but with more emphasis on execution urgency
            # Place kings
            self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
            
            capturing_file = random.randint(1, 6)
            self.capturing_pawn = chess.square(capturing_file, 4)
            self.chess_board.board.set_piece_at(self.capturing_pawn, chess.Piece(chess.PAWN, chess.WHITE))
            
            # Enemy pawn
            enemy_file = capturing_file + random.choice([-1, 1])
            if enemy_file < 0 or enemy_file > 7:  # Safety check
                enemy_file = capturing_file + (1 if capturing_file > 3 else -1)
                
            self.en_passant_pawn = chess.square(enemy_file, 4)
            self.chess_board.board.set_piece_at(self.en_passant_pawn, chess.Piece(chess.PAWN, chess.BLACK))
            
            # Target square
            self.en_passant_target = chess.square(enemy_file, 5)
            self.en_passant_legal = True
            
            # Add more pieces to show this is a real game position
            additional_pieces = [
                (chess.A1, chess.ROOK, chess.WHITE),
                (chess.H1, chess.ROOK, chess.WHITE),
                (chess.A8, chess.ROOK, chess.BLACK),
                (chess.H8, chess.ROOK, chess.BLACK),
                (chess.square(2, 1), chess.PAWN, chess.WHITE),  # c2
                (chess.square(5, 1), chess.PAWN, chess.WHITE),  # f2
                (chess.square(1, 6), chess.PAWN, chess.BLACK),  # b7
                (chess.square(6, 6), chess.PAWN, chess.BLACK),  # g7
            ]
            
            for square, piece_type, color in additional_pieces:
                if (not self.chess_board.board.piece_at(square) and 
                    square != self.capturing_pawn and 
                    square != self.en_passant_pawn):
                    self.chess_board.board.set_piece_at(square, chess.Piece(piece_type, color))
            
            self.target_squares = [self.en_passant_target]
            self.valid_moves = [chess.Move(self.capturing_pawn, self.en_passant_target)]
            
            # Wrong alternatives
            wrong_moves = []
            # Normal pawn moves
            normal_forward = chess.square(capturing_file, 5)
            if not self.chess_board.board.piece_at(normal_forward):
                wrong_moves.append(normal_forward)
            
            # Trying to capture the pawn directly (impossible)
            wrong_moves.append(self.en_passant_pawn)
            
            # Add other invalid squares
            all_squares = list(range(64))
            occupied = [sq for sq in all_squares if self.chess_board.board.piece_at(sq)]
            available = [sq for sq in all_squares if sq not in occupied + self.target_squares + wrong_moves]
            additional_wrong = random.sample(available, min(4, len(available)))
            wrong_moves.extend(additional_wrong)
            
            self.invalid_squares = wrong_moves
            
            self.chess_board.highlight_square(self.capturing_pawn)
            
        except Exception as e:
            logger.error(f"Failed to generate en passant execution: {e}")
            raise
    
    def _generate_special_moves_integration(self):
        """Generate improved integrated special moves exercise with meaningful positions"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Create more meaningful integration scenarios
            integration_type = random.choice([
                'tactical_choice',
                'safety_priority',
                'development_focus',
                'educational_comparison'
            ])
            
            color = chess.WHITE
            
            # Always place both kings
            self.king_square = chess.E1
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, color))
            self.chess_board.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
            
            self.target_squares = []
            self.valid_moves = []
            
            if integration_type == 'tactical_choice':
                # Scenario where en passant wins material
                self.chess_board.board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, color))
                
                # En passant setup that wins a pawn
                self.capturing_pawn = chess.square(3, 4)  # d5
                self.chess_board.board.set_piece_at(self.capturing_pawn, chess.Piece(chess.PAWN, color))
                self.en_passant_pawn = chess.square(4, 4)  # e5
                self.chess_board.board.set_piece_at(self.en_passant_pawn, chess.Piece(chess.PAWN, chess.BLACK))
                self.en_passant_target = chess.square(4, 5)  # e6
                self.en_passant_legal = True
                
                # Add pieces to make position realistic
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, color))
                self.chess_board.board.set_piece_at(chess.A8, chess.Piece(chess.ROOK, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.H8, chess.Piece(chess.ROOK, chess.BLACK))
                
                # En passant is better here (wins material immediately)
                self.target_squares = [self.en_passant_target]
                self.castling_legal['kingside'] = True  # Also available but less urgent
                
            elif integration_type == 'safety_priority':
                # Scenario where castling is clearly better for king safety
                self.chess_board.board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, color))
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, color))
                
                # Add aggressive black pieces threatening the center
                self.chess_board.board.set_piece_at(chess.D8, chess.Piece(chess.QUEEN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.KNIGHT, chess.BLACK))
                
                # Also setup en passant opportunity
                self.capturing_pawn = chess.square(2, 4)  # c5
                self.chess_board.board.set_piece_at(self.capturing_pawn, chess.Piece(chess.PAWN, color))
                self.en_passant_pawn = chess.square(1, 4)  # b5
                self.chess_board.board.set_piece_at(self.en_passant_pawn, chess.Piece(chess.PAWN, chess.BLACK))
                self.en_passant_target = chess.square(1, 5)  # b6
                
                # Castling is clearly better for king safety
                self.castling_legal['kingside'] = True
                self.target_squares = [chess.G1]  # Prioritize castling
                
            elif integration_type == 'development_focus':
                # Early game scenario focusing on development
                self.chess_board.board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, color))
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, color))
                
                # Add some developed pieces
                self.chess_board.board.set_piece_at(chess.F1, chess.Piece(chess.BISHOP, color))
                self.chess_board.board.set_piece_at(chess.G1, chess.Piece(chess.KNIGHT, color))
                
                # Black pieces
                self.chess_board.board.set_piece_at(chess.A8, chess.Piece(chess.ROOK, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.H8, chess.Piece(chess.ROOK, chess.BLACK))
                
                # Wait, this setup has pieces blocking castling, let me fix this
                self.chess_board.board.remove_piece_at(chess.F1)
                self.chess_board.board.remove_piece_at(chess.G1)
                
                # Setup where queenside castling is better
                self.chess_board.board.set_piece_at(chess.C1, chess.Piece(chess.BISHOP, color))
                self.chess_board.board.set_piece_at(chess.D1, chess.Piece(chess.QUEEN, color))
                # These block queenside, so let's make kingside the choice
                self.chess_board.board.remove_piece_at(chess.C1)
                self.chess_board.board.remove_piece_at(chess.D1)
                
                self.castling_legal['kingside'] = True
                self.castling_legal['queenside'] = True
                self.target_squares = [chess.G1, chess.C1]  # Both legal, teach choice
                
            elif integration_type == 'educational_comparison':
                # Show both moves clearly and let student choose based on principle
                self.chess_board.board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, color))
                
                # En passant setup
                self.capturing_pawn = chess.square(4, 4)  # e5
                self.chess_board.board.set_piece_at(self.capturing_pawn, chess.Piece(chess.PAWN, color))
                self.en_passant_pawn = chess.square(5, 4)  # f5
                self.chess_board.board.set_piece_at(self.en_passant_pawn, chess.Piece(chess.PAWN, chess.BLACK))
                self.en_passant_target = chess.square(5, 5)  # f6
                self.en_passant_legal = True
                
                # Add contextual pieces
                self.chess_board.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, color))
                self.chess_board.board.set_piece_at(chess.A8, chess.Piece(chess.ROOK, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.H8, chess.Piece(chess.ROOK, chess.BLACK))
                
                # Both moves available - educational choice
                self.castling_legal['kingside'] = True
                self.target_squares = [chess.G1, self.en_passant_target]
            
            # Add some additional pieces for realistic position
            remaining_squares = [sq for sq in chess.SQUARES if not self.chess_board.board.piece_at(sq)]
            if len(remaining_squares) > 8:
                # Add a few more pieces to make it look like a real game
                pawn_squares = [(chess.square(i, 1), chess.PAWN, chess.WHITE) for i in [0, 1, 6, 7]]
                pawn_squares.extend([(chess.square(i, 6), chess.PAWN, chess.BLACK) for i in [0, 1, 6, 7]])
                
                for square, piece_type, piece_color in pawn_squares:
                    if (not self.chess_board.board.piece_at(square) and 
                        square != self.capturing_pawn and 
                        square != self.en_passant_pawn and
                        square not in self.target_squares):
                        self.chess_board.board.set_piece_at(square, chess.Piece(piece_type, piece_color))
            
            # Add distractors that aren't the target moves
            all_squares = list(range(64))
            occupied = [sq for sq in all_squares if self.chess_board.board.piece_at(sq)]
            available = [sq for sq in all_squares if sq not in occupied + self.target_squares]
            if len(available) > 0:
                distractors = random.sample(available, min(4, len(available)))
                self.invalid_squares.extend(distractors)
            
            # Highlight the main piece to focus on
            if self.target_squares:
                if chess.G1 in self.target_squares or chess.C1 in self.target_squares:
                    self.chess_board.highlight_square(self.king_square)
                else:
                    self.chess_board.highlight_square(self.capturing_pawn)
            else:
                self.chess_board.highlight_square(self.king_square)
                
        except Exception as e:
            logger.error(f"Failed to generate special moves integration: {e}")
            raise
    
    def _setup_hint_progression(self):
        """Setup hint progression for current exercise with proper initialization"""
        try:
            if self.exercise_type in self.instructions:
                self.hint_progression = self.instructions[self.exercise_type]['hints'].copy()
            else:
                self.hint_progression = ["Look for special moves", "Check the rules", "Try different squares"]
                
            self.hint_level = 0
            
            # Initialize first hint text
            if self.hint_progression:
                self.current_hint_text = self.hint_progression[0]
            else:
                self.current_hint_text = "Use the visual aids to help you"
            
        except Exception as e:
            logger.error(f"Error setting up hints: {e}")
            self.hint_progression = ["Use the visual aids to help", "Look for highlighted squares"]
            self.current_hint_text = self.hint_progression[0]
    
    def handle_square_click(self, square):
        """Enhanced square click handling with better feedback"""
        try:
            if self.show_feedback or square is None or self.demonstration_mode:
                return
                
            self.selected_square = square
            self.total_attempts += 1
            
            # Check if move is correct
            if square in self.target_squares:
                self.on_correct_move()
            else:
                self.on_incorrect_move()
                
        except Exception as e:
            logger.error(f"Error handling square click: {e}")
            self.feedback_message = "Error processing move. Please try again."
            self.show_feedback = True
    
    def on_correct_move(self):
        """Enhanced correct move handling"""
        try:
            self.correct_moves += 1
            self.show_feedback = True
            self.feedback_timer = 0
            
            # Calculate score based on attempts and hints used
            score_multiplier = max(0.3, 1.0 - (self.total_attempts - 1) * 0.2 - self.hint_used_count * 0.1)
            exercise_score = score_multiplier * 100
            
            # Update mastery score
            if self.exercise_type:
                current_mastery = self.mastery_scores[self.exercise_type]
                self.mastery_scores[self.exercise_type] = max(current_mastery, exercise_score)
            
            # Specific feedback messages
            feedback_messages = {
                'castling_basics': [
                    "Perfect! You executed castling correctly!",
                    "Excellent! King safety and rook development in one move!",
                    "Outstanding! You've mastered basic castling!"
                ],
                'castling_requirements': [
                    "Great! You correctly identified the legal castling move!", 
                    "Perfect! You checked all the castling requirements!",
                    "Excellent rule application!"
                ],
                'castling_obstacles': [
                    "Correct! You spotted what prevents castling!",
                    "Perfect analysis of the position!",
                    "Great job identifying the obstacle!"
                ],
                'en_passant_recognition': [
                    "Excellent! You found the en passant opportunity!",
                    "Perfect! You caught the pawn 'in passing'!",
                    "Outstanding pattern recognition!"
                ],
                'en_passant_execution': [
                    "Perfect execution! En passant captured correctly!",
                    "Excellent! You seized the one-move opportunity!",
                    "Great timing - that was your only chance!"
                ],
                'special_moves_integration': [
                    "Outstanding! You chose the best special move!",
                    "Perfect strategic thinking!",
                    "Excellent integration of special moves knowledge!"
                ]
            }
            
            if self.exercise_type in feedback_messages:
                self.feedback_message = random.choice(feedback_messages[self.exercise_type])
            else:
                self.feedback_message = "Correct move! Well done!"
            
            # Visual feedback
            if self.selected_square is not None:
                self.chess_board.select_square(self.selected_square)
                
            # Start success animation
            self._start_success_animation()
            
            # Update progress
            if self.exercise_type:
                # Check if we've already completed max exercises for this type
                if self.exercises_completed[self.exercise_type] < self.exercises_per_type:
                    self.exercises_completed[self.exercise_type] += 1
                total_completed = sum(self.exercises_completed.values())
                # self.progress_bar.set_value(total_completed)
            
            # Audio feedback
            try:
                success_sounds = ['success.wav', 'correct.wav', 'achievement.wav']
                sound = random.choice(success_sounds)
                self.engine.audio_manager.play_sound(sound)
            except Exception as e:
                logger.warning(f"Failed to play success sound: {e}")
            
            # Create celebration
            self.create_celebration_effect()
            
        except Exception as e:
            logger.error(f"Error in on_correct_move: {e}")
            self.feedback_message = "Correct! Great job!"
            self.show_feedback = True
    
    def on_incorrect_move(self):
        """Enhanced incorrect move handling with specific guidance"""
        try:
            self.show_feedback = True
            self.feedback_timer = 0
            
            # Analyze the incorrect move to provide specific feedback
            specific_feedback = self._analyze_incorrect_move()
            
            if specific_feedback:
                self.feedback_message = specific_feedback
            else:
                # Generic feedback based on exercise type
                generic_feedback = {
                    'castling_basics': "Not quite! Remember: King moves 2 squares toward the rook.",
                    'castling_requirements': "Check the castling requirements - something blocks this move.",
                    'castling_obstacles': "That move isn't legal. Look for what prevents castling.",
                    'en_passant_recognition': "Not en passant! Look for the diagonal capture square.",
                    'en_passant_execution': "Wrong square! En passant captures diagonally to empty square.",
                    'special_moves_integration': "Consider your options - which special move is best here?"
                }
                
                self.feedback_message = generic_feedback.get(self.exercise_type, "Not quite right. Try again!")
            
            # Audio feedback
            try:
                error_sounds = ['error.wav', 'wrong.wav', 'buzzer.wav']
                sound = random.choice(error_sounds)
                self.engine.audio_manager.play_sound(sound)
            except Exception as e:
                logger.warning(f"Failed to play error sound: {e}")
                
            # Visual error indication
            if self.selected_square is not None:
                self._create_error_effect(self.selected_square)
                
            # Suggest hint if multiple attempts
            if self.total_attempts >= 3 and not self.show_hints:
                self.feedback_message += " (Try using hints for guidance!)"
                
        except Exception as e:
            logger.error(f"Error in on_incorrect_move: {e}")
            self.feedback_message = "Not quite right. Try again!"
    
    def _analyze_incorrect_move(self):
        """Analyze incorrect move to provide specific feedback"""
        try:
            if self.selected_square is None:
                return None
                
            # Castling-specific feedback
            if 'castling' in self.exercise_type:
                if self.selected_square == self.king_square:
                    return "Click where the king should MOVE TO, not the king itself!"
                elif self.selected_square in self.rook_squares:
                    return "Click the king's destination, not the rook!"
                elif self.selected_square in self.blocked_squares:
                    return "That square is blocked by a piece!"
                elif self.selected_square in [chess.F1, chess.G1, chess.C1, chess.D1]:
                    if self.selected_square in [chess.F1, chess.G1]:
                        if not self.castling_legal.get('kingside', False):
                            return "Kingside castling is not legal here!"
                    elif self.selected_square in [chess.C1, chess.D1]:
                        if not self.castling_legal.get('queenside', False):
                            return "Queenside castling is not legal here!"
            
            # En passant specific feedback
            elif 'en_passant' in self.exercise_type:
                if self.selected_square == self.en_passant_pawn:
                    return "You can't capture that pawn directly! Use en passant!"
                elif self.selected_square == self.capturing_pawn:
                    return "Click where the pawn should MOVE TO!"
                elif self.capturing_pawn and self.selected_square == chess.square(chess.square_file(self.capturing_pawn), 5):
                    return "That's a normal pawn move. Look for the en passant capture!"
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing incorrect move: {e}")
            return None
    
    def _start_success_animation(self):
        """Start success animation sequence"""
        try:
            self.animation_active = True
            self.animation_timer = 0
            
        except Exception as e:
            logger.warning(f"Failed to start success animation: {e}")
    
    def _create_error_effect(self, square):
        """Create visual error effect on square"""
        try:
            # Add pulsing red effect particles
            square_rect = self.chess_board.get_square_rect(square)
            if square_rect:
                center_x = square_rect.centerx
                center_y = square_rect.centery
                
                for _ in range(8):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(50, 150)
                    self.move_trail_particles.append({
                        'x': center_x,
                        'y': center_y,
                        'vx': speed * math.cos(angle),
                        'vy': speed * math.sin(angle),
                        'color': (255, 0, 0),
                        'life': 1.0,
                        'size': random.randint(3, 8)
                    })
                    
        except Exception as e:
            logger.warning(f"Failed to create error effect: {e}")
    
    def create_celebration_effect(self):
        """Create enhanced celebration particle effect"""
        try:
            # Determine celebration intensity based on performance
            if self.hint_used_count == 0 and self.total_attempts == 1:
                particle_count = 50  # Perfect performance
                colors = [(255, 215, 0), (255, 255, 255), (0, 255, 0)]  # Gold, white, green
            elif self.total_attempts <= 2:
                particle_count = 35  # Good performance  
                colors = [(255, 215, 0), (255, 255, 255), (0, 200, 255)]  # Gold, white, blue
            else:
                particle_count = 25  # Adequate performance
                colors = [(255, 255, 255), (0, 255, 0), (255, 165, 0)]  # White, green, orange
            
            # Create celebration particles
            center_x = self.config.SCREEN_WIDTH // 2
            center_y = 350
            
            for _ in range(particle_count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(100, 400)
                
                self.celebration_particles.append({
                    'x': center_x + random.uniform(-50, 50),
                    'y': center_y + random.uniform(-30, 30),
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle) - random.uniform(50, 150),  # Upward bias
                    'color': random.choice(colors),
                    'life': random.uniform(2.0, 4.0),
                    'size': random.randint(4, 12),
                    'gravity': random.uniform(200, 400)
                })
                
        except Exception as e:
            logger.warning(f"Failed to create celebration effect: {e}")
    
    # Fixed hint system methods
    def toggle_hints(self):
        """Toggle hint display with proper state management"""
        try:
            self.show_hints = not self.show_hints
            
            if self.show_hints:
                self.hint_used_count += 1
                self._update_visual_hints()
                # Update current hint text
                if self.hint_progression and self.hint_level < len(self.hint_progression):
                    self.current_hint_text = self.hint_progression[self.hint_level]
            else:
                self._clear_visual_hints()
                self.current_hint_text = ""
                
        except Exception as e:
            logger.error(f"Error toggling hints: {e}")
    
    def next_hint(self):
        """Show next hint in progression"""
        try:
            if self.hint_level < len(self.hint_progression) - 1:
                self.hint_level += 1
                self.hint_used_count += 1
                if self.show_hints:
                    self._update_visual_hints()
                # Update current hint text
                if self.hint_progression and self.hint_level < len(self.hint_progression):
                    self.current_hint_text = self.hint_progression[self.hint_level]
                    
        except Exception as e:
            logger.error(f"Error showing next hint: {e}")
    
    def previous_hint(self):
        """Show previous hint in progression"""
        try:
            if self.hint_level > 0:
                self.hint_level -= 1
                if self.show_hints:
                    self._update_visual_hints()
                # Update current hint text
                if self.hint_progression and self.hint_level < len(self.hint_progression):
                    self.current_hint_text = self.hint_progression[self.hint_level]
                    
        except Exception as e:
            logger.error(f"Error showing previous hint: {e}")
    
    def _update_visual_hints(self):
        """Update visual hints based on current level"""
        try:
            if not self.show_hints:
                return
                
            # Clear previous hints
            self._clear_visual_hints()
            
            # Progressive hint revelation
            if self.hint_level >= 0:
                # Level 0: Highlight relevant pieces
                if 'castling' in self.exercise_type and self.king_square:
                    self.chess_board.highlight_square(self.king_square)
                    for rook_sq in self.rook_squares:
                        self.chess_board.highlight_square(rook_sq)
                elif 'en_passant' in self.exercise_type and self.capturing_pawn:
                    self.chess_board.highlight_square(self.capturing_pawn)
                    if self.en_passant_pawn:
                        self.chess_board.highlight_square(self.en_passant_pawn)
            
            if self.hint_level >= 1:
                # Level 1: Show target squares
                for square in self.target_squares:
                    self.chess_board.highlight_square(square)
            
            if self.hint_level >= 2:
                # Level 2: Show move paths
                self.show_move_paths = True
            
            if self.hint_level >= 3:
                # Level 3: Show legal moves overlay
                self.show_legal_moves = True
                
        except Exception as e:
            logger.error(f"Error updating visual hints: {e}")
    
    def _clear_visual_hints(self):
        """Clear all visual hint indicators"""
        try:
            self.chess_board.clear_highlights()
            self.show_move_paths = False
            self.show_legal_moves = False
            
            # Re-highlight current selection if any
            if self.selected_square:
                self.chess_board.select_square(self.selected_square)
                
        except Exception as e:
            logger.error(f"Error clearing visual hints: {e}")
    
    # UI toggle methods
    def toggle_conditions(self):
        """Toggle conditions/rules display"""
        self.show_conditions = not self.show_conditions
    
    def toggle_move_paths(self):
        """Toggle move path visualization"""
        self.show_move_paths = not self.show_move_paths
    
    def toggle_legal_moves(self):
        """Toggle legal moves highlighting"""
        self.show_legal_moves = not self.show_legal_moves
    
    def toggle_step_mode(self):
        """Toggle step-by-step mode"""
        self.step_by_step_mode = not self.step_by_step_mode
    
    def start_demonstration(self):
        """Start interactive demonstration"""
        try:
            if self.demonstration_mode:
                return
                
            self.demonstration_mode = True
            self.auto_play_demo = True
            
            # Create demonstration text
            demo_messages = {
                'castling_basics': "Watch: Castling moves king 2 squares and rook jumps over!",
                'castling_requirements': "See: All castling conditions must be met!",
                'castling_obstacles': "Learn: What prevents castling in this position!",
                'en_passant_recognition': "Observe: Enemy pawn jumped 2 squares - capture it 'in passing'!",
                'en_passant_execution': "Demo: Diagonal capture to empty square removes enemy pawn!",
                'special_moves_integration': "Master: Choose the best special move for this position!"
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
            pygame.time.set_timer(pygame.USEREVENT + 6, 4000)
            
        except Exception as e:
            logger.error(f"Error starting demonstration: {e}")
            self.demonstration_mode = False
    
    def reset_exercise(self):
        """Reset current exercise to initial state"""
        try:
            if self.current_board_state:
                self.chess_board.board = self.current_board_state.copy()
                self.chess_board.clear_highlights()
                self.chess_board.select_square(None)
                
            self.show_feedback = False
            self.selected_square = None
            self.total_attempts = 0  # Reset attempts for this exercise
            self.hint_level = 0
            self.show_hints = False
            self.hint_used_count = 0
            self.current_hint_text = ""
            
            # Re-setup hints
            self._setup_hint_progression()
            
            # Re-highlight starting position
            if 'castling' in self.exercise_type and self.king_square:
                self.chess_board.highlight_square(self.king_square)
            elif 'en_passant' in self.exercise_type and self.capturing_pawn:
                self.chess_board.highlight_square(self.capturing_pawn)
                
        except Exception as e:
            logger.error(f"Error resetting exercise: {e}")
    
    def skip_exercise(self):
        """Skip current exercise"""
        try:
            if self.exercise_type:
                self.exercises_completed[self.exercise_type] += 1
                # Lower mastery score for skipped exercises
                self.mastery_scores[self.exercise_type] = max(
                    self.mastery_scores[self.exercise_type], 30.0
                )
                
            self.next_exercise()
            
        except Exception as e:
            logger.error(f"Error skipping exercise: {e}")
            self.next_exercise()
    
    def next_exercise(self):
        """Move to next exercise with enhanced progression"""
        try:
            self.current_exercise += 1
            
            # Check if current type is complete
            if self.exercise_type and self.exercises_completed[self.exercise_type] >= self.exercises_per_type:
                self.current_type_index += 1
                
                # Show type completion message
                if self.current_type_index < len(self.movement_types):
                    mastery = self.mastery_scores[self.exercise_type]
                    if mastery >= 80:
                        completion_msg = f" {self.exercise_type.replace('_', ' ').title()} MASTERED!"
                    elif mastery >= 60:
                        completion_msg = f" {self.exercise_type.replace('_', ' ').title()} completed!"
                    else:
                        completion_msg = f" {self.exercise_type.replace('_', ' ').title()} finished - review recommended"
                    
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
            
            # Prevent going beyond total exercises
            total_completed = sum(self.exercises_completed.values())
            max_exercises = len(self.movement_types) * self.exercises_per_type
            
            # Check if module is complete
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
        """Complete the special moves module with enhanced celebration"""
        try:
            self.module_completed = True
            self.completion_timer = 0
            
            # Calculate final performance metrics
            total_exercises = sum(self.exercises_completed.values())
            accuracy = (self.correct_moves / max(self.total_attempts, 1)) * 100
            avg_mastery = sum(self.mastery_scores.values()) / len(self.mastery_scores)
            hint_dependency = (self.hint_used_count / max(total_exercises, 1)) * 100
            
            self.performance_metrics.update({
                'accuracy': accuracy,
                'avg_mastery': avg_mastery,
                'hint_dependency': hint_dependency,
                'total_time': (pygame.time.get_ticks() - self.session_start_time) / 1000.0
            })
            
            self.final_score = (accuracy * 0.4 + avg_mastery * 0.4 + max(0, 100 - hint_dependency) * 0.2)
            
            # Create epic completion celebration
            particle_count = 100 if self.final_score >= 85 else 75
            
            for _ in range(particle_count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(200, 600)
                colors = [
                    (255, 215, 0),   # Gold
                    (255, 255, 255), # White  
                    (138, 43, 226),  # Purple
                    (255, 20, 147),  # Deep pink
                    (0, 255, 255),   # Cyan
                ]
                
                self.celebration_particles.append({
                    'x': self.config.SCREEN_WIDTH // 2,
                    'y': self.config.SCREEN_HEIGHT // 2,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle),
                    'color': random.choice(colors),
                    'life': random.uniform(3.0, 6.0),
                    'size': random.randint(5, 20),
                    'gravity': random.uniform(150, 300)
                })
            
            # Play completion sound
            try:
                completion_sounds = ['fanfare.wav', 'victory.wav', 'complete.wav']
                sound = random.choice(completion_sounds)
                self.engine.audio_manager.play_sound(sound)
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
            try:
                self.engine.running = False
            except:
                pass
    
    def handle_event(self, event):
        """Enhanced event handling"""
        try:
            # UI button events
            self.back_button.handle_event(event)
            self.hint_button.handle_event(event)
            self.conditions_button.handle_event(event)
            #self.paths_button.handle_event(event)
            #self.legal_moves_button.handle_event(event)
            #self.reset_button.handle_event(event)
            #self.step_mode_button.handle_event(event)
            
            if not self.show_feedback:
                #self.demo_button.handle_event(event)
                if self.total_attempts > 1:
                    self.skip_button.handle_event(event)
            
            if self.show_feedback:
                self.next_button.handle_event(event)
            
            if self.show_hints:
                self.hint_prev_button.handle_event(event)
                self.hint_next_button.handle_event(event)
            
            # Mouse clicks on chess board
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
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
                elif event.key == pygame.K_c:
                    self.toggle_conditions()
                elif event.key == pygame.K_p:
                    self.toggle_move_paths()
                elif event.key == pygame.K_l:
                    self.toggle_legal_moves()
                elif event.key == pygame.K_d and not self.show_feedback:
                    self.start_demonstration()
                elif event.key == pygame.K_s and self.total_attempts > 1:
                    self.skip_exercise()
                elif event.key == pygame.K_LEFT and self.show_hints:
                    self.previous_hint()
                elif event.key == pygame.K_RIGHT and self.show_hints:
                    self.next_hint()
            
            # Timer events
            if event.type == pygame.USEREVENT + 6:
                self.demonstration_mode = False
                self.auto_play_demo = False
                pygame.time.set_timer(pygame.USEREVENT + 6, 0)
                
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def update(self, dt):
        """Enhanced update with comprehensive state management"""
        try:
            super().update(dt)
            
            # Update mouse position
            mouse_pos = pygame.mouse.get_pos()
            
            # Update UI elements
            self.back_button.update(dt, mouse_pos)
            self.hint_button.update(dt, mouse_pos)
            self.conditions_button.update(dt, mouse_pos)
            #self.paths_button.update(dt, mouse_pos)
            #self.legal_moves_button.update(dt, mouse_pos)
            #self.reset_button.update(dt, mouse_pos)
            #self.step_mode_button.update(dt, mouse_pos)
            
            if not self.show_feedback:
                #self.demo_button.update(dt, mouse_pos)
                if self.total_attempts > 1:
                    self.skip_button.update(dt, mouse_pos)
            
            if self.show_feedback:
                self.next_button.update(dt, mouse_pos)
            
            if self.show_hints:
                self.hint_prev_button.update(dt, mouse_pos)
                self.hint_next_button.update(dt, mouse_pos)
            
            # Update feedback timer
            if self.show_feedback and not self.module_completed:
                self.feedback_timer += dt
            
            # Update animations
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
            
            # Update celebration particles
            for particle in self.celebration_particles[:]:
                try:
                    particle['x'] += particle['vx'] * dt
                    particle['y'] += particle['vy'] * dt
                    particle['vy'] += particle.get('gravity', 300) * dt
                    particle['life'] -= dt
                    particle['size'] = max(1, particle['size'] - dt * 1.5)
                    
                    if particle['life'] <= 0:
                        self.celebration_particles.remove(particle)
                except Exception as e:
                    logger.warning(f"Error updating celebration particle: {e}")
                    self.celebration_particles.remove(particle)
            
            # Update move trail particles
            for particle in self.move_trail_particles[:]:
                try:
                    particle['x'] += particle['vx'] * dt
                    particle['y'] += particle['vy'] * dt
                    particle['life'] -= dt
                    particle['size'] = max(1, particle['size'] - dt * 3)
                    
                    if particle['life'] <= 0:
                        self.move_trail_particles.remove(particle)
                except Exception as e:
                    logger.warning(f"Error updating trail particle: {e}")
                    self.move_trail_particles.remove(particle)
            
            # Update success animation
            if self.animation_active:
                self.animation_timer += dt
                if self.animation_timer > 3.0:
                    self.animation_active = False
                    self.animation_timer = 0
                    self.animation_sequence = []
            
            # Auto-advance after module completion
            if self.module_completed:
                self.completion_timer += dt
                if self.completion_timer > 8.0:
                    self.engine.change_state(GameState.MAIN_MENU)
                    
        except Exception as e:
            logger.error(f"Error in update: {e}")
    
    def render(self, screen):
        """Enhanced rendering with comprehensive visual system"""
        try:
            # Fill background
            screen.fill(self.config.COLORS['background'])
            
            # Render title
            title_surface = self.title_font.render(
                "Master Special Moves - En Passant & Castling", 
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
                
                # Render overlays
                if self.show_move_paths:
                    self._render_move_paths(screen)
                if self.show_legal_moves:
                    self._render_legal_moves(screen)
                if self.show_danger_zones:
                    self._render_danger_zones(screen)
                    
            except Exception as e:
                logger.error(f"Error drawing chess board: {e}")
                error_surface = self.instruction_font.render(
                    "Error displaying board", True, self.config.COLORS.get('error', (255, 0, 0))
                )
                screen.blit(error_surface, error_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400)))
            
            # Render hint system
            if self.show_hints and self.current_hint_text:
                self._render_hint_system(screen)
            
            # Render conditions panel
            if self.show_conditions:
                self._render_conditions_panel(screen)
            
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
            self.conditions_button.render(screen)
            #self.paths_button.render(screen)
            #self.legal_moves_button.render(screen)
            #self.reset_button.render(screen)
            #self.step_mode_button.render(screen)
            
            if not self.show_feedback:
                #self.demo_button.render(screen)
                if self.total_attempts > 1:
                    self.skip_button.render(screen)
            
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
                    logger.warning(f"Error rendering celebration particle: {e}")
            
            for particle in self.move_trail_particles:
                try:
                    pygame.draw.circle(
                        screen, particle['color'],
                        (int(particle['x']), int(particle['y'])),
                        int(particle['size'])
                    )
                except Exception as e:
                    logger.warning(f"Error rendering trail particle: {e}")
            
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
    
    def _render_move_paths(self, screen):
        """Render move path visualizations"""
        try:
            alpha = int(100 + 50 * math.sin(self.visual_effects['pulse_timer'] * 3))
            
            if 'castling' in self.exercise_type and self.king_square:
                # Show castling paths
                king_rect = self.chess_board.get_square_rect(self.king_square)
                if king_rect and self.target_squares:
                    for target in self.target_squares:
                        if target in [chess.G1, chess.C1]:  # Only show for castling targets
                            target_rect = self.chess_board.get_square_rect(target)
                            if target_rect:
                                # Draw arrow from king to target
                                start_pos = king_rect.center
                                end_pos = target_rect.center
                                
                                # Draw arrow line
                                pygame.draw.line(screen, (0, 255, 255), start_pos, end_pos, 4)
                                
                                # Draw arrowhead
                                angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
                                arrow_length = 15
                                arrow_angle = 0.5
                                
                                arrow_p1 = (
                                    end_pos[0] - arrow_length * math.cos(angle - arrow_angle),
                                    end_pos[1] - arrow_length * math.sin(angle - arrow_angle)
                                )
                                arrow_p2 = (
                                    end_pos[0] - arrow_length * math.cos(angle + arrow_angle),
                                    end_pos[1] - arrow_length * math.sin(angle + arrow_angle)
                                )
                                
                                pygame.draw.polygon(screen, (0, 255, 255), [end_pos, arrow_p1, arrow_p2])
            
            elif 'en_passant' in self.exercise_type and self.capturing_pawn:
                # Show en passant path
                pawn_rect = self.chess_board.get_square_rect(self.capturing_pawn)
                if pawn_rect and self.en_passant_target:
                    target_rect = self.chess_board.get_square_rect(self.en_passant_target)
                    if target_rect:
                        start_pos = pawn_rect.center
                        end_pos = target_rect.center
                        
                        # Draw curved path for diagonal move
                        control_x = (start_pos[0] + end_pos[0]) // 2
                        control_y = min(start_pos[1], end_pos[1]) - 20
                        
                        # Draw bezier curve (simplified)
                        points = []
                        for t in range(11):
                            t = t / 10.0
                            x = (1-t)**2 * start_pos[0] + 2*(1-t)*t * control_x + t**2 * end_pos[0]
                            y = (1-t)**2 * start_pos[1] + 2*(1-t)*t * control_y + t**2 * end_pos[1]
                            points.append((int(x), int(y)))
                        
                        if len(points) > 1:
                            pygame.draw.lines(screen, (255, 165, 0), False, points, 4)
                            
        except Exception as e:
            logger.warning(f"Error rendering move paths: {e}")
    
    def _render_legal_moves(self, screen):
        """Render legal move indicators"""
        try:
            alpha = int(80 + 40 * math.sin(self.visual_effects['glow_timer'] * 4))
            
            for square in self.target_squares:
                square_rect = self.chess_board.get_square_rect(square)
                if square_rect:
                    overlay = pygame.Surface((square_rect.width, square_rect.height))
                    overlay.set_alpha(alpha)
                    overlay.fill((0, 255, 0))  # Green for legal moves
                    screen.blit(overlay, square_rect.topleft)
                    
        except Exception as e:
            logger.warning(f"Error rendering legal moves: {e}")
    
    def _render_danger_zones(self, screen):
        """Render danger zone indicators"""
        try:
            alpha = int(60 + 30 * math.sin(self.visual_effects['warning_timer'] * 5))
            
            for square in self.invalid_squares[:5]:  # Limit display
                square_rect = self.chess_board.get_square_rect(square)
                if square_rect:
                    overlay = pygame.Surface((square_rect.width, square_rect.height))
                    overlay.set_alpha(alpha)
                    overlay.fill((255, 0, 0))  # Red for danger
                    screen.blit(overlay, square_rect.topleft)
                    
        except Exception as e:
            logger.warning(f"Error rendering danger zones: {e}")
    
    def _render_hint_system(self, screen):
        """Render progressive hint system with proper text display"""
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
    
    def _render_conditions_panel(self, screen):
        """Render detailed conditions/rules panel"""
        try:
            panel_width = 400
            panel_height = 500
            panel_x = 50
            panel_y = 180
            
            # Background
            panel_surface = pygame.Surface((panel_width, panel_height))
            panel_surface.set_alpha(240)
            panel_surface.fill((30, 30, 40))
            screen.blit(panel_surface, (panel_x, panel_y))
            
            # Border
            pygame.draw.rect(screen, self.config.COLORS['primary'], 
                           (panel_x, panel_y, panel_width, panel_height), 3)
            
            y_offset = panel_y + 20
            
            # Title
            if 'castling' in self.exercise_type:
                title = "Castling Rules & Requirements"
                rules = [
                    "1. King and rook must never have moved",
                    "2. No pieces between king and rook",
                    "3. King cannot be in check",
                    "4. King cannot move through check",
                    "5. King cannot castle into check",
                    "6. King moves exactly 2 squares",
                    "7. Rook jumps to adjacent square",
                    "",
                    "K.I.N.G Memory Aid:",
                    "K - King not in check",
                    "I - In original position",
                    "N - No pieces between",
                    "G - Good squares (no attacks)"
                ]
            else:  # en passant
                title = "En Passant Rules & Requirements"
                rules = [
                    "1. Enemy pawn moves exactly 2 squares",
                    "2. From its starting position",
                    "3. Lands adjacent to your pawn",
                    "4. Your pawn on 5th rank (White)",
                    "5. Must capture IMMEDIATELY",
                    "6. Capture diagonally to empty square",
                    "7. Enemy pawn disappears",
                    "",
                    "Remember: 'En Passant' = 'In Passing'",
                    "This prevents unfair pawn advancement",
                    "It's now or never - don't wait!"
                ]
            
            title_surface = self.info_font.render(title, True, (255, 255, 100))
            screen.blit(title_surface, (panel_x + 10, y_offset))
            y_offset += 35
            
            # Rules list
            for rule in rules:
                if rule == "":
                    y_offset += 15
                    continue
                    
                color = (255, 255, 255) if not rule.startswith(("K.I.N.G", "Remember")) else (100, 255, 100)
                rule_surface = self.tip_font.render(rule, True, color)
                screen.blit(rule_surface, (panel_x + 15, y_offset))
                y_offset += 22
                
                if y_offset > panel_y + panel_height - 30:
                    break
            
            # Current position analysis
            if self.castling_blocked_reasons:
                y_offset += 20
                if y_offset < panel_y + panel_height - 60:
                    analysis_title = self.info_font.render("Position Analysis:", True, (255, 100, 100))
                    screen.blit(analysis_title, (panel_x + 10, y_offset))
                    y_offset += 25
                    
                    for reason in self.castling_blocked_reasons[:3]:  # Limit display
                        if y_offset < panel_y + panel_height - 25:
                            reason_surface = self.tip_font.render(f"• {reason}", True, (255, 150, 150))
                            screen.blit(reason_surface, (panel_x + 15, y_offset))
                            y_offset += 20
                            
        except Exception as e:
            logger.warning(f"Error rendering conditions panel: {e}")
    
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
                main_message = "🏆 SPECIAL MOVES GRANDMASTER! 🏆"
                color = (255, 215, 0)  # Gold
            elif self.final_score >= 75:
                main_message = "⭐ SPECIAL MOVES EXPERT! ⭐"
                color = (255, 255, 255)  # Silver
            elif self.final_score >= 60:
                main_message = "🎯 SPECIAL MOVES SCHOLAR! 🎯"
                color = (205, 127, 50)  # Bronze
            else:
                main_message = "📚 SPECIAL MOVES STUDENT 📚"
                color = (100, 149, 237)  # Cornflower blue
            
            success_font = pygame.font.Font(None, 64)
            success_surface = success_font.render(main_message, True, color)
            screen.blit(success_surface, success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 140)))
            
            # Subtitle
            subtitle = "You've conquered En Passant & Castling!"
            subtitle_surface = self.title_font.render(subtitle, True, (255, 255, 255))
            screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 200)))
            
            # Performance metrics
            metrics_y = 260
            metrics = [
                f"Final Score: {self.final_score:.1f}%",
                f"Accuracy: {self.performance_metrics['accuracy']:.1f}%",
                f"Average Mastery: {self.performance_metrics['avg_mastery']:.1f}%",
                f"Exercises Completed: {sum(self.exercises_completed.values())}",
                f"Total Time: {self.performance_metrics['total_time']:.1f}s"
            ]
            
            for i, metric in enumerate(metrics):
                metric_surface = self.instruction_font.render(metric, True, (255, 255, 255))
                screen.blit(metric_surface, metric_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, metrics_y + i * 30)))
            
            # Individual mastery scores
            mastery_y = 420
            mastery_title = self.info_font.render("Mastery by Topic:", True, (255, 255, 100))
            screen.blit(mastery_title, mastery_title.get_rect(center=(self.config.SCREEN_WIDTH // 2, mastery_y)))
            
            for i, (topic, score) in enumerate(self.mastery_scores.items()):
                if score > 0:
                    topic_name = topic.replace('_', ' ').title()
                    mastery_text = f"{topic_name}: {score:.0f}%"
                    
                    # Color based on mastery level
                    if score >= 80:
                        topic_color = (0, 255, 0)  # Green
                    elif score >= 60:
                        topic_color = (255, 255, 0)  # Yellow
                    else:
                        topic_color = (255, 165, 0)  # Orange
                    
                    mastery_surface = self.tip_font.render(mastery_text, True, topic_color)
                    screen.blit(mastery_surface, mastery_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, mastery_y + 30 + i * 20)))
            
            # Achievement message
            achievement_y = 580
            if self.final_score >= 90:
                achievement = "PERFECT! You're ready for advanced chess tactics!"
            elif self.final_score >= 75:
                achievement = "EXCELLENT! You've mastered these special moves!"
            elif self.final_score >= 60:
                achievement = "GOOD WORK! Keep practicing these moves!"
            else:
                achievement = "KEEP LEARNING! Review and practice more!"
            
            achievement_surface = self.info_font.render(achievement, True, self.config.COLORS['accent'])
            screen.blit(achievement_surface, achievement_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, achievement_y)))
            
            # Summary of what was learned
            summary_y = 620
            summary_lines = [
                "Special Moves Mastery Summary:",
                "✓ Castling: King safety + rook development in one move",
                "✓ En Passant: Capture pawns 'in passing' - timing is critical!",
                "✓ Strategic thinking: Know when to use these powerful moves",
                "✓ Rule mastery: All conditions and requirements understood"
            ]
            
            for i, line in enumerate(summary_lines):
                font = self.info_font if i == 0 else self.tip_font
                color = (255, 215, 0) if i == 0 else (200, 200, 200)
                line_surface = font.render(line, True, color)
                screen.blit(line_surface, line_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, summary_y + i * 22)))
            
            # Auto-return message
            auto_return_surface = self.tip_font.render(
                "Returning to main menu automatically...", 
                True, (150, 150, 150)
            )
            screen.blit(auto_return_surface, auto_return_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 720)))
            
        except Exception as e:
            logger.error(f"Error rendering completion screen: {e}")
            # Fallback completion screen
            try:
                screen.fill((0, 0, 50))
                fallback_font = pygame.font.SysFont('Arial', 36)
                fallback_text = fallback_font.render("Special Moves Module Complete!", True, (255, 255, 255))
                screen.blit(fallback_text, fallback_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2)))
            except:
                pass