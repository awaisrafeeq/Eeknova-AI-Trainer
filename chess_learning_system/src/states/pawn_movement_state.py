# src/states/pawn_movement_state.py

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

class PawnMovementState(BaseState):
    """Module for teaching pawn movement and capture rules"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Module configuration
            self.exercises_per_type = 3  # Exercises for each movement type
            self.movement_types = [
                'basic_forward',      # Single square forward
                'initial_double',     # Two squares from starting position
                'capture',           # Diagonal capture
                'blocked',           # Understanding when pawns are blocked
                'en_passant_setup'   # Basic en passant scenarios (advanced)
            ]
            
            # Progress tracking
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            self.exercises_completed = {}
            for move_type in self.movement_types:
                self.exercises_completed[move_type] = 0
            
            # Current exercise data
            self.current_pawn_square = None
            self.target_squares = []  # Valid move squares
            self.invalid_squares = []  # Squares that look valid but aren't
            self.selected_square = None
            self.show_feedback = False
            self.feedback_timer = 0
            self.feedback_message = ""
            self.exercise_type = None
            self.show_hint = False
            
            # Chess board
            try:
                self.chess_board = ChessBoard(
                    self.engine.screen,
                    self.engine.resource_manager,
                    board_size=480
                )
                # Center the board
                self.chess_board.board_offset_x = (self.config.SCREEN_WIDTH - 480) // 2
                self.chess_board.board_offset_y = 180
            except Exception as e:
                logger.error(f"Failed to initialize chess board: {e}")
                raise
            
            # UI elements
            self.create_ui_elements()
            
            # Instructions for each movement type
            self.instructions = {
                'basic_forward': "Pawns move forward one square. Click where this pawn can move.",
                'initial_double': "Pawns can move two squares forward from their starting position.",
                'capture': "Pawns capture diagonally forward. Click where this pawn can capture.",
                'blocked': "Pawns cannot move if blocked. Can this pawn move?",
                'en_passant_setup': "Special move: En passant capture. Can you find it?"
            }
            
            # Load fonts
            try:
                self.title_font = pygame.font.Font(None, 48)
                self.instruction_font = pygame.font.Font(None, 32)
                self.info_font = pygame.font.Font(None, 24)
            except Exception as e:
                logger.error(f"Failed to load fonts: {e}")
                # Fallback to system font
                self.title_font = pygame.font.SysFont('Arial', 48)
                self.instruction_font = pygame.font.SysFont('Arial', 32)
                self.info_font = pygame.font.SysFont('Arial', 24)
            
            # Animation elements
            self.animated_texts = []
            self.celebration_particles = []
            self.arrow_animation = 0
            
            # Module completion
            self.module_completed = False
            self.completion_timer = 0
            
            # Session timer
            self.session_timer = Timer()
            
        except Exception as e:
            logger.error(f"Failed to initialize PawnMovementState: {e}")
            raise
        
    def create_ui_elements(self):
        """Create UI elements for the module"""
        try:
            # Progress bar
            total_exercises = len(self.movement_types) * self.exercises_per_type
            #self.progress_bar = ProgressBar(
            #    pos=(self.config.SCREEN_WIDTH // 2 - 200, 30),
            #    size=(400, 25),
            #    max_value=total_exercises,
            #    config=self.config
            #)
            
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
                size=(150, 40),
                callback=self.toggle_hint,
                config=self.config
            )
            
            # Skip button for difficult exercises
            self.skip_button = Button(
                text="Skip",
                pos=(self.config.SCREEN_WIDTH - 100, 100),
                size=(150, 40),
                callback=self.skip_exercise,
                config=self.config
            )
            
            # Next button (shown after completing exercise)
            self.next_button = Button(
                text="Next Exercise",
                pos=(self.config.SCREEN_WIDTH // 2, 650),
                size=(200, 50),
                callback=self.next_exercise,
                config=self.config
            )
        except Exception as e:
            logger.error(f"Failed to create UI elements: {e}")
            raise
        
    def enter(self):
        """Called when entering the pawn movement state"""
        try:
            super().enter()
            
            # Reset session
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            for move_type in self.movement_types:
                self.exercises_completed[move_type] = 0
            #self.progress_bar.set_value(0)
            self.module_completed = False
            self.session_timer.reset()
            
            # Start first exercise
            self.generate_exercise()
            
            # Play learning music
            try:
                self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
            except Exception as e:
                logger.warning(f"Failed to play learning music: {e}")
                
        except Exception as e:
            logger.error(f"Failed to enter PawnMovementState: {e}")
            # Return to main menu on critical error
            self.engine.change_state(GameState.MAIN_MENU)
        
    def generate_exercise(self):
        """Generate a new pawn movement exercise"""
        try:
            self.show_feedback = False
            self.selected_square = None
            self.show_hint = False
            self.target_squares = []
            self.invalid_squares = []
            self.chess_board.clear_highlights()
            self.chess_board.select_square(None)
            
            # Get current exercise type
            if self.current_type_index < len(self.movement_types):
                self.exercise_type = self.movement_types[self.current_type_index]
            else:
                self.complete_module()
                return
                
            # Generate exercise based on type
            try:
                if self.exercise_type == 'basic_forward':
                    self._generate_basic_forward()
                elif self.exercise_type == 'initial_double':
                    self._generate_initial_double()
                elif self.exercise_type == 'capture':
                    self._generate_capture()
                elif self.exercise_type == 'blocked':
                    self._generate_blocked()
                elif self.exercise_type == 'en_passant_setup':
                    self._generate_en_passant()
                else:
                    logger.warning(f"Unknown exercise type: {self.exercise_type}")
                    self.next_exercise()
            except Exception as e:
                logger.error(f"Failed to generate exercise for type {self.exercise_type}: {e}")
                self.next_exercise()
                
        except Exception as e:
            logger.error(f"Failed to generate exercise: {e}")
            self.feedback_message = "Error generating exercise. Skipping to next..."
            self.next_exercise()
            
    def _generate_basic_forward(self):
        """Generate exercise for basic forward movement"""
        try:
            # Clear board
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place a white pawn in the middle of the board
            pawn_file = random.randint(1, 6)  # Avoid edges
            pawn_rank = random.randint(2, 5)  # Middle ranks
            pawn_square = chess.square(pawn_file, pawn_rank)
            
            self.chess_board.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
            self.current_pawn_square = pawn_square
            
            # The target square is one square forward
            target_square = pawn_square + 8
            if target_square <= 63:  # Validate square is on board
                self.target_squares = [target_square]
            else:
                raise ValueError(f"Invalid target square: {target_square}")
            
            # Add some invalid squares (sideways, backward)
            self.invalid_squares = [
                pawn_square - 8,  # Backward
                pawn_square + 1 if pawn_file < 7 else None,  # Right
                pawn_square - 1 if pawn_file > 0 else None,  # Left
            ]
            self.invalid_squares = [sq for sq in self.invalid_squares if sq is not None and 0 <= sq <= 63]
            
            # Highlight the pawn
            self.chess_board.highlight_square(pawn_square)
            
        except Exception as e:
            logger.error(f"Failed to generate basic forward exercise: {e}")
            raise
        
    def _generate_initial_double(self):
        """Generate exercise for initial two-square move"""
        try:
            # Clear board
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place a white pawn on the second rank
            pawn_file = random.randint(1, 6)
            pawn_square = chess.square(pawn_file, 1)  # Second rank
            
            self.chess_board.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
            self.current_pawn_square = pawn_square
            
            # Target squares are one and two squares forward
            self.target_squares = []
            one_forward = pawn_square + 8
            two_forward = pawn_square + 16
            
            if one_forward <= 63:
                self.target_squares.append(one_forward)
            if two_forward <= 63:
                self.target_squares.append(two_forward)
                
            if not self.target_squares:
                raise ValueError("No valid target squares generated")
            
            # Invalid squares
            self.invalid_squares = [
                pawn_square + 24 if pawn_square + 24 <= 63 else None,  # Three squares forward
                pawn_square + 7 if pawn_file > 0 else None,  # Diagonal without capture
                pawn_square + 9 if pawn_file < 7 else None,  # Diagonal without capture
            ]
            self.invalid_squares = [sq for sq in self.invalid_squares if sq is not None and 0 <= sq <= 63]
            
            # Highlight the pawn
            self.chess_board.highlight_square(pawn_square)
            
        except Exception as e:
            logger.error(f"Failed to generate initial double exercise: {e}")
            raise
        
    def _generate_capture(self):
        """Generate exercise for diagonal capture"""
        try:
            # Clear board
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place a white pawn
            pawn_file = random.randint(1, 6)
            pawn_rank = random.randint(2, 5)
            pawn_square = chess.square(pawn_file, pawn_rank)
            
            self.chess_board.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
            self.current_pawn_square = pawn_square
            
            # Place enemy pieces diagonally ahead
            self.target_squares = []
            
            # Left diagonal capture
            if pawn_file > 0 and pawn_rank < 7:
                left_capture = pawn_square + 7
                if 0 <= left_capture <= 63:
                    self.chess_board.board.set_piece_at(left_capture, chess.Piece(chess.PAWN, chess.BLACK))
                    self.target_squares.append(left_capture)
                
            # Right diagonal capture
            if pawn_file < 7 and pawn_rank < 7:
                right_capture = pawn_square + 9
                if 0 <= right_capture <= 63:
                    self.chess_board.board.set_piece_at(right_capture, chess.Piece(chess.KNIGHT, chess.BLACK))
                    self.target_squares.append(right_capture)
                
            # The forward square is NOT a valid capture square
            forward_square = pawn_square + 8
            if forward_square <= 63:
                self.invalid_squares.append(forward_square)
                
            if not self.target_squares:
                # If no captures possible, regenerate
                raise ValueError("No capture squares available, regenerating...")
                
            # Highlight the pawn
            self.chess_board.highlight_square(pawn_square)
            
        except Exception as e:
            logger.error(f"Failed to generate capture exercise: {e}")
            raise
        
    def _generate_blocked(self):
        """Generate exercise for blocked pawns"""
        try:
            # Clear board
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place a white pawn
            pawn_file = random.randint(1, 6)
            pawn_rank = random.randint(2, 5)
            pawn_square = chess.square(pawn_file, pawn_rank)
            
            self.chess_board.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
            self.current_pawn_square = pawn_square
            
            # Block the pawn with a piece directly in front
            blocking_square = pawn_square + 8
            if blocking_square <= 63:
                self.chess_board.board.set_piece_at(blocking_square, chess.Piece(chess.BISHOP, chess.BLACK))
            
            # In this case, there are NO valid moves
            self.target_squares = []
            
            # But we might have capture options
            if pawn_file > 0:
                left_capture = pawn_square + 7
                if 0 <= left_capture <= 63 and random.choice([True, False]):
                    self.chess_board.board.set_piece_at(left_capture, chess.Piece(chess.ROOK, chess.BLACK))
                    self.target_squares.append(left_capture)
                    
            if pawn_file < 7:
                right_capture = pawn_square + 9
                if 0 <= right_capture <= 63 and random.choice([True, False]) and not self.target_squares:
                    self.chess_board.board.set_piece_at(right_capture, chess.Piece(chess.QUEEN, chess.BLACK))
                    self.target_squares.append(right_capture)
                    
            # Invalid squares include the blocked forward square
            if blocking_square <= 63:
                self.invalid_squares = [blocking_square]
            
            # Highlight the pawn
            self.chess_board.highlight_square(pawn_square)
            
        except Exception as e:
            logger.error(f"Failed to generate blocked exercise: {e}")
            raise
        
    def _generate_en_passant(self):
        """Generate exercise for en passant (simplified)"""
        try:
            # This is an advanced concept, so we'll keep it simple
            # Clear board
            self.chess_board.reset()
            self.chess_board.board.clear()
            
            # Place a white pawn on the 5th rank
            pawn_file = random.randint(1, 6)
            pawn_square = chess.square(pawn_file, 4)  # 5th rank
            
            self.chess_board.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
            self.current_pawn_square = pawn_square
            
            # Place a black pawn that just moved two squares
            if pawn_file > 0:
                enemy_file = pawn_file - 1
            else:
                enemy_file = pawn_file + 1
                
            enemy_square = chess.square(enemy_file, 4)
            self.chess_board.board.set_piece_at(enemy_square, chess.Piece(chess.PAWN, chess.BLACK))
            
            # The en passant capture square
            en_passant_square = chess.square(enemy_file, 5)
            if 0 <= en_passant_square <= 63:
                self.target_squares = [en_passant_square]
            
            # Normal forward move is also valid
            forward_square = pawn_square + 8
            if forward_square <= 63:
                self.target_squares.append(forward_square)
                
            if not self.target_squares:
                raise ValueError("No valid target squares for en passant")
            
            # Highlight both pawns
            self.chess_board.highlight_square(pawn_square)
            self.chess_board.highlight_square(enemy_square)
            
        except Exception as e:
            logger.error(f"Failed to generate en passant exercise: {e}")
            raise
        
    def handle_square_click(self, square):
        """Handle when a square is clicked"""
        try:
            if self.show_feedback or square is None:
                return
                
            self.selected_square = square
            self.total_attempts += 1
            
            if square in self.target_squares:
                self.on_correct_move()
            else:
                #print("incorrect move is starting executing")
                self.on_incorrect_move()
                #print("incorrect move is completed")
                
        except Exception as e:
            logger.error(f"Error handling square click: {e}")
            self.feedback_message = "Error processing move. Please try again."
            self.show_feedback = True
            
    def on_correct_move(self):
        """Handle correct move selection"""
        try:
            self.correct_moves += 1
            self.show_feedback = True
            self.feedback_timer = 0
            self.feedback_message = "Correct! Well done!"
            
            # Highlight the correct square in green
            if self.selected_square is not None:
                self.chess_board.select_square(self.selected_square)
            
            # Update progress
            if self.exercise_type:
                # Check if we've already completed max exercises for this type
                if self.exercises_completed[self.exercise_type] < self.exercises_per_type:
                    self.exercises_completed[self.exercise_type] += 1
                total_completed = sum(self.exercises_completed.values())
                #self.progress_bar.set_value(total_completed)
            
            # Play success sound
            try:
                self.engine.audio_manager.play_sound('success.mp3')
            except Exception as e:
                logger.warning(f"Failed to play success sound: {e}")
            
            # Create celebration effect
            self.create_celebration()
            
            # Add points
            points = 100
            try:
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
        """Handle incorrect move selection"""
        try:
            #print("Incorrect move selected")
            self.show_feedback = True
            self.feedback_timer = 0
            
            if self.selected_square is not None and self.selected_square in self.invalid_squares:
                self.feedback_message = "Not quite! Pawns can't move there."
            elif self.selected_square == self.current_pawn_square:
                self.feedback_message = "Click on a square where the pawn can move to."
            else:
                self.feedback_message = "That's not a valid move for this pawn."
                
            # Play error sound
            try:
                self.engine.audio_manager.play_sound('error.wav')
            except Exception as e:
                logger.warning(f"Failed to play error sound: {e}")
                
            #print(f"Feedback message: {self.feedback_message}")
            
        except Exception as e:
            logger.error(f"Error in on_incorrect_move: {e}")
            self.feedback_message = "That's not a valid move. Try again!"
            
    def toggle_hint(self):
        """Toggle hint display"""
        try:
            self.show_hint = not self.show_hint
            if self.show_hint:
                # Briefly highlight all valid moves
                for square in self.target_squares:
                    if 0 <= square <= 63:
                        self.chess_board.highlight_square(square)
        except Exception as e:
            logger.error(f"Error toggling hint: {e}")
                    
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
            
            # Check if we've completed enough exercises for this type
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
            # Try to recover by moving to next type
            self.current_type_index += 1
            total_completed = sum(self.exercises_completed.values())
            max_exercises = len(self.movement_types) * self.exercises_per_type
            if self.current_type_index >= len(self.movement_types) or total_completed >= max_exercises:
                self.complete_module()
            else:
                self.generate_exercise()
            
    def complete_module(self):
        """Complete the pawn movement module"""
        try:
            self.module_completed = True
            self.completion_timer = 0
            
            # Calculate accuracy
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            
            # Create celebration
            for _ in range(50):
                try:
                    angle = random.uniform(0, 2 * 3.14159)
                    speed = random.uniform(200, 400)
                    self.celebration_particles.append({
                        'x': self.config.SCREEN_WIDTH // 2,
                        'y': self.config.SCREEN_HEIGHT // 2,
                        'vx': speed * math.cos(angle),
                        'vy': speed * math.sin(angle),
                        'color': random.choice([
                            (255, 215, 0),
                            (255, 255, 0),
                            self.config.COLORS.get('accent', (155, 89, 182))
                        ]),
                        'life': 3.0,
                        'size': random.randint(5, 15)
                    })
                except Exception as e:
                    logger.warning(f"Failed to create celebration particle: {e}")
                    break
                
            # Play completion sound
            try:
                self.engine.audio_manager.play_sound('complete.wav')
            except Exception as e:
                logger.warning(f"Failed to play completion sound: {e}")
                
        except Exception as e:
            logger.error(f"Error completing module: {e}")
            # Still mark as completed and return to menu
            self.module_completed = True
        
    def create_celebration(self):
        """Create visual celebration effect"""
        try:
            import math
            for _ in range(20):
                angle = random.uniform(0, 2 * 3.14159)
                speed = random.uniform(100, 300)
                self.celebration_particles.append({
                    'x': self.config.SCREEN_WIDTH // 2,
                    'y': 350,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle),
                    'color': random.choice([
                        self.config.COLORS.get('accent', (155, 89, 182)),
                        self.config.COLORS.get('secondary', (46, 204, 113)),
                        (255, 255, 0)
                    ]),
                    'life': 1.5,
                    'size': random.randint(3, 8)
                })
        except Exception as e:
            logger.warning(f"Failed to create celebration effect: {e}")
            
    def on_back_clicked(self):
        """Handle back button click"""
        try:
            self.engine.change_state(GameState.MAIN_MENU)
        except Exception as e:
            logger.error(f"Error returning to main menu: {e}")
            # Force quit to main menu
            try:
                self.engine.running = False
            except:
                pass
        
    def handle_event(self, event):
        """Handle events"""
        try:
            # Handle button events
            #print("handle event is called in pawn movement state")
            self.back_button.handle_event(event)
            self.hint_button.handle_event(event)
            
            if self.total_attempts > 2 and not self.show_feedback:
                self.skip_button.handle_event(event)
                
            if self.show_feedback:
                self.next_button.handle_event(event)
                
            # Handle mouse clicks on board
            if event.type == pygame.MOUSEBUTTONDOWN:
                try:
                    square = self.chess_board.get_square_from_pos(event.pos)
                    self.handle_square_click(square)
                except Exception as e:
                    logger.error(f"Error getting square from position: {e}")
                    
                #print(f"handle event is returned successfully")
                
            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.show_feedback:
                    self.next_exercise()
                elif event.key == pygame.K_h:
                    self.toggle_hint()
                    
            #print("handle event is completed successfully")
            
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            
    def update(self, dt):
        """Update the pawn movement state"""
        try:
            super().update(dt)
            #print("update function is called in pawn movement state")
            
            # Update UI elements
            mouse_pos = pygame.mouse.get_pos()
            self.back_button.update(dt, mouse_pos)
            self.hint_button.update(dt, mouse_pos)
            
            if self.total_attempts > 2 and not self.show_feedback:
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
                    particle['size'] = max(1, particle['size'] - dt * 2)
                    
                    if particle['life'] <= 0:
                        self.celebration_particles.remove(particle)
                except Exception as e:
                    logger.warning(f"Error updating particle: {e}")
                    self.celebration_particles.remove(particle)
                    
            # Update arrow animation
            self.arrow_animation += dt * 2
            if self.arrow_animation > 1:
                self.arrow_animation = 0
                
            # Check module completion
            if self.module_completed:
                self.completion_timer += dt
                if self.completion_timer > 5.0:
                    self.engine.change_state(GameState.MAIN_MENU)
                    
            #print("update function is completed in pawn movement state")
            
        except Exception as e:
            logger.error(f"Error in update: {e}")
            
    def render(self, screen):
        """Render the pawn movement state"""
        try:
            # Clear screen
            screen.fill(self.config.COLORS['background'])
            
            # Draw title
            title_text = "Learn Pawn Movement"
            title_surface = self.title_font.render(title_text, True, self.config.COLORS['text_dark'])
            title_rect = title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 40))
            screen.blit(title_surface, title_rect)
            
            # Draw progress bar
            #self.progress_bar.render(screen)
            
            # Draw current exercise type
            if not self.module_completed and self.exercise_type:
                type_text = self.exercise_type.replace('_', ' ').title()
                type_surface = self.instruction_font.render(f"Exercise: {type_text}", True, 
                                                          self.config.COLORS['primary'])
                type_rect = type_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 100))
                screen.blit(type_surface, type_rect)
                
                # Draw instruction
                instruction = self.instructions.get(self.exercise_type, "")
                inst_surface = self.info_font.render(instruction, True, self.config.COLORS['text_dark'])
                inst_rect = inst_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 140))
                screen.blit(inst_surface, inst_rect)
                
            # Draw chess board
            try:
                self.chess_board.draw()
            except Exception as e:
                logger.error(f"Error drawing chess board: {e}")
                # Draw error message
                error_surface = self.instruction_font.render("Error displaying board", True, 
                                                            self.config.COLORS.get('error', (255, 0, 0)))
                error_rect = error_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400))
                screen.blit(error_surface, error_rect)
            
            # Draw hint if enabled
            if self.show_hint and not self.show_feedback:
                hint_surface = self.info_font.render("Valid moves are highlighted in yellow", 
                                                   True, self.config.COLORS['secondary'])
                hint_rect = hint_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 670))
                screen.blit(hint_surface, hint_rect)
                
            # Draw feedback
            if self.feedback_message and not self.module_completed:
                color = self.config.COLORS['secondary'] if "Correct" in self.feedback_message else self.config.COLORS.get('error', (255, 0, 0))
                feedback_surface = self.instruction_font.render(self.feedback_message, True, color)
                feedback_rect = feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 600))
                screen.blit(feedback_surface, feedback_rect)
                
            # Draw navigation buttons
            self.back_button.render(screen)
            self.hint_button.render(screen)
            
            if self.total_attempts > 2 and not self.show_feedback:
                self.skip_button.render(screen)
                
            if self.show_feedback:
                self.next_button.render(screen)
                
            # Draw animated texts
            for text in self.animated_texts:
                try:
                    text.render(screen)
                except Exception as e:
                    logger.warning(f"Error rendering animated text: {e}")
                
            # Draw celebration particles
            for particle in self.celebration_particles:
                try:
                    pygame.draw.circle(screen, particle['color'], 
                                     (int(particle['x']), int(particle['y'])), 
                                     int(particle['size']))
                except Exception as e:
                    logger.warning(f"Error rendering particle: {e}")
                
            # Draw completion screen
            if self.module_completed:
                try:
                    # Draw overlay
                    overlay = pygame.Surface((screen.get_width(), screen.get_height()))
                    overlay.set_alpha(128)
                    overlay.fill((0, 0, 0))
                    screen.blit(overlay, (0, 0))
                    
                    # Draw success message
                    success_font = pygame.font.Font(None, 72)
                    success_text = "Congratulations!"
                    success_surface = success_font.render(success_text, True, (255, 215, 0))
                    success_rect = success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 200))
                    screen.blit(success_surface, success_rect)
                    
                    # Draw completion message
                    complete_text = "You've mastered pawn movement!"
                    complete_surface = self.title_font.render(complete_text, True, (255, 255, 255))
                    complete_rect = complete_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 300))
                    screen.blit(complete_surface, complete_rect)
                    
                    # Draw accuracy
                    accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
                    accuracy_text = f"Accuracy: {accuracy:.1f}%"
                    accuracy_surface = self.instruction_font.render(accuracy_text, True, (255, 255, 255))
                    accuracy_rect = accuracy_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400))
                    screen.blit(accuracy_surface, accuracy_rect)
                except Exception as e:
                    logger.error(f"Error rendering completion screen: {e}")
                    
        except Exception as e:
            logger.error(f"Critical error in render: {e}")
            # Try to draw a basic error message
            try:
                screen.fill((200, 200, 200))
                font = pygame.font.SysFont('Arial', 24)
                error_text = font.render("Error: Unable to render. Press Back to return.", True, (255, 0, 0))
                screen.blit(error_text, (50, 50))
            except:
                pass