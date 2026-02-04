# ============================================================================
# FILE: src/training/exercises/en_passant_recognition.py
# PURPOSE: Phase 5 - Recognizing en passant opportunities
# ============================================================================

import pygame
import chess
import random
import logging
from typing import List
from .base_exercise import BaseExercise

logger = logging.getLogger(__name__)

class EnPassantRecognition(BaseExercise):
    """Teaches recognition of en passant opportunities"""
    
    def __init__(self, config, chess_board, audio_manager):
        super().__init__(config, chess_board, audio_manager)
        self.capturing_pawn = None
        self.enemy_pawn = None
        self.en_passant_square = None
        self.pawn_color = chess.WHITE
    
    def get_title(self) -> str:
        return "En Passant Recognition - Spot the Opportunity"
    
    def get_instruction(self) -> str:
        return "Enemy pawn just moved 2 squares! Click WHERE to capture 'en passant'!"
    
    def get_learning_tip(self) -> str:
        return "En Passant = 'in passing' - capture diagonally to EMPTY square! ⚡"
    
    def generate_position(self) -> bool:
        """Generate en passant opportunity position"""
        try:
            self.chess_board.board.clear()
            
            # Use white pawns for consistency (can expand later)
            self.pawn_color = chess.WHITE
            
            # Place capturing pawn on 5th rank (for white)
            capturing_file = random.randint(1, 6)  # b-g files (avoid edges for simplicity)
            capturing_rank = 4  # 5th rank (0-indexed)
            self.capturing_pawn = chess.square(capturing_file, capturing_rank)
            
            # Place enemy pawn that "just moved 2 squares"
            enemy_file = capturing_file + random.choice([-1, 1])  # Adjacent file
            enemy_rank = 4  # Same rank after 2-square move
            self.enemy_pawn = chess.square(enemy_file, enemy_rank)
            
            # En passant target square (where capturing pawn moves)
            self.en_passant_square = chess.square(enemy_file, 5)  # 6th rank
            
            # Place the pawns
            self.chess_board.board.set_piece_at(
                self.capturing_pawn, 
                chess.Piece(chess.PAWN, self.pawn_color)
            )
            self.chess_board.board.set_piece_at(
                self.enemy_pawn, 
                chess.Piece(chess.PAWN, chess.BLACK)
            )
            
            # Add kings for realistic position
            self.chess_board.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            self.chess_board.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
            
            # Target is the en passant capture square
            self.target_squares = [self.en_passant_square]
            
            # Invalid squares include common mistakes
            self.invalid_squares = [
                self.enemy_pawn,  # Can't capture pawn directly
                chess.square(capturing_file, 5)  # Normal pawn move forward
            ]
            
            # Add some random distractors
            all_squares = list(range(64))
            occupied = [sq for sq in all_squares if self.chess_board.board.piece_at(sq)]
            available = [sq for sq in all_squares if sq not in occupied + self.target_squares + self.invalid_squares]
            if available:
                additional_invalid = random.sample(available, min(5, len(available)))
                self.invalid_squares.extend(additional_invalid)
            
            # Highlight the capturing pawn
            self.chess_board.highlight_square(self.capturing_pawn)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate en passant recognition position: {e}")
            return False
    
    def check_move(self, square: int) -> bool:
        """Check if clicked square is the en passant capture square"""
        return square == self.en_passant_square
    
    def get_hints(self) -> List[str]:
        """Progressive hints for en passant recognition"""
        enemy_square_name = chess.square_name(self.enemy_pawn).upper()
        target_square_name = chess.square_name(self.en_passant_square).upper()
        
        return [
            "Look for the pawn that just jumped 2 squares!",
            f"Black pawn on {enemy_square_name} just moved from {enemy_square_name[0]}7 to {enemy_square_name}",
            "You can capture it 'in passing' - diagonally!",
            f"Click the EMPTY square {target_square_name}",
            f"Your pawn moves to {target_square_name}, enemy pawn disappears!"
        ]
    
    def _get_error_message(self) -> str:
        """Specific error messages for common en passant mistakes"""
        # This could be enhanced to detect what square was clicked
        return "Wrong square! En passant captures diagonally to the EMPTY square the pawn passed over!"
    
    def _render_hints(self, screen):
        """Render visual hints for en passant recognition"""
        if not self.show_hints:
            return
            
        try:
            # Highlight the en passant capture square with pulsing effect
            if self.en_passant_square is not None:
                square_rect = self.chess_board.get_square_rect(self.en_passant_square)
                if square_rect:
                    alpha = int(150 + 80 * math.sin(pygame.time.get_ticks() * 0.006))
                    hint_surface = pygame.Surface((square_rect.width, square_rect.height))
                    hint_surface.set_alpha(alpha)
                    hint_surface.fill((255, 165, 0))  # Orange for en passant
                    screen.blit(hint_surface, square_rect)
            
            # Draw curved arrow from capturing pawn to target
            if self.capturing_pawn is not None and self.en_passant_square is not None:
                pawn_rect = self.chess_board.get_square_rect(self.capturing_pawn)
                target_rect = self.chess_board.get_square_rect(self.en_passant_square)
                
                if pawn_rect and target_rect:
                    start_pos = pawn_rect.center
                    end_pos = target_rect.center
                    
                    # Draw diagonal line (en passant is diagonal move)
                    pygame.draw.line(screen, (255, 255, 0), start_pos, end_pos, 3)
                    
                    # Draw arrow head
                    import math
                    angle = math.atan2(end_pos[1] - start_pos[1], end_pos[0] - start_pos[0])
                    arrow_length = 12
                    arrow_angle = 0.5
                    
                    arrow_p1 = (
                        end_pos[0] - arrow_length * math.cos(angle - arrow_angle),
                        end_pos[1] - arrow_length * math.sin(angle - arrow_angle)
                    )
                    arrow_p2 = (
                        end_pos[0] - arrow_length * math.cos(angle + arrow_angle), 
                        end_pos[1] - arrow_length * math.sin(angle + arrow_angle)
                    )
                    
                    pygame.draw.polygon(screen, (255, 255, 0), [end_pos, arrow_p1, arrow_p2])
            
            # Highlight the enemy pawn that can be captured (with X mark)
            if self.enemy_pawn is not None:
                enemy_rect = self.chess_board.get_square_rect(self.enemy_pawn)
                if enemy_rect:
                    # Draw red X over the enemy pawn
                    center = enemy_rect.center
                    size = 15
                    pygame.draw.line(screen, (255, 0, 0), 
                                   (center[0] - size, center[1] - size),
                                   (center[0] + size, center[1] + size), 3)
                    pygame.draw.line(screen, (255, 0, 0),
                                   (center[0] + size, center[1] - size),
                                   (center[0] - size, center[1] + size), 3)
                    
        except Exception as e:
            logger.warning(f"Failed to render en passant hints: {e}")

