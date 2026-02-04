# ============================================================================
# FILE: src/training/exercises/castling_basics.py
# PURPOSE: Phase 1 - Basic castling mechanics and execution
# ============================================================================

import pygame
import chess
import random
import logging
from typing import List
from .base_exercise import BaseExercise

logger = logging.getLogger(__name__)

class CastlingBasics(BaseExercise):
    """Teaches fundamental castling mechanics - moving king 2 squares toward rook"""
    
    def __init__(self, config, chess_board, audio_manager):
        super().__init__(config, chess_board, audio_manager)
        self.castling_side = None
        self.king_square = None
        self.rook_square = None
        self.king_target = None
        self.rook_target = None
    
    def get_title(self) -> str:
        return "Castling Basics - Learn the Move"
    
    def get_instruction(self) -> str:
        if self.castling_side == 'kingside':
            return "Click where the WHITE KING moves to castle KINGSIDE (short castling)"
        else:
            return "Click where the WHITE KING moves to castle QUEENSIDE (long castling)"
    
    def get_learning_tip(self) -> str:
        return "Remember: King moves exactly 2 squares toward the rook, rook jumps over! 👑"
    
    def generate_position(self) -> bool:
        """Generate perfect castling position"""
        try:
            # Clear board and set up castling position
            self.chess_board.board.clear()
            
            # Always use white for consistency in learning
            color = chess.WHITE
            self.king_square = chess.E1
            kingside_rook = chess.H1
            queenside_rook = chess.A1
            
            # Place pieces
            self.chess_board.board.set_piece_at(self.king_square, chess.Piece(chess.KING, color))
            self.chess_board.board.set_piece_at(kingside_rook, chess.Piece(chess.ROOK, color))
            self.chess_board.board.set_piece_at(queenside_rook, chess.Piece(chess.ROOK, color))
            
            # Choose castling side for this exercise
            self.castling_side = random.choice(['kingside', 'queenside'])
            
            if self.castling_side == 'kingside':
                self.rook_square = kingside_rook
                self.king_target = chess.G1
                self.rook_target = chess.F1
            else:
                self.rook_square = queenside_rook
                self.king_target = chess.C1
                self.rook_target = chess.D1
            
            # Set target for this exercise (where king should move)
            self.target_squares = [self.king_target]
            
            # Invalid squares include other moves
            all_squares = list(range(64))
            occupied = [self.king_square, kingside_rook, queenside_rook]
            
            # Add some logical "wrong" choices
            wrong_choices = []
            if self.castling_side == 'kingside':
                wrong_choices = [chess.F1, chess.H1, chess.C1]  # Rook squares and wrong side
            else:
                wrong_choices = [chess.D1, chess.A1, chess.G1]  # Rook squares and wrong side
                
            available = [sq for sq in all_squares if sq not in occupied + self.target_squares]
            self.invalid_squares = wrong_choices + random.sample(available, min(6, len(available)))
            
            # Highlight the king to show it's the piece that needs to move
            self.chess_board.highlight_square(self.king_square)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate castling basics position: {e}")
            return False
    
    def check_move(self, square: int) -> bool:
        """Check if clicked square is correct"""
        return square == self.king_target
    
    def get_hints(self) -> List[str]:
        """Progressive hints for castling basics"""
        side_name = "kingside (short)" if self.castling_side == 'kingside' else "queenside (long)"
        return [
            f"You're learning {side_name} castling",
            "The KING moves exactly 2 squares toward the rook",
            f"King goes from e1 to {chess.square_name(self.king_target)}",
            f"Click on square {chess.square_name(self.king_target).upper()}!"
        ]
    
    def _get_error_message(self) -> str:
        """Specific error messages for common mistakes"""
        return f"Wrong square! King moves 2 squares toward the {self.castling_side} rook!"
    
    def _render_hints(self, screen):
        """Render visual hints for castling basics"""
        if not self.show_hints:
            return
            
        try:
            # Highlight target square
            target_rect = self.chess_board.get_square_rect(self.king_target)
            if target_rect:
                # Pulsing yellow highlight
                alpha = int(100 + 50 * math.sin(pygame.time.get_ticks() * 0.005))
                hint_surface = pygame.Surface((target_rect.width, target_rect.height))
                hint_surface.set_alpha(alpha)
                hint_surface.fill((255, 255, 0))  # Yellow
                screen.blit(hint_surface, target_rect)
            
            # Draw arrow from king to target
            king_rect = self.chess_board.get_square_rect(self.king_square)
            if king_rect and target_rect:
                start_pos = king_rect.center
                end_pos = target_rect.center
                pygame.draw.line(screen, (0, 255, 255), start_pos, end_pos, 4)
                
                # Arrow head
                import math
                angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
                arrow_length = 15
                arrow_angle = 0.5
                
                arrow_p1 = (
                    end_pos[0] - arrow_length * math.cos(angle - arrow_angle),
                    end_pos[1] - arrow_length * math.sin(angle - arrow_angle)
                )
                arrow_p2 = (
                    end_pos[0] - arrow_length * math.cos(angle + arrow_angle),
                    end_pos[1] - arrow_length * math.sin(angle + arrow_angle)
                )
                
                pygame.draw.polygon(screen, (0, 255, 255), [end_pos, arrow_p1, arrow_p2])
                
        except Exception as e:
            logger.warning(f"Failed to render castling hints: {e}")
