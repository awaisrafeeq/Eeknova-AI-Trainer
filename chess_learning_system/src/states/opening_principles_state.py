# src/states/opening_principles_state_enhanced.py
"""
Enhanced version of Opening Principles State with full exercise integration
This replaces the basic opening_principles_state.py with more features
"""

import pygame
import chess
import random
from src.core.state_machine import BaseState, GameState
from src.chess.chess_board import ChessBoard
from src.ui.components import Button, ProgressBar, AnimatedText
from src.utils.timer import Timer
from .parts.opening_analyzer import OpeningAnalyzer
from .parts.first_game_engine import FirstGameEngine
from .parts.game_analyzer import GameAnalyzer
from .parts.opening_exercises import OpeningExercises
import math
import logging

logger = logging.getLogger(__name__)

class OpeningPrinciplesState(BaseState):
    """Complete Opening Principles & First Game Module"""
    
    def __init__(self, engine):
        try:
            super().__init__(engine)
            
            # Initialize exercise system
            self.exercises = OpeningExercises()
            
            # Module phases
            self.module_phases = [
                'welcome',                      # Welcome and overview
                'principle_introduction',        # Learn each principle
                'principle_practice',           # Practice exercises
                'mistake_recognition',          # Find opening mistakes
                'opening_repertoire',           # Learn openings
                'pre_game_coaching',           # Preparation for first game
                'guided_first_game',           # Play with guidance
                'post_game_analysis',          # Analyze the game
                'graduation'                   # Module completion
            ]
            
            self.current_phase_index = 0
            self.current_phase = self.module_phases[0]
            
            # Phase-specific state
            self.current_principle_index = 0
            self.current_exercise = None
            self.current_opening_index = 0
            self.selected_answer = None
            
            # Opening principles (comprehensive)
            self.opening_principles = {
                'control_center': {
                    'name': 'Control the Center',
                    'description': 'Place pawns on e4, d4, e5, or d5 to control key squares',
                    'importance': 10,
                    'icon': '♟',
                    'color': (100, 200, 100)
                },
                'develop_pieces': {
                    'name': 'Develop Your Pieces',
                    'description': 'Bring knights and bishops into active positions',
                    'importance': 9,
                    'icon': '♞',
                    'color': (200, 150, 100)
                },
                'king_safety': {
                    'name': 'Ensure King Safety',
                    'description': 'Castle early to protect your king',
                    'importance': 10,
                    'icon': '♔',
                    'color': (255, 215, 0)
                },
                'dont_move_piece_twice': {
                    'name': "Don't Move Pieces Twice",
                    'description': 'Develop all pieces before moving any twice',
                    'importance': 7,
                    'icon': '⚡',
                    'color': (150, 150, 255)
                },
                'dont_bring_queen_early': {
                    'name': "Don't Bring Queen Out Early",
                    'description': 'The queen is vulnerable to attacks from minor pieces',
                    'importance': 8,
                    'icon': '♕',
                    'color': (255, 150, 150)
                },
                'connect_rooks': {
                    'name': 'Connect Your Rooks',
                    'description': 'Complete development by connecting rooks',
                    'importance': 6,
                    'icon': '♜',
                    'color': (200, 200, 200)
                }
            }
            
            # Initialize components
            self.opening_analyzer = OpeningAnalyzer(self.opening_principles)
            self.first_game_engine = FirstGameEngine(self.config)
            self.game_analyzer = GameAnalyzer()
            
            # Chess board
            self.chess_board = ChessBoard(
                self.engine.screen,
                self.engine.resource_manager,
                board_size=480
            )
            self.chess_board.board_offset_x = 50
            self.chess_board.board_offset_y = 120
            
            # Game state
            self.game_board = chess.Board()
            self.game_moves = []
            self.move_evaluations = []
            self.is_player_turn = True
            self.selected_square = None
            self.legal_moves = []
            
            # Progress tracking
            self.phase_scores = {}
            self.total_score = 0
            self.exercises_completed = 0
            self.correct_answers = 0
            self.total_attempts = 0
            self.principle_mastery = {key: 0 for key in self.opening_principles}
            
            # UI state
            self.show_feedback = False
            self.feedback_message = ""
            self.feedback_timer = 0
            self.feedback_color = None
            self.show_hints = False
            self.hint_text = ""
            
            # Animations
            self.animated_texts = []
            self.particle_effects = []
            
            # Timers
            self.session_timer = Timer()
            self.phase_timer = Timer()
            
            # Create UI
            self.create_ui_elements()
            
            # Load resources
            self.load_resources()
            
        except Exception as e:
            logger.error(f"Failed to initialize OpeningPrinciplesState: {e}")
            raise
    
    def load_resources(self):
        """Load fonts and other resources"""
        try:
            self.title_font = pygame.font.Font(None, 48)
            self.subtitle_font = pygame.font.Font(None, 36)
            self.text_font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 20)
            self.icon_font = pygame.font.Font(None, 64)
        except Exception as e:
            logger.error(f"Failed to load resources: {e}")
    
    def create_ui_elements(self):
        """Create all UI elements"""
        try:
            # Navigation
            self.back_button = Button(
                text="← Back",
                pos=(50, 30),
                size=(100, 40),
                callback=self.on_back_clicked,
                config=self.config
            )
            
            # Progress
            self.phase_progress_bar = ProgressBar(
                pos=(200, 30),
                size=(400, 25),
                max_value=len(self.module_phases),
                config=self.config
            )
            
            # Controls
            self.next_button = Button(
                text="Next →",
                pos=(650, 680),
                size=(120, 45),
                callback=self.next_phase,
                config=self.config
            )
            
            self.hint_button = Button(
                text="💡 Hint",
                pos=(650, 30),
                size=(100, 40),
                callback=self.toggle_hints,
                config=self.config
            )
            
            # Exercise buttons
            self.answer_buttons = []
            for i in range(4):
                button = Button(
                    text="",
                    pos=(550, 300 + i * 60),
                    size=(220, 45),
                    callback=lambda idx=i: self.select_answer(idx),
                    config=self.config
                )
                self.answer_buttons.append(button)
            
            # Game controls
            self.resign_button = Button(
                text="Resign",
                pos=(550, 450),
                size=(100, 35),
                callback=self.resign_game,
                config=self.config
            )
            
            self.analyze_button = Button(
                text="Analyze",
                pos=(670, 450),
                size=(100, 35),
                callback=self.analyze_position,
                config=self.config
            )
            
        except Exception as e:
            logger.error(f"Failed to create UI: {e}")
    
    def enter(self):
        """Enter the module"""
        super().enter()
        self.session_timer.reset()
        self.phase_timer.reset()
        
        # Reset state
        self.current_phase_index = 0
        self.current_phase = self.module_phases[0]
        self.total_score = 0
        self.exercises_completed = 0
        
        # Start first phase
        self.start_phase('welcome')
        
        # Play music
        try:
            self.engine.audio_manager.play_music('opening_theme.ogg', loops=-1)
        except:
            pass
    
    def start_phase(self, phase_name):
        """Initialize a new phase"""
        self.current_phase = phase_name
        self.phase_timer.reset()
        self.show_feedback = False
        self.animated_texts.clear()
        
        # Phase-specific initialization
        phase_handlers = {
            'welcome': self.start_welcome,
            'principle_introduction': self.start_principle_intro,
            'principle_practice': self.start_practice,
            'mistake_recognition': self.start_mistake_recognition,
            'opening_repertoire': self.start_repertoire,
            'pre_game_coaching': self.start_pre_game,
            'guided_first_game': self.start_game,
            'post_game_analysis': self.start_analysis,
            'graduation': self.start_graduation
        }
        
        handler = phase_handlers.get(phase_name)
        if handler:
            handler()
    
    def start_welcome(self):
        """Welcome phase"""
        self.game_board.reset()
        self.chess_board.set_board(self.game_board)
        
        welcome_text = "Welcome to Your Chess Journey's Final Chapter!"
        self.create_animated_text(welcome_text, (400, 100), size=36, duration=5.0)
        
        subtitle = "Master the Opening Principles & Play Your First Complete Game"
        self.create_animated_text(subtitle, (400, 150), size=24, duration=5.0, delay=1.0)
    
    def start_principle_intro(self):
        """Introduce principles one by one"""
        if self.current_principle_index < len(self.opening_principles):
            principle_key = list(self.opening_principles.keys())[self.current_principle_index]
            principle = self.opening_principles[principle_key]
            
            # Show principle
            self.create_animated_text(
                principle['name'],
                (400, 100),
                size=32,
                duration=4.0,
                color=principle['color']
            )
            
            # Show description
            self.create_animated_text(
                principle['description'],
                (400, 150),
                size=24,
                duration=4.0,
                delay=0.5
            )
            
            # Show icon
            self.current_principle_icon = principle['icon']
            
            # Get tips
            tips = self.exercises.get_principle_tips(principle_key)
            for i, tip in enumerate(tips[:3]):
                self.create_animated_text(
                    f"• {tip}",
                    (400, 250 + i * 30),
                    size=20,
                    duration=4.0,
                    delay=1.0 + i * 0.3
                )
        else:
            self.next_phase()
    
    def start_practice(self):
        """Start practice exercises"""
        # Get exercise for current principle
        principle_key = list(self.opening_principles.keys())[
            self.current_principle_index % len(self.opening_principles)
        ]
        
        self.current_exercise = self.exercises.create_quiz_position(principle_key)
        
        if self.current_exercise:
            # Set up board
            self.chess_board.set_board(self.current_exercise['board'])
            
            # Update answer buttons
            for i, button in enumerate(self.answer_buttons):
                if i < len(self.current_exercise['options']):
                    button.text = self.current_exercise['options'][i]
                    button.visible = True
                else:
                    button.visible = False
    
    def start_mistake_recognition(self):
        """Start mistake recognition phase"""
        mistake = self.exercises.get_random_mistake_position()
        
        if mistake:
            self.current_exercise = mistake
            self.chess_board.set_board(chess.Board(mistake['fen']))
            
            # Show description
            self.create_animated_text(
                "Find the Opening Mistake!",
                (400, 100),
                size=28,
                duration=3.0,
                color=(255, 100, 100)
            )
    
    def start_repertoire(self):
        """Learn opening sequences"""
        openings = list(self.exercises.opening_sequences.values())
        
        if self.current_opening_index < len(openings):
            opening = openings[self.current_opening_index]
            
            # Show opening name
            self.create_animated_text(
                opening['name'],
                (400, 100),
                size=32,
                duration=4.0
            )
            
            # Show description
            self.create_animated_text(
                opening['description'],
                (400, 150),
                size=20,
                duration=4.0,
                delay=0.5
            )
            
            # Demonstrate moves
            self.demonstrate_opening(opening['moves'])
    
    def start_pre_game(self):
        """Pre-game coaching"""
        self.create_animated_text(
            "Ready for Your First Complete Game!",
            (400, 100),
            size=32,
            duration=4.0,
            color=(100, 255, 100)
        )
        
        tips = [
            "Remember: Control the center with pawns",
            "Develop knights before bishops",
            "Castle within the first 10 moves",
            "Don't move pieces twice without reason",
            "Keep your queen safe",
            "I'll guide you through each move!"
        ]
        
        for i, tip in enumerate(tips):
            self.create_animated_text(
                tip,
                (400, 200 + i * 40),
                size=20,
                duration=5.0,
                delay=1.0 + i * 0.5
            )
    
    def start_game(self):
        """Start the guided game"""
        self.game_board.reset()
        self.chess_board.set_board(self.game_board)
        self.game_moves.clear()
        self.move_evaluations.clear()
        self.is_player_turn = True
        
        self.first_game_engine.start_new_game()
        
        self.create_animated_text(
            "Your First Game Begins! You play White.",
            (400, 100),
            size=28,
            duration=3.0
        )
    
    def start_analysis(self):
        """Analyze the completed game"""
        if self.game_moves:
            analysis = self.game_analyzer.analyze_game(
                self.game_moves,
                self.move_evaluations,
                self.opening_principles
            )
            
            self.game_analysis = analysis
            
            # Show analysis summary
            self.create_animated_text(
                "Game Analysis Complete!",
                (400, 100),
                size=32,
                duration=4.0
            )
            
            # Show key metrics
            metrics = [
                f"Accuracy: {analysis['accuracy']:.1f}%",
                f"Opening Score: {analysis['opening_score']:.0f}/100",
                f"Total Moves: {analysis['total_moves']}"
            ]
            
            for i, metric in enumerate(metrics):
                self.create_animated_text(
                    metric,
                    (400, 200 + i * 40),
                    size=24,
                    duration=4.0,
                    delay=1.0 + i * 0.3
                )
    
    def start_graduation(self):
        """Module completion celebration"""
        self.calculate_final_score()
        
        self.create_animated_text(
            "🎉 Congratulations! Module Complete! 🎉",
            (400, 100),
            size=36,
            duration=6.0,
            color=(255, 215, 0)
        )
        
        # Create celebration particles
        self.create_celebration_effects()
        
        # Show achievements
        achievements = self.calculate_achievements()
        for i, achievement in enumerate(achievements[:5]):
            self.create_animated_text(
                f"🏆 {achievement}",
                (400, 250 + i * 35),
                size=22,
                duration=6.0,
                delay=2.0 + i * 0.5,
                color=(255, 200, 100)
            )
    
    def update(self, dt):
        """Update module state"""
        super().update(dt)
        
        # Update timers
        if self.show_feedback:
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                self.show_feedback = False
        
        # Update animations
        for text in self.animated_texts[:]:
            text.update(dt)
            if text.is_complete():
                self.animated_texts.remove(text)
        
        # Update particles
        for particle in self.particle_effects[:]:
            particle.update(dt)
            if particle.is_dead():
                self.particle_effects.remove(particle)
        
        # Handle AI moves in game phase
        if self.current_phase == 'guided_first_game':
            if not self.is_player_turn and not self.game_board.is_game_over():
                if self.first_game_engine.is_thinking():
                    move = self.first_game_engine.get_ai_move(self.game_board)
                    if move:
                        self.make_move(move)
                        self.is_player_turn = True
        
        # Update UI
        mouse_pos = pygame.mouse.get_pos()
        self.update_buttons(dt, mouse_pos)
    
    def render(self, screen):
        """Render the module"""
        screen.fill(self.config.COLORS['background'])
        
        # Draw title
        self.render_title(screen)
        
        # Draw progress
        self.phase_progress_bar.set_value(self.current_phase_index)
        self.phase_progress_bar.render(screen)
        
        # Draw chess board
        self.chess_board.render(screen)
        
        # Phase-specific rendering
        render_methods = {
            'welcome': self.render_welcome,
            'principle_introduction': self.render_principle_intro,
            'principle_practice': self.render_practice,
            'mistake_recognition': self.render_mistakes,
            'opening_repertoire': self.render_repertoire,
            'pre_game_coaching': self.render_pre_game,
            'guided_first_game': self.render_game,
            'post_game_analysis': self.render_analysis,
            'graduation': self.render_graduation
        }
        
        render_method = render_methods.get(self.current_phase)
        if render_method:
            render_method(screen)
        
        # Draw UI elements
        self.render_ui(screen)
        
        # Draw animations
        for text in self.animated_texts:
            text.render(screen)
        
        for particle in self.particle_effects:
            particle.render(screen)
        
        # Draw feedback
        if self.show_feedback:
            self.render_feedback(screen)
        
        # Draw hints
        if self.show_hints and self.hint_text:
            self.render_hints(screen)
    
    def render_title(self, screen):
        """Render phase title"""
        titles = {
            'welcome': "Welcome to Opening Mastery!",
            'principle_introduction': f"Principle {self.current_principle_index + 1} of 6",
            'principle_practice': "Practice Time!",
            'mistake_recognition': "Spot the Mistake!",
            'opening_repertoire': "Learn Classic Openings",
            'pre_game_coaching': "Pre-Game Preparation",
            'guided_first_game': "Your First Game",
            'post_game_analysis': "Game Analysis",
            'graduation': "Module Complete!"
        }
        
        title = titles.get(self.current_phase, "Opening Principles")
        title_surface = self.title_font.render(title, True, self.config.COLORS['primary'])
        screen.blit(title_surface, (50, 70))
    
    # Additional render methods for each phase...
    def render_welcome(self, screen):
        """Render welcome phase"""
        pass
    
    def render_principle_intro(self, screen):
        """Render principle introduction"""
        if self.current_principle_index < len(self.opening_principles):
            principle_key = list(self.opening_principles.keys())[self.current_principle_index]
            principle = self.opening_principles[principle_key]
            
            # Draw principle icon
            if hasattr(self, 'current_principle_icon'):
                icon_surface = self.icon_font.render(
                    self.current_principle_icon,
                    True,
                    principle['color']
                )
                screen.blit(icon_surface, (600, 200))
    
    def render_practice(self, screen):
        """Render practice phase"""
        if self.current_exercise:
            # Draw question
            question_surface = self.subtitle_font.render(
                self.current_exercise['question'],
                True,
                self.config.COLORS['text']
            )
            screen.blit(question_surface, (550, 250))
    
    def render_mistakes(self, screen):
        """Render mistake recognition"""
        if self.current_exercise:
            desc_surface = self.text_font.render(
                self.current_exercise.get('description', ''),
                True,
                self.config.COLORS['text_light']
            )
            screen.blit(desc_surface, (550, 200))
    
    def render_repertoire(self, screen):
        """Render opening repertoire"""
        pass
    
    def render_pre_game(self, screen):
        """Render pre-game coaching"""
        pass
    
    def render_game(self, screen):
        """Render the game phase"""
        # Show turn indicator
        turn_text = "Your Turn" if self.is_player_turn else "Opponent's Turn"
        turn_color = (100, 255, 100) if self.is_player_turn else (255, 200, 100)
        turn_surface = self.subtitle_font.render(turn_text, True, turn_color)
        screen.blit(turn_surface, (550, 150))
        
        # Show move list
        move_list_y = 200
        moves_title = self.text_font.render("Moves:", True, self.config.COLORS['text'])
        screen.blit(moves_title, (550, move_list_y))
        
        for i, move in enumerate(self.game_moves[-8:]):
            move_num = i + len(self.game_moves) - min(8, len(self.game_moves)) + 1
            move_text = f"{move_num}. {move}"
            move_surface = self.small_font.render(move_text, True, self.config.COLORS['text_light'])
            screen.blit(move_surface, (550, move_list_y + 30 + i * 20))
    
    def render_analysis(self, screen):
        """Render game analysis"""
        if hasattr(self, 'game_analysis'):
            # Show strengths
            y_offset = 200
            if self.game_analysis.get('strengths'):
                strength_title = self.text_font.render("Strengths:", True, (100, 255, 100))
                screen.blit(strength_title, (550, y_offset))
                y_offset += 30
                
                for strength in self.game_analysis['strengths'][:3]:
                    text = f"✓ {strength}"
                    surface = self.small_font.render(text, True, self.config.COLORS['text'])
                    screen.blit(surface, (550, y_offset))
                    y_offset += 25
    
    def render_graduation(self, screen):
        """Render graduation ceremony"""
        # Show final score
        score_text = f"Final Score: {self.total_score}/100"
        score_surface = self.subtitle_font.render(score_text, True, (255, 215, 0))
        screen.blit(score_surface, (300, 200))
    
    def render_ui(self, screen):
        """Render UI elements"""
        self.back_button.render(screen)
        self.hint_button.render(screen)
        
        # Phase-specific buttons
        if self.current_phase in ['welcome', 'principle_introduction', 'graduation']:
            self.next_button.render(screen)
        
        if self.current_phase == 'principle_practice':
            for button in self.answer_buttons:
                if hasattr(button, 'visible') and button.visible:
                    button.render(screen)
        
        if self.current_phase == 'guided_first_game':
            self.resign_button.render(screen)
            self.analyze_button.render(screen)
    
    def render_feedback(self, screen):
        """Render feedback overlay"""
        if self.feedback_message:
            # Create overlay
            overlay = pygame.Surface((500, 100))
            overlay.set_alpha(220)
            overlay.fill((40, 40, 40))
            
            x = self.config.SCREEN_WIDTH // 2 - 250
            y = self.config.SCREEN_HEIGHT // 2 - 50
            screen.blit(overlay, (x, y))
            
            # Draw message
            color = self.feedback_color or self.config.COLORS['success']
            feedback_surface = self.subtitle_font.render(
                self.feedback_message,
                True,
                color
            )
            rect = feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2,
                                                    self.config.SCREEN_HEIGHT // 2))
            screen.blit(feedback_surface, rect)
    
    def render_hints(self, screen):
        """Render hint overlay"""
        hint_surface = self.text_font.render(self.hint_text, True, (255, 255, 150))
        screen.blit(hint_surface, (550, 500))
    
    # Utility methods
    def create_animated_text(self, text, pos, size=24, duration=3.0, delay=0, color=None):
        """Create animated text"""
        if color is None:
            color = self.config.COLORS['text']
        
        animated = AnimatedText(text, pos, size, color, duration, self.config)
        animated.delay = delay
        self.animated_texts.append(animated)
    
    def create_celebration_effects(self):
        """Create celebration particle effects"""
        # This would create confetti or star particles
        pass
    
    def update_buttons(self, dt, mouse_pos):
        """Update all buttons"""
        buttons = [
            self.back_button, self.hint_button, self.next_button,
            self.resign_button, self.analyze_button
        ] + self.answer_buttons
        
        for button in buttons:
            button.update(dt, mouse_pos)
    
    def calculate_final_score(self):
        """Calculate final module score"""
        # Weighted scoring
        practice_weight = 0.3
        game_weight = 0.4
        principle_weight = 0.3
        
        practice_score = (self.correct_answers / max(self.total_attempts, 1)) * 100
        game_score = self.game_analysis.get('accuracy', 50) if hasattr(self, 'game_analysis') else 50
        principle_score = sum(self.principle_mastery.values()) / len(self.principle_mastery) * 100
        
        self.total_score = int(
            practice_score * practice_weight +
            game_score * game_weight +
            principle_score * principle_weight
        )
    
    def calculate_achievements(self):
        """Calculate earned achievements"""
        achievements = []
        
        if self.total_score >= 90:
            achievements.append("Opening Master")
        if self.total_score >= 75:
            achievements.append("Principle Student")
        if self.correct_answers >= self.total_attempts * 0.8:
            achievements.append("Quick Learner")
        if len(self.game_moves) >= 30:
            achievements.append("Endurance Fighter")
        if hasattr(self, 'game_analysis'):
            if self.game_analysis.get('opening_score', 0) >= 80:
                achievements.append("Opening Specialist")
        
        achievements.append("Course Complete!")
        
        return achievements
    
    # Event handlers
    def handle_event(self, event):
        """Handle input events"""
        self.back_button.handle_event(event)
        self.hint_button.handle_event(event)
        
        if self.current_phase in ['welcome', 'principle_introduction', 'graduation']:
            self.next_button.handle_event(event)
        
        if self.current_phase == 'principle_practice':
            for button in self.answer_buttons:
                button.handle_event(event)
        
        if self.current_phase == 'guided_first_game':
            self.resign_button.handle_event(event)
            self.analyze_button.handle_event(event)
            
            # Handle board clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.is_player_turn:
                    self.handle_board_click(event.pos)
    
    def handle_board_click(self, pos):
        """Handle chess board clicks during game"""
        square = self.chess_board.get_square_from_pos(pos)
        
        if square is not None:
            if self.selected_square is None:
                # Select piece
                piece = self.game_board.piece_at(square)
                if piece and piece.color == chess.WHITE:
                    self.selected_square = square
                    self.legal_moves = [
                        move for move in self.game_board.legal_moves
                        if move.from_square == square
                    ]
                    self.highlight_legal_moves()
            else:
                # Try to move
                move = self.get_move_to_square(square)
                if move:
                    self.make_move(move)
                    self.is_player_turn = False
                
                # Clear selection
                self.selected_square = None
                self.legal_moves = []
                self.chess_board.clear_highlights()
    
    def get_move_to_square(self, square):
        """Get legal move to target square"""
        for move in self.legal_moves:
            if move.to_square == square:
                return move
        return None
    
    def highlight_legal_moves(self):
        """Highlight legal move squares"""
        self.chess_board.clear_highlights()
        for move in self.legal_moves:
            self.chess_board.highlight_square(
                move.to_square,
                self.config.COLORS['highlight']
            )
    
    def make_move(self, move):
        """Execute a move"""
        try:
            # Record move
            san = self.game_board.san(move)
            self.game_moves.append(san)
            
            # Make move
            self.game_board.push(move)
            self.chess_board.set_board(self.game_board)
            
            # Evaluate if player move
            if self.is_player_turn:
                evaluation = self.opening_analyzer.evaluate_move(
                    self.game_board,
                    move,
                    len(self.game_moves)
                )
                self.move_evaluations.append(evaluation)
                self.provide_move_coaching(evaluation)
            
            # Check game end
            if self.game_board.is_game_over():
                self.handle_game_end()
            
            # Sound effect
            try:
                self.engine.audio_manager.play_sound('move.wav')
            except:
                pass
                
        except Exception as e:
            logger.error(f"Move error: {e}")
    
    def provide_move_coaching(self, evaluation):
        """Provide coaching feedback on moves"""
        score = evaluation.get('score', 0.5)
        
        if score >= 0.8:
            messages = ["Excellent!", "Perfect opening move!", "Great principle application!"]
            color = (100, 255, 100)
        elif score >= 0.6:
            messages = ["Good move!", "Solid choice.", "Nice development!"]
            color = (200, 255, 200)
        elif score >= 0.4:
            messages = ["Acceptable.", "Consider the principles.", "Room for improvement."]
            color = (255, 255, 200)
        else:
            messages = ["Hmm, reconsider.", "Check opening principles.", "Better moves available."]
            color = (255, 200, 200)
        
        self.show_feedback_message(
            random.choice(messages),
            duration=2.0,
            color=color
        )
    
    def handle_game_end(self):
        """Handle game ending"""
        result = self.game_board.result()
        
        if "1-0" in result:
            message = "Victory! Well played!"
            color = (100, 255, 100)
        elif "0-1" in result:
            message = "Defeat, but you learned!"
            color = (255, 100, 100)
        else:
            message = "Draw! Good fight!"
            color = (255, 255, 100)
        
        self.show_feedback_message(message, duration=4.0, color=color)
        
        # Move to analysis after delay
        pygame.time.set_timer(pygame.USEREVENT + 1, 4000)
    
    def show_feedback_message(self, message, duration=2.0, color=None):
        """Display feedback message"""
        self.feedback_message = message
        self.feedback_timer = duration
        self.feedback_color = color
        self.show_feedback = True
    
    # Navigation
    def next_phase(self):
        """Move to next phase"""
        # Handle phase transitions
        if self.current_phase == 'principle_introduction':
            self.current_principle_index += 1
            if self.current_principle_index >= len(self.opening_principles):
                self.current_phase_index += 1
                self.current_principle_index = 0
                self.start_phase('principle_practice')
            else:
                self.start_phase('principle_introduction')
        else:
            self.current_phase_index += 1
            if self.current_phase_index < len(self.module_phases):
                self.start_phase(self.module_phases[self.current_phase_index])
    
    def select_answer(self, index):
        """Handle answer selection in exercises"""
        if self.current_exercise and index < len(self.current_exercise['options']):
            answer = self.current_exercise['options'][index]
            correct = self.exercises.evaluate_answer(
                answer,
                self.current_exercise['correct_answers']
            )
            
            self.total_attempts += 1
            if correct:
                self.correct_answers += 1
                self.show_feedback_message("Correct! Well done!", color=(100, 255, 100))
                
                # Update principle mastery
                principle = self.current_exercise.get('principle')
                if principle:
                    self.principle_mastery[principle] = min(
                        self.principle_mastery[principle] + 0.2,
                        1.0
                    )
            else:
                self.show_feedback_message(
                    f"Not quite. {self.current_exercise.get('explanation', '')}",
                    duration=3.0,
                    color=(255, 200, 100)
                )
            
            # Next exercise after delay
            pygame.time.set_timer(pygame.USEREVENT + 2, 2000)
    
    def toggle_hints(self):
        """Toggle hint display"""
        self.show_hints = not self.show_hints
        
        if self.show_hints and self.current_exercise:
            self.hint_text = self.current_exercise.get('hint', 'Think about the opening principles!')
    
    def demonstrate_opening(self, moves):
        """Demonstrate an opening sequence"""
        self.game_board.reset()
        for move_san in moves:
            try:
                move = self.game_board.parse_san(move_san)
                self.game_board.push(move)
            except:
                break
        
        self.chess_board.set_board(self.game_board)
    
    def resign_game(self):
        """Handle resignation"""
        self.show_feedback_message("Game resigned. Let's analyze!", duration=3.0)
        self.handle_game_end()
    
    def analyze_position(self):
        """Quick position analysis"""
        analysis = self.opening_analyzer.analyze_position(
            self.game_board,
            len(self.game_moves)
        )
        
        message = f"Position: {analysis.get('evaluation', 'Equal')}"
        self.show_feedback_message(message, duration=3.0)
    
    def on_back_clicked(self):
        """Return to main menu"""
        self.engine.change_state(GameState.MAIN_MENU)