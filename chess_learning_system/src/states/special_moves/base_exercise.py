# ============================================================================
# FILE: src/training/exercises/base_exercise.py
# PURPOSE: Base class for all special moves exercises
# ============================================================================

import pygame
import chess
import random
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class ExerciseResult:
    """Container for exercise completion results"""
    def __init__(self):
        self.success = False
        self.score = 0
        self.attempts = 0
        self.hints_used = 0
        self.time_taken = 0.0
        self.feedback_message = ""
        self.next_exercise = None

class BaseExercise(ABC):
    """Base class for all special moves exercises"""
    
    def __init__(self, config, chess_board, audio_manager):
        self.config = config
        self.chess_board = chess_board
        self.audio_manager = audio_manager
        
        # Exercise state
        self.is_active = False
        self.attempts = 0
        self.hints_used = 0
        self.start_time = 0
        self.current_board_state = None
        
        # Target answers
        self.target_squares = []
        self.valid_moves = []
        self.invalid_squares = []
        
        # Visual aids
        self.show_hints = False
        self.show_paths = False
        self.highlight_legal = False
        
        # Feedback system
        self.feedback_message = ""
        self.show_feedback = False
        self.feedback_timer = 0
        
    @abstractmethod
    def get_title(self) -> str:
        """Return exercise title"""
        pass
    
    @abstractmethod
    def get_instruction(self) -> str:
        """Return main instruction text"""
        pass
    
    @abstractmethod
    def get_learning_tip(self) -> str:
        """Return learning tip for this exercise"""
        pass
    
    @abstractmethod
    def generate_position(self) -> bool:
        """Generate a new exercise position. Return True if successful."""
        pass
    
    @abstractmethod
    def check_move(self, square: int) -> bool:
        """Check if the clicked square is correct. Return True if correct."""
        pass
    
    @abstractmethod
    def get_hints(self) -> List[str]:
        """Return list of progressive hints"""
        pass
    
    def start_exercise(self):
        """Initialize and start the exercise"""
        try:
            self.is_active = True
            self.attempts = 0
            self.hints_used = 0
            self.start_time = pygame.time.get_ticks()
            self.show_feedback = False
            self.feedback_message = ""
            
            # Generate position
            success = self.generate_position()
            if not success:
                raise Exception("Failed to generate exercise position")
            
            # Store initial state for reset
            self.current_board_state = self.chess_board.board.copy()
            
            logger.info(f"Started {self.get_title()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start exercise: {e}")
            return False
    
    def handle_click(self, square: int) -> Optional[ExerciseResult]:
        """Handle square click, return result if exercise is complete"""
        if not self.is_active or self.show_feedback:
            return None
            
        self.attempts += 1
        
        if self.check_move(square):
            return self._handle_success()
        else:
            self._handle_incorrect()
            return None
    
    def _handle_success(self) -> ExerciseResult:
        """Handle successful move"""
        self.is_active = False
        self.show_feedback = True
        
        # Calculate score
        time_taken = (pygame.time.get_ticks() - self.start_time) / 1000.0
        base_score = 100
        time_penalty = min(30, max(0, time_taken - 10) * 2)  # Penalty after 10s
        attempt_penalty = (self.attempts - 1) * 10
        hint_penalty = self.hints_used * 15
        
        final_score = max(10, base_score - time_penalty - attempt_penalty - hint_penalty)
        
        # Create result
        result = ExerciseResult()
        result.success = True
        result.score = final_score
        result.attempts = self.attempts
        result.hints_used = self.hints_used
        result.time_taken = time_taken
        result.feedback_message = self._get_success_message()
        
        # Play success sound
        try:
            self.audio_manager.play_sound('success.wav')
        except Exception as e:
            logger.warning(f"Failed to play success sound: {e}")
        
        return result
    
    def _handle_incorrect(self):
        """Handle incorrect move"""
        self.feedback_message = self._get_error_message()
        self.show_feedback = True
        self.feedback_timer = pygame.time.get_ticks()
        
        # Play error sound
        try:
            self.audio_manager.play_sound('error.wav')
        except Exception as e:
            logger.warning(f"Failed to play error sound: {e}")
    
    def _get_success_message(self) -> str:
        """Get success feedback message"""
        if self.attempts == 1 and self.hints_used == 0:
            return "Perfect! First try with no hints! 🌟"
        elif self.attempts <= 2:
            return "Excellent! Great understanding! ✨"
        elif self.attempts <= 3:
            return "Good job! You're learning! 👍"
        else:
            return "Correct! Keep practicing! 💪"
    
    def _get_error_message(self) -> str:
        """Get error feedback message - should be overridden by subclasses"""
        return "Not quite right. Try again!"
    
    def toggle_hints(self):
        """Toggle hint display"""
        self.show_hints = not self.show_hints
        if self.show_hints:
            self.hints_used += 1
    
    def reset_exercise(self):
        """Reset exercise to initial state"""
        if self.current_board_state:
            self.chess_board.board = self.current_board_state.copy()
        self.attempts = 0
        self.show_feedback = False
        self.feedback_message = ""
        self.chess_board.clear_highlights()
    
    def update(self, dt):
        """Update exercise state"""
        if self.show_feedback:
            self.feedback_timer += dt * 1000  # Convert to milliseconds
            if self.feedback_timer > 2000:  # Hide after 2 seconds
                self.show_feedback = False
                self.feedback_timer = 0
    
    def render_overlay(self, screen):
        """Render exercise-specific overlays"""
        if self.show_hints:
            self._render_hints(screen)
        if self.show_feedback and self.feedback_message:
            self._render_feedback(screen)
    
    def _render_hints(self, screen):
        """Render hint overlay"""
        # This should be overridden by subclasses for specific hint rendering
        pass
    
    def _render_feedback(self, screen):
        """Render feedback message"""
        try:
            font = pygame.font.Font(None, 32)
            color = (0, 255, 0) if "Perfect" in self.feedback_message or "Excellent" in self.feedback_message else (255, 100, 100)
            
            feedback_surface = font.render(self.feedback_message, True, color)
            feedback_rect = feedback_surface.get_rect(center=(self.config.SCREEN_WIDTH // 2, 550))
            screen.blit(feedback_surface, feedback_rect)
            
        except Exception as e:
            logger.warning(f"Failed to render feedback: {e}")

