# chess_engine.py - Complete Chess Engine API for Yoga Project Backend
# This provides all pygame chess functionality as web API endpoints

from __future__ import annotations
import chess
import random
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# ---- Chess Engine Classes ----

class PieceType(Enum):
    PAWN = "pawn"
    ROOK = "rook"
    KNIGHT = "knight"
    BISHOP = "bishop"
    QUEEN = "queen"
    KING = "king"

class PieceColor(Enum):
    WHITE = "white"
    BLACK = "black"

@dataclass
class ChessSquare:
    file: str  # a-h
    rank: int  # 1-8
    index: int  # 0-63
    
    @classmethod
    def from_index(cls, index: int) -> 'ChessSquare':
        file = chr(ord('a') + chess.square_file(index))
        rank = chess.square_rank(index) + 1
        return cls(file=file, rank=rank, index=index)
    
    @classmethod
    def from_notation(cls, notation: str) -> 'ChessSquare':
        index = chess.parse_square(notation)
        return cls.from_index(index)

@dataclass
class ChessPiece:
    type: PieceType
    color: PieceColor
    square: ChessSquare
    
    def to_chess_piece(self) -> chess.Piece:
        color_map = {PieceColor.WHITE: chess.WHITE, PieceColor.BLACK: chess.BLACK}
        type_map = {
            PieceType.PAWN: chess.PAWN,
            PieceType.ROOK: chess.ROOK,
            PieceType.KNIGHT: chess.KNIGHT,
            PieceType.BISHOP: chess.BISHOP,
            PieceType.QUEEN: chess.QUEEN,
            PieceType.KING: chess.KING
        }
        return chess.Piece(type_map[self.type], color_map[self.color])

@dataclass
class BoardPosition:
    """Represents a complete chess board position with all metadata"""
    fen: str
    pieces: List[ChessPiece]
    legal_moves: List[str]
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool
    turn: PieceColor
    fullmove_number: int
    halfmove_clock: int

@dataclass
class ExerciseState:
    """Complete exercise state for frontend"""
    exercise_id: str
    module_id: str
    exercise_type: str
    board_position: BoardPosition
    highlighted_squares: List[str]
    target_squares: List[str]
    invalid_squares: List[str]
    selected_square: Optional[str]
    instructions: str
    feedback_message: Optional[str]
    is_correct: Optional[bool]
    progress_current: int
    progress_total: int
    hint_available: bool
    exercise_completed: bool
    module_completed: bool
    # Board setup specific properties
    pieces_inventory: Optional[Dict[str, Dict[str, Any]]] = None
    placed_pieces: Optional[Dict[str, Dict[str, Any]]] = None
    current_piece_type: Optional[str] = None

class ChessEngine:
    """Complete chess engine that replicates pygame functionality"""
    
    def __init__(self):
        self.board = chess.Board()
        self.highlighted_squares: List[int] = []
        self.selected_square: Optional[int] = None
        self.target_squares: List[int] = []
        self.invalid_squares: List[int] = []
        
        # Board colors (same as pygame)
        self.light_square_color = "#F0D9B5"  # (240, 217, 181)
        self.dark_square_color = "#B58863"   # (181, 136, 99)
        self.highlight_color = "#FFFF00"     # Yellow
        self.selected_color = "#00FF00"     # Green
        
    def reset_board(self) -> None:
        """Reset board to starting position"""
        self.board.reset()
        self.clear_highlights()
        self.selected_square = None
        self.target_squares = []
        self.invalid_squares = []
    
    def set_position(self, fen: str) -> None:
        """Set board position from FEN"""
        self.board.set_fen(fen)
        self.clear_highlights()
        self.selected_square = None
    
    def get_board_position(self) -> BoardPosition:
        """Get complete board position"""
        pieces = []
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                # Convert to our piece format
                piece_type = {
                    chess.PAWN: PieceType.PAWN,
                    chess.ROOK: PieceType.ROOK,
                    chess.KNIGHT: PieceType.KNIGHT,
                    chess.BISHOP: PieceType.BISHOP,
                    chess.QUEEN: PieceType.QUEEN,
                    chess.KING: PieceType.KING
                }[piece.piece_type]
                
                piece_color = PieceColor.WHITE if piece.color else PieceColor.BLACK
                square_obj = ChessSquare.from_index(square)
                
                pieces.append(ChessPiece(
                    type=piece_type,
                    color=piece_color,
                    square=square_obj
                ))
        
        legal_moves = [move.uci() for move in self.board.legal_moves]
        turn = PieceColor.WHITE if self.board.turn else PieceColor.BLACK
        
        return BoardPosition(
            fen=self.board.fen(),
            pieces=pieces,
            legal_moves=legal_moves,
            is_check=self.board.is_check(),
            is_checkmate=self.board.is_checkmate(),
            is_stalemate=self.board.is_stalemate(),
            turn=turn,
            fullmove_number=self.board.fullmove_number,
            halfmove_clock=self.board.halfmove_clock
        )
    
    def highlight_square(self, square: str) -> None:
        """Highlight a square"""
        index = chess.parse_square(square)
        if index not in self.highlighted_squares:
            self.highlighted_squares.append(index)
    
    def clear_highlights(self) -> None:
        """Clear all highlights"""
        self.highlighted_squares = []
    
    def select_square(self, square: Optional[str]) -> None:
        """Select a square"""
        if square:
            self.selected_square = chess.parse_square(square)
        else:
            self.selected_square = None
    
    def get_square_color(self, square: str) -> str:
        """Get the color of a square (light/dark)"""
        index = chess.parse_square(square)
        file = chess.square_file(index)
        rank = chess.square_rank(index)
        is_light = (file + rank) % 2 == 0
        return self.light_square_color if is_light else self.dark_square_color
    
    def is_valid_move(self, from_square: str, to_square: str) -> bool:
        """Check if a move is valid"""
        try:
            move = chess.Move.from_uci(f"{from_square}{to_square}")
            return move in self.board.legal_moves
        except:
            return False
    
    def make_move(self, from_square: str, to_square: str) -> bool:
        """Make a move on the board"""
        if self.is_valid_move(from_square, to_square):
            move = chess.Move.from_uci(f"{from_square}{to_square}")
            self.board.push(move)
            return True
        return False
    
    def get_board_layout(self) -> Dict[str, Any]:
        """Get complete board layout for frontend rendering"""
        layout = {
            "squares": [],
            "pieces": [],
            "labels": {
                "files": ["a", "b", "c", "d", "e", "f", "g", "h"],
                "ranks": ["1", "2", "3", "4", "5", "6", "7", "8"]
            },
            "colors": {
                "light_square": self.light_square_color,
                "dark_square": self.dark_square_color,
                "highlight": self.highlight_color,
                "selected": self.selected_color
            }
        }
        
        # Add squares with colors
        for rank in range(8):
            for file in range(8):
                square_name = f"{chr(ord('a') + file)}{8 - rank}"
                color = self.get_square_color(square_name)
                is_highlighted = chess.parse_square(square_name) in self.highlighted_squares
                is_selected = chess.parse_square(square_name) == self.selected_square
                
                layout["squares"].append({
                    "name": square_name,
                    "file": chr(ord('a') + file),
                    "rank": str(8 - rank),
                    "color": color,
                    "is_light": (file + rank) % 2 == 0,
                    "is_highlighted": is_highlighted,
                    "is_selected": is_selected
                })
        
        # Add pieces
        position = self.get_board_position()
        for piece in position.pieces:
            layout["pieces"].append({
                "type": piece.type.value,
                "color": piece.color.value,
                "square": piece.square.file + str(piece.square.rank),
                "symbol": self.get_piece_symbol(piece.type, piece.color)
            })
        
        return layout
    
    def get_piece_symbol(self, piece_type: PieceType, color: PieceColor) -> str:
        """Get Unicode symbol for piece"""
        symbols = {
            (PieceType.KING, PieceColor.WHITE): "♔",
            (PieceType.QUEEN, PieceColor.WHITE): "♕",
            (PieceType.ROOK, PieceColor.WHITE): "♖",
            (PieceType.BISHOP, PieceColor.WHITE): "♗",
            (PieceType.KNIGHT, PieceColor.WHITE): "♘",
            (PieceType.PAWN, PieceColor.WHITE): "♙",
            (PieceType.KING, PieceColor.BLACK): "♚",
            (PieceType.QUEEN, PieceColor.BLACK): "♛",
            (PieceType.ROOK, PieceColor.BLACK): "♜",
            (PieceType.BISHOP, PieceColor.BLACK): "♝",
            (PieceType.KNIGHT, PieceColor.BLACK): "♞",
            (PieceType.PAWN, PieceColor.BLACK): "♟"
        }
        return symbols.get((piece_type, color), "")

