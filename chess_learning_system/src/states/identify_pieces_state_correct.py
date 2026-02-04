# 4. Updated identify_pieces_state.py
# src/states/identify_pieces_state.py

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
        self.questions_per_session = 12  # 2 questions per piece type
        self.hint_after_attempts = 2
        self.time_per_question = 30  # seconds
        
        # Progress tracking
        self.current_question = 0
        self.correct_answers = 0
        self.total_attempts = 0
        self.current_attempts = 0
        self.session_timer = Timer()
        
        # Current question data
        self.current_square = None
        self.current_piece_type = None
        self.showing_options = False
        self.selected_option = None
        self.show_feedback = False
        self.feedback_timer = 0
        self.feedback_message = ""
        
        # Chess board
        self.chess_board = ChessBoard(
            self.engine.screen, 
            self.engine.resource_manager,
            board_size=400  # Smaller board for this module
        )
        
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
        
        # Multiple choice options
        self.option_buttons = []
        self.create_option_buttons()
        
        # Animation elements
        self.animated_texts = []
        self.celebration_particles = []
        
        # Track which pieces have been asked about
        self.asked_pieces = []
        
    def _setup_learning_position(self):
        """Set up a position with all pieces visible"""
        # Custom position with all pieces clearly visible
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.chess_board.set_position(fen)
        
    def create_ui_elements(self):
        """Create UI elements for the module"""
        # Progress bar
        self.progress_bar = ProgressBar(
            pos=(50, 30),
            size=(300, 25),
            max_value=self.questions_per_session,
            config=self.config
        )
        
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
            pos=(self.config.SCREEN_WIDTH - 60, 50),
            size=(100, 40),
            callback=self.on_hint_clicked,
            config=self.config
        )
        
        # Skip button (for difficult questions)
        self.skip_button = Button(
            text="Skip",
            pos=(self.config.SCREEN_WIDTH // 2, 650),
            size=(100, 40),
            callback=self.skip_question,
            config=self.config
        )
        
    def create_option_buttons(self):
        """Create multiple choice option buttons"""
        self.option_buttons = []
        button_width = 150
        button_height = 50
        spacing = 20
        start_x = self.config.SCREEN_WIDTH // 2
        start_y = 480
        
        for i in range(4):
            row = i // 2
            col = i % 2
            x = start_x + (col - 0.5) * (button_width + spacing)
            y = start_y + row * (button_height + spacing)
            
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
        self.asked_pieces = []
        self.session_timer.reset()
        self.progress_bar.set_value(0)
        
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
        
        # Find all pieces on the board
        piece_squares = []
        for square in chess.SQUARES:
            piece = self.chess_board.get_piece_at(square)
            if piece:
                piece_squares.append((square, piece))
        
        # Select a random piece that hasn't been asked about recently
        available_pieces = [ps for ps in piece_squares if ps not in self.asked_pieces[-6:]]
        if not available_pieces:
            available_pieces = piece_squares
            self.asked_pieces = []
        
        square, piece = random.choice(available_pieces)
        self.current_square = square
        self.current_piece_type = piece.piece_type
        self.asked_pieces.append((square, piece))
        
        # Highlight the selected square
        self.chess_board.highlight_square(square)
        
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
        
        # Store correct answer index
        self.correct_option_index = self.options.index(correct_answer)
    
    def on_option_selected(self, index):
        """Handle option selection"""
        if not self.show_feedback and self.showing_options:
            self.selected_option = index
            self.current_attempts += 1
            self.total_attempts += 1
            
            if index == self.correct_option_index:
                self.on_correct_answer()

            else:
                self.on_incorrect_answer()
        print("on_option_selected function completed")
    
    def on_correct_answer(self):
        """Handle correct answer"""
        print("Correct answer selected")
        self.correct_answers += 1
        self.show_feedback = True
        self.feedback_timer = 0
        self.feedback_message = "Correct! Well done!"
        
        # Update progress
        self.progress_bar.set_value(self.current_question + 1)
        print("audio_manager is called")
        # Play success sound
        self.engine.audio_manager.play_sound('success.wav')
        print("returned from audio manager")
        # Create celebration effect
        print("create celebration is called")
        self.create_celebration()
        print("celebration created")
        # Add animated text
        points = max(100 - (self.current_attempts - 1) * 20, 20)
        print("animated text is creating")
        animated_text = AnimatedText(
            f"+{points} points!",
            (self.config.SCREEN_WIDTH // 2, 300),
            48,
            self.config.COLORS['secondary'],
            2.0,
            self.config
        )
        self.animated_texts.append(animated_text)
        print("on_correct_answer function completed")
    def on_incorrect_answer(self):
        """Handle incorrect answer"""
        self.show_feedback = True
        self.feedback_timer = 0
        self.feedback_message = f"Not quite. That was {self.options[self.selected_option]}."
        
        # Play error sound (gentle)
        self.engine.audio_manager.play_sound('error.wav')
        
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
    
    def skip_question(self):
        """Skip to next question"""
        if not self.show_feedback:
            self.next_question()
    
    def next_question(self):
        """Move to the next question"""
        self.current_question += 1
        
        if self.current_question >= self.questions_per_session:
            self.complete_session()
        else:
            self.generate_question()
    
    def complete_session(self):
        """Complete the learning session"""
        # Calculate performance
        print("Session complete! is called")
        accuracy = (self.correct_answers / self.questions_per_session) * 100
        avg_attempts = self.total_attempts / self.questions_per_session
        
        # TODO: Save progress and show results screen
        print(f"Session complete! Accuracy: {accuracy:.1f}%, Average attempts: {avg_attempts:.1f}")
        
        # Play completion sound
        self.engine.audio_manager.play_sound('complete.wav')
        
        # Return to main menu after a delay
        pygame.time.wait(2000)
        self.engine.change_state(GameState.MAIN_MENU)
        print("returning from complte session")
    def create_celebration(self):
        """Create visual celebration effect"""
        # Create particle effects
        print("create celebration funtion started execution entering the loop")
        for _ in range(20):
            #print("inside the loop")
            angle = random.uniform(0, 2 * 3.14159)
            #print("angle is generated")
            speed = random.uniform(100, 300)
            #print("speed is generated")
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
        print("celebration particles created")
    
    def on_back_clicked(self):
        """Handle back button click"""
        self.engine.change_state(GameState.MAIN_MENU)
    
    def handle_event(self, event):
        """Handle events"""
        # Handle button events
        #print("handle_event function started execution")
        self.back_button.handle_event(event)
        self.hint_button.handle_event(event)
        
        if self.current_attempts >= 3:
            self.skip_button.handle_event(event)
        
        # Handle option buttons
        if self.showing_options and not self.show_feedback:
            for button in self.option_buttons:
                button.handle_event(event)
        
        # Handle keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.show_feedback:
                self.next_question()
            elif event.key >= pygame.K_1 and event.key <= pygame.K_4:
                # Number keys for quick option selection
                option_index = event.key - pygame.K_1
                if option_index < len(self.option_buttons):
                    self.on_option_selected(option_index)
        #print("handle_event function completed")
    '''    
    def update(self, dt):
        """Update the identify pieces state"""
        super().update(dt)
        
        # Update UI elements
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.update(dt, mouse_pos)
        self.hint_button.update(dt, mouse_pos)
        
        if self.current_attempts >= 3:
            self.skip_button.update(dt, mouse_pos)
        
        for button in self.option_buttons:
            button.update(dt, mouse_pos)
        
        # Update feedback timer
        if self.show_feedback:
            self.feedback_timer += dt
            if self.feedback_timer > 3.0:
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
                self.celebration_particles.remove(particle)'''
    def update(self, dt):
        super().update(dt)  # Handle transitions from BaseState
        
        # Update UI elements
        mouse_pos = pygame.mouse.get_pos()
        try:
            self.back_button.update(dt, mouse_pos)
            self.hint_button.update(dt, mouse_pos)
            if self.current_attempts >= 3:
                self.skip_button.update(dt, mouse_pos)
            for button in self.option_buttons:
                button.update(dt, mouse_pos)
        except Exception as e:
            print(f"Error updating buttons: {e}")
        
        # Update feedback timer
        if self.show_feedback:
            self.feedback_timer += dt
            if self.feedback_timer > 3.0:
                self.next_question()
        
        # Update animated texts
        for text in self.animated_texts[:]:
            try:
                text.update(dt)
                if text.is_finished():
                    self.animated_texts.remove(text)
            except Exception as e:
                print(f"Error updating animated text: {e}")
        
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
                print(f"Error updating particle: {e}")
    
    def render(self, screen):
        """Render the identify pieces state"""
        # Clear screen
        screen.fill(self.config.COLORS['background'])
        
        # Draw title
        title_text = "Learn Chess Pieces"
        title_surface = self.question_font.render(title_text, True, self.config.COLORS['text_dark'])
        title_rect = title_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 40))
        screen.blit(title_surface, title_rect)
        
        # Draw progress bar
        self.progress_bar.render(screen)
        
        # Draw question
        question_text = "What is this piece called?"
        question_surface = self.option_font.render(question_text, True, self.config.COLORS['text_dark'])
        question_rect = question_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 120))
        screen.blit(question_surface, question_rect)
        
        # Draw chess board
        self.chess_board.draw()
        
        # Draw option buttons
        if self.showing_options:
            for i, button in enumerate(self.option_buttons):
                # Highlight correct answer if showing feedback
                if self.show_feedback:
                    if i == self.correct_option_index:
                        button.base_color = (0, 255, 0)  # Green for correct
                    elif i == self.selected_option and i != self.correct_option_index:
                        button.base_color = (255, 0, 0)  # Red for wrong selection
                button.render(screen)
        
        # Draw feedback
        if self.feedback_message:
            lines = self.feedback_message.split('\n')
            y = 580
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
            fact_rect = fact_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 640))
            screen.blit(fact_surface, fact_rect)
        
        # Draw navigation buttons
        self.back_button.render(screen)
        self.hint_button.render(screen)
        
        if self.current_attempts >= 3:
            self.skip_button.render(screen)
        
        # Draw score/stats
        score_text = f"Score: {self.correct_answers}/{self.current_question}"
        score_surface = self.info_font.render(score_text, True, self.config.COLORS['text_dark'])
        score_rect = score_surface.get_rect(topright=(self.config.SCREEN_WIDTH - 50, 100))
        screen.blit(score_surface, score_rect)
        
        # Draw animated texts
        for text in self.animated_texts:
            text.render(screen)
        
        # Draw celebration particles
        for particle in self.celebration_particles:
            pygame.draw.circle(screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             int(particle['size']))