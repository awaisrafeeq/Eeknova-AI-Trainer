# 1. First, let's create the generalized ChessBoard class
# src/chess/chess_board.py

import pygame
import chess
from typing import Optional, List, Tuple

class ChessBoard:
    """Generalized chess board that can be used by all modules"""
    
    def __init__(self, screen: pygame.Surface, resource_manager, 
                 board_size: int = 480, position: str = chess.STARTING_FEN):
        self.screen = screen
        self.resource_manager = resource_manager
        self.board = chess.Board(position)
        
        # Board dimensions
        self.board_size = board_size
        self.square_size = board_size // 8
        
        # Center the board on screen
        self.board_offset_x = (screen.get_width() - self.board_size) // 2
        self.board_offset_y = (screen.get_height() - self.board_size) // 2 + 50  # Extra offset for UI
        
        # Visual states
        self.highlighted_squares = []
        self.arrow_list = []
        self.selected_square = None
        
        # Colors
        self.light_square_color = (240, 217, 181)
        self.dark_square_color = (181, 136, 99)
        self.highlight_color = (255, 255, 0, 200)  # Yellow with more opacity (200/255 = 78%)
        self.selected_color = (0, 255, 0, 128)  # Green with transparency
        
        # Create surface for transparent overlays
        self.overlay_surface = pygame.Surface((self.board_size, self.board_size), pygame.SRCALPHA)
        
    def draw(self):
        """Draw the chess board and pieces"""
        # Draw board squares
        for row in range(8):
            for col in range(8):
                # Calculate square color
                is_light = (row + col) % 2 == 0
                color = self.light_square_color if is_light else self.dark_square_color
                
                # Draw square
                rect = pygame.Rect(
                    col * self.square_size + self.board_offset_x,
                    (7 - row) * self.square_size + self.board_offset_y,  # Flip for correct orientation
                    self.square_size,
                    self.square_size
                )
                pygame.draw.rect(self.screen, color, rect)
                
                # Draw file and rank labels
                if row == 0:  # Bottom row - file labels
                    label = chr(ord('a') + col)
                    font = pygame.font.Font(None, 20)
                    text = font.render(label, True, 
                                     self.dark_square_color if is_light else self.light_square_color)
                    text_rect = text.get_rect(bottomright=(rect.right - 2, rect.bottom - 2))
                    self.screen.blit(text, text_rect)
                
                if col == 0:  # Left column - rank labels
                    label = str(row + 1)
                    font = pygame.font.Font(None, 20)
                    text = font.render(label, True,
                                     self.dark_square_color if is_light else self.light_square_color)
                    text_rect = text.get_rect(topleft=(rect.left + 2, rect.top + 2))
                    self.screen.blit(text, text_rect)
        
        # Draw pieces
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                self._draw_piece(piece, square)
        
        # Draw highlights and selections
        self._draw_overlays()
    
    def _draw_piece(self, piece: chess.Piece, square: int):
        """Draw a chess piece at the given square"""
        col = chess.square_file(square)
        row = chess.square_rank(square)
        
        # Get piece image
        color = 'white' if piece.color else 'black'
        piece_name = chess.piece_name(piece.piece_type)
        
        # Load and scale piece image
        piece_image = self.resource_manager.load_piece_image(
            piece_name, color, (self.square_size - 10, self.square_size - 10)
        )
        
        # Calculate position (centered in square)
        x = col * self.square_size + self.board_offset_x + 5
        y = (7 - row) * self.square_size + self.board_offset_y + 5
        
        self.screen.blit(piece_image, (x, y))
    
    def _draw_overlays(self):
        """Draw highlights, selections, and other overlays"""
        # Clear overlay surface
        self.overlay_surface.fill((0, 0, 0, 0))
        
        # Draw highlighted squares
        for square in self.highlighted_squares:
            col = chess.square_file(square)
            row = chess.square_rank(square)
            rect = pygame.Rect(
                col * self.square_size,
                (7 - row) * self.square_size,
                self.square_size,
                self.square_size
            )
            pygame.draw.rect(self.overlay_surface, self.highlight_color, rect)
            pygame.draw.rect(self.overlay_surface, self.highlight_color[:3], rect, 3)
        
        # Draw selected square
        if self.selected_square is not None:
            col = chess.square_file(self.selected_square)
            row = chess.square_rank(self.selected_square)
            rect = pygame.Rect(
                col * self.square_size,
                (7 - row) * self.square_size,
                self.square_size,
                self.square_size
            )
            pygame.draw.rect(self.overlay_surface, self.selected_color, rect)
            pygame.draw.rect(self.overlay_surface, self.selected_color[:3], rect, 3)
        
        # Blit overlay surface
        self.screen.blit(self.overlay_surface, (self.board_offset_x, self.board_offset_y))
    
    def get_square_from_pos(self, pos: Tuple[int, int]) -> Optional[int]:
        """Convert screen position to board square"""
        x, y = pos
        x -= self.board_offset_x
        y -= self.board_offset_y
        
        if 0 <= x < self.board_size and 0 <= y < self.board_size:
            col = x // self.square_size
            row = 7 - (y // self.square_size)  # Flip for correct orientation
            
            if 0 <= col < 8 and 0 <= row < 8:
                return chess.square(col, row)
        return None
    
    def highlight_square(self, square: int):
        """Highlight a specific square"""
        if square not in self.highlighted_squares:
            self.highlighted_squares.append(square)
    
    def clear_highlights(self):
        """Clear all highlighted squares"""
        self.highlighted_squares.clear()
    
    def select_square(self, square: Optional[int]):
        """Select a square"""
        self.selected_square = square
    
    def get_piece_at(self, square: int) -> Optional[chess.Piece]:
        """Get piece at given square"""
        return self.board.piece_at(square)
    
    def set_position(self, fen: str):
        """Set board position from FEN string"""
        self.board.set_fen(fen)
        self.clear_highlights()
        self.selected_square = None
    
    def make_move(self, move: chess.Move) -> bool:
        """Make a move on the board"""
        if move in self.board.legal_moves:
            self.board.push(move)
            return True
        return False
    
    def reset(self):
        """Reset board to starting position"""
        self.board.reset()
        self.clear_highlights()
        self.selected_square = None