# ---- Lesson Engine Classes ----

class LessonEngine:
    """Manages all chess lessons with complete pygame logic"""
    
    def __init__(self):
        self.engine = ChessEngine()
        self.current_exercise: Optional[ExerciseState] = None
        
    # ---- Pawn Movement Lessons (Complete from pygame) ----
    
    def create_pawn_exercise(self, exercise_type: str, exercise_number: int) -> ExerciseState:
        """Create pawn movement exercise exactly like pygame"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        exercise_id = f"pawn_{exercise_type}_{exercise_number}"
        
        if exercise_type == "basic_forward":
            return self._create_basic_forward_exercise(exercise_id, exercise_number)
        elif exercise_type == "initial_double":
            return self._create_initial_double_exercise(exercise_id, exercise_number)
        elif exercise_type == "capture":
            return self._create_capture_exercise(exercise_id, exercise_number)
        elif exercise_type == "blocked":
            return self._create_blocked_exercise(exercise_id, exercise_number)
        elif exercise_type == "en_passant":
            return self._create_en_passant_exercise(exercise_id, exercise_number)
        else:
            raise ValueError(f"Unknown exercise type: {exercise_type}")
    
    def _create_basic_forward_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """Basic forward movement exercise"""
        pawn_file = random.randint(1, 6)  # Avoid edges
        pawn_rank = random.randint(2, 5)  # Middle ranks
        pawn_square = chess.square(pawn_file, pawn_rank)
        
        self.engine.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        
        # Target square is one forward
        target_square = pawn_square + 8
        target_squares = [target_square] if target_square <= 63 else []
        
        # Invalid squares (backward, sideways)
        invalid_squares = [
            pawn_square - 8,  # Backward
            pawn_square + 1 if pawn_file < 7 else None,  # Right
            pawn_square - 1 if pawn_file > 0 else None,  # Left
        ]
        invalid_squares = [sq for sq in invalid_squares if sq is not None and 0 <= sq <= 63]
        
        # Highlight the pawn
        self.engine.highlight_square(chess.square_name(pawn_square))
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="pawn_movement",
            exercise_type="basic_forward",
            board_position=self.engine.get_board_position(),
            highlighted_squares=[chess.square_name(pawn_square)],
            target_squares=[chess.square_name(sq) for sq in target_squares],
            invalid_squares=[chess.square_name(sq) for sq in invalid_squares],
            selected_square=None,
            instructions="Pawns move forward one square. Click where this pawn can move.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=15,  # 3 exercises × 5 types
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )
    
    def _create_initial_double_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """Initial two-square move exercise"""
        pawn_file = random.randint(1, 6)
        pawn_square = chess.square(pawn_file, 1)  # Second rank
        
        self.engine.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        
        # Target squares are one and two forward
        target_squares = []
        one_forward = pawn_square + 8
        two_forward = pawn_square + 16
        
        if one_forward <= 63:
            target_squares.append(one_forward)
        if two_forward <= 63:
            target_squares.append(two_forward)
        
        # Invalid squares
        invalid_squares = [
            pawn_square + 24 if pawn_square + 24 <= 63 else None,  # Three squares forward
            pawn_square + 7 if pawn_file > 0 else None,  # Diagonal without capture
            pawn_square + 9 if pawn_file < 7 else None,  # Diagonal without capture
        ]
        invalid_squares = [sq for sq in invalid_squares if sq is not None and 0 <= sq <= 63]
        
        self.engine.highlight_square(chess.square_name(pawn_square))
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="pawn_movement",
            exercise_type="initial_double",
            board_position=self.engine.get_board_position(),
            highlighted_squares=[chess.square_name(pawn_square)],
            target_squares=[chess.square_name(sq) for sq in target_squares],
            invalid_squares=[chess.square_name(sq) for sq in invalid_squares],
            selected_square=None,
            instructions="Pawns can move two squares forward from their starting position.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=15,
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )
    
    def _create_capture_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """Diagonal capture exercise"""
        pawn_file = random.randint(1, 6)
        pawn_rank = random.randint(1, 5)
        pawn_square = chess.square(pawn_file, pawn_rank)
        
        self.engine.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        
        target_squares = []
        
        # Place enemy pieces diagonally ahead
        if pawn_file > 0 and pawn_rank < 7:
            left_capture = pawn_square + 7
            if 0 <= left_capture <= 63:
                self.engine.board.set_piece_at(left_capture, chess.Piece(chess.PAWN, chess.BLACK))
                target_squares.append(left_capture)
        
        if pawn_file < 7 and pawn_rank < 7:
            right_capture = pawn_square + 9
            if 0 <= right_capture <= 63:
                self.engine.board.set_piece_at(right_capture, chess.Piece(chess.KNIGHT, chess.BLACK))
                target_squares.append(right_capture)
        
        # Forward square is NOT a valid capture
        forward_square = pawn_square + 8
        invalid_squares = [forward_square] if forward_square <= 63 else []
        
        self.engine.highlight_square(chess.square_name(pawn_square))
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="pawn_movement",
            exercise_type="capture",
            board_position=self.engine.get_board_position(),
            highlighted_squares=[chess.square_name(pawn_square)],
            target_squares=[chess.square_name(sq) for sq in target_squares],
            invalid_squares=[chess.square_name(sq) for sq in invalid_squares],
            selected_square=None,
            instructions="Pawns capture diagonally forward. Click where this pawn can capture.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=15,
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )
    
    def _create_blocked_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """Blocked pawn exercise"""
        pawn_file = random.randint(1, 6)
        pawn_rank = random.randint(2, 5)
        pawn_square = chess.square(pawn_file, pawn_rank)
        
        self.engine.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        
        # Block the pawn
        blocking_square = pawn_square + 8
        if blocking_square <= 63:
            self.engine.board.set_piece_at(blocking_square, chess.Piece(chess.BISHOP, chess.BLACK))
        
        target_squares = []
        
        # Maybe add capture options
        if pawn_file > 0:
            left_capture = pawn_square + 7
            if 0 <= left_capture <= 63 and random.choice([True, False]):
                self.engine.board.set_piece_at(left_capture, chess.Piece(chess.ROOK, chess.BLACK))
                target_squares.append(left_capture)
        
        if pawn_file < 7:
            right_capture = pawn_square + 9
            if 0 <= right_capture <= 63 and random.choice([True, False]) and not target_squares:
                self.engine.board.set_piece_at(right_capture, chess.Piece(chess.QUEEN, chess.BLACK))
                target_squares.append(right_capture)
        
        invalid_squares = [blocking_square] if blocking_square <= 63 else []
        
        self.engine.highlight_square(chess.square_name(pawn_square))
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="pawn_movement",
            exercise_type="blocked",
            board_position=self.engine.get_board_position(),
            highlighted_squares=[chess.square_name(pawn_square)],
            target_squares=[chess.square_name(sq) for sq in target_squares],
            invalid_squares=[chess.square_name(sq) for sq in invalid_squares],
            selected_square=None,
            instructions="Pawns cannot move if blocked. Is this pawn blocked? Click where it can move or the pawn if blocked.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=15,
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )
    
    def _create_en_passant_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """En passant exercise"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        pawn_file = random.randint(1, 6)
        pawn_square = chess.square(pawn_file, 4)  # 5th rank
        
        self.engine.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        
        # Place black pawn that just moved two squares
        enemy_file = pawn_file - 1 if pawn_file > 0 else pawn_file + 1
        enemy_square = chess.square(enemy_file, 4)
        self.engine.board.set_piece_at(enemy_square, chess.Piece(chess.PAWN, chess.BLACK))
        
        # En passant capture square
        en_passant_square = chess.square(enemy_file, 5)
        target_squares = [en_passant_square] if 0 <= en_passant_square <= 63 else []
        
        # Normal forward move is also valid
        forward_square = pawn_square + 8
        if forward_square <= 63:
            target_squares.append(forward_square)
        
        self.engine.highlight_square(chess.square_name(pawn_square))
        self.engine.highlight_square(chess.square_name(enemy_square))
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="special_moves",  # Fixed: Use special_moves instead of pawn_movement
            exercise_type="en_passant",
            board_position=self.engine.get_board_position(),
            highlighted_squares=[
                chess.square_name(pawn_square),
                chess.square_name(enemy_square)
            ],
            target_squares=[chess.square_name(sq) for sq in target_squares],
            invalid_squares=[],
            selected_square=None,
            instructions="En passant: Special pawn capture when enemy pawn moves two squares.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=5,
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )
    
    # ---- Board Setup Helper Methods ----
    
    def handle_board_setup_piece_selection(self, exercise: ExerciseState, piece_type: str) -> ExerciseState:
        """Handle piece selection for board setup"""
        exercise.current_piece_type = piece_type
        piece_info = exercise.pieces_inventory[piece_type]
        piece_name = piece_type.replace('_', ' ').title()
        
        # Check how many of this piece type are already placed
        placed_count = sum(1 for p in exercise.placed_pieces.values() if p['type'] == piece_type)
        remaining = piece_info['count'] - placed_count
        
        if remaining <= 0:
            exercise.feedback_message = f"All {piece_name}s are already placed!"
            exercise.is_correct = False
        else:
            exercise.feedback_message = f"Selected {piece_name}. Click on the board to place it. ({remaining} remaining)"
            exercise.is_correct = None
        
        return exercise
    
    def handle_board_setup_placement(self, exercise: ExerciseState, square: str) -> ExerciseState:
        """Handle piece placement for board setup"""
        print(f"🔍 DEBUG: handle_board_setup_placement called with square: {square}")
        print(f"🔍 DEBUG: Current placed_pieces count: {len(exercise.placed_pieces)}")
        
        if not exercise.current_piece_type:
            exercise.feedback_message = "Please select a piece to place first."
            exercise.is_correct = False
            return exercise
        
        # Convert square to coordinates
        col = ord(square[0]) - ord('a')
        row = int(square[1]) - 1
        
        piece_type = exercise.current_piece_type
        piece_info = exercise.pieces_inventory[piece_type]
        piece_name = piece_type.replace('_', ' ').title()
        
        # Check how many of this piece type are already placed
        placed_count = sum(1 for p in exercise.placed_pieces.values() if p['type'] == piece_type)
        remaining = piece_info['count'] - placed_count
        
        if remaining <= 0:
            exercise.feedback_message = f"All {piece_name}s have been placed."
            exercise.is_correct = False
            return exercise
        
        # Check if this position is correct for this piece type
        is_correct_position = (col, row) in piece_info['positions']
        
        print(f"🔍 DEBUG: Position check - square: {square}, col: {col}, row: {row}, is_correct: {is_correct_position}")
        
        # Check if square is already occupied
        if square in exercise.placed_pieces:
            exercise.feedback_message = "This square is already occupied!"
            exercise.is_correct = False
            return exercise
        
        # PREVENT placement in wrong positions
        if not is_correct_position:
            exercise.feedback_message = f"Wrong position! {piece_name} cannot be placed at {square}."
            exercise.is_correct = False
            # Don't place the piece, just return error
            return exercise
        
        # Only place piece if position is correct
        piece_symbol = piece_info['symbol']
        piece_color = piece_info['color']
        
        # Update the board
        piece = chess.Piece.from_symbol(piece_symbol)
        self.engine.board.set_piece_at(chess.SQUARES[col + row * 8], piece)
        
        # Record the placement
        exercise.placed_pieces[square] = {
            'type': piece_type,
            'symbol': piece_symbol,
            'color': piece_color,
            'correct': is_correct_position
        }
        
        print(f"🔍 DEBUG: Before progress update - progress_current: {exercise.progress_current}")
        
        # Update progress
        exercise.progress_current = len(exercise.placed_pieces)
        
        # DEBUG: Log progress update
        print(f"🔍 DEBUG: Updated progress_current to {exercise.progress_current} (placed_pieces: {len(exercise.placed_pieces)})")
        
        # Provide feedback
        if is_correct_position:
            exercise.feedback_message = f"Correct! {piece_name} placed at {square}."
            exercise.is_correct = True
        else:
            exercise.feedback_message = f"Wrong position! {piece_name} should not be at {square}."
            exercise.is_correct = False
        
        # Check if all pieces are placed
        if exercise.progress_current >= exercise.progress_total:
            # Verify all pieces are in correct positions
            all_correct = all(p['correct'] for p in exercise.placed_pieces.values())
            
            if all_correct:
                exercise.feedback_message = "Perfect! Board setup complete and correct!"
                exercise.exercise_completed = True
                exercise.module_completed = True
            else:
                exercise.feedback_message = "Board setup complete, but some pieces are in wrong positions. Please fix them."
                exercise.exercise_completed = False
        
        return exercise
    
    def handle_board_setup_remove_piece(self, exercise: ExerciseState, square: str) -> ExerciseState:
        """Handle piece removal for board setup"""
        if square in exercise.placed_pieces:
            removed_piece = exercise.placed_pieces[square]
            del exercise.placed_pieces[square]
            
            # Clear the square on the board
            self.engine.board.remove_piece_at(chess.SQUARES[ord(square[0]) - ord('a') + (int(square[1]) - 1) * 8])
            
            # Update progress
            exercise.progress_current = len(exercise.placed_pieces)
            
            piece_name = removed_piece['type'].replace('_', ' ').title()
            exercise.feedback_message = f"Removed {piece_name} from {square}."
            exercise.is_correct = None
        else:
            exercise.feedback_message = "No piece to remove at this square."
            exercise.is_correct = False
        
        return exercise
    
    # ---- Board Setup Lessons ----
    
    def create_board_setup_exercise(self) -> ExerciseState:
        """Create board setup exercise"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        # Define all pieces and their correct positions
        pieces_inventory = {
            'white_pawn': {'count': 8, 'positions': [(i, 1) for i in range(8)], 'symbol': 'P', 'color': 'white'},
            'white_rook': {'count': 2, 'positions': [(0, 0), (7, 0)], 'symbol': 'R', 'color': 'white'},
            'white_knight': {'count': 2, 'positions': [(1, 0), (6, 0)], 'symbol': 'N', 'color': 'white'},
            'white_bishop': {'count': 2, 'positions': [(2, 0), (5, 0)], 'symbol': 'B', 'color': 'white'},
            'white_queen': {'count': 1, 'positions': [(3, 0)], 'symbol': 'Q', 'color': 'white'},
            'white_king': {'count': 1, 'positions': [(4, 0)], 'symbol': 'K', 'color': 'white'},
            'black_pawn': {'count': 8, 'positions': [(i, 6) for i in range(8)], 'symbol': 'p', 'color': 'black'},
            'black_rook': {'count': 2, 'positions': [(0, 7), (7, 7)], 'symbol': 'r', 'color': 'black'},
            'black_knight': {'count': 2, 'positions': [(1, 7), (6, 7)], 'symbol': 'n', 'color': 'black'},
            'black_bishop': {'count': 2, 'positions': [(2, 7), (5, 7)], 'symbol': 'b', 'color': 'black'},
            'black_queen': {'count': 1, 'positions': [(3, 7)], 'symbol': 'q', 'color': 'black'},
            'black_king': {'count': 1, 'positions': [(4, 7)], 'symbol': 'k', 'color': 'black'}
        }
        
        # Create instructions with piece list
        piece_list = []
        for piece_type, info in pieces_inventory.items():
            piece_name = piece_type.replace('_', ' ').title()
            piece_list.append(f"{info['count']}x {piece_name}")
        
        instructions = f"Set up the chess board with all pieces in their starting positions.\\n\\nPieces to place:\\n" + "\\n".join(piece_list) + "\\n\\nSelect a piece type and click on the board to place it."
        
        return ExerciseState(
            exercise_id="board_setup_1",
            module_id="board_setup",
            exercise_type="board_setup",
            board_position=self.engine.get_board_position(),
            highlighted_squares=sorted(set(highlighted_squares)),
            target_squares=sorted(set(target_squares)),
            invalid_squares=[],
            selected_square=None,
            instructions=instructions,
            feedback_message="Select a piece to place on the board",
            is_correct=None,
            progress_current=0,
            progress_total=32,  # Total pieces to place
            hint_available=True,
            exercise_completed=False,
            module_completed=False,
            # Add board setup specific data
            pieces_inventory=pieces_inventory,
            placed_pieces={},
            current_piece_type=None
        )
    
    # ---- Identify Pieces Lessons ----
    
    def create_identify_pieces_exercise(self, question_number: int) -> ExerciseState:
        """Create piece identification exercise"""
        self.engine.reset_board()
        
        # Pick a random piece and highlight it
        piece_types = [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]
        colors = [chess.WHITE, chess.BLACK]
        
        piece_type = random.choice(piece_types)
        color = random.choice(colors)
        
        # Find squares with this piece
        squares = [s for s in chess.SQUARES if self.engine.board.piece_at(s) and 
                   self.engine.board.piece_at(s).piece_type == piece_type and 
                   self.engine.board.piece_at(s).color == color]
        
        if squares:
            selected_square = random.choice(squares)
            self.engine.highlight_square(chess.square_name(selected_square))
            
            piece_names = {
                chess.PAWN: "Pawn",
                chess.KNIGHT: "Knight",
                chess.BISHOP: "Bishop",
                chess.ROOK: "Rook",
                chess.QUEEN: "Queen",
                chess.KING: "King"
            }
            
            correct_name = piece_names[piece_type]
            other_names = [name for pt, name in piece_names.items() if pt != piece_type]
            wrong_answers = random.sample(other_names, 3)
            
            options = [correct_name] + wrong_answers
            random.shuffle(options)
            
            return ExerciseState(
                exercise_id=f"identify_pieces_{question_number}",
                module_id="identify_pieces",
                exercise_type="identify_pieces",
                board_position=self.engine.get_board_position(),
                highlighted_squares=[chess.square_name(selected_square)],
                target_squares=[],
                invalid_squares=[],
                selected_square=None,
                instructions=f"What is the highlighted piece?|{','.join(options)}|{correct_name}",
                feedback_message=None,
                is_correct=None,
                progress_current=question_number,
                progress_total=12,
                hint_available=True,
                exercise_completed=False,
                module_completed=False
            )
        
        return self.create_identify_pieces_exercise(question_number)
    
    def check_answer(self, exercise: ExerciseState, answer: str) -> bool:
        """Check answer for identification exercises"""
        if exercise.exercise_type == "identify_pieces":
            # Get the correct answer from the third part of instructions
            parts = exercise.instructions.split("|")
            print(f"DEBUG: Instructions: {exercise.instructions}")
            print(f"DEBUG: Parts: {parts}")
            if len(parts) >= 3:
                correct_answer = parts[2].strip()
                print(f"DEBUG: Correct answer: '{correct_answer}'")
                print(f"DEBUG: User answer: '{answer}'")
                result = answer.strip().lower() == correct_answer.lower()
                print(f"DEBUG: Result: {result}")
                return result
        return False
    
    def create_knight_exercise(self, exercise_type: str, exercise_number: int) -> ExerciseState:
        """Create knight movement exercise"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        exercise_id = f"knight_{exercise_type}_{exercise_number}"
        
        if exercise_type == "basic":
            # Place knight in center
            knight_file = random.randint(2, 5)
            knight_rank = random.randint(2, 5)
            knight_square = chess.square(knight_file, knight_rank)
            
            self.engine.board.set_piece_at(knight_square, chess.Piece(chess.KNIGHT, chess.WHITE))
            
            # Get all legal knight moves
            legal_moves = list(self.engine.board.legal_moves)
            target_squares = [m.to_square for m in legal_moves]
            
            self.engine.highlight_square(chess.square_name(knight_square))
            
            return ExerciseState(
                exercise_id=exercise_id,
                module_id="knight_movement",
                exercise_type="basic",
                board_position=self.engine.get_board_position(),
                highlighted_squares=[chess.square_name(knight_square)],
                target_squares=[chess.square_name(sq) for sq in target_squares],
                invalid_squares=[],
                selected_square=None,
                instructions="Knights move in an L-shape: 2 squares in one direction, then 1 square perpendicular. Click any square the knight can move to.",
                feedback_message=None,
                is_correct=None,
                progress_current=exercise_number,
                progress_total=9,
                hint_available=True,
                exercise_completed=False,
                module_completed=False
            )
        elif exercise_type == "capture":
            # Place knight and enemy piece for capture
            knight_file = random.randint(2, 5)
            knight_rank = random.randint(2, 5)
            knight_square = chess.square(knight_file, knight_rank)
            
            self.engine.board.set_piece_at(knight_square, chess.Piece(chess.KNIGHT, chess.WHITE))
            
            # Place enemy piece for capture
            legal_moves = list(self.engine.board.legal_moves)
            if legal_moves:
                target_move = random.choice(legal_moves)
                self.engine.board.set_piece_at(target_move.to_square, chess.Piece(chess.PAWN, chess.BLACK))
                target_squares = [target_move.to_square]
            
            self.engine.highlight_square(chess.square_name(knight_square))
            
            return ExerciseState(
                exercise_id=exercise_id,
                module_id="knight_movement",
                exercise_type="capture",
                board_position=self.engine.get_board_position(),
                highlighted_squares=[chess.square_name(knight_square)],
                target_squares=[chess.square_name(sq) for sq in target_squares],
                invalid_squares=[],
                selected_square=None,
                instructions="Knights capture by jumping over pieces. Capture the black pawn with your knight.",
                feedback_message=None,
                is_correct=None,
                progress_current=exercise_number,
                progress_total=9,
                hint_available=True,
                exercise_completed=False,
                module_completed=False
            )
        else:
            return self.create_knight_exercise("basic", exercise_number)
    
    def create_rook_exercise(self, exercise_type: str, exercise_number: int) -> ExerciseState:
        """Create rook movement exercise"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        exercise_id = f"rook_{exercise_type}_{exercise_number}"
        
        if exercise_type == "basic":
            # Place rook in center
            rook_file = random.randint(2, 5)
            rook_rank = random.randint(2, 5)
            rook_square = chess.square(rook_file, rook_rank)
            
            self.engine.board.set_piece_at(rook_square, chess.Piece(chess.ROOK, chess.WHITE))
            
            # Get all legal rook moves
            legal_moves = list(self.engine.board.legal_moves)
            target_squares = [m.to_square for m in legal_moves]
            
            self.engine.highlight_square(chess.square_name(rook_square))
            
            return ExerciseState(
                exercise_id=exercise_id,
                module_id="rook_movement",
                exercise_type="basic",
                board_position=self.engine.get_board_position(),
                highlighted_squares=[chess.square_name(rook_square)],
                target_squares=[chess.square_name(sq) for sq in target_squares],
                invalid_squares=[],
                selected_square=None,
                instructions="Rooks move in straight lines: horizontally or vertically any number of squares. Click any square the rook can move to.",
                feedback_message=None,
                is_correct=None,
                progress_current=exercise_number,
                progress_total=9,
                hint_available=True,
                exercise_completed=False,
                module_completed=False
            )
        else:
            return self.create_rook_exercise("basic", exercise_number)
    
    def create_bishop_exercise(self, exercise_type: str, exercise_number: int) -> ExerciseState:
        """Create bishop movement exercise"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        exercise_id = f"bishop_{exercise_type}_{exercise_number}"
        
        if exercise_type == "basic":
            # Place bishop in center
            bishop_file = random.randint(2, 5)
            bishop_rank = random.randint(2, 5)
            bishop_square = chess.square(bishop_file, bishop_rank)
            
            self.engine.board.set_piece_at(bishop_square, chess.Piece(chess.BISHOP, chess.WHITE))
            
            # Get all legal bishop moves
            legal_moves = list(self.engine.board.legal_moves)
            target_squares = [m.to_square for m in legal_moves]
            
            self.engine.highlight_square(chess.square_name(bishop_square))
            
            return ExerciseState(
                exercise_id=exercise_id,
                module_id="bishop_movement",
                exercise_type="basic",
                board_position=self.engine.get_board_position(),
                highlighted_squares=[chess.square_name(bishop_square)],
                target_squares=[chess.square_name(sq) for sq in target_squares],
                invalid_squares=[],
                selected_square=None,
                instructions="Bishops move diagonally any number of squares. Click any square the bishop can move to.",
                feedback_message=None,
                is_correct=None,
                progress_current=exercise_number,
                progress_total=9,
                hint_available=True,
                exercise_completed=False,
                module_completed=False
            )
        else:
            return self.create_bishop_exercise("basic", exercise_number)
    
    def create_queen_exercise(self, exercise_type: str, exercise_number: int) -> ExerciseState:
        """Create queen movement exercise"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        exercise_id = f"queen_{exercise_type}_{exercise_number}"
        
        if exercise_type == "basic":
            # Place queen in center
            queen_file = random.randint(2, 5)
            queen_rank = random.randint(2, 5)
            queen_square = chess.square(queen_file, queen_rank)
            
            self.engine.board.set_piece_at(queen_square, chess.Piece(chess.QUEEN, chess.WHITE))
            
            # Get all legal queen moves
            legal_moves = list(self.engine.board.legal_moves)
            target_squares = [m.to_square for m in legal_moves]
            
            self.engine.highlight_square(chess.square_name(queen_square))
            
            return ExerciseState(
                exercise_id=exercise_id,
                module_id="queen_movement",
                exercise_type="basic",
                board_position=self.engine.get_board_position(),
                highlighted_squares=[chess.square_name(queen_square)],
                target_squares=[chess.square_name(sq) for sq in target_squares],
                invalid_squares=[],
                selected_square=None,
                instructions="The Queen is the most powerful piece! She combines rook and bishop moves. Click any square the queen can move to.",
                feedback_message=None,
                is_correct=None,
                progress_current=exercise_number,
                progress_total=9,
                hint_available=True,
                exercise_completed=False,
                module_completed=False
            )
        else:
            return self.create_queen_exercise("basic", exercise_number)
    
    def create_king_exercise(self, exercise_type: str, exercise_number: int) -> ExerciseState:
        """Create king movement exercise"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        exercise_id = f"king_{exercise_type}_{exercise_number}"
        
        if exercise_type == "basic":
            # Place king in center
            king_file = random.randint(2, 5)
            king_rank = random.randint(2, 5)
            king_square = chess.square(king_file, king_rank)
            
            self.engine.board.set_piece_at(king_square, chess.Piece(chess.KING, chess.WHITE))
            
            # Get all legal king moves
            legal_moves = list(self.engine.board.legal_moves)
            target_squares = [m.to_square for m in legal_moves]
            
            self.engine.highlight_square(chess.square_name(king_square))
            
            return ExerciseState(
                exercise_id=exercise_id,
                module_id="king_movement",
                exercise_type="basic",
                board_position=self.engine.get_board_position(),
                highlighted_squares=[chess.square_name(king_square)],
                target_squares=[chess.square_name(sq) for sq in target_squares],
                invalid_squares=[],
                selected_square=None,
                instructions="The King can move one square in any direction. Protect your king! Click any square the king can move to.",
                feedback_message=None,
                is_correct=None,
                progress_current=exercise_number,
                progress_total=9,
                hint_available=True,
                exercise_completed=False,
                module_completed=False
            )
        else:
            return self.create_king_exercise("basic", exercise_number)

    def create_special_moves_exercise(self, exercise_type: str, exercise_number: int) -> ExerciseState:
        """Create special moves exercise"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        exercise_id = f"special_{exercise_type}_{exercise_number}"
        
        if exercise_type == "castling":
            return self._create_castling_exercise(exercise_id, exercise_number)
        elif exercise_type == "promotion":
            return self._create_promotion_exercise(exercise_id, exercise_number)
        elif exercise_type == "en_passant":
            return self._create_en_passant_exercise(exercise_id, exercise_number)
        else:
            return self._create_castling_exercise(exercise_id, exercise_number)
    
    def _create_castling_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """Castling exercise - Learning focused like pygame"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        # Set up perfect castling position (like pygame)
        color = chess.WHITE
        
        # Always place both kings for valid position
        king_square = chess.E1
        self.engine.board.set_piece_at(king_square, chess.Piece(chess.KING, color))
        self.engine.board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
        
        # Place rooks for castling options
        kingside_rook = chess.H1
        queenside_rook = chess.A1
        self.engine.board.set_piece_at(kingside_rook, chess.Piece(chess.ROOK, color))
        self.engine.board.set_piece_at(queenside_rook, chess.Piece(chess.ROOK, color))
        
        # Set castling rights using the correct approach
        # Create a fresh board to get proper castling rights
        fresh_board = chess.Board()
        self.engine.board.castling_rights = fresh_board.castling_rights
        
        # Set turn to white for castling
        self.engine.board.turn = chess.WHITE
        
        # Choose castling side for this exercise
        castling_side = "kingside" if exercise_number % 2 == 0 else "queenside"
        
        if castling_side == "kingside":
            target_squares = [chess.G1]
        else:
            target_squares = [chess.C1]
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="special_moves",
            exercise_type="castling",
            board_position=self.engine.get_board_position(),
            highlighted_squares=[chess.square_name(king_square)],
            target_squares=[chess.square_name(sq) for sq in target_squares],
            invalid_squares=[],
            selected_square=None,
            instructions="Castling: Special king move for safety. Move king two squares towards rook.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=5,
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )
    
    def _create_promotion_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """Pawn promotion exercise"""
        # Place pawn on 7th rank ready for promotion
        pawn_file = random.randint(1, 6)
        pawn_square = chess.square(pawn_file, 6)
        self.engine.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        
        target_squares = [chess.square(pawn_file, 7)]
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="special_moves",
            exercise_type="promotion",
            board_position=self.engine.get_board_position(),
            highlighted_squares=[chess.square_name(pawn_square)],
            target_squares=[chess.square_name(sq) for sq in target_squares],
            invalid_squares=[],
            selected_square=None,
            instructions="Promotion: When pawn reaches the end, it becomes a stronger piece.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=5,
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )
    
    def create_check_checkmate_stalemate_exercise(self, exercise_type: str, exercise_number: int) -> ExerciseState:
        """Create check/checkmate/stalemate exercise"""
        self.engine.reset_board()
        self.engine.board.clear()
        
        exercise_id = f"check_{exercise_type}_{exercise_number}"
        
        if exercise_type == "check":
            return self._create_check_exercise(exercise_id, exercise_number)
        elif exercise_type == "checkmate":
            return self._create_checkmate_exercise(exercise_id, exercise_number)
        elif exercise_type == "stalemate":
            return self._create_stalemate_exercise(exercise_id, exercise_number)
        else:
            return self._create_check_exercise(exercise_id, exercise_number)
    
    def _create_check_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """Check exercise"""
        # Simple check position
        self.engine.board.set_piece_at(chess.parse_square('e8'), chess.Piece(chess.KING, chess.BLACK))
        self.engine.board.set_piece_at(chess.parse_square('e1'), chess.Piece(chess.KING, chess.WHITE))
        self.engine.board.set_piece_at(chess.parse_square('a1'), chess.Piece(chess.ROOK, chess.WHITE))
        
        # Set turn to white to deliver check
        self.engine.board.turn = chess.WHITE

        # Calculate target squares that give check
        target_moves = []
        for move in self.engine.board.legal_moves:
            test_board = self.engine.board.copy()
            test_board.push(move)
            if test_board.is_check():
                target_moves.append(move)

        target_squares = [chess.square_name(move.to_square) for move in target_moves]
        highlighted_squares = [chess.square_name(move.from_square) for move in target_moves]
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="check_checkmate_stalemate",
            exercise_type="check",
            board_position=self.engine.get_board_position(),
            highlighted_squares=sorted(set(highlighted_squares)),
            target_squares=sorted(set(target_squares)),
            invalid_squares=[],
            selected_square=None,
            instructions="Check: When king is under attack. Find the checking move.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=5,
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )
    
    def _create_checkmate_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """Checkmate exercise"""
        # Deterministic mate-in-1 position
        self.engine.board.clear()
        self.engine.board.set_piece_at(chess.parse_square('h8'), chess.Piece(chess.KING, chess.BLACK))
        self.engine.board.set_piece_at(chess.parse_square('g6'), chess.Piece(chess.KING, chess.WHITE))
        self.engine.board.set_piece_at(chess.parse_square('h6'), chess.Piece(chess.QUEEN, chess.WHITE))
        # White to move: Qh7#
        self.engine.board.turn = chess.WHITE

        # Calculate target squares that give checkmate
        target_moves = []
        for move in self.engine.board.legal_moves:
            test_board = self.engine.board.copy()
            test_board.push(move)
            if test_board.is_checkmate():
                target_moves.append(move)

        target_squares = [chess.square_name(move.to_square) for move in target_moves]
        highlighted_squares = [chess.square_name(move.from_square) for move in target_moves]
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="check_checkmate_stalemate",
            exercise_type="checkmate",
            board_position=self.engine.get_board_position(),
            highlighted_squares=sorted(set(highlighted_squares)),
            target_squares=sorted(set(target_squares)),
            invalid_squares=[],
            selected_square=None,
            instructions="Checkmate: When king is trapped and under attack. Find the checkmating move.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=5,
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )
    
    def _create_stalemate_exercise(self, exercise_id: str, exercise_number: int) -> ExerciseState:
        """Stalemate exercise"""
        # Deterministic stalemate-in-1 position
        self.engine.board.clear()
        self.engine.board.set_piece_at(chess.parse_square('a8'), chess.Piece(chess.KING, chess.BLACK))
        self.engine.board.set_piece_at(chess.parse_square('c6'), chess.Piece(chess.KING, chess.WHITE))
        self.engine.board.set_piece_at(chess.parse_square('b5'), chess.Piece(chess.QUEEN, chess.WHITE))
        # White to move: Qb6 (stalemate)
        self.engine.board.turn = chess.WHITE

        # Calculate target squares that cause stalemate
        target_moves = []
        for move in self.engine.board.legal_moves:
            test_board = self.engine.board.copy()
            test_board.push(move)
            if test_board.is_stalemate():
                target_moves.append(move)

        target_squares = [chess.square_name(move.to_square) for move in target_moves]
        highlighted_squares = [chess.square_name(move.from_square) for move in target_moves]
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="check_checkmate_stalemate",
            exercise_type="stalemate",
            board_position=self.engine.get_board_position(),
            highlighted_squares=sorted(set(highlighted_squares)),
            target_squares=sorted(set(target_squares)),
            invalid_squares=[],
            selected_square=None,
            instructions="Stalemate: When king is not under attack but has no legal moves. It's a draw.",
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=5,
            hint_available=True,
            exercise_completed=False,
            module_completed=False
        )

    def create_test_checkmate_position(self) -> None:
        """Create a test checkmate position for testing"""
        # Clear the board
        self.engine.board.clear()
        
        # Place white queen on d6
        self.engine.board.set_piece_at(chess.parse_square('d6'), chess.Piece(chess.QUEEN, chess.WHITE))
        
        # Place black king on h8
        self.engine.board.set_piece_at(chess.parse_square('h8'), chess.Piece(chess.KING, chess.BLACK))
        
        # Place white king on g6 to block escape
        self.engine.board.set_piece_at(chess.parse_square('g6'), chess.Piece(chess.KING, chess.WHITE))
        
        # Set turn to black (black is in checkmate)
        self.engine.board.turn = chess.BLACK
        
        print("Test checkmate position created: White wins by checkmate!")
        print(f"FEN: {self.engine.board.fen()}")

    def create_gameplay_exercise(self, game_mode: str, exercise_number: int, difficulty_level: str = "beginner") -> ExerciseState:
        """Create gameplay exercise with different game modes"""
        self.engine.reset_board()
        
        exercise_id = f"gameplay_{game_mode}_{exercise_number}"
        
        if game_mode == "human_vs_ai":
            # Human vs AI - Human plays as white
            instructions = "You are playing as White against the AI. Make your move and wait for the AI's response."
        elif game_mode == "ai_vs_ai":
            # AI vs AI - Watch AI play against itself
            instructions = "AI vs AI: Watch the computer play against itself. Turn: AI"
        elif game_mode == "human_vs_human":
            # Human vs Human - Two players on same device
            instructions = "Two-player mode: Both players play on the same device. White moves first."
        else:
            game_mode = "human_vs_ai"
            instructions = settings["instructions"]
        
        # Get the board position after reset
        board_position = self.engine.get_board_position()
        
        return ExerciseState(
            exercise_id=exercise_id,
            module_id="gameplay",
            exercise_type=game_mode,
            board_position=board_position,
            highlighted_squares=[],
            target_squares=[],
            invalid_squares=[],
            selected_square=None,
            instructions=instructions,
            feedback_message=None,
            is_correct=None,
            progress_current=exercise_number,
            progress_total=3,
            hint_available=False,
            exercise_completed=False,
            module_completed=False
        )

    def find_best_move(self) -> Optional[str]:
        """Find the best move using AI logic based on difficulty level"""
        try:
            legal_moves = list(self.engine.board.legal_moves)
            if not legal_moves:
                return None
            
            # Get difficulty settings
            if hasattr(self, 'ai_difficulty'):
                settings = self.ai_difficulty
            else:
                # Default to beginner settings
                settings = {"ai_randomness": 0.8, "ai_depth": 1}
            
            # Decide whether to make a random move or best move
            import random
            if random.random() < settings.get("ai_randomness", 0.8):
                # Make a random move (easier difficulty)
                return str(random.choice(legal_moves))
            else:
                # Make a smarter move based on difficulty
                captures = [move for move in legal_moves if self.engine.board.is_capture(move)]
                checks = [move for move in legal_moves if self.engine.board.gives_check(move)]
                
                # Prioritize checks and captures
                if checks:
                    return str(random.choice(checks))
                elif captures:
                    return str(random.choice(captures))
                else:
                    return str(random.choice(legal_moves))
                    
        except Exception as e:
            print(f"Error finding best move: {e}")
            return None

    def make_ai_move(self) -> bool:
        """Make an AI move"""
        try:
            print(f"AI attempting to move. Current turn: {'White' if self.engine.board.turn else 'Black'}")
            move_str = self.find_best_move()
            print(f"AI found move: {move_str}")
            if move_str:
                move = chess.Move.from_uci(move_str)
                print(f"AI move object: {move}")
                print(f"Legal moves: {list(self.engine.board.legal_moves)}")
                if move in self.engine.board.legal_moves:
                    print(f"AI making move: {move_str}")
                    self.engine.board.push(move)
                    print(f"New FEN after move: {self.engine.board.fen()}")
                    return True
                else:
                    print(f"Move {move_str} not in legal moves!")
            else:
                print("AI could not find any move!")
        except Exception as e:
            print(f"Error making AI move: {e}")
            import traceback
            traceback.print_exc()
        return False

    def is_ai_turn(self, game_mode: str) -> bool:
        """Check if it's AI's turn"""
        if game_mode == "human_vs_ai":
            # Human plays as white, AI plays as black
            # board.turn = True for white, False for black
            return not self.engine.board.turn  # AI's turn when it's black (False)
        elif game_mode == "ai_vs_ai":
            # AI plays both sides
            return True
        elif game_mode == "human_vs_human":
            # Both players are human
            return False
        return False

    def validate_move(self, exercise: ExerciseState, target_square: str) -> bool:
        """Validate if a move is correct for the exercise"""
        if exercise.exercise_type in ["basic_forward", "initial_double", "capture", "blocked", "en_passant"]:
            return target_square in exercise.target_squares
        elif exercise.exercise_type in ["basic", "capture"]:
            return target_square in exercise.target_squares
        elif exercise.exercise_type in ["human_vs_ai", "ai_vs_ai", "human_vs_human"]:
            # For gameplay, check if the move is legal in chess
            return target_square in self.engine.board.legal_moves
        return False

# Global instances
chess_engine = ChessEngine()
lesson_engine = LessonEngine()
