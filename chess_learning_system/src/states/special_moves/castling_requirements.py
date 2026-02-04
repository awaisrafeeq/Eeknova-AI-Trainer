# ============================================================================
# FILE: src/training/exercises/castling_requirements.py
# PURPOSE: Phase 2 - Understanding when castling is legal
# ============================================================================

import pygame
import chess
import random
import logging
from typing import List
from .base_exercise import BaseExercise

logger = logging.getLogger(__name__)

class CastlingRequirements(BaseExercise):
    """Teaches the KING checklist - all conditions for legal castling"""
    
    def __init__(self, config, chess_board, audio_manager):
        super().__init__(config, chess_board, audio_manager)
        self.scenario_type = None
        self.blocking_reasons = []
        self.legal_sides = {'kingside': False, 'queenside': False}
    
    def get_title(self) -> str:
        return "Castling Requirements - KING Checklist"
    
    def get_instruction(self) -> str:
        return "Which castling moves are LEGAL in this position? Click the king's destination!"
    
    def get_learning_tip(self) -> str:
        return "KING checklist: King safe, In position, No pieces between, Good squares only! 🏰"
    
    def generate_position(self) -> bool:
        """Generate position testing castling requirements"""
        try:
            self.chess_board.board.clear()
            self.blocking_reasons = []
            
            # Base position - always white
            king_square = chess.E1
            kingside_rook = chess.H1
            queenside_rook = chess.A1
            
            self.chess_board.board.set_piece_at(king_square, chess.Piece(chess.KING, chess.WHITE))
            self.chess_board.board.set_piece_at(kingside_rook, chess.Piece(chess.ROOK, chess.WHITE))
            self.chess_board.board.set_piece_at(queenside_rook, chess.Piece(chess.ROOK, chess.WHITE))
            
            # Choose scenario to test specific requirements
            scenarios = [
                'both_legal',
                'pieces_blocking_kingside',
                'pieces_blocking_queenside', 
                'pieces_blocking_both',
                'king_in_check',
                'king_through_check_kingside',
                'king_through_check_queenside'
            ]
            
            self.scenario_type = random.choice(scenarios)
            
            # Reset legal sides
            self.legal_sides = {'kingside': True, 'queenside': True}
            
            if self.scenario_type == 'both_legal':
                # Perfect position - both castling moves legal
                pass  # Nothing to add
                
            elif self.scenario_type == 'pieces_blocking_kingside':
                # Block kingside castling
                self.chess_board.board.set_piece_at(chess.F1, chess.Piece(chess.BISHOP, chess.WHITE))
                self.legal_sides['kingside'] = False
                self.blocking_reasons.append("Bishop blocks kingside castling")
                
            elif self.scenario_type == 'pieces_blocking_queenside':
                # Block queenside castling
                self.chess_board.board.set_piece_at(chess.D1, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.legal_sides['queenside'] = False
                self.blocking_reasons.append("Knight blocks queenside castling")
                
            elif self.scenario_type == 'pieces_blocking_both':
                # Block both sides
                self.chess_board.board.set_piece_at(chess.F1, chess.Piece(chess.BISHOP, chess.WHITE))
                self.chess_board.board.set_piece_at(chess.B1, chess.Piece(chess.KNIGHT, chess.WHITE))
                self.legal_sides['kingside'] = False
                self.legal_sides['queenside'] = False
                self.blocking_reasons.extend(["Bishop blocks kingside", "Knight blocks queenside"])
                
            elif self.scenario_type == 'king_in_check':
                # King in check - no castling allowed
                self.chess_board.board.set_piece_at(chess.E8, chess.Piece(chess.ROOK, chess.BLACK))
                self.legal_sides['kingside'] = False
                self.legal_sides['queenside'] = False
                self.blocking_reasons.append("King in check - cannot castle!")
                
            elif self.scenario_type == 'king_through_check_kingside':
                # King would pass through check on kingside
                self.chess_board.board.set_piece_at(chess.F8, chess.Piece(chess.ROOK, chess.BLACK))
                self.legal_sides['kingside'] = False
                self.blocking_reasons.append("King would pass through check on f1")
                
            elif self.scenario_type == 'king_through_check_queenside':
                # King would pass through check on queenside
                self.chess_board.board.set_piece_at(chess.D8, chess.Piece(chess.ROOK, chess.BLACK))
                self.legal_sides['queenside'] = False
                self.blocking_reasons.append("King would pass through check on d1")
            
            # Set targets based on what's legal
            self.target_squares = []
            if self.legal_sides['kingside']:
                self.target_squares.append(chess.G1)
            if self.legal_sides['queenside']:
                self.target_squares.append(chess.C1)
            
            # Invalid squares are the blocked castling destinations
            self.invalid_squares = []
            if not self.legal_sides['kingside']:
                self.invalid_squares.append(chess.G1)
            if not self.legal_sides['queenside']:
                self.invalid_squares.append(chess.C1)
            
            # Add random invalid squares
            available_squares = [sq for sq in range(64) 
                               if not self.chess_board.board.piece_at(sq) 
                               and sq not in self.target_squares + self.invalid_squares]
            if available_squares:
                additional_invalid = random.sample(available_squares, min(4, len(available_squares)))
                self.invalid_squares.extend(additional_invalid)
            
            # Highlight king
            self.chess_board.highlight_square(king_square)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate castling requirements position: {e}")
            return False
    
    def check_move(self, square: int) -> bool:
        """Check if clicked square is a legal castling destination"""
        return square in self.target_squares
    
    def get_hints(self) -> List[str]:
        """Progressive hints for requirements checking"""
        hints = ["Check the KING requirements systematically:"]
        
        if self.blocking_reasons:
            hints.append(f"Problem: {self.blocking_reasons[0]}")
        
        hints.extend([
            "K - King not in check",
            "I - In original position (not moved)", 
            "N - No pieces between king and rook",
            "G - Good squares (king won't move through/into check)"
        ])
        
        if self.target_squares:
            square_names = [chess.square_name(sq).upper() for sq in self.target_squares]
            hints.append(f"Legal destinations: {', '.join(square_names)}")
        else:
            hints.append("No castling is legal in this position!")
            
        return hints
    
    def _get_error_message(self) -> str:
        """Specific error message based on what was clicked and scenario"""
        if self.blocking_reasons:
            return f"Can't castle! {self.blocking_reasons[0]}"
        else:
            return "Check the KING requirements! Something is blocking that castling move."
    
    def _render_hints(self, screen):
        """Render visual hints showing legal/illegal castling"""
        if not self.show_hints:
            return
            
        try:
            # Highlight legal castling squares in green
            for square in self.target_squares:
                square_rect = self.chess_board.get_square_rect(square)
                if square_rect:
                    alpha = int(120 + 50 * math.sin(pygame.time.get_ticks() * 0.003))
                    hint_surface = pygame.Surface((square_rect.width, square_rect.height))
                    hint_surface.set_alpha(alpha)
                    hint_surface.fill((0, 255, 0))  # Green for legal
                    screen.blit(hint_surface, square_rect)
            
            # Highlight illegal castling squares in red
            for square in self.invalid_squares:
                if square in [chess.G1, chess.C1]:  # Only show castling squares, not random ones
                    square_rect = self.chess_board.get_square_rect(square)
                    if square_rect:
                        alpha = int(80 + 30 * math.sin(pygame.time.get_ticks() * 0.004))
                        hint_surface = pygame.Surface((square_rect.width, square_rect.height))
                        hint_surface.set_alpha(alpha)
                        hint_surface.fill((255, 0, 0))  # Red for illegal
                        screen.blit(hint_surface, square_rect)
                        
        except Exception as e:
            logger.warning(f"Failed to render castling requirements hints: {e}")
