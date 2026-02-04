# src/states/identify_pieces_state.py - Fixed version with improved UI and functionality

import pygame
import random
import chess
import math
from src.core.state_machine import BaseState, GameState
from src.chess.chess_board import ChessBoard
from src.ui.components import Button, ProgressBar, AnimatedText
from src.utils.timer import Timer

class IdentifyPiecesState(BaseState):
    """Module for teaching chess piece identification"""
    
    def __init__(self, engine):
        super().__init__(engine)
        
        # Module configuration
        self.questions_per_session = 12  # 2 questions per piece type (1 white, 1 black)
        self.hint_after_attempts = 2
        self.time_per_question = 30  # seconds
        
        # Progress tracking
        self.current_question = 0
        self.correct_answers = 0
        self.total_attempts = 0
        self.current_attempts = 0
        self.session_timer = Timer()
        self.session_start_time = None
        
        # Current question data
        self.current_square = None
        self.current_piece_type = None
        self.current_piece_color = None
        self.showing_options = False
        self.selected_option = None
        self.show_feedback = False
        self.feedback_timer = 0
        self.feedback_message = ""
        
        # Chess board - positioned to the left
        self.chess_board = ChessBoard(
            self.engine.screen, 
            self.engine.resource_manager,
            board_size=400
        )
        # Position board on the left side
        self.chess_board.board_offset_x = 50
        self.chess_board.board_offset_y = 150
        
        # Set up a position with all pieces
        self._setup_learning_position()
        
        # UI elements
        self.create_ui_elements()
        
        # Piece information
        self.piece_names = {
            chess.PAWN: "Pawn",
            chess.KNIGHT: "Knight",
            chess.BISHOP: "Bishop",
            chess.ROOK: "Rook",
            chess.QUEEN: "Queen",
            chess.KING: "King"
        }
        
        self.piece_info = {
            chess.PAWN: {
                'description': 'The smallest piece that moves forward',
                'hint': 'This piece looks like a small soldier',
                'fun_fact': 'You start with 8 pawns!'
            },
            chess.ROOK: {
                'description': 'Moves in straight lines like a castle',
                'hint': 'This piece looks like a castle tower',
                'fun_fact': 'Rooks are also called castles!'
            },
            chess.KNIGHT: {
                'description': 'Moves in an L-shape and can jump',
                'hint': 'This piece looks like a horse',
                'fun_fact': 'Knights are the only pieces that can jump!'
            },
            chess.BISHOP: {
                'description': 'Moves diagonally across the board',
                'hint': 'This piece has a pointed hat',
                'fun_fact': 'Bishops always stay on the same color squares!'
            },
            chess.QUEEN: {
                'description': 'The most powerful piece',
                'hint': 'This piece wears a crown with points',
                'fun_fact': 'The Queen can move in any direction!'
            },
            chess.KING: {
                'description': 'The most important piece to protect',
                'hint': 'This piece has a cross on top',
                'fun_fact': 'The game ends if the King is captured!'
            }
        }
        
        # Load fonts
        self.question_font = pygame.font.Font(None, 36)
        self.option_font = pygame.font.Font(None, 28)
        self.info_font = pygame.font.Font(None, 24)
        
        # Multiple choice options - positioned on the right side
        self.option_buttons = []
        self.create_option_buttons()
        
        # Animation elements
        self.animated_texts = []
        self.celebration_particles = []
        
        # Track which piece/color combinations have been asked
        self.asked_combinations = set()  # Will store (piece_type, color) tuples
        self.questions_history = []  # Store all questions for final report
        
        # Final results screen
        self.show_results = False
        self.results_timer = 0
        
    def _setup_learning_position(self):
        """Set up a position with all pieces visible"""
        # Standard starting position
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.chess_board.set_position(fen)
        
    def create_ui_elements(self):
        """Create UI elements for the module"""
        # Progress bar - moved to top right
        ##self.progress_bar = ProgressBar(
        #    pos=(self.config.SCREEN_WIDTH - 350, 30),
        #    size=(300, 25),
        #    max_value=self.questions_per_session,
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
            text="Hint",
            pos=(self.config.SCREEN_WIDTH - 60, 90),
            size=(100, 40),
            callback=self.on_hint_clicked,
            config=self.config
        )
        
        # Continue button for results screen
        self.continue_button = Button(
            text="Continue",
            pos=(self.config.SCREEN_WIDTH // 2, 600),
            size=(150, 50),
            callback=self.return_to_menu,
            config=self.config
        )
        
    def create_option_buttons(self):
        """Create multiple choice option buttons on the right side"""
        self.option_buttons = []
        button_width = 180
        button_height = 60
        spacing = 20
        
        # Position buttons on the right side, away from the board
        start_x = 600  # Right side of the screen
        start_y = 250  # Below the title and score
        
        for i in range(4):
            x = start_x
            y = start_y + i * (button_height + spacing)
            
            button = Button(
                text="",  # Will be set when generating options
                pos=(x, y),
                size=(button_width, button_height),
                callback=lambda idx=i: self.on_option_selected(idx),
                config=self.config
            )
            self.option_buttons.append(button)
    
    def enter(self):
        """Called when entering the identify pieces state"""
        super().enter()
        
        # Reset session
        self.current_question = 0
        self.correct_answers = 0
        self.total_attempts = 0
        self.asked_combinations.clear()
        self.questions_history = []
        self.session_timer.reset()
        self.session_start_time = pygame.time.get_ticks()
        #self.progress_bar.set_value(0)
        self.show_results = False
        
        # Start first question
        self.generate_question()
        
        # Play learning music
        self.engine.audio_manager.play_music('learning_theme.ogg', loops=-1)
    
    def generate_question(self):
        """Generate a new piece identification question"""
        self.current_attempts = 0
        self.show_feedback = False
        self.selected_option = None
        self.showing_options = True
        self.chess_board.clear_highlights()
        
        # Get all available piece/color combinations that haven't been asked
        available_combinations = []
        
        # We need to ask about each piece type twice (once white, once black)
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
            for color in [chess.WHITE, chess.BLACK]:
                if (piece_type, color) not in self.asked_combinations:
                    available_combinations.append((piece_type, color))
        
        if not available_combinations:
            # This shouldn't happen with 12 questions, but just in case
            self.complete_session()
            return
        
        # Select a random combination
        piece_type, color = random.choice(available_combinations)
        self.asked_combinations.add((piece_type, color))
        
        # Find all squares with this piece type and color
        matching_squares = []
        for square in chess.SQUARES:
            piece = self.chess_board.get_piece_at(square)
            if piece and piece.piece_type == piece_type and piece.color == color:
                matching_squares.append(square)
        
        if matching_squares:
            # Select a random square from matching pieces
            self.current_square = random.choice(matching_squares)
            self.current_piece_type = piece_type
            self.current_piece_color = color
            
            # Highlight the selected square
            self.chess_board.highlight_square(self.current_square)
            
            # Generate multiple choice options
            self._generate_options()
    
    def _generate_options(self):
        """Generate multiple choice options"""
        correct_answer = self.piece_names[self.current_piece_type]
        
        # Get other piece names
        other_pieces = [name for piece_type, name in self.piece_names.items() 
                       if piece_type != self.current_piece_type]
        
        # Select 3 random wrong answers
        wrong_answers = random.sample(other_pieces, 3)
        
        # Create options list and shuffle
        self.options = [correct_answer] + wrong_answers
        random.shuffle(self.options)
        
        # Update button texts
        for i, button in enumerate(self.option_buttons):
            button.text = self.options[i]
            # Reset button colors
            button.base_color = self.config.COLORS['primary']
            button.hover_color = button._brighten_color(button.base_color)
        
        # Store correct answer index
        self.correct_option_index = self.options.index(correct_answer)
    
    def on_option_selected(self, index):
        """Handle option selection"""
        if not self.show_feedback and self.showing_options:
            self.selected_option = index
            self.current_attempts += 1
            self.total_attempts += 1
            
            # Record this question
            self.questions_history.append({
                'piece_type': self.current_piece_type,
                'piece_color': self.current_piece_color,
                'correct': index == self.correct_option_index,
                'attempts': self.current_attempts
            })
            
            if index == self.correct_option_index:
                self.on_correct_answer()
            else:
                self.on_incorrect_answer()
    
    def on_correct_answer(self):
        """Handle correct answer"""
        self.correct_answers += 1
        self.show_feedback = True
        self.feedback_timer = 0
        self.feedback_message = "Correct! Well done!"
        
        # Update progress bar
        #self.progress_bar.set_value(self.current_question + 1)
        
        # Play success sound
        self.engine.audio_manager.play_sound('success')
        
        # Create celebration effect
        self.create_celebration()
        
        # Add animated text
        points = max(100 - (self.current_attempts - 1) * 20, 20)
        animated_text = AnimatedText(
            f"+{points} points!",
            (self.config.SCREEN_WIDTH // 2, 300),
            48,
            self.config.COLORS['secondary'],
            2.0,
            self.config
        )
        self.animated_texts.append(animated_text)
    
    def on_incorrect_answer(self):
        """Handle incorrect answer"""
        self.show_feedback = True
        self.feedback_timer = 0
        self.feedback_message = f"Not quite. That was {self.options[self.selected_option]}."
        
        # Play error sound (gentle)
        self.engine.audio_manager.play_error_sound()
        
        # Show hint after multiple attempts
        if self.current_attempts >= self.hint_after_attempts:
            self.show_hint()
    
    def show_hint(self):
        """Display a hint for the current piece"""
        hint_text = self.piece_info[self.current_piece_type]['hint']
        self.feedback_message += f"\n{hint_text}"
    
    def on_hint_clicked(self):
        """Handle hint button click"""
        if self.showing_options and not self.show_feedback:
            self.show_hint()
            self.feedback_message = self.piece_info[self.current_piece_type]['hint']
            self.feedback_timer = 0
    
    def next_question(self):
        """Move to the next question"""
        self.current_question += 1
        
        if self.current_question >= self.questions_per_session:
            self.complete_session()
        else:
            self.generate_question()
    
    def complete_session(self):
        """Complete the learning session and show results"""
        # Calculate statistics
        accuracy = (self.correct_answers / self.questions_per_session) * 100 if self.questions_per_session > 0 else 0
        avg_attempts = self.total_attempts / self.questions_per_session if self.questions_per_session > 0 else 0
        
        # Calculate time taken
        time_taken = (pygame.time.get_ticks() - self.session_start_time) / 1000  # in seconds
        
        # Show results screen
        self.show_results = True
        self.results_timer = 0
        
        # Play completion sound
        self.engine.audio_manager.play_success_sound()
        
        # Create big celebration
        for _ in range(50):
            self.create_celebration()
    
    def create_celebration(self):
        """Create visual celebration effect"""
        for _ in range(20):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(100, 300)
            self.celebration_particles.append({
                'x': self.config.SCREEN_WIDTH // 2,
                'y': 300,
                'vx': speed * math.cos(angle),
                'vy': speed * math.sin(angle),
                'color': random.choice([
                    self.config.COLORS['accent'],
                    self.config.COLORS['secondary'],
                    (255, 255, 0)
                ]),
                'life': 1.5,
                'size': random.randint(3, 8)
            })
    
    def return_to_menu(self):
        """Return to main menu"""
        self.engine.change_state(GameState.MAIN_MENU)
    
    def on_back_clicked(self):
        """Handle back button click"""
        self.engine.change_state(GameState.MAIN_MENU)
    
    def handle_event(self, event):
        """Handle events"""
        # Handle button events
        self.back_button.handle_event(event)
        self.hint_button.handle_event(event)
        
        if self.show_results:
            self.continue_button.handle_event(event)
            return
        
        # Handle option buttons
        if self.showing_options and not self.show_feedback:
            for i, button in enumerate(self.option_buttons):
                if button.handle_event(event):
                    print(f"🔍 DEBUG: Option button {i} clicked")
                    self.on_option_selected(i)
        
        # Handle keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.show_feedback:
                self.next_question()
            elif event.key >= pygame.K_1 and event.key <= pygame.K_4:
                # Number keys for quick option selection
                option_index = event.key - pygame.K_1
                if option_index < len(self.option_buttons) and not self.show_feedback:
                    self.on_option_selected(option_index)
    
    def update(self, dt):
        """Update the identify pieces state"""
        super().update(dt)
        
        # Update UI elements
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.update(dt, mouse_pos)
        self.hint_button.update(dt, mouse_pos)
        
        if self.show_results:
            self.continue_button.update(dt, mouse_pos)
        else:
            for button in self.option_buttons:
                button.update(dt, mouse_pos)
        
        # Update feedback timer
        if self.show_feedback and not self.show_results:
            self.feedback_timer += dt
            if self.feedback_timer > 2.5:
                self.next_question()
        
        # Update animated texts
        for text in self.animated_texts[:]:
            text.update(dt)
            if text.is_finished():
                self.animated_texts.remove(text)
        
        # Update celebration particles
        for particle in self.celebration_particles[:]:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['vy'] += 500 * dt  # Gravity
            particle['life'] -= dt
            particle['size'] = max(1, particle['size'] - dt * 2)
            
            if particle['life'] <= 0:
                self.celebration_particles.remove(particle)
    
    def render(self, screen):
        """Render the identify pieces state"""
        # Clear screen
        screen.fill(self.config.COLORS['background'])
        
        if self.show_results:
            self._render_results_screen(screen)
            return
        
        # Draw title
        title_text = "Learn Chess Pieces"
        title_surface = self.question_font.render(title_text, True, self.config.COLORS['text_dark'])
        title_rect = title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 40))
        screen.blit(title_surface, title_rect)
        
        # Draw progress bar
        #self.progress_bar.render(screen)
        
        # Draw question
        question_text = "What is this piece called?"
        question_surface = self.option_font.render(question_text, True, self.config.COLORS['text_dark'])
        question_rect = question_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 100))
        screen.blit(question_surface, question_rect)
        
        # Draw chess board
        self.chess_board.draw()
        
        # Draw stylish frame around options area
        options_frame = pygame.Rect(520, 200, 260, 350)
        pygame.draw.rect(screen, (230, 230, 230), options_frame, border_radius=15)
        pygame.draw.rect(screen, (200, 200, 200), options_frame, 3, border_radius=15)
        
        # Draw "Choose your answer:" text
        choose_text = "Choose your answer:"
        choose_surface = self.info_font.render(choose_text, True, self.config.COLORS['text_dark'])
        choose_rect = choose_surface.get_rect(center=(650, 220))
        screen.blit(choose_surface, choose_rect)
        
        # Draw option buttons
        if self.showing_options:
            for i, button in enumerate(self.option_buttons):
                # Highlight correct answer if showing feedback
                if self.show_feedback:
                    if i == self.correct_option_index:
                        button.base_color = self.config.COLORS['secondary']  # Green for correct
                    elif i == self.selected_option and i != self.correct_option_index:
                        button.base_color = self.config.COLORS['danger']  # Red for wrong selection
                button.render(screen)
        
        # Draw feedback at the bottom
        if self.feedback_message:
            # Create a feedback box
            feedback_box = pygame.Rect(50, 580, self.config.SCREEN_WIDTH - 100, 80)
            pygame.draw.rect(screen, (250, 250, 250), feedback_box, border_radius=10)
            pygame.draw.rect(screen, (200, 200, 200), feedback_box, 2, border_radius=10)
            
            lines = self.feedback_message.split('\n')
            y = 600
            for line in lines:
                feedback_surface = self.info_font.render(line, True, self.config.COLORS['text_dark'])
                feedback_rect = feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, y))
                screen.blit(feedback_surface, feedback_rect)
                y += 30
        
        # Draw piece information when correct
        if self.show_feedback and self.selected_option == self.correct_option_index:
            info = self.piece_info[self.current_piece_type]
            
            # Fun fact
            fact_surface = self.info_font.render(info['fun_fact'], True, self.config.COLORS['primary'])
            fact_rect = fact_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 650))
            screen.blit(fact_surface, fact_rect)
        
        # Draw navigation buttons
        self.back_button.render(screen)
        self.hint_button.render(screen)
        
        # Draw score/stats
        score_text = f"Score: {self.correct_answers}/{self.current_question}"
        score_surface = self.info_font.render(score_text, True, self.config.COLORS['text_dark'])
        score_rect = score_surface.get_rect(topright=(self.config.SCREEN_WIDTH - 50, 70))
        screen.blit(score_surface, score_rect)
        
        # Draw animated texts
        for text in self.animated_texts:
            text.render(screen)
        
        # Draw celebration particles
        for particle in self.celebration_particles:
            pygame.draw.circle(screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             int(particle['size']))
    
    def _render_results_screen(self, screen):
        """Render the final results screen"""
        # Calculate statistics
        accuracy = (self.correct_answers / self.questions_per_session) * 100 if self.questions_per_session > 0 else 0
        time_taken = (pygame.time.get_ticks() - self.session_start_time) / 1000
        minutes = int(time_taken // 60)
        seconds = int(time_taken % 60)
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Draw results box
        results_box = pygame.Rect(self.config.SCREEN_WIDTH // 2 - 300, 100, 600, 450)
        pygame.draw.rect(screen, (255, 255, 255), results_box, border_radius=20)
        pygame.draw.rect(screen, self.config.COLORS['primary'], results_box, 4, border_radius=20)
        
        # Title
        title_font = pygame.font.Font(None, 48)
        title_text = "Great Job!"
        title_surface = title_font.render(title_text, True, self.config.COLORS['primary'])
        title_rect = title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 150))
        screen.blit(title_surface, title_rect)
        
        # Draw stars based on accuracy
        stars = 3 if accuracy >= 90 else 2 if accuracy >= 70 else 1
        star_y = 200
        star_spacing = 60
        star_start_x = self.config.SCREEN_WIDTH // 2 - (stars - 1) * star_spacing // 2
        
        for i in range(stars):
            star_x = star_start_x + i * star_spacing
            self._draw_star(screen, (star_x, star_y), 25, (255, 215, 0))
        
        # Statistics
        stats_font = pygame.font.Font(None, 32)
        stats_y = 260
        stats_spacing = 40
        
        # Correct answers
        correct_text = f"Correct Answers: {self.correct_answers}/{self.questions_per_session}"
        correct_surface = stats_font.render(correct_text, True, self.config.COLORS['text_dark'])
        correct_rect = correct_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, stats_y))
        screen.blit(correct_surface, correct_rect)
        
        # Accuracy
        accuracy_text = f"Accuracy: {accuracy:.1f}%"
        accuracy_color = self.config.COLORS['secondary'] if accuracy >= 70 else self.config.COLORS['danger']
        accuracy_surface = stats_font.render(accuracy_text, True, accuracy_color)
        accuracy_rect = accuracy_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, stats_y + stats_spacing))
        screen.blit(accuracy_surface, accuracy_rect)
        
        # Time taken
        time_text = f"Time: {minutes:02d}:{seconds:02d}"
        time_surface = stats_font.render(time_text, True, self.config.COLORS['text_dark'])
        time_rect = time_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, stats_y + stats_spacing * 2))
        screen.blit(time_surface, time_rect)
        
        # Piece breakdown
        breakdown_y = 420
        breakdown_text = "You've learned all 6 chess pieces!"
        breakdown_surface = self.info_font.render(breakdown_text, True, self.config.COLORS['primary'])
        breakdown_rect = breakdown_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, breakdown_y))
        screen.blit(breakdown_surface, breakdown_rect)
        
        # Encouragement message
        if accuracy >= 90:
            message = "Outstanding! You're a chess piece expert!"
        elif accuracy >= 70:
            message = "Well done! Keep practicing!"
        else:
            message = "Good effort! Practice makes perfect!"
        
        message_surface = self.option_font.render(message, True, self.config.COLORS['text_dark'])
        message_rect = message_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 470))
        screen.blit(message_surface, message_rect)
        
        # Continue button
        self.continue_button.render(screen)
        
        # Draw celebration particles
        for particle in self.celebration_particles:
            pygame.draw.circle(screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             int(particle['size']))
    
    def _draw_star(self, screen, pos, size, color):
        """Draw a star shape"""
        points = []
        for i in range(10):
            angle = math.pi * i / 5
            if i % 2 == 0:
                radius = size
            else:
                radius = size * 0.5
            x = pos[0] + radius * math.cos(angle - math.pi / 2)
            y = pos[1] + radius * math.sin(angle - math.pi / 2)
            points.append((x, y))
        
        pygame.draw.polygon(screen, color, points)
        pygame.draw.polygon(screen, (200, 200, 0), points, 2)