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

class KnightMovementState(BaseState):
    """Module for teaching knight movement rules - the most challenging piece to master"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Module configuration based on research recommendations
            self.exercises_per_type = 4  # More exercises due to complexity
            self.movement_types = ['basic_l_shape', 'color_alternation', 'obstacle_navigation', 'fork_patterns']
            
            # Progress tracking
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            self.exercises_completed = {move_type: 0 for move_type in self.movement_types}
            
            # Current exercise data
            self.current_knight_square = None
            self.target_squares = []
            self.invalid_squares = []
            self.selected_square = None
            self.show_feedback = False
            self.feedback_timer = 0
            self.feedback_message = ""
            self.exercise_type = None
            self.show_hint = False
            self.show_l_pattern = False
            
            # Knight-specific learning aids
            self.show_color_pattern = False
            self.current_square_color = None
            self.move_count = 0
            self.demonstration_mode = False
            
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
            
            # Instructions based on pedagogical research
            self.instructions = {
                'basic_l_shape': "Knights move in an L-shape: 2 squares + 1 square perpendicular. Click a valid square.",
                'color_alternation': "Knights always alternate colors. Notice the pattern! Click a valid square.",
                'obstacle_navigation': "Knights can jump over pieces! Find valid landing squares.",
                'fork_patterns': "Knights can attack multiple pieces. Find squares that attack 2+ pieces."
            }
            
            # Learning tips for each type
            self.learning_tips = {
                'basic_l_shape': "Think: 'Two squares, turn, one square' or use the letter L shape",
                'color_alternation': "Remember: Knights change square color with EVERY move",
                'obstacle_navigation': "Knights are the only pieces that can jump over others",
                'fork_patterns': "Look for squares where the knight attacks king, queen, or rook"
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
            self.l_shape_animation = 0
            self.color_pulse = 0
            
            # Module completion
            self.module_completed = False
            self.completion_timer = 0
            
            # Session timer
            self.session_timer = Timer()
            
            # Knight movement patterns for validation
            self.knight_moves = [(2, 1), (2, -1), (-2, 1), (-2, -1), 
                               (1, 2), (1, -2), (-1, 2), (-1, -2)]
            
        except Exception as e:
            logger.error(f"Failed to initialize KnightMovementState: {e}")
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
            
            #self.l_pattern_button = Button(
            #    text="Show L-Pattern",
            #    pos=(self.config.SCREEN_WIDTH - 180, 100),
            #    size=(150, 40),
            #    callback=self.toggle_l_pattern,
            #    config=self.config
            #)
            
            self.demo_button = Button(
                text="Demo Move",
                pos=(self.config.SCREEN_WIDTH - 180, 150),
                size=(150, 40),
                callback=self.start_demonstration,
                config=self.config
            )
            
            self.skip_button = Button(
                text="Skip",
                pos=(self.config.SCREEN_WIDTH - 180, 200),
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
            self.move_count = 0
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
            logger.error(f"Failed to enter KnightMovementState: {e}")
            self.engine.change_state(GameState.MAIN_MENU)
    
    def get_knight_moves(self, square):
        """Get all valid knight moves from a square"""
        try:
            if square is None or not (0 <= square <= 63):
                return []
            
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            moves = []
            
            for df, dr in self.knight_moves:
                new_file = file + df
                new_rank = rank + dr
                if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                    new_square = chess.square(new_file, new_rank)
                    moves.append(new_square)
            
            return moves
        except Exception as e:
            logger.error(f"Error calculating knight moves: {e}")
            return []
    
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
    
    def generate_exercise(self):
        """Generate a new exercise"""
        try:
            self.show_feedback = False
            self.selected_square = None
            self.show_hint = False
            self.show_l_pattern = False
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
                if self.exercise_type == 'basic_l_shape':
                    self._generate_basic_l_shape()
                elif self.exercise_type == 'color_alternation':
                    self._generate_color_alternation()
                elif self.exercise_type == 'obstacle_navigation':
                    self._generate_obstacle_navigation()
                elif self.exercise_type == 'fork_patterns':
                    self._generate_fork_patterns()
            except Exception as e:
                logger.error(f"Failed to generate {self.exercise_type} exercise: {e}")
                self.next_exercise()
                
        except Exception as e:
            logger.error(f"Failed to generate exercise: {e}")
            self.feedback_message = "Error generating exercise. Skipping..."
            self.next_exercise()
    
    def _generate_basic_l_shape(self):
        """Generate basic L-shape movement exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place knight in center area for maximum moves
            knight_file = random.randint(2, 5)
            knight_rank = random.randint(2, 5)
            knight_square = chess.square(knight_file, knight_rank)
            
            self.chess_board.board.set_piece_at(knight_square, chess.Piece(chess.KNIGHT, chess.WHITE))
            self.current_knight_square = knight_square
            self.current_square_color = self.is_light_square(knight_square)
            
            # Get all valid knight moves
            self.target_squares = self.get_knight_moves(knight_square)
            
            # Add some invalid squares for testing
            self.invalid_squares = []
            for _ in range(5):
                while True:
                    invalid_square = random.randint(0, 63)
                    if (invalid_square not in self.target_squares and 
                        invalid_square != knight_square):
                        self.invalid_squares.append(invalid_square)
                        break
            
            self.chess_board.highlight_square(knight_square)
            
        except Exception as e:
            logger.error(f"Failed to generate basic L-shape exercise: {e}")
            raise
    
    def _generate_color_alternation(self):
        """Generate color alternation exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place knight on edge to limit moves and emphasize color pattern
            knight_file = random.choice([0, 1, 6, 7])
            knight_rank = random.randint(1, 6)
            knight_square = chess.square(knight_file, knight_rank)
            
            self.chess_board.board.set_piece_at(knight_square, chess.Piece(chess.KNIGHT, chess.WHITE))
            self.current_knight_square = knight_square
            self.current_square_color = self.is_light_square(knight_square)
            self.show_color_pattern = True
            
            # Get valid moves (all will be opposite color)
            self.target_squares = self.get_knight_moves(knight_square)
            
            # Add same-color squares as invalid options
            self.invalid_squares = []
            same_color_squares = [sq for sq in range(64) 
                                if self.is_light_square(sq) == self.current_square_color 
                                and sq != knight_square]
            self.invalid_squares = random.sample(same_color_squares, min(6, len(same_color_squares)))
            
            self.chess_board.highlight_square(knight_square)
            
        except Exception as e:
            logger.error(f"Failed to generate color alternation exercise: {e}")
            raise
    
    def _generate_obstacle_navigation(self):
        """Generate obstacle navigation exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place knight in center
            knight_file = random.randint(2, 5)
            knight_rank = random.randint(2, 5)
            knight_square = chess.square(knight_file, knight_rank)
            
            self.chess_board.board.set_piece_at(knight_square, chess.Piece(chess.KNIGHT, chess.WHITE))
            self.current_knight_square = knight_square
            
            # Add surrounding pieces as obstacles
            surrounding_squares = []
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    new_file = chess.square_file(knight_square) + df
                    new_rank = chess.square_rank(knight_square) + dr
                    if 0 <= new_file <= 7 and 0 <= new_rank <= 7:
                        surrounding_squares.append(chess.square(new_file, new_rank))
            
            # Place 4-6 obstacles
            obstacles = random.sample(surrounding_squares, min(5, len(surrounding_squares)))
            for obstacle in obstacles:
                piece_type = random.choice([chess.PAWN, chess.ROOK, chess.BISHOP])
                self.chess_board.board.set_piece_at(obstacle, chess.Piece(piece_type, chess.BLACK))
            
            # Knight can still move to all L-shaped squares (jumping over obstacles)
            self.target_squares = self.get_knight_moves(knight_square)
            
            # Invalid squares are the obstacle squares and other random squares
            self.invalid_squares = obstacles + [sq for sq in range(64) 
                                             if sq not in self.target_squares 
                                             and sq != knight_square 
                                             and not self.chess_board.board.piece_at(sq)][:3]
            
            self.chess_board.highlight_square(knight_square)
            
        except Exception as e:
            logger.error(f"Failed to generate obstacle navigation exercise: {e}")
            raise
    
    def _generate_fork_patterns(self):
        """Generate fork pattern exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place knight
            knight_file = random.randint(1, 6)
            knight_rank = random.randint(1, 6)
            knight_square = chess.square(knight_file, knight_rank)
            
            self.chess_board.board.set_piece_at(knight_square, chess.Piece(chess.KNIGHT, chess.WHITE))
            self.current_knight_square = knight_square
            
            # Place enemy pieces that can be forked
            possible_moves = self.get_knight_moves(knight_square)
            
            # Place a king and queen/rook for forking opportunities
            if len(possible_moves) >= 2:
                king_square = random.choice(possible_moves)
                self.chess_board.board.set_piece_at(king_square, chess.Piece(chess.KING, chess.BLACK))
                
                remaining_moves = [sq for sq in possible_moves if sq != king_square]
                if remaining_moves:
                    target_square = random.choice(remaining_moves)
                    target_piece = random.choice([chess.QUEEN, chess.ROOK])
                    self.chess_board.board.set_piece_at(target_square, chess.Piece(target_piece, chess.BLACK))
            
            # Find squares where knight can fork (attack 2+ pieces)
            fork_squares = []
            for square in range(64):
                if square == knight_square or self.chess_board.board.piece_at(square):
                    continue
                
                knight_moves_from_square = self.get_knight_moves(square)
                attacked_pieces = 0
                for move_square in knight_moves_from_square:
                    piece = self.chess_board.board.piece_at(move_square)
                    if piece and piece.color == chess.BLACK:
                        attacked_pieces += 1
                
                if attacked_pieces >= 2:
                    fork_squares.append(square)
            
            self.target_squares = fork_squares if fork_squares else self.get_knight_moves(knight_square)
            
            # Invalid squares are non-forking squares
            self.invalid_squares = [sq for sq in range(64) 
                                  if sq not in self.target_squares 
                                  and sq != knight_square 
                                  and not self.chess_board.board.piece_at(sq)][:5]
            
            self.chess_board.highlight_square(knight_square)
            
        except Exception as e:
            logger.error(f"Failed to generate fork pattern exercise: {e}")
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
            self.move_count += 1
            self.show_feedback = True
            self.feedback_timer = 0
            
            # Specific feedback based on exercise type
            if self.exercise_type == 'basic_l_shape':
                self.feedback_message = "Perfect L-shape! The knight moved 2+1 squares!"
            elif self.exercise_type == 'color_alternation':
                old_color = "light" if self.current_square_color else "dark"
                new_color = "dark" if self.current_square_color else "light"
                self.feedback_message = f"Excellent! Knight changed from {old_color} to {new_color} square!"
            elif self.exercise_type == 'obstacle_navigation':
                self.feedback_message = "Great! The knight jumped over the obstacles!"
            elif self.exercise_type == 'fork_patterns':
                self.feedback_message = "Brilliant fork! Multiple pieces under attack!"
            
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
                points = 150 if self.exercise_type == 'fork_patterns' else 100
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
            
            if self.selected_square == self.current_knight_square:
                self.feedback_message = "Click where the knight can move, not the knight itself."
            elif self.exercise_type == 'color_alternation' and self.selected_square in self.invalid_squares:
                current_color = "light" if self.current_square_color else "dark"
                self.feedback_message = f"Wrong color! Knights must change from {current_color} squares."
            elif self.exercise_type == 'fork_patterns':
                self.feedback_message = "That square doesn't create a fork. Look for squares attacking 2+ pieces."
            elif self.selected_square in self.invalid_squares:
                self.feedback_message = "Knights move in L-shapes only: 2 squares + 1 square perpendicular."
            else:
                self.feedback_message = "Invalid knight move. Remember the L-shape pattern!"
            
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
                if self.current_knight_square is not None:
                    self.chess_board.highlight_square(self.current_knight_square)
        except Exception as e:
            logger.error(f"Error toggling hint: {e}")
    
    def toggle_l_pattern(self):
        """Toggle L-pattern visualization"""
        try:
            self.show_l_pattern = not self.show_l_pattern
        except Exception as e:
            logger.error(f"Error toggling L-pattern: {e}")
    
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
                    "Watch the L-shape movement!",
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
            pygame.time.set_timer(pygame.USEREVENT + 1, 2000)
            
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
        """Complete the knight movement module"""
        try:
            self.module_completed = True
            self.completion_timer = 0
            
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            
            # Create completion celebration
            for _ in range(60):
                try:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(200, 500)
                    self.celebration_particles.append({
                        'x': self.config.SCREEN_WIDTH // 2,
                        'y': self.config.SCREEN_HEIGHT // 2,
                        'vx': speed * math.cos(angle),
                        'vy': speed * math.sin(angle),
                        'color': random.choice([(255, 215, 0), (255, 255, 0), 
                                              self.config.COLORS.get('accent', (155, 89, 182)),
                                              self.config.COLORS.get('secondary', (46, 204, 113))]),
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
            particle_count = 25 if self.exercise_type == 'fork_patterns' else 15
            
            for _ in range(particle_count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(100, 350)
                colors = [self.config.COLORS.get('accent', (155, 89, 182)), 
                         self.config.COLORS.get('secondary', (46, 204, 113)), 
                         (255, 255, 0)]
                
                self.celebration_particles.append({
                    'x': self.config.SCREEN_WIDTH // 2,
                    'y': 350,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle),
                    'color': random.choice(colors),
                    'life': 2.0,
                    'size': random.randint(3, 10)
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
            #self.l_pattern_button.handle_event(event)
            
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
                elif event.key == pygame.K_l:
                    self.toggle_l_pattern()
                elif event.key == pygame.K_d and not self.show_feedback:
                    self.start_demonstration()
                elif event.key == pygame.K_s and self.total_attempts > 2:
                    self.skip_exercise()
            
            # Handle demonstration timer
            if event.type == pygame.USEREVENT + 1:
                self.demonstration_mode = False
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # Cancel timer
                
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
            #self.l_pattern_button.update(dt, mouse_pos)
            
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
                    particle['vy'] += 600 * dt  # Gravity
                    particle['life'] -= dt
                    particle['size'] = max(1, particle['size'] - dt * 3)
                    if particle['life'] <= 0:
                        self.celebration_particles.remove(particle)
                except Exception as e:
                    logger.warning(f"Error updating particle: {e}")
                    self.celebration_particles.remove(particle)
            
            # Update animations
            self.l_shape_animation += dt * 3
            if self.l_shape_animation > 2 * math.pi:
                self.l_shape_animation = 0
            
            self.color_pulse += dt * 4
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
        """Render the knight movement training interface"""
        try:
            # Fill background
            screen.fill(self.config.COLORS['background'])
            
            # Render title
            title_surface = self.title_font.render("Learn Knight Movement", True, self.config.COLORS['text_dark'])
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
                
                # Render L-pattern visualization if enabled
                if self.show_l_pattern and self.current_knight_square is not None:
                    self.render_l_pattern_overlay(screen)
                
                # Render color pattern visualization
                if self.show_color_pattern and self.exercise_type == 'color_alternation':
                    self.render_color_pattern_overlay(screen)
                    
            except Exception as e:
                logger.error(f"Error drawing chess board: {e}")
                error_surface = self.instruction_font.render("Error displaying board", True, 
                                                           self.config.COLORS.get('error', (255, 0, 0)))
                screen.blit(error_surface, error_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400)))
            
            # Render hint text
            if self.show_hint and not self.show_feedback:
                hint_surface = self.info_font.render("Valid knight moves highlighted in yellow", 
                                                   True, self.config.COLORS['secondary'])
                screen.blit(hint_surface, hint_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 680)))
            
            # Render feedback message
            if self.feedback_message and not self.module_completed:
                color = (self.config.COLORS['secondary'] if "Correct" in self.feedback_message or 
                        "Perfect" in self.feedback_message or "Excellent" in self.feedback_message or 
                        "Great" in self.feedback_message or "Brilliant" in self.feedback_message
                        else self.config.COLORS.get('error', (255, 0, 0)))
                feedback_surface = self.instruction_font.render(self.feedback_message, True, color)
                screen.blit(feedback_surface, feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 620)))
            
            # Render UI buttons
            self.back_button.render(screen)
            self.hint_button.render(screen)
            #self.l_pattern_button.render(screen)
            
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
    
    def render_l_pattern_overlay(self, screen):
        """Render L-pattern visualization overlay"""
        try:
            if self.current_knight_square is None:
                return
            
            knight_pos = self.chess_board.get_square_center(self.current_knight_square)
            if knight_pos is None:
                return
            
            # Draw animated L-shape patterns
            alpha = int(128 + 64 * math.sin(self.l_shape_animation))
            
            for df, dr in self.knight_moves:
                try:
                    # Calculate L-shape path
                    square_size = self.chess_board.square_size
                    
                    # First part of L (2 squares)
                    if abs(df) == 2:
                        end_x = knight_pos[0] + df * square_size
                        mid_y = knight_pos[1]
                        pygame.draw.line(screen, (255, 255, 0, alpha), knight_pos, (end_x, mid_y), 3)
                        
                        # Second part of L (1 square)
                        final_y = knight_pos[1] + dr * square_size
                        pygame.draw.line(screen, (255, 255, 0, alpha), (end_x, mid_y), (end_x, final_y), 3)
                    else:
                        # First part of L (2 squares)
                        mid_x = knight_pos[0]
                        end_y = knight_pos[1] + dr * square_size
                        pygame.draw.line(screen, (255, 255, 0, alpha), knight_pos, (mid_x, end_y), 3)
                        
                        # Second part of L (1 square)
                        final_x = knight_pos[0] + df * square_size
                        pygame.draw.line(screen, (255, 255, 0, alpha), (mid_x, end_y), (final_x, end_y), 3)
                        
                except Exception as e:
                    logger.warning(f"Error drawing L-pattern line: {e}")
                    
        except Exception as e:
            logger.error(f"Error rendering L-pattern overlay: {e}")
    
    def render_color_pattern_overlay(self, screen):
        """Render color pattern visualization"""
        try:
            alpha = int(64 + 32 * math.sin(self.color_pulse))
            
            # Highlight squares of the same color as knight
            for square in range(64):
                if self.is_light_square(square) == self.current_square_color:
                    square_rect = self.chess_board.get_square_rect(square)
                    if square_rect:
                        overlay = pygame.Surface((square_rect.width, square_rect.height))
                        overlay.set_alpha(alpha)
                        overlay.fill((0, 255, 255))  # Cyan for current color
                        screen.blit(overlay, square_rect.topleft)
                        
        except Exception as e:
            logger.error(f"Error rendering color pattern overlay: {e}")
    
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
            success_surface = success_font.render("Knight Master!", True, (255, 215, 0))
            screen.blit(success_surface, success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 200)))
            
            # Completion message
            complete_surface = self.title_font.render("You've mastered the knight's movement!", 
                                                    True, (255, 255, 255))
            screen.blit(complete_surface, complete_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 280)))
            
            # Statistics
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            stats = [
                f"Accuracy: {accuracy:.1f}%",
                f"Correct Moves: {self.correct_moves}/{self.total_attempts}",
                f"L-shapes Mastered: {sum(self.exercises_completed.values())} exercises"
            ]
            
            for i, stat in enumerate(stats):
                stat_surface = self.instruction_font.render(stat, True, (255, 255, 255))
                screen.blit(stat_surface, stat_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 350 + i * 40)))
            
            # Achievement message
            if accuracy >= 90:
                achievement = "Outstanding! You're ready for advanced tactics!"
            elif accuracy >= 75:
                achievement = "Well done! The knight holds no more secrets for you!"
            else:
                achievement = "Good progress! Practice makes perfect with knights!"
            
            achievement_surface = self.info_font.render(achievement, True, self.config.COLORS['accent'])
            screen.blit(achievement_surface, achievement_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 500)))
            
        except Exception as e:
            logger.error(f"Error rendering completion screen: {e}")