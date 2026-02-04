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

class RookMovementState(BaseState):
    """Module for teaching rook movement rules"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Module configuration
            self.exercises_per_type = 3  # Exercises for each movement type
            self.movement_types = ['horizontal', 'vertical', 'blocked']
            
            # Progress tracking
            self.current_exercise = 0
            self.current_type_index = 0
            self.correct_moves = 0
            self.total_attempts = 0
            self.exercises_completed = {move_type: 0 for move_type in self.movement_types}
            
            # Current exercise data
            self.current_rook_square = None
            self.target_squares = []
            self.invalid_squares = []
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
                self.chess_board.board_offset_x = (self.config.SCREEN_WIDTH - 480) // 2
                self.chess_board.board_offset_y = 180
            except Exception as e:
                logger.error(f"Failed to initialize chess board: {e}")
                raise
            
            # UI elements
            self.create_ui_elements()
            
            # Instructions
            self.instructions = {
                'horizontal': "Rooks move horizontally any number of squares. Click a valid square.",
                'vertical': "Rooks move vertically any number of squares. Click a valid square.",
                'blocked': "Rooks can't jump over pieces. Click a valid square."
            }
            
            # Fonts
            try:
                self.title_font = pygame.font.Font(None, 48)
                self.instruction_font = pygame.font.Font(None, 32)
                self.info_font = pygame.font.Font(None, 24)
            except Exception as e:
                logger.error(f"Failed to load fonts: {e}")
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
            logger.error(f"Failed to initialize RookMovementState: {e}")
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
                pos=(self.config.SCREEN_WIDTH - 100, 50),
                size=(150, 40),
                callback=self.toggle_hint,
                config=self.config
            )
            
            self.skip_button = Button(
                text="Skip",
                pos=(self.config.SCREEN_WIDTH - 100, 100),
                size=(150, 40),
                callback=self.skip_exercise,
                config=self.config
            )
            
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
            logger.error(f"Failed to enter RookMovementState: {e}")
            self.engine.change_state(GameState.MAIN_MENU)
    
    def generate_exercise(self):
        """Generate a new exercise"""
        try:
            self.show_feedback = False
            self.selected_square = None
            self.show_hint = False
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
                if self.exercise_type == 'horizontal':
                    self._generate_horizontal()
                elif self.exercise_type == 'vertical':
                    self._generate_vertical()
                elif self.exercise_type == 'blocked':
                    self._generate_blocked()
            except Exception as e:
                logger.error(f"Failed to generate {self.exercise_type} exercise: {e}")
                self.next_exercise()
                
        except Exception as e:
            logger.error(f"Failed to generate exercise: {e}")
            self.feedback_message = "Error generating exercise. Skipping..."
            self.next_exercise()
    
    def _generate_horizontal(self):
        """Generate horizontal movement exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            rook_file = random.randint(0, 7)
            rook_rank = random.randint(0, 7)
            rook_square = chess.square(rook_file, rook_rank)
            self.chess_board.board.set_piece_at(rook_square, chess.Piece(chess.ROOK, chess.WHITE))
            self.current_rook_square = rook_square
            self.target_squares = [chess.square(f, rook_rank) for f in range(8) if f != rook_file]
            invalid_file = (rook_file + 4) % 8
            self.invalid_squares = [chess.square(invalid_file, r) for r in range(8) if r != rook_rank]
            self.chess_board.highlight_square(rook_square)
        except Exception as e:
            logger.error(f"Failed to generate horizontal exercise: {e}")
            raise
    
    def _generate_vertical(self):
        """Generate vertical movement exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            rook_file = random.randint(0, 7)
            rook_rank = random.randint(0, 7)
            rook_square = chess.square(rook_file, rook_rank)
            self.chess_board.board.set_piece_at(rook_square, chess.Piece(chess.ROOK, chess.WHITE))
            self.current_rook_square = rook_square
            self.target_squares = [chess.square(rook_file, r) for r in range(8) if r != rook_rank]
            invalid_rank = (rook_rank + 4) % 8
            self.invalid_squares = [chess.square(f, invalid_rank) for f in range(8) if f != rook_file]
            self.chess_board.highlight_square(rook_square)
        except Exception as e:
            logger.error(f"Failed to generate vertical exercise: {e}")
            raise
    
    def _generate_blocked(self):
        """Generate blocked movement exercise"""
        try:
            self.chess_board.reset()
            self.chess_board.board.clear()
            rook_file = random.randint(1, 6)
            rook_rank = random.randint(1, 6)
            rook_square = chess.square(rook_file, rook_rank)
            self.chess_board.board.set_piece_at(rook_square, chess.Piece(chess.ROOK, chess.WHITE))
            self.current_rook_square = rook_square
            
            if rook_file > 0:
                block_file = random.randint(0, rook_file - 1)
                self.chess_board.board.set_piece_at(chess.square(block_file, rook_rank), chess.Piece(chess.PAWN, chess.BLACK))
            if rook_file < 7:
                block_file = random.randint(rook_file + 1, 7)
                self.chess_board.board.set_piece_at(chess.square(block_file, rook_rank), chess.Piece(chess.PAWN, chess.BLACK))
            if rook_rank < 7:
                block_rank = random.randint(rook_rank + 1, 7)
                self.chess_board.board.set_piece_at(chess.square(rook_file, block_rank), chess.Piece(chess.PAWN, chess.BLACK))
            if rook_rank > 0:
                block_rank = random.randint(0, rook_rank - 1)
                self.chess_board.board.set_piece_at(chess.square(rook_file, block_rank), chess.Piece(chess.PAWN, chess.BLACK))
            
            self.target_squares = []
            for f in range(rook_file - 1, -1, -1):
                sq = chess.square(f, rook_rank)
                if self.chess_board.board.piece_at(sq):
                    break
                self.target_squares.append(sq)
            for f in range(rook_file + 1, 8):
                sq = chess.square(f, rook_rank)
                if self.chess_board.board.piece_at(sq):
                    break
                self.target_squares.append(sq)
            for r in range(rook_rank + 1, 8):
                sq = chess.square(rook_file, r)
                if self.chess_board.board.piece_at(sq):
                    break
                self.target_squares.append(sq)
            for r in range(rook_rank - 1, -1, -1):
                sq = chess.square(rook_file, r)
                if self.chess_board.board.piece_at(sq):
                    break
                self.target_squares.append(sq)
                
            self.invalid_squares = [sq for sq in range(64) if sq not in self.target_squares and sq != rook_square][:5]
            self.chess_board.highlight_square(rook_square)
        except Exception as e:
            logger.error(f"Failed to generate blocked exercise: {e}")
            raise
    
    def handle_square_click(self, square):
        """Handle square click"""
        try:
            if self.show_feedback or square is None:
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
            self.feedback_message = "Correct! Well done!"
            if self.selected_square is not None:
                self.chess_board.select_square(self.selected_square)
            if self.exercise_type:
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
                animated_text = AnimatedText(
                    "+100 points!",
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
            if self.selected_square in self.invalid_squares:
                self.feedback_message = "Not quite! Rooks can't move there."
            elif self.selected_square == self.current_rook_square:
                self.feedback_message = "Click where the rook can move."
            else:
                self.feedback_message = "Invalid move for this rook."
            try:
                self.engine.audio_manager.play_sound('error.wav')
            except Exception as e:
                logger.warning(f"Failed to play error sound: {e}")
        except Exception as e:
            logger.error(f"Error in on_incorrect_move: {e}")
            self.feedback_message = "Invalid move. Try again!"
    
    def toggle_hint(self):
        """Toggle hint"""
        try:
            self.show_hint = not self.show_hint
            if self.show_hint:
                for square in self.target_squares:
                    if 0 <= square <= 63:
                        self.chess_board.highlight_square(square)
        except Exception as e:
            logger.error(f"Error toggling hint: {e}")
    
    def skip_exercise(self):
        """Skip exercise"""
        try:
            if not self.show_feedback and self.exercise_type:
                self.exercises_completed[self.exercise_type] += 1
                self.next_exercise()
        except Exception as e:
            logger.error(f"Error skipping exercise: {e}")
            self.next_exercise()
    
    def next_exercise(self):
        """Next exercise"""
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
        """Complete module"""
        try:
            self.module_completed = True
            self.completion_timer = 0
            accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
            for _ in range(50):
                try:
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(200, 400)
                    self.celebration_particles.append({
                        'x': self.config.SCREEN_WIDTH // 2,
                        'y': self.config.SCREEN_HEIGHT // 2,
                        'vx': speed * math.cos(angle),
                        'vy': speed * math.sin(angle),
                        'color': random.choice([(255, 215, 0), (255, 255, 0), self.config.COLORS.get('accent', (155, 89, 182))]),
                        'life': 3.0,
                        'size': random.randint(5, 15)
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
        """Create celebration effect"""
        try:
            for _ in range(20):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(100, 300)
                self.celebration_particles.append({
                    'x': self.config.SCREEN_WIDTH // 2,
                    'y': 350,
                    'vx': speed * math.cos(angle),
                    'vy': speed * math.sin(angle),
                    'color': random.choice([self.config.COLORS.get('accent', (155, 89, 182)), self.config.COLORS.get('secondary', (46, 204, 113)), (255, 255, 0)]),
                    'life': 1.5,
                    'size': random.randint(3, 8)
                })
        except Exception as e:
            logger.warning(f"Failed to create celebration effect: {e}")
    
    def on_back_clicked(self):
        """Handle back button"""
        try:
            self.engine.change_state(GameState.MAIN_MENU)
        except Exception as e:
            logger.error(f"Error returning to main menu: {e}")
            try:
                self.engine.running = False
            except:
                pass
    
    def handle_event(self, event):
        """Handle events"""
        try:
            self.back_button.handle_event(event)
            self.hint_button.handle_event(event)
            if self.total_attempts > 2 and not self.show_feedback:
                self.skip_button.handle_event(event)
            if self.show_feedback:
                self.next_button.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                try:
                    square = self.chess_board.get_square_from_pos(event.pos)
                    self.handle_square_click(square)
                except Exception as e:
                    logger.error(f"Error getting square from position: {e}")
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.show_feedback:
                    self.next_exercise()
                elif event.key == pygame.K_h:
                    self.toggle_hint()
                elif event.key == pygame.K_s and self.total_attempts > 2:
                    self.skip_exercise()
        except Exception as e:
            logger.error(f"Error handling event: {e}")
    
    def update(self, dt):
        """Update state"""
        try:
            super().update(dt)
            mouse_pos = pygame.mouse.get_pos()
            self.back_button.update(dt, mouse_pos)
            self.hint_button.update(dt, mouse_pos)
            if self.total_attempts > 2 and not self.show_feedback:
                self.skip_button.update(dt, mouse_pos)
            if self.show_feedback:
                self.next_button.update(dt, mouse_pos)
            if self.show_feedback and not self.module_completed:
                self.feedback_timer += dt
            for text in self.animated_texts[:]:
                try:
                    text.update(dt)
                    if text.is_finished():
                        self.animated_texts.remove(text)
                except Exception as e:
                    logger.warning(f"Error updating animated text: {e}")
                    self.animated_texts.remove(text)
            for particle in self.celebration_particles[:]:
                try:
                    particle['x'] += particle['vx'] * dt
                    particle['y'] += particle['vy'] * dt
                    particle['vy'] += 500 * dt
                    particle['life'] -= dt
                    particle['size'] = max(1, particle['size'] - dt * 2)
                    if particle['life'] <= 0:
                        self.celebration_particles.remove(particle)
                except Exception as e:
                    logger.warning(f"Error updating particle: {e}")
                    self.celebration_particles.remove(particle)
            self.arrow_animation += dt * 2
            if self.arrow_animation > 1:
                self.arrow_animation = 0
            if self.module_completed:
                self.completion_timer += dt
                if self.completion_timer > 5.0:
                    self.engine.change_state(GameState.MAIN_MENU)
        except Exception as e:
            logger.error(f"Error in update: {e}")
    
    def render(self, screen):
        """Render state"""
        try:
            screen.fill(self.config.COLORS['background'])
            title_surface = self.title_font.render("Learn Rook Movement", True, self.config.COLORS['text_dark'])
            screen.blit(title_surface, title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 40)))
            #self.progress_bar.render(screen)
            if not self.module_completed and self.exercise_type:
                type_surface = self.instruction_font.render(f"Exercise: {self.exercise_type.title()}", True, self.config.COLORS['primary'])
                screen.blit(type_surface, type_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 100)))
                inst_surface = self.info_font.render(self.instructions.get(self.exercise_type, ""), True, self.config.COLORS['text_dark'])
                screen.blit(inst_surface, inst_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 140)))
            try:
                self.chess_board.draw()
            except Exception as e:
                logger.error(f"Error drawing chess board: {e}")
                error_surface = self.instruction_font.render("Error displaying board", True, self.config.COLORS.get('error', (255, 0, 0)))
                screen.blit(error_surface, error_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400)))
            if self.show_hint and not self.show_feedback:
                hint_surface = self.info_font.render("Valid moves highlighted in yellow", True, self.config.COLORS['secondary'])
                screen.blit(hint_surface, hint_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 670)))
            if self.feedback_message and not self.module_completed:
                color = self.config.COLORS['secondary'] if "Correct" in self.feedback_message else self.config.COLORS.get('error', (255, 0, 0))
                feedback_surface = self.instruction_font.render(self.feedback_message, True, color)
                screen.blit(feedback_surface, feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 600)))
            self.back_button.render(screen)
            self.hint_button.render(screen)
            if self.total_attempts > 2 and not self.show_feedback:
                self.skip_button.render(screen)
            if self.show_feedback:
                self.next_button.render(screen)
            for text in self.animated_texts:
                try:
                    text.render(screen)
                except Exception as e:
                    logger.warning(f"Error rendering animated text: {e}")
            for particle in self.celebration_particles:
                try:
                    pygame.draw.circle(screen, particle['color'], (int(particle['x']), int(particle['y'])), int(particle['size']))
                except Exception as e:
                    logger.warning(f"Error rendering particle: {e}")
            if self.module_completed:
                try:
                    overlay = pygame.Surface((screen.get_width(), screen.get_height()))
                    overlay.set_alpha(128)
                    overlay.fill((0, 0, 0))
                    screen.blit(overlay, (0, 0))
                    success_font = pygame.font.Font(None, 72)
                    success_surface = success_font.render("Congratulations!", True, (255, 215, 0))
                    screen.blit(success_surface, success_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 200)))
                    complete_surface = self.title_font.render("You've mastered rook movement!", True, (255, 255, 255))
                    screen.blit(complete_surface, complete_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 300)))
                    accuracy = (self.correct_moves / self.total_attempts * 100) if self.total_attempts > 0 else 0
                    accuracy_surface = self.instruction_font.render(f"Accuracy: {accuracy:.1f}%", True, (255, 255, 255))
                    screen.blit(accuracy_surface, accuracy_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 400)))
                except Exception as e:
                    logger.error(f"Error rendering completion screen: {e}")
        except Exception as e:
            logger.error(f"Critical error in render: {e}")
            try:
                screen.fill((200, 200, 200))
                font = pygame.font.SysFont('Arial', 24)
                error_text = font.render("Error: Unable to render. Press Back to return.", True, (255, 0, 0))
                screen.blit(error_text, (50, 50))
            except:
                pass