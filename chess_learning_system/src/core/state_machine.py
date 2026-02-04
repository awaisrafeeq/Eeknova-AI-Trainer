# src/core/state_machine.py - State machine for managing game states

from enum import Enum, auto
from typing import Dict, Optional
import pygame

class GameState(Enum):
    """Enumeration of all possible game states"""
    WELCOME = auto()
    PROFILE_SELECT = auto()
    MAIN_MENU = auto()
    IDENTIFY_PIECES = auto()
    BOARD_SETUP = auto()
    PAWN_MOVEMENT = auto()
    ROOK_MOVEMENT = auto()
    KNIGHT_MOVEMENT = auto()
    BISHOP_MOVEMENT = auto()
    QUEEN_MOVEMENT = auto()
    KING_MOVEMENT = auto()
    SPECIAL_MOVES = auto()
    CHECK_CHECKMATE_STALEMATE = auto()
    OPENING_PRINCIPLES_FIRST_GAME = auto()
    OPENING_PRINCIPLES = auto()
    PlayWithAI = auto()
    MINI_MATCH = auto()
    CAPTURE_GAME = auto()
    ACHIEVEMENTS = auto()
    SETTINGS = auto()
    PAUSE = auto()

class BaseState:
    """Base class for all game states"""
    
    def __init__(self, engine):
        self.engine = engine
        self.config = engine.config
        self.transition_alpha = 0
        self.transitioning_in = True
        self.transitioning_out = False
        
    def enter(self):
        """Called when entering this state"""
        self.transition_alpha = 0
        self.transitioning_in = True
        self.transitioning_out = False
        
    def exit(self):
        """Called when leaving this state"""
        self.transitioning_out = True
        
    def update(self, dt):
        """Update the state"""
        # Handle transitions
        #print(f"Updating state base update is called : {self.__class__.__name__}")
        if self.transitioning_in:
            #print("if condition passed in update")
            self.transition_alpha = min(255, self.transition_alpha + 500 * dt)
            #print(f"Transition alpha: {self.transition_alpha}")
            if self.transition_alpha >= 255:
                self.transitioning_in = False
        
        elif self.transitioning_out:
            #print("elif condition passed in update")
            self.transition_alpha = max(0, self.transition_alpha - 500 * dt)
            #print("elif is completed")
        #print("update function executed basestate")
    def render(self, screen):
        """Render the state"""
        # Subclasses should override this
        pass
        
    def handle_event(self, event):
        """Handle pygame events"""
        # Subclasses should override this
        pass
        
    def handle_back(self):
        """Handle back button/escape key"""
        # Default behavior - go to main menu
        self.engine.change_state(GameState.MAIN_MENU)

class StateMachine:
    """Manages game state transitions"""
    
    def __init__(self):
        self.states: Dict[GameState, BaseState] = {}
        self.current_state: Optional[BaseState] = None
        self.current_state_id: Optional[GameState] = None
        self.previous_state_id: Optional[GameState] = None
        self.state_stack = []
        
    def register_state(self, state_id: GameState, state: BaseState):
        """Register a new state"""
        self.states[state_id] = state
        
    def change_state(self, new_state_id: GameState):
        """Change to a new state"""
        if new_state_id not in self.states:
            print(f"Error: State {new_state_id} not registered!")
            return
            
        # Exit current state
        if self.current_state:
            self.current_state.exit()
            self.previous_state_id = self.current_state_id
            
        # Enter new state
        self.current_state_id = new_state_id
        self.current_state = self.states[new_state_id]
        self.current_state.enter()
        
        # Add to state stack for back navigation
        if self.previous_state_id:
            self.state_stack.append(self.previous_state_id)
            # Keep stack size reasonable
            if len(self.state_stack) > 10:
                self.state_stack.pop(0)
    
    def push_state(self, new_state_id: GameState):
        """Push a new state onto the stack (for overlays like pause)"""
        if self.current_state_id:
            self.state_stack.append(self.current_state_id)
        self.change_state(new_state_id)
    
    def pop_state(self):
        """Pop back to the previous state"""
        if self.state_stack:
            previous_state = self.state_stack.pop()
            self.change_state(previous_state)
        else:
            # Default to main menu if stack is empty
            self.change_state(GameState.MAIN_MENU)
    
    def update(self, dt):
        """Update the current state"""
        #print(f"Updating state state_machine : {self.current_state_id}")
        if self.current_state:
            #print("if condition is true from state_machine")
            self.current_state.update(dt)
            #print("update is completed from state_machine")
        #print("update funtion is executed")
    
    def render(self, screen):
        """Render the current state"""
        if self.current_state:
            self.current_state.render(screen)
    
    def handle_event(self, event):
        """Handle events for the current state"""
        if self.current_state:
            self.current_state.handle_event(event)
    
    def handle_back(self):
        """Handle back navigation"""
        if self.current_state:
            self.current_state.handle_back()
    
    def cleanup(self):
        """Clean up all states"""
        if self.current_state:
            self.current_state.exit()
        
        # Clean up all registered states
        for state in self.states.values():
            if hasattr(state, 'cleanup'):
                state.cleanup()