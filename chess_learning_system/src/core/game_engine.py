# src/core/game_engine.py - Main game engine for the chess education system

import pygame
import time
from enum import Enum
from typing import Dict, Optional

from src.core.state_machine import StateMachine, GameState
from src.core.resource_manager import ResourceManager
from src.core.audio_manager import AudioManager
from src.core.event_manager import EventManager
from src.utils.singleton import Singleton

class ChessEducationEngine(metaclass=Singleton):
    """Main game engine that manages the educational chess system"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
        self.clock = pygame.time.Clock()
        
        # Initialize pygame
        pygame.init()
        pygame.mixer.init(
            frequency=config.AUDIO['frequency'],
            size=config.AUDIO['size'],
            channels=config.AUDIO['channels'],
            buffer=config.AUDIO['buffer']
        )
        
        # Create display
        self.screen = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(config.WINDOW_TITLE)
        
        # Initialize core systems
        self.resource_manager = ResourceManager(config)
        self.audio_manager = AudioManager(config)
        self.event_manager = EventManager()
        self.state_machine = StateMachine()
        
        # Initialize timing
        self.dt = 0
        self.fps = config.FPS
        
        # Session management
        self.session_start_time = time.time()
        self.last_break_reminder = time.time()
        
        # Background
        self.background = pygame.Surface(self.screen.get_size())
        self.background.fill(config.COLORS['background'])
        
        # Initialize states
        self._initialize_states()
        
    def _initialize_states(self):
        """Initialize all game states"""
        from src.states.welcome_state import WelcomeState
        from src.states.main_menu_state import MainMenuState
        from src.states.identify_pieces_state import IdentifyPiecesState
        from src.states.board_setup_state import BoardSetupState
        from src.states.pawn_movement_state import PawnMovementState
        from src.states.rook_movement_state import RookMovementState
        from src.states.knight_movement_state import KnightMovementState
        from src.states.bishop_movement_state import BishopMovementState
        from src.states.queen_combo_movement_state import QueenMovementState
        from src.states.king_check_state import KingCheckState
        from src.states.special_moves_state import SpecialMovesState
        from src.states.Check_Checkmate_Stalemate_State import CheckCheckmateStalemateState
        from src.states.game import OpeningPrinciplesFirstGameState
        from src.states.opening_principles_state import OpeningPrinciplesState
        from src.states.play_vs_ai_state import AIChessGameState
        # Register states
        self.state_machine.register_state(GameState.WELCOME, WelcomeState(self))
        self.state_machine.register_state(GameState.MAIN_MENU, MainMenuState(self))
        self.state_machine.register_state(GameState.IDENTIFY_PIECES, IdentifyPiecesState(self))
        self.state_machine.register_state(GameState.BOARD_SETUP, BoardSetupState(self))
        self.state_machine.register_state(GameState.PAWN_MOVEMENT, PawnMovementState(self))
        self.state_machine.register_state(GameState.ROOK_MOVEMENT, RookMovementState(self))
        self.state_machine.register_state(GameState.KNIGHT_MOVEMENT, KnightMovementState(self))
        self.state_machine.register_state(GameState.BISHOP_MOVEMENT, BishopMovementState(self))
        self.state_machine.register_state(GameState.QUEEN_MOVEMENT, QueenMovementState(self))
        self.state_machine.register_state(GameState.KING_MOVEMENT, KingCheckState(self))
        self.state_machine.register_state(GameState.SPECIAL_MOVES, SpecialMovesState(self))
        self.state_machine.register_state(GameState.CHECK_CHECKMATE_STALEMATE, CheckCheckmateStalemateState(self))
        #self.state_machine.register_state(GameState.OPENING_PRINCIPLES_FIRST_GAME, OpeningPrinciplesFirstGameState(self))
        self.state_machine.register_state(GameState.OPENING_PRINCIPLES_FIRST_GAME, OpeningPrinciplesState(self))
        self.state_machine.register_state(GameState.PlayWithAI, AIChessGameState(self))
        # Start with welcome state
        self.state_machine.change_state(GameState.WELCOME)
    
    def run(self):
        """Main game loop"""
        self.running = True
        
        while self.running:
            # Calculate delta time
            self.dt = self.clock.tick(self.fps) / 1000.0
            #print("hangle event is calling from game_engine")
            # Handle events
            self._handle_events()
            #print("hangle event is completed from game_engine")
            # Update current state
            #print("update is calling from game_engine")
            self.state_machine.update(self.dt)
            #print("update is completed from game_engine")
            # Check for break reminders
            #print("check break reminder is calling from game_engine")
            self._check_break_reminder()
            #print("check break reminder is completed from game_engine")
            # Render
            self._render()
            
            # Update display
            pygame.display.flip()
            #print("run is completed from game_engine")
    def _handle_events(self):
        """Handle pygame events"""
        events = pygame.event.get()
        
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Go back or show pause menu
                    self.state_machine.handle_back()
            
            # Pass events to current state
            self.state_machine.handle_event(event)
            
            # Pass to event manager for global handlers
            self.event_manager.handle_event(event)
    
    def _render(self):
        """Render the current frame"""
        # Clear screen with background
        self.screen.blit(self.background, (0, 0))
        
        # Render current state
        self.state_machine.render(self.screen)
        
        # Render any overlays (e.g., break reminder)
        self._render_overlays()
    
    def _render_overlays(self):
        """Render any overlay elements"""
        # Could add break reminders, notifications, etc. here
        pass
    
    def _check_break_reminder(self):
        """Check if it's time for a break reminder"""
        current_time = time.time()
        session_duration = current_time - self.session_start_time
        
        if (session_duration > self.config.EDUCATION['break_reminder_time'] and
            current_time - self.last_break_reminder > 300):  # Don't remind more than every 5 minutes
            
            self.last_break_reminder = current_time
            # TODO: Show break reminder overlay
            print("Time for a break! You've been playing for 15 minutes.")
    
    def change_state(self, new_state: GameState):
        """Change to a new game state"""
        self.state_machine.change_state(new_state)
    
    def get_screen_center(self):
        """Get the center coordinates of the screen"""
        return (self.config.SCREEN_WIDTH // 2, self.config.SCREEN_HEIGHT // 2)
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        self.audio_manager.cleanup()
        self.resource_manager.cleanup()
        self.state_machine.cleanup()
        
        # Save any session data
        # TODO: Implement session saving
        
        print("Cleanup complete. Goodbye!")