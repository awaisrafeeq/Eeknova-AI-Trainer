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

class OpeningPrinciplesFirstGameState(BaseState):
    """Opening Principles & First Game Playthrough - Capstone Module"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Module progression phases
            self.module_phases = [
                'opening_principles_tutorial',  # Learn the 6 core principles
                'mistake_recognition',          # Identify common opening mistakes
                'guided_practice',             # Practice applying principles
                'first_game_preparation',      # Pre-game coaching
                'guided_first_game',          # Full game with real-time coaching
                'game_analysis',              # Post-game review
                'completion_celebration'      # Module completion
            ]
            
            # Current phase tracking
            self.current_phase = 0
            self.phase_progress = 0
            self.exercises_per_phase = {
                'opening_principles_tutorial': 6,
                'mistake_recognition': 5,
                'guided_practice': 4,
                'first_game_preparation': 1,
                'guided_first_game': 1,
                'game_analysis': 1,
                'completion_celebration': 1
            }
            
            # Core Opening Principles (The Foundation)
            self.opening_principles = {
                'center_control': {
                    'name': 'Control the Center',
                    'description': 'Place pawns on e4/d4 (e5/d5) to control key central squares',
                    'importance': 'The center is like the highway of chess - control it to move pieces efficiently',
                    'examples': ['1.e4', '1.d4', '1...e5', '1...d5', '1...c5'],
                    'violations': ['1.a4', '1.h4', 'excessive flank pawn moves'],
                    'memory_aid': 'Center first, sides later!'
                },
                'piece_development': {
                    'name': 'Develop Your Pieces',
                    'description': 'Bring knights and bishops into the game quickly and effectively',
                    'importance': 'Pieces on starting squares do nothing - get them into battle!',
                    'examples': ['Nf3', 'Bc4', 'Nc6', 'Bf5'],
                    'violations': ['leaving pieces on back rank', 'developing same piece twice'],
                    'memory_aid': 'Knights before bishops, minor pieces before major pieces!'
                },
                'king_safety': {
                    'name': 'Castle Early',
                    'description': 'Get your king to safety behind a wall of pawns by move 10',
                    'importance': 'A king in the center is vulnerable to attack',
                    'examples': ['O-O (kingside)', 'O-O-O (queenside)'],
                    'violations': ['delaying castling', 'moving king without castling'],
                    'memory_aid': 'Safety first - castle before you attack!'
                },
                'avoid_early_queen': {
                    'name': "Don't Bring Queen Out Early",
                    'description': 'Keep the queen safe until minor pieces are developed',
                    'importance': 'Early queen moves waste time and make the queen a target',
                    'examples': ['Qd2 connecting rooks', 'Qc2 supporting center'],
                    'violations': ['Qh5 (Scholar\'s Mate attempt)', 'Qf3 too early'],
                    'memory_aid': 'Queen last, not first!'
                },
                'no_wasted_moves': {
                    'name': "Don't Move Same Piece Twice",
                    'description': 'Develop each piece once to an optimal square',
                    'importance': 'Every move counts - don\'t waste tempo in the opening',
                    'examples': ['Nf3-d2-f3 wastes time', 'Develop all pieces first'],
                    'violations': ['moving developed pieces unnecessarily'],
                    'memory_aid': 'One piece, one move, one purpose!'
                },
                'coordinate_pieces': {
                    'name': 'Coordinate Your Pieces',
                    'description': 'Make pieces work together and support each other',
                    'importance': 'Teamwork makes the dream work in chess too!',
                    'examples': ['Rook supporting pawn', 'Bishop protecting knight'],
                    'violations': ['isolated pieces', 'undefended pieces'],
                    'memory_aid': 'Together we stand, divided we fall!'
                }
            }
            
            # Common Opening Mistakes (What NOT to do)
            self.common_mistakes = {
                'scholars_mate_attempt': {
                    'name': "Scholar's Mate Trap",
                    'description': 'Trying to checkmate with Qh5 and Bc4 attacking f7',
                    'why_bad': 'Develops queen too early, easily defended, leads to bad position',
                    'punishment': 'Black plays Nf6, attacks queen, develops with tempo',
                    'lesson': 'Quick wins rarely work against good players'
                },
                'too_many_pawn_moves': {
                    'name': 'Pawn Storm Opening',
                    'description': 'Moving many pawns instead of developing pieces',
                    'why_bad': 'Wastes time, weakens position, falls behind in development',
                    'punishment': 'Opponent develops pieces and attacks',
                    'lesson': 'Pieces are stronger than pawns in the opening'
                },
                'copying_opponent': {
                    'name': 'Copycat Strategy',
                    'description': 'Mindlessly copying opponent\'s moves',
                    'why_bad': 'No independent plan, allows opponent to set traps',
                    'punishment': 'Forced checkmate or material loss',
                    'lesson': 'Think for yourself, don\'t just copy'
                },
                'neglecting_king_safety': {
                    'name': 'King in Center',
                    'description': 'Keeping king in center too long',
                    'why_bad': 'King becomes target for attack when center opens',
                    'punishment': 'Quick checkmate or constant king harassment',
                    'lesson': 'Castle early, ask questions later'
                },
                'premature_attacks': {
                    'name': 'Rushing to Attack',
                    'description': 'Attacking before pieces are developed',
                    'why_bad': 'Attack lacks support, easily defended',
                    'punishment': 'Attack fails, position becomes worse',
                    'lesson': 'Develop first, attack second'
                },
                'wrong_piece_order': {
                    'name': 'Wrong Development Order',
                    'description': 'Developing pieces in inefficient order',
                    'why_bad': 'Wastes time, creates problems later',
                    'punishment': 'Falls behind in development race',
                    'lesson': 'Knights before bishops, minor before major pieces'
                }
            }
            
            # Progress tracking
            self.total_attempts = 0
            self.correct_answers = 0
            self.principle_mastery = {principle: 0.0 for principle in self.opening_principles}
            self.mistake_recognition_score = 0.0
            
            # Game state management
            self.current_exercise = None
            self.selected_square = None
            self.show_feedback = False
            self.feedback_message = ""
            self.feedback_timer = 0
            
            # First game coaching system
            self.game_move_count = 0
            self.coaching_messages = []
            self.move_evaluations = []
            self.real_time_coaching = True
            self.game_phase = 'opening'  # opening, middlegame, endgame
            
            # AI Opponent for first game (simplified)
            self.ai_personality = 'beginner_friendly'  # Plays reasonable but not perfect moves
            self.ai_move_history = []
            
            # Hint and guidance system
            self.hint_level = 0
            self.show_hints = False
            self.hint_progression = []
            self.current_hint_text = ""
            
            # Visual aids and annotations
            self.show_principle_highlights = False
            self.show_mistake_warnings = False
            self.show_suggested_moves = False
            self.show_evaluation_bars = False
            
            # Chess board
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
            
            # Create UI elements
            self.create_ui_elements()
            
            # Font system
            try:
                self.title_font = pygame.font.Font(None, 48)
                self.subtitle_font = pygame.font.Font(None, 36)
                self.instruction_font = pygame.font.Font(None, 28)
                self.info_font = pygame.font.Font(None, 24)
                self.tip_font = pygame.font.Font(None, 20)
                self.hint_font = pygame.font.Font(None, 22)
                self.coaching_font = pygame.font.Font(None, 26)
            except Exception as e:
                logger.error(f"Failed to load fonts: {e}")
                # Fallback fonts
                self.title_font = pygame.font.SysFont('Arial', 48)
                self.subtitle_font = pygame.font.SysFont('Arial', 36)
                self.instruction_font = pygame.font.SysFont('Arial', 28)
                self.info_font = pygame.font.SysFont('Arial', 24)
                self.tip_font = pygame.font.SysFont('Arial', 20)
                self.hint_font = pygame.font.SysFont('Arial', 22)
                self.coaching_font = pygame.font.SysFont('Arial', 26)
            
            # Animation and visual effects
            self.animated_texts = []
            self.celebration_particles = []
            self.coaching_bubbles = []
            self.visual_effects = {
                'principle_glow': 0,
                'mistake_pulse': 0,
                'coaching_highlight': 0,
                'completion_celebration': 0
            }
            
            # Module completion tracking
            self.module_completed = False
            self.completion_timer = 0
            self.final_performance = {}
            
            # Session management
            self.session_timer = Timer()
            self.session_start_time = 0
            
            # Initialize first phase
            self.reset_phase_state()
            
        except Exception as e:
            logger.error(f"Failed to initialize OpeningPrinciplesFirstGameState: {e}")
            raise
    
    def create_ui_elements(self):
        """Create comprehensive UI system for the final module"""
        try:
            # Navigation buttons
            self.back_button = Button(
                text="← Back to Menu",
                pos=(50, 40),
                size=(140, 45),
                callback=self.on_back_clicked,
                config=self.config
            )
            
            # Phase progress bar
            total_phases = len(self.module_phases)
            self.phase_progress_bar = ProgressBar(
                pos=(self.config.SCREEN_WIDTH // 2 - 300, 25),
                size=(600, 30),
                max_value=total_phases,
                config=self.config
            )
            
            # Learning aid buttons (left side)
            button_x = 50
            button_width = 140
            button_height = 35
            button_spacing = 45
            
            self.hint_button = Button(
                text="💡 Get Hint",
                pos=(button_x, 100),
                size=(button_width, button_height),
                callback=self.toggle_hints,
                config=self.config
            )
            
            self.principles_button = Button(
                text="📚 Show Rules",
                pos=(button_x, 100 + button_spacing),
                size=(button_width, button_height),
                callback=self.toggle_principle_highlights,
                config=self.config
            )
            
            self.suggestions_button = Button(
                text="🎯 Suggestions",
                pos=(button_x, 100 + button_spacing * 2),
                size=(button_width, button_height),
                callback=self.toggle_suggested_moves,
                config=self.config
            )
            
            self.coaching_button = Button(
                text="🎓 Coach Mode",
                pos=(button_x, 100 + button_spacing * 3),
                size=(button_width, button_height),
                callback=self.toggle_coaching_mode,
                config=self.config
            )
            
            # Control buttons (right side)
            control_x = self.config.SCREEN_WIDTH - 190
            
            self.reset_button = Button(
                text="🔄 Reset",
                pos=(control_x, 100),
                size=(button_width, button_height),
                callback=self.reset_current_exercise,
                config=self.config
            )
            
            self.skip_button = Button(
                text="⏭️ Skip",
                pos=(control_x, 100 + button_spacing),
                size=(button_width, button_height),
                callback=self.skip_current_exercise,
                config=self.config
            )
            
            self.analyze_button = Button(
                text="🔍 Analyze",
                pos=(control_x, 100 + button_spacing * 2),
                size=(button_width, button_height),
                callback=self.analyze_position,
                config=self.config
            )
            
            # Phase-specific buttons
            self.next_phase_button = Button(
                text="Continue →",
                pos=(self.config.SCREEN_WIDTH // 2 - 100, 680),
                size=(200, 50),
                callback=self.advance_to_next_phase,
                config=self.config
            )
            
            self.start_game_button = Button(
                text="🚀 Start First Game!",
                pos=(self.config.SCREEN_WIDTH // 2 - 120, 680),
                size=(240, 50),
                callback=self.start_first_game,
                config=self.config
            )
            
            # Answer buttons for tutorial phases
            answer_y = 680
            self.principle_buttons = {}
            for i, principle in enumerate(self.opening_principles.keys()):
                x_pos = 100 + (i % 3) * 200
                y_pos = answer_y + (i // 3) * 60
                
                self.principle_buttons[principle] = Button(
                    text=self.opening_principles[principle]['name'][:12] + "...",
                    pos=(x_pos, y_pos),
                    size=(180, 45),
                    callback=lambda p=principle: self.select_principle(p),
                    config=self.config
                )
            
            # Coaching feedback panel
            self.coaching_panel_visible = False
            
            # Hint navigation
            self.hint_prev_button = Button(
                text="← Prev",
                pos=(self.config.SCREEN_WIDTH // 2 - 150, 630),
                size=(80, 35),
                callback=self.previous_hint,
                config=self.config
            )
            
            self.hint_next_button = Button(
                text="Next →",
                pos=(self.config.SCREEN_WIDTH // 2 + 70, 630),
                size=(80, 35),
                callback=self.next_hint,
                config=self.config
            )
            
        except Exception as e:
            logger.error(f"Failed to create UI elements: {e}")
            raise
    
    def enter(self):
        """Enter the opening principles and first game module"""
        try:
            super().enter()
            self.session_start_time = pygame.time.get_ticks()
            self.session_timer.reset()
            
            # Reset all progress
            self.current_phase = 0
            self.phase_progress = 0
            self.total_attempts = 0
            self.correct_answers = 0
            
            for principle in self.opening_principles:
                self.principle_mastery[principle] = 0.0
            
            self.phase_progress_bar.set_value(0)
            self.module_completed = False
            
            # Start with opening principles tutorial
            self.start_opening_principles_tutorial()
            
            # Start background music
            try:
                self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
            except Exception as e:
                logger.warning(f"Failed to play learning music: {e}")
                
        except Exception as e:
            logger.error(f"Failed to enter OpeningPrinciplesFirstGameState: {e}")
            self.engine.change_state(GameState.MAIN_MENU)
    
    def reset_phase_state(self):
        """Reset state for current phase"""
        self.current_exercise = None
        self.selected_square = None
        self.show_feedback = False
        self.feedback_message = ""
        self.feedback_timer = 0
        self.hint_level = 0
        self.show_hints = False
        self.current_hint_text = ""
        
        # Clear board highlights
        self.chess_board.clear_highlights()
        self.chess_board.select_square(None)
    
    def start_opening_principles_tutorial(self):
        """Start the opening principles tutorial phase"""
        try:
            self.reset_phase_state()
            self.current_phase = 0
            
            # Generate first principle exercise
            self._generate_principle_exercise()
            
            # Show welcome message
            welcome_text = "Welcome to your final chess lesson! Let's master opening principles together!"
            try:
                animated_text = AnimatedText(
                    welcome_text,
                    (self.config.SCREEN_WIDTH // 2, 200),
                    32,
                    self.config.COLORS['secondary'],
                    4.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create welcome text: {e}")
                
        except Exception as e:
            logger.error(f"Error starting opening principles tutorial: {e}")
    
    def _generate_principle_exercise(self):
        """Generate an exercise for teaching opening principles"""
        try:
            # Cycle through principles
            principle_keys = list(self.opening_principles.keys())
            current_principle = principle_keys[self.phase_progress % len(principle_keys)]
            
            self.current_exercise = {
                'type': 'principle_tutorial',
                'principle': current_principle,
                'question': f"Which position better demonstrates: {self.opening_principles[current_principle]['name']}?",
                'correct_answer': None
            }
            
            # Create demonstration positions
            if current_principle == 'center_control':
                self._setup_center_control_demo()
            elif current_principle == 'piece_development':
                self._setup_development_demo()
            elif current_principle == 'king_safety':
                self._setup_king_safety_demo()
            elif current_principle == 'avoid_early_queen':
                self._setup_early_queen_demo()
            elif current_principle == 'no_wasted_moves':
                self._setup_wasted_moves_demo()
            elif current_principle == 'coordinate_pieces':
                self._setup_coordination_demo()
            
            # Setup hints for this principle
            self._setup_principle_hints(current_principle)
            
        except Exception as e:
            logger.error(f"Error generating principle exercise: {e}")
    
    def _setup_center_control_demo(self):
        """Create demonstration of center control principle"""
        try:
            self.chess_board.reset()
            
            # Show good center control
            if random.choice([True, False]):
                # Good example: Classical center
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.D5, chess.Piece(chess.PAWN, chess.BLACK))
                
                # Add some pieces
                self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NC6, chess.Piece(chess.KNIGHT, chess.BLACK))
                
                self.current_exercise['explanation'] = "Excellent! Both sides control the center with pawns on e4/d4 and e5/d5."
                self.current_exercise['correct_answer'] = 'good'
            else:
                # Bad example: No center control
                self.chess_board.board.set_piece_at(chess.A4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.H4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.A5, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.H5, chess.Piece(chess.PAWN, chess.BLACK))
                
                self.current_exercise['explanation'] = "Poor center control! Both sides ignored the important central squares."
                self.current_exercise['correct_answer'] = 'bad'
            
            # Highlight central squares
            for square in [chess.E4, chess.D4, chess.E5, chess.D5]:
                self.chess_board.highlight_square(square)
                
        except Exception as e:
            logger.error(f"Error setting up center control demo: {e}")
    
    def _setup_development_demo(self):
        """Create demonstration of piece development principle"""
        try:
            self.chess_board.reset()
            
            if random.choice([True, False]):
                # Good development
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NC3, chess.Piece(chess.KNIGHT, chess.WHITE))
                
                # Black development
                self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.NC6, chess.Piece(chess.KNIGHT, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.BC5, chess.Piece(chess.BISHOP, chess.BLACK))
                
                self.current_exercise['explanation'] = "Great development! Both sides brought out knights and bishops quickly."
                self.current_exercise['correct_answer'] = 'good'
            else:
                # Poor development - pieces still on back rank
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.H4, chess.Piece(chess.PAWN, chess.WHITE))
                
                # Black also underdeveloped
                self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.A5, chess.Piece(chess.PAWN, chess.BLACK))
                
                self.current_exercise['explanation'] = "Poor development! Too many pawn moves, pieces still sleeping."
                self.current_exercise['correct_answer'] = 'bad'
            
            # Highlight developed pieces vs undeveloped
            developed_squares = [chess.NF3, chess.BC4, chess.NC3, chess.NC6, chess.BC5]
            for square in developed_squares:
                if self.chess_board.board.piece_at(square):
                    self.chess_board.highlight_square(square)
                    
        except Exception as e:
            logger.error(f"Error setting up development demo: {e}")
    
    def _setup_king_safety_demo(self):
        """Create demonstration of king safety principle"""
        try:
            self.chess_board.reset()
            
            # Setup basic opening position
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.NC6, chess.Piece(chess.KNIGHT, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.BC5, chess.Piece(chess.BISHOP, chess.BLACK))
            
            if random.choice([True, False]):
                # Good: Both sides castled
                # Move rook for White castling
                self.chess_board.board.remove_piece_at(chess.H1)
                self.chess_board.board.set_piece_at(chess.F1, chess.Piece(chess.ROOK, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.G1, chess.Piece(chess.KING, chess.WHITE))
                
                # Black castled too
                self.chess_board.board.remove_piece_at(chess.H8)
                self.chess_board.board.set_piece_at(chess.F8, chess.Piece(chess.ROOK, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.G8, chess.Piece(chess.KING, chess.BLACK))
                
                self.current_exercise['explanation'] = "Perfect! Both kings are safely castled behind pawns."
                self.current_exercise['correct_answer'] = 'good'
                
                # Highlight castled kings
                self.chess_board.highlight_square(chess.G1)
                self.chess_board.highlight_square(chess.G8)
            else:
                # Bad: Kings still in center
                self.current_exercise['explanation'] = "Dangerous! Both kings are still in the center - easy targets!"
                self.current_exercise['correct_answer'] = 'bad'
                
                # Highlight vulnerable kings
                self.chess_board.highlight_square(chess.E1)
                self.chess_board.highlight_square(chess.E8)
                
        except Exception as e:
            logger.error(f"Error setting up king safety demo: {e}")
    
    def _setup_early_queen_demo(self):
        """Create demonstration of avoiding early queen moves"""
        try:
            self.chess_board.reset()
            
            if random.choice([True, False]):
                # Good: Queen stays home
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NC3, chess.Piece(chess.KNIGHT, chess.WHITE))
                
                self.current_exercise['explanation'] = "Excellent! Developed minor pieces first, queen stays safe."
                self.current_exercise['correct_answer'] = 'good'
                
                # Highlight good development
                for square in [chess.NF3, chess.BC4, chess.NC3]:
                    self.chess_board.highlight_square(square)
            else:
                # Bad: Early queen attack (Scholar's Mate attempt)
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.QH5, chess.Piece(chess.QUEEN, chess.WHITE))
                
                # Black defends properly
                self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
                self.chess_board.board.set_piece_at(chess.NF6, chess.Piece(chess.KNIGHT, chess.BLACK))
                
                self.current_exercise['explanation'] = "Bad idea! Queen came out too early and is now attacked by the knight."
                self.current_exercise['correct_answer'] = 'bad'
                
                # Highlight the problem
                self.chess_board.highlight_square(chess.QH5)  # Exposed queen
                self.chess_board.highlight_square(chess.NF6)  # Knight attacking it
                
        except Exception as e:
            logger.error(f"Error setting up early queen demo: {e}")
    
    def _setup_wasted_moves_demo(self):
        """Create demonstration of not wasting moves"""
        try:
            self.chess_board.reset()
            
            if random.choice([True, False]):
                # Good: Each piece developed once
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NC3, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.D3, chess.Piece(chess.PAWN, chess.WHITE))
                
                self.current_exercise['explanation'] = "Perfect! Each piece moved once to a good square."
                self.current_exercise['correct_answer'] = 'good'
                
                # Highlight efficient development
                for square in [chess.NF3, chess.BC4, chess.NC3]:
                    self.chess_board.highlight_square(square)
            else:
                # Bad: Moving same piece multiple times
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.BD3, chess.Piece(chess.BISHOP, chess.WHITE))  # Bishop moved twice
                # Simulate: Bc1-e3-d3 (two moves for same piece)
                
                self.current_exercise['explanation'] = "Wasteful! The bishop moved twice while other pieces aren't developed."
                self.current_exercise['correct_answer'] = 'bad'
                
                # Highlight the inefficient piece
                self.chess_board.highlight_square(chess.BD3)
                
        except Exception as e:
            logger.error(f"Error setting up wasted moves demo: {e}")
    
    def _setup_coordination_demo(self):
        """Create demonstration of piece coordination"""
        try:
            self.chess_board.reset()
            
            if random.choice([True, False]):
                # Good: Pieces support each other
                self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NC3, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.BE2, chess.Piece(chess.BISHOP, chess.WHITE))
                
                # Pieces work together: pawns control center, knight protects pawn, etc.
                self.current_exercise['explanation'] = "Excellent coordination! Pieces support each other and the center."
                self.current_exercise['correct_answer'] = 'good'
                
                # Highlight coordinated pieces
                for square in [chess.E4, chess.D4, chess.NF3, chess.NC3]:
                    self.chess_board.highlight_square(square)
            else:
                # Bad: Pieces don't coordinate
                self.chess_board.board.set_piece_at(chess.A4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.H4, chess.Piece(chess.PAWN, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NA3, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.NH3, chess.Piece(chess.KNIGHT, chess.WHITE))
                
                self.current_exercise['explanation'] = "Poor coordination! Pieces are isolated and don't work together."
                self.current_exercise['correct_answer'] = 'bad'
                
                # Highlight poorly placed pieces
                for square in [chess.NA3, chess.NH3]:
                    self.chess_board.highlight_square(square)
                    
        except Exception as e:
            logger.error(f"Error setting up coordination demo: {e}")
    
    def _setup_principle_hints(self, principle):
        """Setup hints for the current principle"""
        try:
            principle_data = self.opening_principles[principle]
            
            self.hint_progression = [
                f"Focus on: {principle_data['name']}",
                f"Key idea: {principle_data['description']}",
                f"Why important: {principle_data['importance']}",
                f"Remember: {principle_data['memory_aid']}"
            ]
            
            self.hint_level = 0
            if self.hint_progression:
                self.current_hint_text = self.hint_progression[0]
                
        except Exception as e:
            logger.error(f"Error setting up principle hints: {e}")
    
    def start_mistake_recognition_phase(self):
        """Start the mistake recognition phase"""
        try:
            self.reset_phase_state()
            self.current_phase = 1
            self._generate_mistake_exercise()
            
            # Show phase transition message
            transition_text = "Now let's learn to spot common opening mistakes!"
            try:
                animated_text = AnimatedText(
                    transition_text,
                    (self.config.SCREEN_WIDTH // 2, 200),
                    32,
                    self.config.COLORS['accent'],
                    3.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create transition text: {e}")
                
        except Exception as e:
            logger.error(f"Error starting mistake recognition phase: {e}")
    
    def _generate_mistake_exercise(self):
        """Generate an exercise for recognizing common mistakes"""
        try:
            # Cycle through common mistakes
            mistake_keys = list(self.common_mistakes.keys())
            current_mistake = mistake_keys[self.phase_progress % len(mistake_keys)]
            
            self.current_exercise = {
                'type': 'mistake_recognition',
                'mistake': current_mistake,
                'question': f"What's wrong with this opening play?",
                'correct_answer': current_mistake
            }
            
            # Create positions showing the mistake
            if current_mistake == 'scholars_mate_attempt':
                self._setup_scholars_mate_mistake()
            elif current_mistake == 'too_many_pawn_moves':
                self._setup_pawn_storm_mistake()
            elif current_mistake == 'copying_opponent':
                self._setup_copycat_mistake()
            elif current_mistake == 'neglecting_king_safety':
                self._setup_unsafe_king_mistake()
            elif current_mistake == 'premature_attacks':
                self._setup_premature_attack_mistake()
            elif current_mistake == 'wrong_piece_order':
                self._setup_wrong_order_mistake()
            
        except Exception as e:
            logger.error(f"Error generating mistake exercise: {e}")
    
    def _setup_scholars_mate_mistake(self):
        """Setup Scholar's Mate attempt demonstration"""
        try:
            self.chess_board.reset()
            
            # White's Scholar's Mate attempt
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.QH5, chess.Piece(chess.QUEEN, chess.WHITE))
            
            # Black's proper defense
            self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NF6, chess.Piece(chess.KNIGHT, chess.BLACK))
            
            self.current_exercise['explanation'] = "Scholar's Mate attempt! Queen came out too early and is now attacked."
            
            # Highlight the problems
            self.chess_board.highlight_square(chess.QH5)  # Premature queen
            self.chess_board.highlight_square(chess.NF6)  # Knight attacking it
            
        except Exception as e:
            logger.error(f"Error setting up Scholar's Mate mistake: {e}")
    
    def _setup_pawn_storm_mistake(self):
        """Setup too many pawn moves mistake"""
        try:
            self.chess_board.reset()
            
            # White moving too many pawns
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.F4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.G4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.H4, chess.Piece(chess.PAWN, chess.WHITE))
            
            # Black develops pieces properly
            self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NC6, chess.Piece(chess.KNIGHT, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NF6, chess.Piece(chess.KNIGHT, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.BC5, chess.Piece(chess.BISHOP, chess.BLACK))
            
            self.current_exercise['explanation'] = "Too many pawn moves! White fell behind in development."
            
            # Highlight the excessive pawns
            for square in [chess.F4, chess.G4, chess.H4]:
                self.chess_board.highlight_square(square)
                
        except Exception as e:
            logger.error(f"Error setting up pawn storm mistake: {e}")
    
    def _setup_copycat_mistake(self):
        """Setup copycat strategy mistake"""
        try:
            self.chess_board.reset()
            
            # Both sides mirror each other exactly
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.NF6, chess.Piece(chess.KNIGHT, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.BC5, chess.Piece(chess.BISHOP, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NG5, chess.Piece(chess.KNIGHT, chess.WHITE))
            # Black copies again, but this allows a tactic
            self.chess_board.board.set_piece_at(chess.NG4, chess.Piece(chess.KNIGHT, chess.BLACK))
            
            # Now White can play Nxf7! forking king and rook
            
            self.current_exercise['explanation'] = "Dangerous copying! Black mindlessly copied and walked into a fork."
            
            # Highlight the problematic mirroring
            self.chess_board.highlight_square(chess.NG5)
            self.chess_board.highlight_square(chess.NG4)
            
        except Exception as e:
            logger.error(f"Error setting up copycat mistake: {e}")
    
    def _setup_unsafe_king_mistake(self):
        """Setup king safety neglect mistake"""
        try:
            self.chess_board.reset()
            
            # Position where center is opening but king hasn't castled
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
            
            # Black pieces attacking the center/king
            self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NC6, chess.Piece(chess.KNIGHT, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.BC5, chess.Piece(chess.BISHOP, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.QF6, chess.Piece(chess.QUEEN, chess.BLACK))
            
            self.current_exercise['explanation'] = "King in danger! White should have castled before the center opened up."
            
            # Highlight the exposed king
            self.chess_board.highlight_square(chess.E1)
            
        except Exception as e:
            logger.error(f"Error setting up unsafe king mistake: {e}")
    
    def _setup_premature_attack_mistake(self):
        """Setup premature attack mistake"""
        try:
            self.chess_board.reset()
            
            # White attacks too early without development
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.QH5, chess.Piece(chess.QUEEN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
            # Attacking f7 with only 2 pieces
            
            # Black defends properly and develops
            self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NC6, chess.Piece(chess.KNIGHT, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NF6, chess.Piece(chess.KNIGHT, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.D6, chess.Piece(chess.PAWN, chess.BLACK))
            
            self.current_exercise['explanation'] = "Premature attack! White attacks with insufficient force."
            
            # Highlight the weak attack
            self.chess_board.highlight_square(chess.QH5)
            self.chess_board.highlight_square(chess.BC4)
            
        except Exception as e:
            logger.error(f"Error setting up premature attack mistake: {e}")
    
    def _setup_wrong_order_mistake(self):
        """Setup wrong development order mistake"""
        try:
            self.chess_board.reset()
            
            # Wrong order: Queen and rooks before minor pieces
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.QE2, chess.Piece(chess.QUEEN, chess.WHITE))  # Queen too early
            self.chess_board.board.set_piece_at(chess.RE1, chess.Piece(chess.ROOK, chess.WHITE))   # Rook too early
            # Minor pieces still undeveloped
            
            self.current_exercise['explanation'] = "Wrong order! Develop knights and bishops before queen and rooks."
            
            # Highlight the misplaced major pieces
            self.chess_board.highlight_square(chess.QE2)
            self.chess_board.highlight_square(chess.RE1)
            
        except Exception as e:
            logger.error(f"Error setting up wrong order mistake: {e}")
    
    def start_guided_practice_phase(self):
        """Start the guided practice phase"""
        try:
            self.reset_phase_state()
            self.current_phase = 2
            self._generate_practice_exercise()
            
            # Show phase transition message
            transition_text = "Time to practice! Apply the principles you've learned!"
            try:
                animated_text = AnimatedText(
                    transition_text,
                    (self.config.SCREEN_WIDTH // 2, 200),
                    32,
                    self.config.COLORS['primary'],
                    3.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create transition text: {e}")
                
        except Exception as e:
            logger.error(f"Error starting guided practice phase: {e}")
    
    def _generate_practice_exercise(self):
        """Generate a practice exercise"""
        try:
            practice_scenarios = [
                'choose_opening_move',
                'best_development',
                'castle_timing',
                'piece_coordination'
            ]
            
            scenario = practice_scenarios[self.phase_progress % len(practice_scenarios)]
            
            self.current_exercise = {
                'type': 'guided_practice',
                'scenario': scenario,
                'target_squares': [],
                'correct_moves': []
            }
            
            if scenario == 'choose_opening_move':
                self._setup_opening_move_choice()
            elif scenario == 'best_development':
                self._setup_development_choice()
            elif scenario == 'castle_timing':
                self._setup_castling_choice()
            elif scenario == 'piece_coordination':
                self._setup_coordination_choice()
                
        except Exception as e:
            logger.error(f"Error generating practice exercise: {e}")
    
    def _setup_opening_move_choice(self):
        """Setup opening move choice exercise"""
        try:
            self.chess_board.reset()
            
            self.current_exercise['question'] = "Choose the best opening move for White:"
            self.current_exercise['target_squares'] = [chess.E4, chess.D4]  # Good center moves
            self.current_exercise['explanation'] = "Excellent! Both e4 and d4 control the center - the foundation of good chess!"
            
            # Highlight the central squares
            for square in [chess.E4, chess.D4, chess.E5, chess.D5]:
                self.chess_board.highlight_square(square)
                
        except Exception as e:
            logger.error(f"Error setting up opening move choice: {e}")
    
    def _setup_development_choice(self):
        """Setup development choice exercise"""
        try:
            self.chess_board.reset()
            
            # Position after 1.e4 e5
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
            
            self.current_exercise['question'] = "What's White's best developing move?"
            self.current_exercise['target_squares'] = [chess.NF3, chess.BC4, chess.NC3]  # Good development
            self.current_exercise['explanation'] = "Perfect! Developing pieces quickly is key to good opening play!"
            
        except Exception as e:
            logger.error(f"Error setting up development choice: {e}")
    
    def _setup_castling_choice(self):
        """Setup castling timing exercise"""
        try:
            self.chess_board.reset()
            
            # Position where castling is available and good
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.NC6, chess.Piece(chess.KNIGHT, chess.BLACK))
            self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.BC5, chess.Piece(chess.BISHOP, chess.BLACK))
            
            self.current_exercise['question'] = "White can castle now. Should they?"
            self.current_exercise['correct_answer'] = 'yes'
            self.current_exercise['explanation'] = "Yes! Castle early to keep your king safe!"
            
            # Highlight the king (candidate for castling)
            self.chess_board.highlight_square(chess.E1)
            
        except Exception as e:
            logger.error(f"Error setting up castling choice: {e}")
    
    def _setup_coordination_choice(self):
        """Setup piece coordination exercise"""
        try:
            self.chess_board.reset()
            
            # Position where pieces can coordinate
            self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
            
            self.current_exercise['question'] = "Where should the knight on b1 go to best coordinate?"
            self.current_exercise['target_squares'] = [chess.NC3, chess.ND2]  # Supporting the center
            self.current_exercise['explanation'] = "Great! The knight supports the center and coordinates with other pieces!"
            
            # Highlight the center that needs support
            for square in [chess.E4, chess.D4]:
                self.chess_board.highlight_square(square)
                
        except Exception as e:
            logger.error(f"Error setting up coordination choice: {e}")
    
    def start_first_game_preparation(self):
        """Start preparation for the first full game"""
        try:
            self.reset_phase_state()
            self.current_phase = 3
            
            # Show preparation screen
            prep_text = "🎉 Ready for your first complete chess game! Let me prepare you..."
            try:
                animated_text = AnimatedText(
                    prep_text,
                    (self.config.SCREEN_WIDTH // 2, 300),
                    36,
                    self.config.COLORS['secondary'],
                    4.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create prep text: {e}")
            
            # Setup fresh board for game
            self.chess_board.reset()
            
            # Enable coaching mode
            self.real_time_coaching = True
            self.coaching_panel_visible = True
            
        except Exception as e:
            logger.error(f"Error starting first game preparation: {e}")
    
    def start_first_game(self):
        """Start the guided first game"""
        try:
            self.reset_phase_state()
            self.current_phase = 4
            
            # Initialize game state
            self.chess_board.reset()
            self.game_move_count = 0
            self.coaching_messages = []
            self.move_evaluations = []
            self.game_phase = 'opening'
            
            # Show game start message
            start_text = "🚀 Your first chess game begins! I'll guide you every step of the way!"
            try:
                animated_text = AnimatedText(
                    start_text,
                    (self.config.SCREEN_WIDTH // 2, 200),
                    32,
                    self.config.COLORS['accent'],
                    4.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create start text: {e}")
            
            # First coaching message
            self.add_coaching_message("Welcome to your first game! Remember: control center, develop pieces, castle early!")
            
            # Enable all helpful aids
            self.show_principle_highlights = True
            self.show_suggested_moves = True
            self.real_time_coaching = True
            
        except Exception as e:
            logger.error(f"Error starting first game: {e}")
    
    def add_coaching_message(self, message):
        """Add a coaching message to the queue"""
        try:
            self.coaching_messages.append({
                'text': message,
                'timestamp': pygame.time.get_ticks(),
                'duration': 5000,  # 5 seconds
                'type': 'coaching'
            })
        except Exception as e:
            logger.error(f"Error adding coaching message: {e}")
    
    def handle_square_click(self, square):
        """Handle square clicks for all phases"""
        try:
            if self.show_feedback or square is None:
                return
            
            self.selected_square = square
            self.total_attempts += 1
            
            current_phase_name = self.module_phases[self.current_phase]
            
            if current_phase_name == 'opening_principles_tutorial':
                self._handle_principle_tutorial_click(square)
            elif current_phase_name == 'mistake_recognition':
                self._handle_mistake_recognition_click(square)
            elif current_phase_name == 'guided_practice':
                self._handle_practice_click(square)
            elif current_phase_name == 'guided_first_game':
                self._handle_game_move(square)
                
        except Exception as e:
            logger.error(f"Error handling square click: {e}")
    
    def _handle_principle_tutorial_click(self, square):
        """Handle clicks during principle tutorial"""
        try:
            # For tutorial, we mainly use buttons, but we can highlight squares
            if self.current_exercise and 'explanation' in self.current_exercise:
                self.show_feedback = True
                self.feedback_message = self.current_exercise['explanation']
                self.correct_answers += 1
                
        except Exception as e:
            logger.error(f"Error in principle tutorial click: {e}")
    
    def _handle_mistake_recognition_click(self, square):
        """Handle clicks during mistake recognition"""
        try:
            # Similar to tutorial - mainly educational
            if self.current_exercise and 'explanation' in self.current_exercise:
                self.show_feedback = True
                self.feedback_message = self.current_exercise['explanation']
                self.correct_answers += 1
                
        except Exception as e:
            logger.error(f"Error in mistake recognition click: {e}")
    
    def _handle_practice_click(self, square):
        """Handle clicks during guided practice"""
        try:
            if not self.current_exercise:
                return
                
            target_squares = self.current_exercise.get('target_squares', [])
            
            if square in target_squares:
                self.show_feedback = True
                self.feedback_message = self.current_exercise.get('explanation', 'Correct!')
                self.correct_answers += 1
                
                # Make the move on the board
                if self.chess_board.board.piece_at(square) is None:
                    # Find a piece that can move to this square
                    self._make_practice_move(square)
            else:
                self.show_feedback = True
                self.feedback_message = "Not the best choice. Remember the opening principles!"
                
        except Exception as e:
            logger.error(f"Error in practice click: {e}")
    
    def _make_practice_move(self, target_square):
        """Make a practice move to demonstrate"""
        try:
            scenario = self.current_exercise.get('scenario', '')
            
            if scenario == 'choose_opening_move':
                if target_square == chess.E4:
                    self.chess_board.board.set_piece_at(chess.E4, chess.Piece(chess.PAWN, chess.WHITE))
                elif target_square == chess.D4:
                    self.chess_board.board.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))
            elif scenario == 'best_development':
                if target_square == chess.NF3:
                    self.chess_board.board.set_piece_at(chess.NF3, chess.Piece(chess.KNIGHT, chess.WHITE))
                elif target_square == chess.BC4:
                    self.chess_board.board.set_piece_at(chess.BC4, chess.Piece(chess.BISHOP, chess.WHITE))
                elif target_square == chess.NC3:
                    self.chess_board.board.set_piece_at(chess.NC3, chess.Piece(chess.KNIGHT, chess.WHITE))
            
            # Highlight the moved piece
            self.chess_board.highlight_square(target_square)
            
        except Exception as e:
            logger.error(f"Error making practice move: {e}")
    
    def _handle_game_move(self, square):
        """Handle moves during the actual game"""
        try:
            # This is where we handle real chess moves with coaching
            self.game_move_count += 1
            
            # Evaluate the move according to opening principles
            move_evaluation = self._evaluate_move_against_principles(square)
            self.move_evaluations.append(move_evaluation)
            
            # Provide real-time coaching
            if self.real_time_coaching:
                coaching_message = self._generate_coaching_message(move_evaluation)
                self.add_coaching_message(coaching_message)
            
            # Make AI response (simplified)
            if self.game_move_count % 2 == 1:  # After player's move
                ai_move = self._generate_ai_move()
                if ai_move:
                    self.game_move_count += 1
            
            # Check if we've reached middlegame
            if self.game_move_count > 20:
                self.game_phase = 'middlegame'
                self.add_coaching_message("Great job! You've completed the opening. The middlegame begins!")
                self.advance_to_next_phase()  # Move to analysis
                
        except Exception as e:
            logger.error(f"Error handling game move: {e}")
    
    def _evaluate_move_against_principles(self, square):
        """Evaluate a move against opening principles"""
        try:
            evaluation = {
                'square': square,
                'move_number': self.game_move_count,
                'principles_followed': [],
                'principles_violated': [],
                'score': 50  # Base score
            }
            
            # Check against each principle
            piece = self.chess_board.board.piece_at(square)
            
            # Center control
            if square in [chess.E4, chess.D4, chess.E5, chess.D5]:
                evaluation['principles_followed'].append('center_control')
                evaluation['score'] += 20
            
            # Development
            if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                evaluation['principles_followed'].append('piece_development')
                evaluation['score'] += 15
            
            # Early queen check
            if piece and piece.piece_type == chess.QUEEN and self.game_move_count < 8:
                evaluation['principles_violated'].append('avoid_early_queen')
                evaluation['score'] -= 25
            
            # Castling (simplified check)
            if square in [chess.G1, chess.C1, chess.G8, chess.C8]:
                evaluation['principles_followed'].append('king_safety')
                evaluation['score'] += 25
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating move: {e}")
            return {'square': square, 'score': 50, 'principles_followed': [], 'principles_violated': []}
    
    def _generate_coaching_message(self, evaluation):
        """Generate coaching message based on move evaluation"""
        try:
            score = evaluation['score']
            followed = evaluation['principles_followed']
            violated = evaluation['principles_violated']
            
            if score >= 80:
                messages = [
                    "Excellent move! Perfect application of opening principles!",
                    "Outstanding! You're really getting the hang of this!",
                    "Perfect! That move follows all the right principles!"
                ]
            elif score >= 60:
                messages = [
                    "Good move! You're applying the principles well.",
                    "Nice! That's solid opening play.",
                    "Well done! Keep following those principles!"
                ]
            elif score >= 40:
                messages = [
                    "Reasonable move, but consider the opening principles.",
                    "Not bad, but there might be better options.",
                    "Think about development and center control."
                ]
            else:
                messages = [
                    "Careful! That move violates opening principles.",
                    "Let's reconsider - remember the fundamentals!",
                    "Think about what we learned about good openings."
                ]
            
            base_message = random.choice(messages)
            
            # Add specific principle feedback
            if followed:
                principle_names = [self.opening_principles[p]['name'] for p in followed]
                base_message += f" Great use of: {', '.join(principle_names)}!"
            
            if violated:
                principle_names = [self.opening_principles[p]['name'] for p in violated]
                base_message += f" Watch out for: {', '.join(principle_names)}."
            
            return base_message
            
        except Exception as e:
            logger.error(f"Error generating coaching message: {e}")
            return "Keep going! You're learning!"
    
    def _generate_ai_move(self):
        """Generate AI move (simplified for beginner-friendly opponent)"""
        try:
            # Very basic AI that makes reasonable but not perfect moves
            # This is just a placeholder - in a real implementation, you'd use a proper chess engine
            
            available_moves = []
            
            # AI tries to follow basic principles too
            if self.game_move_count < 10:  # Opening phase
                # Try to develop pieces or control center
                if self.game_move_count == 2:  # AI's first move
                    return chess.E5  # Respond to e4 with e5
                elif self.game_move_count == 4:  # AI's second move
                    return chess.NC6  # Develop knight
            
            return None  # Simplified - just return None for now
            
        except Exception as e:
            logger.error(f"Error generating AI move: {e}")
            return None
    
    def start_game_analysis_phase(self):
        """Start the game analysis phase"""
        try:
            self.reset_phase_state()
            self.current_phase = 5
            
            # Calculate game performance
            total_score = sum(eval.get('score', 50) for eval in self.move_evaluations)
            average_score = total_score / max(len(self.move_evaluations), 1)
            
            # Show analysis message
            analysis_text = f"Game complete! Let's analyze your performance (Average: {average_score:.0f}/100)"
            try:
                animated_text = AnimatedText(
                    analysis_text,
                    (self.config.SCREEN_WIDTH // 2, 200),
                    32,
                    self.config.COLORS['primary'],
                    4.0,
                    self.config
                )
                self.animated_texts.append(animated_text)
            except Exception as e:
                logger.warning(f"Failed to create analysis text: {e}")
            
            # Prepare analysis data
            self._prepare_game_analysis()
            
        except Exception as e:
            logger.error(f"Error starting game analysis: {e}")
    
    def _prepare_game_analysis(self):
        """Prepare detailed game analysis"""
        try:
            analysis = {
                'total_moves': len(self.move_evaluations),
                'average_score': sum(eval.get('score', 50) for eval in self.move_evaluations) / max(len(self.move_evaluations), 1),
                'principles_mastered': {},
                'areas_for_improvement': [],
                'best_moves': [],
                'questionable_moves': []
            }
            
            # Analyze principle adherence
            for principle in self.opening_principles:
                followed_count = sum(1 for eval in self.move_evaluations if principle in eval.get('principles_followed', []))
                violated_count = sum(1 for eval in self.move_evaluations if principle in eval.get('principles_violated', []))
                
                if followed_count > violated_count:
                    analysis['principles_mastered'][principle] = followed_count
                elif violated_count > 0:
                    analysis['areas_for_improvement'].append(principle)
            
            # Find best and worst moves
            for evaluation in self.move_evaluations:
                if evaluation.get('score', 50) >= 75:
                    analysis['best_moves'].append(evaluation)
                elif evaluation.get('score', 50) < 40:
                    analysis['questionable_moves'].append(evaluation)
            
            self.final_performance = analysis
            
        except Exception as e:
            logger.error(f"Error preparing game analysis: {e}")
    
    def complete_module(self):
        """Complete the entire module"""
        try:
            self.current_phase = 6
            self.module_completed = True
            self.completion_timer = 0
            
            # Calculate final score
            principle_scores = list(self.principle_mastery.values())
            avg_principle_mastery = sum(principle_scores) / max(len(principle_scores), 1)
            
            game_performance = self.final_performance.get('average_score', 50)
            accuracy = (self.correct_answers / max(self.total_attempts, 1)) * 100
            
            final_score = (avg_principle_mastery * 0.4 + game_performance * 0.4 + accuracy * 0.2)
            
            self.final_performance['overall_score'] = final_score
            
            # Epic celebration
            for _ in range(150):  # Huge celebration for completing the course!
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(200, 600)
                colors = [
                    (255, 215, 0),   # Gold
                    (255, 255, 255), # White
                    (255, 0, 255),   # Magenta
                    (0, 255, 255),   # Cyan
                    (255, 100, 100), # Light red
                    (100, 255, 100), # Light green
                ]
                
                self.celebration_particles.append({
                    'x': self.config.SCREEN_WIDTH // 2,
                    'y': self.config.SCREEN_HEIGHT // 2,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle),
                    'color': random.choice(colors),
                    'life': random.uniform(4.0, 8.0),
                    'size': random.randint(6, 25),
                    'gravity': random.uniform(100, 250)
                })
            
            # Play completion fanfare
            try:
                self.engine.audio_manager.play_sound('victory.wav')
            except Exception as e:
                logger.warning(f"Failed to play completion sound: {e}")
                
        except Exception as e:
            logger.error(f"Error completing module: {e}")
            self.module_completed = True
    
    # UI and interaction methods
    def select_principle(self, principle):
        """Handle principle selection"""
        try:
            if principle in self.opening_principles:
                self.show_feedback = True
                principle_data = self.opening_principles[principle]
                self.feedback_message = f"{principle_data['name']}: {principle_data['description']}"
                self.correct_answers += 1
                
        except Exception as e:
            logger.error(f"Error selecting principle: {e}")
    
    def toggle_hints(self):
        """Toggle hint display"""
        try:
            self.show_hints = not self.show_hints
            if self.show_hints and self.hint_progression:
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
                if self.show_hints:
                    self.current_hint_text = self.hint_progression[self.hint_level]
                    
        except Exception as e:
            logger.error(f"Error showing next hint: {e}")
    
    def previous_hint(self):
        """Show previous hint"""
        try:
            if self.hint_level > 0:
                self.hint_level -= 1
                if self.show_hints:
                    self.current_hint_text = self.hint_progression[self.hint_level]
                    
        except Exception as e:
            logger.error(f"Error showing previous hint: {e}")
    
    def toggle_principle_highlights(self):
        """Toggle principle highlighting"""
        self.show_principle_highlights = not self.show_principle_highlights
    
    def toggle_suggested_moves(self):
        """Toggle suggested move display"""
        self.show_suggested_moves = not self.show_suggested_moves
    
    def toggle_coaching_mode(self):
        """Toggle coaching mode"""
        self.real_time_coaching = not self.real_time_coaching
        self.coaching_panel_visible = not self.coaching_panel_visible
    
    def reset_current_exercise(self):
        """Reset current exercise"""
        try:
            current_phase_name = self.module_phases[self.current_phase]
            
            if current_phase_name == 'opening_principles_tutorial':
                self._generate_principle_exercise()
            elif current_phase_name == 'mistake_recognition':
                self._generate_mistake_exercise()
            elif current_phase_name == 'guided_practice':
                self._generate_practice_exercise()
            elif current_phase_name == 'guided_first_game':
                self.chess_board.reset()
                self.game_move_count = 0
                self.coaching_messages = []
                self.move_evaluations = []
                
            self.show_feedback = False
            self.selected_square = None
            
        except Exception as e:
            logger.error(f"Error resetting exercise: {e}")
    
    def skip_current_exercise(self):
        """Skip current exercise"""
        try:
            self.advance_to_next_phase()
        except Exception as e:
            logger.error(f"Error skipping exercise: {e}")
    
    def analyze_position(self):
        """Analyze current position"""
        try:
            self.show_principle_highlights = True
            self.show_suggested_moves = True
            
            # Show analysis message
            self.show_feedback = True
            self.feedback_message = "Analysis mode: See highlighted squares for principle-based suggestions!"
            
        except Exception as e:
            logger.error(f"Error analyzing position: {e}")
    
    def advance_to_next_phase(self):
        """Advance to the next phase or exercise"""
        try:
            current_phase_name = self.module_phases[self.current_phase]
            max_exercises = self.exercises_per_phase[current_phase_name]
            
            self.phase_progress += 1
            
            if self.phase_progress >= max_exercises:
                # Move to next phase
                self.current_phase += 1
                self.phase_progress = 0
                self.phase_progress_bar.set_value(self.current_phase)
                
                if self.current_phase >= len(self.module_phases):
                    self.complete_module()
                else:
                    # Start next phase
                    next_phase_name = self.module_phases[self.current_phase]
                    
                    if next_phase_name == 'mistake_recognition':
                        self.start_mistake_recognition_phase()
                    elif next_phase_name == 'guided_practice':
                        self.start_guided_practice_phase()
                    elif next_phase_name == 'first_game_preparation':
                        self.start_first_game_preparation()
                    elif next_phase_name == 'guided_first_game':
                        self.start_first_game()
                    elif next_phase_name == 'game_analysis':
                        self.start_game_analysis_phase()
                    elif next_phase_name == 'completion_celebration':
                        self.complete_module()
            else:
                # Generate next exercise in current phase
                if current_phase_name == 'opening_principles_tutorial':
                    self._generate_principle_exercise()
                elif current_phase_name == 'mistake_recognition':
                    self._generate_mistake_exercise()
                elif current_phase_name == 'guided_practice':
                    self._generate_practice_exercise()
            
            self.show_feedback = False
            
        except Exception as e:
            logger.error(f"Error advancing to next phase: {e}")
    
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
            self.principles_button.handle_event(event)
            self.suggestions_button.handle_event(event)
            self.coaching_button.handle_event(event)
            self.reset_button.handle_event(event)
            self.skip_button.handle_event(event)
            self.analyze_button.handle_event(event)
            
            # Phase-specific buttons
            if self.current_phase in [0, 1, 2]:  # Tutorial, mistakes, practice
                self.next_phase_button.handle_event(event)
            elif self.current_phase == 3:  # Game preparation
                self.start_game_button.handle_event(event)
            
            # Principle buttons (for tutorial phase)
            if self.current_phase == 0:
                for button in self.principle_buttons.values():
                    button.handle_event(event)
            
            # Hint navigation
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
                if event.key == pygame.K_SPACE:
                    if self.show_feedback:
                        self.advance_to_next_phase()
                    elif self.current_phase == 3:
                        self.start_first_game()
                elif event.key == pygame.K_h:
                    self.toggle_hints()
                elif event.key == pygame.K_r:
                    self.reset_current_exercise()
                elif event.key == pygame.K_c:
                    self.toggle_coaching_mode()
                elif event.key == pygame.K_p:
                    self.toggle_principle_highlights()
                elif event.key == pygame.K_s:
                    self.toggle_suggested_moves()
                elif event.key == pygame.K_a:
                    self.analyze_position()
                elif event.key == pygame.K_LEFT and self.show_hints:
                    self.previous_hint()
                elif event.key == pygame.K_RIGHT and self.show_hints:
                    self.next_hint()
                    
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
            self.principles_button.update(dt, mouse_pos)
            self.suggestions_button.update(dt, mouse_pos)
            self.coaching_button.update(dt, mouse_pos)
            self.reset_button.update(dt, mouse_pos)
            self.skip_button.update(dt, mouse_pos)
            self.analyze_button.update(dt, mouse_pos)
            
            # Phase-specific buttons
            if self.current_phase in [0, 1, 2]:
                self.next_phase_button.update(dt, mouse_pos)
            elif self.current_phase == 3:
                self.start_game_button.update(dt, mouse_pos)
            
            # Principle buttons
            if self.current_phase == 0:
                for button in self.principle_buttons.values():
                    button.update(dt, mouse_pos)
            
            # Hint navigation
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
            
            # Update coaching messages
            current_time = pygame.time.get_ticks()
            self.coaching_messages = [
                msg for msg in self.coaching_messages 
                if current_time - msg['timestamp'] < msg['duration']
            ]
            
            # Update feedback timer
            if self.show_feedback:
                self.feedback_timer += dt
            
            # Auto-advance after module completion
            if self.module_completed:
                self.completion_timer += dt
                if self.completion_timer > 12.0:  # Longer celebration for final module
                    self.engine.change_state(GameState.MAIN_MENU)
                    
        except Exception as e:
            logger.error(f"Error in update: {e}")
    
    def render(self, screen):
        """Render the game state"""
        try:
            # Fill background
            screen.fill(self.config.COLORS['background'])
            
            # Render title
            title_text = "🎓 Opening Principles & Your First Game"
            title_surface = self.title_font.render(title_text, True, self.config.COLORS['text_dark'])
            screen.blit(title_surface, title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 50)))
            
            # Render phase progress
            self.phase_progress_bar.render(screen)
            
            # Render current phase info
            if not self.module_completed:
                current_phase_name = self.module_phases[self.current_phase].replace('_', ' ').title()
                phase_text = f"Phase: {current_phase_name} ({self.phase_progress + 1}/{self.exercises_per_phase[self.module_phases[self.current_phase]]})"
                
                phase_surface = self.subtitle_font.render(phase_text, True, self.config.COLORS['primary'])
                screen.blit(phase_surface, phase_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 90)))
                
                # Render phase-specific instruction
                if self.current_exercise:
                    question = self.current_exercise.get('question', '')
                    if question:
                        question_surface = self.instruction_font.render(question, True, self.config.COLORS['text_dark'])
                        screen.blit(question_surface, question_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 120)))
            
            # Render chess board
            try:
                self.chess_board.draw()
                
                # Render visual aids
                if self.show_principle_highlights:
                    self._render_principle_highlights(screen)
                if self.show_suggested_moves:
                    self._render_suggested_moves(screen)
                    
            except Exception as e:
                logger.error(f"Error drawing chess board: {e}")
                error_surface = self.instruction_font.render(
                    "Error displaying board", True, self.config.COLORS.get('error', (255, 0, 0))
                )
                screen.blit(error_surface, error_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400)))
            
            # Render coaching panel
            if self.coaching_panel_visible and self.coaching_messages:
                self._render_coaching_panel(screen)
            
            # Render hint system
            if self.show_hints and self.current_hint_text:
                self._render_hint_system(screen)
            
            # Render feedback
            if self.feedback_message:
                color = (
                    self.config.COLORS['secondary'] 
                    if any(word in self.feedback_message for word in ["Excellent", "Perfect", "Great", "Outstanding", "Correct"])
                    else self.config.COLORS.get('error', (255, 0, 0))
                )
                feedback_surface = self.instruction_font.render(self.feedback_message, True, color)
                screen.blit(feedback_surface, feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 600)))
            
            # Render UI buttons
            self.back_button.render(screen)
            self.hint_button.render(screen)
            self.principles_button.render(screen)
            self.suggestions_button.render(screen)
            self.coaching_button.render(screen)
            self.reset_button.render(screen)
            self.skip_button.render(screen)
            self.analyze_button.render(screen)
            
            # Phase-specific buttons
            if self.current_phase in [0, 1, 2] and self.show_feedback:
                self.next_phase_button.render(screen)
            elif self.current_phase == 3:
                self.start_game_button.render(screen)
            
            # Principle buttons (for tutorial)
            if self.current_phase == 0 and not self.show_feedback:
                for button in self.principle_buttons.values():
                    button.render(screen)
            
            # Hint navigation
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
    
    def _render_principle_highlights(self, screen):
        """Render highlights for opening principles"""
        try:
            alpha = int(100 + 50 * math.sin(self.visual_effects['principle_glow'] * 3))
            
            # Highlight central squares
            for square in [chess.E4, chess.D4, chess.E5, chess.D5]:
                square_rect = self.chess_board.get_square_rect(square)
                if square_rect:
                    overlay = pygame.Surface((square_rect.width, square_rect.height))
                    overlay.set_alpha(alpha)
                    overlay.fill((255, 215, 0))  # Gold for center control
                    screen.blit(overlay, square_rect.topleft)
            
            # Highlight developed pieces
            development_squares = [chess.NF3, chess.BC4, chess.NC3, chess.NF6, chess.BC5, chess.NC6]
            for square in development_squares:
                if self.chess_board.board.piece_at(square):
                    square_rect = self.chess_board.get_square_rect(square)
                    if square_rect:
                        overlay = pygame.Surface((square_rect.width, square_rect.height))
                        overlay.set_alpha(alpha)
                        overlay.fill((0, 255, 0))  # Green for good development
                        screen.blit(overlay, square_rect.topleft)
                        
        except Exception as e:
            logger.warning(f"Error rendering principle highlights: {e}")
    
    def _render_suggested_moves(self, screen):
        """Render suggested move indicators"""
        try:
            if not self.current_exercise:
                return
                
            target_squares = self.current_exercise.get('target_squares', [])
            alpha = int(120 + 60 * math.sin(self.visual_effects['coaching_highlight'] * 4))
            
            for square in target_squares:
                square_rect = self.chess_board.get_square_rect(square)
                if square_rect:
                    overlay = pygame.Surface((square_rect.width, square_rect.height))
                    overlay.set_alpha(alpha)
                    overlay.fill((0, 255, 255))  # Cyan for suggestions
                    screen.blit(overlay, square_rect.topleft)
                    
        except Exception as e:
            logger.warning(f"Error rendering suggested moves: {e}")
    
    def _render_coaching_panel(self, screen):
        """Render real-time coaching panel"""
        try:
            if not self.coaching_messages:
                return
            
            # Panel dimensions
            panel_width = 500
            panel_height = 120
            panel_x = (self.config.SCREEN_WIDTH - panel_width) // 2
            panel_y = 520
            
            # Background
            coaching_surface = pygame.Surface((panel_width, panel_height))
            coaching_surface.set_alpha(240)
            coaching_surface.fill((40, 60, 40))  # Greenish for coaching
            screen.blit(coaching_surface, (panel_x, panel_y))
            
            # Border
            pygame.draw.rect(screen, self.config.COLORS['accent'], 
                           (panel_x, panel_y, panel_width, panel_height), 3)
            
            # Title
            coach_title = "🎓 Your Chess Coach"
            title_surface = self.info_font.render(coach_title, True, (255, 255, 100))
            screen.blit(title_surface, (panel_x + 20, panel_y + 10))
            
            # Latest coaching message
            if self.coaching_messages:
                latest_message = self.coaching_messages[-1]['text']
                # Wrap text if too long
                if len(latest_message) > 60:
                    lines = [latest_message[i:i+60] for i in range(0, len(latest_message), 60)]
                    for i, line in enumerate(lines[:2]):  # Max 2 lines
                        msg_surface = self.coaching_font.render(line, True, (255, 255, 255))
                        screen.blit(msg_surface, (panel_x + 20, panel_y + 35 + i * 25))
                else:
                    msg_surface = self.coaching_font.render(latest_message, True, (255, 255, 255))
                    screen.blit(msg_surface, (panel_x + 20, panel_y + 40))
            
        except Exception as e:
            logger.warning(f"Error rendering coaching panel: {e}")
    
    def _render_hint_system(self, screen):
        """Render hint system"""
        try:
            if not self.current_hint_text:
                return
            
            # Hint panel
            panel_width = 600
            panel_height = 80
            panel_x = (self.config.SCREEN_WIDTH - panel_width) // 2
            panel_y = 450
            
            # Background
            hint_surface = pygame.Surface((panel_width, panel_height))
            hint_surface.set_alpha(220)
            hint_surface.fill((60, 40, 60))  # Purple for hints
            screen.blit(hint_surface, (panel_x, panel_y))
            
            # Border
            pygame.draw.rect(screen, self.config.COLORS['primary'], 
                           (panel_x, panel_y, panel_width, panel_height), 3)
            
            # Hint title
            hint_title = f"💡 Hint {self.hint_level + 1}/{len(self.hint_progression)}"
            title_surface = self.info_font.render(hint_title, True, (255, 215, 0))
            screen.blit(title_surface, (panel_x + 20, panel_y + 10))
            
            # Current hint text
            hint_surface = self.hint_font.render(self.current_hint_text, True, (255, 255, 255))
            screen.blit(hint_surface, (panel_x + 20, panel_y + 35))
            
        except Exception as e:
            logger.warning(f"Error rendering hint system: {e}")
    
    def _render_completion_screen(self, screen):
        """Render the comprehensive completion screen for the entire course"""
        try:
            # Semi-transparent overlay
            overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            overlay.set_alpha(220)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Main celebration message
            overall_score = self.final_performance.get('overall_score', 75)
            
            if overall_score >= 90:
                main_message = "🏆 CHESS MASTERY ACHIEVED! 🏆"
                subtitle = "Congratulations! You're ready to conquer the chess world!"
                color = (255, 215, 0)  # Gold
            elif overall_score >= 75:
                main_message = "⭐ CHESS CHAMPION! ⭐"
                subtitle = "Excellent! You've mastered the fundamentals of chess!"
                color = (255, 255, 255)  # Silver
            elif overall_score >= 60:
                main_message = "🎯 CHESS PLAYER! 🎯"
                subtitle = "Well done! You now understand how to play chess!"
                color = (205, 127, 50)  # Bronze
            else:
                main_message = "📚 CHESS LEARNER 📚"
                subtitle = "Great start! Keep practicing to improve your game!"
                color = (100, 149, 237)  # Cornflower blue
            
            success_font = pygame.font.Font(None, 64)
            success_surface = success_font.render(main_message, True, color)
            screen.blit(success_surface, success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 120)))
            
            # Subtitle
            subtitle_surface = self.title_font.render(subtitle, True, (255, 255, 255))
            screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 180)))
            
            # Course completion summary
            completion_text = "🎓 COMPLETE CHESS COURSE FINISHED! 🎓"
            completion_surface = self.subtitle_font.render(completion_text, True, (255, 215, 0))
            screen.blit(completion_surface, completion_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 220)))
            
            # Performance metrics
            metrics_y = 260
            total_time = (pygame.time.get_ticks() - self.session_start_time) / 1000.0
            
            metrics = [
                f"Overall Score: {overall_score:.1f}/100",
                f"Session Accuracy: {(self.correct_answers / max(self.total_attempts, 1)) * 100:.1f}%",
                f"Game Performance: {self.final_performance.get('average_score', 50):.0f}/100",
                f"Total Session Time: {total_time:.0f} seconds",
                f"Opening Principles Mastered: {len(self.final_performance.get('principles_mastered', {}))}/6"
            ]
            
            for i, metric in enumerate(metrics):
                metric_surface = self.instruction_font.render(metric, True, (255, 255, 255))
                screen.blit(metric_surface, metric_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, metrics_y + i * 25)))
            
            # What you've learned (course summary)
            learned_y = 400
            learned_title = self.info_font.render("🎯 Complete Chess Journey Accomplished:", True, (255, 255, 100))
            screen.blit(learned_title, learned_title.get_rect(center=(self.config.SCREEN_WIDTH // 2, learned_y)))
            
            # All 10 lessons mastered
            lessons_mastered = [
                "✓ Lesson 1: Chess Board & Piece Setup",
                "✓ Lesson 2: Pawn Movement & Capturing", 
                "✓ Lesson 3: Rook Movement & Castling",
                "✓ Lesson 4: Bishop & Diagonal Movement",
                "✓ Lesson 5: Knight's Unique L-Movement",
                "✓ Lesson 6: Queen's Combined Powers",
                "✓ Lesson 7: King Movement & Check",
                "✓ Lesson 8: Special Moves Mastery",
                "✓ Lesson 9: Check, Checkmate & Stalemate",
                "✓ Lesson 10: Opening Principles & First Game!"
            ]
            
            # Display in two columns
            col1_x = self.config.SCREEN_WIDTH // 2 - 200
            col2_x = self.config.SCREEN_WIDTH // 2 + 200
            
            for i, lesson in enumerate(lessons_mastered):
                x_pos = col1_x if i % 2 == 0 else col2_x
                y_pos = learned_y + 30 + (i // 2) * 18
                
                lesson_surface = self.tip_font.render(lesson, True, (200, 255, 200))
                screen.blit(lesson_surface, lesson_surface.get_rect(center=(x_pos, y_pos)))
            
            # Opening principles mastered
            principles_y = 580
            principles_title = self.info_font.render("🎲 Opening Principles Mastered:", True, (255, 215, 0))
            screen.blit(principles_title, principles_title.get_rect(center=(self.config.SCREEN_WIDTH // 2, principles_y)))
            
            mastered_principles = self.final_performance.get('principles_mastered', {})
            principle_names = [
                "Center Control", "Piece Development", "King Safety",
                "Avoid Early Queen", "No Wasted Moves", "Piece Coordination"
            ]
            
            for i, principle in enumerate(principle_names):
                x_pos = col1_x if i % 2 == 0 else col2_x
                y_pos = principles_y + 25 + (i // 2) * 16
                
                # Check if mastered
                principle_key = list(self.opening_principles.keys())[i]
                mastered = principle_key in mastered_principles
                color = (0, 255, 0) if mastered else (255, 255, 0)
                symbol = "✓" if mastered else "○"
                
                principle_text = f"{symbol} {principle}"
                principle_surface = self.tip_font.render(principle_text, True, color)
                screen.blit(principle_surface, principle_surface.get_rect(center=(x_pos, y_pos)))
            
            # Achievements unlocked
            achievements_y = 650
            achievement_title = self.info_font.render("🏅 Achievements Unlocked:", True, (255, 100, 255))
            screen.blit(achievement_title, achievement_title.get_rect(center=(self.config.SCREEN_WIDTH // 2, achievements_y)))
            
            achievements = []
            if overall_score >= 90:
                achievements.extend(["🥇 Chess Grandmaster", "🎯 Perfect Student", "⭐ Opening Expert"])
            elif overall_score >= 75:
                achievements.extend(["🥈 Chess Master", "📚 Excellent Student", "✨ Strong Player"])
            elif overall_score >= 60:
                achievements.extend(["🥉 Chess Player", "🎓 Good Student", "🌟 Solid Foundation"])
            else:
                achievements.extend(["🏆 Chess Learner", "📖 Dedicated Student", "🚀 Future Master"])
            
            # Add special achievements
            if len(mastered_principles) >= 5:
                achievements.append("🎲 Principle Master")
            if self.final_performance.get('average_score', 0) >= 80:
                achievements.append("🎮 Game Champion")
            
            achievement_text = " • ".join(achievements)
            achievement_surface = self.tip_font.render(achievement_text, True, (255, 200, 255))
            screen.blit(achievement_surface, achievement_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, achievements_y + 25)))
            
            # Next steps and encouragement
            next_steps_y = 690
            if overall_score >= 80:
                next_steps = "🚀 Ready for: Tournament Play, Advanced Tactics, Chess Clubs!"
            elif overall_score >= 60:
                next_steps = "📚 Recommended: Practice games, tactical puzzles, opening study"
            else:
                next_steps = "🔄 Suggested: Review lessons, practice fundamentals, play more games"
            
            next_steps_surface = self.info_font.render(next_steps, True, (150, 200, 255))
            screen.blit(next_steps_surface, next_steps_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, next_steps_y)))
            
            # Final encouragement
            encouragement_y = 720
            encouragements = [
                "The journey of a thousand games begins with a single move!",
                "Every chess master was once a beginner - you're well on your way!",
                "Chess is a lifetime journey - enjoy every game!",
                "Remember: the best move is the one that improves your position!"
            ]
            
            encouragement = random.choice(encouragements)
            encouragement_surface = self.tip_font.render(encouragement, True, (255, 255, 150))
            screen.blit(encouragement_surface, encouragement_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, encouragement_y)))
            
            # Auto-return message
            auto_return_surface = self.tip_font.render(
                "🎉 Congratulations on completing the entire chess course! Returning to menu...", 
                True, (150, 150, 150)
            )
            screen.blit(auto_return_surface, auto_return_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 750)))
            
        except Exception as e:
            logger.error(f"Error rendering completion screen: {e}")
            # Fallback completion screen
            try:
                screen.fill((0, 0, 50))
                fallback_font = pygame.font.SysFont('Arial', 36)
                fallback_text = fallback_font.render("🎓 Chess Course Complete! Congratulations! 🎓", True, (255, 255, 255))
                screen.blit(fallback_text, fallback_text.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2)))
                
                # Show basic completion info
                score_text = f"Final Score: {self.final_performance.get('overall_score', 75):.0f}/100"
                score_surface = pygame.font.SysFont('Arial', 24).render(score_text, True, (255, 255, 255))
                screen.blit(score_surface, score_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2 + 50)))
            except:
                pass