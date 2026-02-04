# src/education/lesson_core.py - Headless chess lesson logic for API backend

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal, Any
import uuid

import chess


# ---- Core data models (internal, not Pydantic) ----

@dataclass
class ModuleInfo:
    id: str
    name: str
    description: str
    icon: str


@dataclass
class ExerciseState:
    module_id: str
    board_fen: str
    highlights: List[str] = field(default_factory=list)
    selected_square: Optional[str] = None
    instructions: str = ""
    feedback_message: Optional[str] = None
    is_correct: Optional[bool] = None
    progress_current: int = 0
    progress_total: int = 0
    hint_available: bool = True
    module_completed: bool = False


@dataclass
class SessionState:
    session_id: str
    module_id: str
    current_exercise_index: int = 0
    total_exercises: int = 0
    correct_moves: int = 0
    total_attempts: int = 0
    completed: bool = False


# ---- Base lesson abstraction ----

class BaseLesson:
    """Abstract base for all chess lessons.

    This class is **headless**: it contains no pygame logic and is safe to use in FastAPI.
    """

    module_id: str

    def __init__(self, module_id: str):
        self.module_id = module_id

    def get_state(self) -> ExerciseState:
        raise NotImplementedError

    def handle_action(self, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        raise NotImplementedError


# ---- Pawn movement lesson (ported from PawnMovementState core ideas) ----

class PawnLesson(BaseLesson):
    """Teaches pawn movement using simplified exercises.

    This is a headless version inspired by src/states/pawn_movement_state.PawnMovementState.
    It focuses on reproducing the *learning behaviour* (what is correct / incorrect) rather
    than the exact visual animations.
    """

    def __init__(self, module_id: str = "pawn_movement"):
        super().__init__(module_id)

        # Lesson configuration
        self.exercises_per_type = 3
        self.movement_types = [
            "basic_forward",
            "initial_double",
            "capture",
            "blocked",
        ]

        # Progress tracking
        self.current_exercise = 0
        self.current_type_index = 0
        self.correct_moves = 0
        self.total_attempts = 0

        # Internal chess state
        self.board: chess.Board = chess.Board()
        self.current_pawn_square: Optional[int] = None
        self.target_squares: List[int] = []
        self.invalid_squares: List[int] = []

        # Feedback state
        self.feedback_message: Optional[str] = None
        self.is_correct: Optional[bool] = None
        self.show_hint: bool = False

        # Instructions per type
        self.instructions_map: Dict[str, str] = {
            "basic_forward": "Pawns move forward one square. Click where this pawn can move.",
            "initial_double": "Pawns can move two squares forward from their starting position.",
            "capture": "Pawns capture diagonally forward. Click where this pawn can capture.",
            "blocked": "Pawns cannot move if blocked. Is this pawn blocked? If it can move, click the square. If not, click the pawn.",
        }

        # Prepare first exercise
        self._generate_exercise()

    # ---- Exercise generation ----

    def _generate_exercise(self) -> None:
        """Generate a new exercise based on current_type_index and counters."""
        self.feedback_message = None
        self.is_correct = None
        self.show_hint = False
        self.target_squares = []
        self.invalid_squares = []

        # Determine current type
        if self.current_type_index >= len(self.movement_types):
            # All types done – mark completed
            return

        self.exercise_type = self.movement_types[self.current_type_index]

        # Create base empty board
        self.board = chess.Board()
        self.board.clear()
        self.current_pawn_square = None

        if self.exercise_type == "basic_forward":
            self._generate_basic_forward()
        elif self.exercise_type == "initial_double":
            self._generate_initial_double()
        elif self.exercise_type == "capture":
            self._generate_capture()
        elif self.exercise_type == "blocked":
            self._generate_blocked()

    def _generate_basic_forward(self) -> None:
        import random

        pawn_file = random.randint(1, 6)  # avoid edges
        pawn_rank = random.randint(2, 5)  # middle ranks
        pawn_square = chess.square(pawn_file, pawn_rank)

        self.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        self.current_pawn_square = pawn_square

        target_square = pawn_square + 8
        if target_square <= 63:
            self.target_squares = [target_square]

        # Non-legal but tempting squares
        self.invalid_squares = []
        backward = pawn_square - 8
        if 0 <= backward <= 63:
            self.invalid_squares.append(backward)
        if pawn_file < 7:
            self.invalid_squares.append(chess.square(pawn_file + 1, pawn_rank))
        if pawn_file > 0:
            self.invalid_squares.append(chess.square(pawn_file - 1, pawn_rank))

    def _generate_initial_double(self) -> None:
        import random

        pawn_file = random.randint(0, 7)
        pawn_rank = 1  # rank 2 (0-based index 1)
        pawn_square = chess.square(pawn_file, pawn_rank)
        self.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        self.current_pawn_square = pawn_square

        one_step = pawn_square + 8
        two_step = pawn_square + 16
        self.target_squares = [one_step, two_step]
        self.invalid_squares = []

    def _generate_capture(self) -> None:
        import random

        pawn_file = random.randint(1, 6)
        pawn_rank = random.randint(1, 5)
        pawn_square = chess.square(pawn_file, pawn_rank)
        self.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        self.current_pawn_square = pawn_square

        # Place an enemy piece diagonally forward
        capture_dirs = []
        if pawn_file > 0:
            capture_dirs.append(-1)
        if pawn_file < 7:
            capture_dirs.append(1)
        capture_file_offset = random.choice(capture_dirs)

        target_square = chess.square(pawn_file + capture_file_offset, pawn_rank + 1)
        self.board.set_piece_at(target_square, chess.Piece(chess.PAWN, chess.BLACK))
        self.target_squares = [target_square]

        # Invalid squares: straight ahead or opposite diagonal
        self.invalid_squares = []
        straight = pawn_square + 8
        if 0 <= straight <= 63:
            self.invalid_squares.append(straight)
        other_diag_file = pawn_file - capture_file_offset
        if 0 <= other_diag_file <= 7:
            other_diag = chess.square(other_diag_file, pawn_rank + 1)
            if other_diag != target_square:
                self.invalid_squares.append(other_diag)

    def _generate_blocked(self) -> None:
        import random

        pawn_file = random.randint(1, 6)
        pawn_rank = random.randint(2, 5)
        pawn_square = chess.square(pawn_file, pawn_rank)
        self.board.set_piece_at(pawn_square, chess.Piece(chess.PAWN, chess.WHITE))
        self.current_pawn_square = pawn_square

        # 50% chance blocked, 50% not blocked
        blocked = random.choice([True, False])
        one_step = pawn_square + 8
        if blocked and one_step <= 63:
            self.board.set_piece_at(one_step, chess.Piece(chess.PAWN, chess.WHITE))
            # No legal targets when blocked; correct answer is clicking the pawn itself
            self.target_squares = [pawn_square]
        else:
            # Not blocked: normal forward move is legal
            if one_step <= 63:
                self.target_squares = [one_step]
        self.invalid_squares = []

    # ---- Public API for lesson ----

    def _current_instructions(self) -> str:
        return self.instructions_map.get(self.exercise_type, "")

    def get_state(self) -> ExerciseState:
        total_exercises = len(self.movement_types) * self.exercises_per_type
        module_completed = self.current_exercise >= total_exercises

        highlights: List[str] = []
        if self.current_pawn_square is not None:
            highlights.append(chess.square_name(self.current_pawn_square))

        return ExerciseState(
            module_id=self.module_id,
            board_fen=self.board.fen(),
            highlights=highlights,
            selected_square=None,
            instructions=self._current_instructions(),
            feedback_message=self.feedback_message,
            is_correct=self.is_correct,
            progress_current=min(self.current_exercise, total_exercises),
            progress_total=total_exercises,
            hint_available=True,
            module_completed=module_completed,
        )

    def _advance_exercise_counter(self) -> None:
        self.current_exercise += 1
        if self.current_exercise % self.exercises_per_type == 0:
            self.current_type_index += 1

    def handle_action(self, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        self.total_attempts += 1

        if action_type == "select_square":
            square_name = payload.get("square")
            try:
                square_index = chess.parse_square(square_name)
            except Exception:
                self.feedback_message = "Invalid square."
                self.is_correct = False
                return self.get_state()

            if square_index in self.target_squares:
                self.correct_moves += 1
                self.is_correct = True
                self.feedback_message = "Great job! That is a correct pawn move."
                self._advance_exercise_counter()
                self._generate_exercise()
            else:
                self.is_correct = False
                self.feedback_message = "Not quite. Try a different square for this pawn."

        elif action_type == "hint":
            self.show_hint = True
            hint_squares = [chess.square_name(sq) for sq in self.target_squares]
            if hint_squares:
                self.feedback_message = f"Hint: look at square(s) {', '.join(hint_squares)}."
            else:
                self.feedback_message = "For this exercise, think about whether the pawn can move at all."
            self.is_correct = None

        elif action_type in {"skip", "next"}:
            self.feedback_message = "Skipping to the next exercise."
            self.is_correct = None
            self._advance_exercise_counter()
            self._generate_exercise()

        elif action_type == "back":
            # In lesson context, treat as no-op; higher level can handle navigation
            self.feedback_message = "Returning to the module menu."
            self.is_correct = None

        return self.get_state()


# ---- Identify Pieces Lesson ----

class IdentifyPiecesLesson(BaseLesson):
    """Teaches piece identification using multiple choice questions."""

    def __init__(self, module_id: str = "identify_pieces"):
        super().__init__(module_id)
        self.questions_per_session = 12
        self.current_question = 0
        self.correct_answers = 0
        self.total_attempts = 0
        
        self.piece_names = {
            chess.PAWN: "Pawn",
            chess.KNIGHT: "Knight",
            chess.BISHOP: "Bishop",
            chess.ROOK: "Rook",
            chess.QUEEN: "Queen",
            chess.KING: "King"
        }
        
        self.board = chess.Board()
        self.current_square: Optional[int] = None
        self.current_piece_type: Optional[int] = None
        self.options: List[str] = []
        self.correct_option_index: int = -1
        self.feedback_message: Optional[str] = None
        self.is_correct: Optional[bool] = None
        
        self._generate_exercise()

    def _generate_exercise(self) -> None:
        if self.current_question >= self.questions_per_session:
            return

        import random
        # Reset board to starting position
        self.board = chess.Board()
        
        # Pick a random piece type and color
        piece_type = random.choice(list(self.piece_names.keys()))
        color = random.choice([chess.WHITE, chess.BLACK])
        
        # Find squares with this piece
        squares = [s for s in chess.SQUARES if self.board.piece_at(s) and 
                   self.board.piece_at(s).piece_type == piece_type and 
                   self.board.piece_at(s).color == color]
        
        if not squares:
            # Fallback (shouldn't happen on starting board)
            self._generate_exercise()
            return
            
        self.current_square = random.choice(squares)
        self.current_piece_type = piece_type
        
        # Generate options
        correct_name = self.piece_names[piece_type]
        other_names = [name for pt, name in self.piece_names.items() if pt != piece_type]
        wrong_answers = random.sample(other_names, 3)
        
        self.options = [correct_name] + wrong_answers
        random.shuffle(self.options)
        self.correct_option_index = self.options.index(correct_name)
        
        self.feedback_message = None
        self.is_correct = None

    def get_state(self) -> ExerciseState:
        module_completed = self.current_question >= self.questions_per_session
        highlights = [chess.square_name(self.current_square)] if self.current_square is not None else []
        
        # We use instructions to pass the multiple choice options as well
        # In a real app, we might add an 'options' field to ExerciseState
        options_str = ",".join(self.options)
        instructions = f"What is the highlighted piece?|{options_str}"
        
        return ExerciseState(
            module_id=self.module_id,
            board_fen=self.board.fen(),
            highlights=highlights,
            instructions=instructions,
            feedback_message=self.feedback_message,
            is_correct=self.is_correct,
            progress_current=min(self.current_question, self.questions_per_session),
            progress_total=self.questions_per_session,
            module_completed=module_completed
        )

    def handle_action(self, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        self.total_attempts += 1
        
        if action_type == "select_option":
            option_index = payload.get("index")
            if option_index == self.correct_option_index:
                self.correct_answers += 1
                self.is_correct = True
                self.feedback_message = f"Correct! That is a {self.options[option_index]}."
                self.current_question += 1
                self._generate_exercise()
            else:
                self.is_correct = False
                self.feedback_message = f"Wrong. That is not a {self.options[option_index]}."
        
        elif action_type == "hint":
            hints = {
                chess.PAWN: "This is the smallest piece that moves forward.",
                chess.KNIGHT: "This piece looks like a horse and moves in an L-shape.",
                chess.BISHOP: "This piece moves diagonally on the board.",
                chess.ROOK: "This piece looks like a castle tower and moves in straight lines.",
                chess.QUEEN: "The most powerful piece, combining rook and bishop moves.",
                chess.KING: "The most important piece – losing it means the game is over."
            }
            if self.current_piece_type is not None:
                self.feedback_message = hints.get(self.current_piece_type, "Look carefully at the shape of the piece.")
            else:
                self.feedback_message = "Look carefully at the shape of the piece."
            self.is_correct = None
        
        elif action_type in {"skip", "next"}:
            self.current_question += 1
            self._generate_exercise()
            
        return self.get_state()


# ---- Rook/Bishop/Knight/Queen/King Movement Lesson ----

class PieceMovementLesson(BaseLesson):
    """Generic lesson for piece movements."""

    def __init__(self, piece_type: int, module_id: str):
        super().__init__(module_id)
        self.piece_type = piece_type
        self.exercises_per_type = 3
        self.types = ["basic", "capture", "blocked"]
        self.current_type_index = 0
        self.current_exercise_in_type = 0
        self.current_exercise = 0
        
        self.board = chess.Board()
        self.current_square: Optional[int] = None
        self.target_squares: List[int] = []
        self.feedback_message: Optional[str] = None
        self.is_correct: Optional[bool] = None
        
        self.piece_name = {
            chess.ROOK: "Rook",
            chess.KNIGHT: "Knight",
            chess.BISHOP: "Bishop",
            chess.QUEEN: "Queen",
            chess.KING: "King"
        }[piece_type]

        self._generate_exercise()

    def _generate_exercise(self) -> None:
        if self.current_type_index >= len(self.types):
            return

        import random
        self.board = chess.Board()
        self.board.clear()
        
        exercise_type = self.types[self.current_type_index]
        
        # Place piece in center area
        self.current_square = chess.square(random.randint(2, 5), random.randint(2, 5))
        self.board.set_piece_at(self.current_square, chess.Piece(self.piece_type, chess.WHITE))
        
        if exercise_type == "basic":
            # Just move to any legal square
            self.target_squares = list(self.board.legal_moves)
            self.target_squares = [m.to_square for m in self.board.legal_moves]
            self.instructions = f"Click any square the {self.piece_name} can move to."
            
        elif exercise_type == "capture":
            # Place an enemy piece to capture
            legal_moves = list(self.board.legal_moves)
            if not legal_moves:
                self._generate_exercise()
                return
            target_move = random.choice(legal_moves)
            self.board.set_piece_at(target_move.to_square, chess.Piece(chess.PAWN, chess.BLACK))
            self.target_squares = [target_move.to_square]
            self.instructions = f"Capture the black pawn with your {self.piece_name}."
            
        elif exercise_type == "blocked":
            # Place a friendly piece blocking some moves
            legal_moves = list(self.board.legal_moves)
            if not legal_moves:
                self._generate_exercise()
                return
            block_move = random.choice(legal_moves)
            self.board.set_piece_at(block_move.to_square, chess.Piece(chess.PAWN, chess.WHITE))
            # New legal moves after blocking
            self.target_squares = [m.to_square for m in self.board.legal_moves]
            self.instructions = f"Some squares are blocked by your own pawn. Click a valid square for the {self.piece_name}."

        self.feedback_message = None
        self.is_correct = None

    def get_state(self) -> ExerciseState:
        total = len(self.types) * self.exercises_per_type
        module_completed = self.current_exercise >= total
        highlights = [chess.square_name(self.current_square)] if self.current_square is not None else []
        
        return ExerciseState(
            module_id=self.module_id,
            board_fen=self.board.fen(),
            highlights=highlights,
            instructions=self.instructions,
            feedback_message=self.feedback_message,
            is_correct=self.is_correct,
            progress_current=min(self.current_exercise, total),
            progress_total=total,
            module_completed=module_completed
        )

    def handle_action(self, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        # Check if module is already completed
        total = len(self.types) * self.exercises_per_type
        module_completed = self.current_exercise >= total
        
        if action_type == "select_square":
            # Don't process if already completed
            if module_completed:
                self.feedback_message = "Lesson completed! Go back to select another lesson."
                return self.get_state()
                
            sq_name = payload.get("square")
            sq = chess.parse_square(sq_name)
            if sq in self.target_squares:
                self.is_correct = True
                self.feedback_message = "Correct move!"
                self.current_exercise += 1
                self.current_exercise_in_type += 1
                if self.current_exercise_in_type >= self.exercises_per_type:
                    self.current_type_index += 1
                    self.current_exercise_in_type = 0
                self._generate_exercise()
            else:
                self.is_correct = False
                self.feedback_message = f"The {self.piece_name} cannot move there."
        
        elif action_type == "hint":
            if self.target_squares:
                squares = ", ".join(chess.square_name(sq) for sq in self.target_squares[:4])
                self.feedback_message = f"Hint: try moving the {self.piece_name} towards {squares}."
            else:
                self.feedback_message = f"Think about how a {self.piece_name} normally moves."
            self.is_correct = None
        
        elif action_type in {"skip", "next"}:
            # Don't process if already completed
            if module_completed:
                self.feedback_message = "Lesson completed! Go back to select another lesson."
                return self.get_state()
                
            self.current_exercise += 1
            self.current_exercise_in_type += 1
            if self.current_exercise_in_type >= self.exercises_per_type:
                self.current_type_index += 1
                self.current_exercise_in_type = 0
            self._generate_exercise()
            
        return self.get_state()


# ---- Play vs AI Lesson ----

class PlayVsAILesson(BaseLesson):
    """Full game play against the custom AI."""

    def __init__(self, module_id: str = "play_vs_ai"):
        super().__init__(module_id)
        # We need the custom engine and AI
        from states import engine as ChessEngine
        from states import chessAi as ChessAI
        
        self.ChessEngine = ChessEngine
        self.gs = ChessEngine.GameState()
        self.ChessAI = ChessAI
        self.feedback_message = "Your turn (White). Good luck!"
        self.is_correct = None
        self.selected_sq: Optional[tuple] = None
        # Mode: controls who is human vs AI
        # human_vs_ai: White = human, Black = AI
        # ai_vs_ai: both AI
        # human_vs_human: both human
        self.mode: str = "human_vs_ai"
        self.white_is_human = True
        self.black_is_human = False
    def _board_to_fen(self) -> str:
        # Convert custom engine board to FEN for frontend
        rows = []
        for r in range(8):
            empty = 0
            row_str = ""
            for c in range(8):
                p = self.gs.board[r][c]
                if p == "--":
                    empty += 1
                else:
                    if empty > 0:
                        row_str += str(empty)
                        empty = 0
                    # 'wp' -> 'P', 'bN' -> 'n'
                    char = p[1].upper() if p[0] == 'w' else p[1].lower()
                    row_str += char
            if empty > 0:
                row_str += str(empty)
            rows.append(row_str)
        
        fen = "/".join(rows)
        turn = "w" if self.gs.whiteToMove else "b"
        return f"{fen} {turn} KQkq - 0 1"

    def _is_human_turn(self) -> bool:
        if self.gs.whiteToMove:
            return self.white_is_human
        return self.black_is_human

    def _maybe_ai_move(self) -> None:
        """Let AI make one move if it's AI's turn in the current mode."""
        if self.gs.checkmate or self.gs.stalemate:
            return
        # If it's human's turn for the side to move, stop
        if self._is_human_turn():
            return

        # AI move
        valid_moves = self.gs.getValidMoves()
        if not valid_moves:
            return
        ai_move = self.ChessAI.findBestMove(self.gs, valid_moves, None)
        if ai_move is None:
            ai_move = self.ChessAI.findRandomMove(valid_moves)
        self.gs.makeMove(ai_move)
        color = "White" if not self.gs.whiteToMove else "Black" # Side that just moved
        self.feedback_message = f"AI ({color}) moved {ai_move.getChessNotation()}."

    def get_state(self) -> ExerciseState:
        highlights: List[str] = []
        files = "abcdefgh"
        if self.selected_sq:
            # Selected square
            highlights.append(f"{files[self.selected_sq[1]]}{8 - self.selected_sq[0]}")
            # Also highlight all legal destination squares for this piece
            for move in self.gs.getValidMoves():
                if move.startRow == self.selected_sq[0] and move.startCol == self.selected_sq[1]:
                    highlights.append(f"{files[move.endCol]}{8 - move.endRow}")

        # Determine whose turn it is
        turn_actor = "Human" if self._is_human_turn() else "AI"
        turn_color = "White" if self.gs.whiteToMove else "Black"
        turn_info = f" | Turn: {turn_actor}({turn_color})"

        mode_label = {
            "human_vs_ai": "Mode: Human vs AI (You are White)",
            "ai_vs_ai": "Mode: AI vs AI",
            "human_vs_human": "Mode: Human vs Human",
        }.get(self.mode, "Game Play") + turn_info

        return ExerciseState(
            module_id=self.module_id,
            board_fen=self._board_to_fen(),
            highlights=highlights,
            instructions=mode_label,
            feedback_message=self.feedback_message,
            is_correct=self.is_correct,
            progress_current=0, # Game play doesn't have a fixed progress
            progress_total=100,
            module_completed=self.gs.checkmate or self.gs.stalemate
        )

    def handle_action(self, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        if action_type == "set_mode":
            mode = payload.get("mode")
            if mode in {"human_vs_ai", "ai_vs_ai", "human_vs_human"}:
                self.mode = mode
                if mode == "human_vs_ai":
                    self.white_is_human = True
                    self.black_is_human = False
                    self.feedback_message = "Mode: Human vs AI. You are White."
                elif mode == "ai_vs_ai":
                    self.white_is_human = False
                    self.black_is_human = False
                    self.feedback_message = "Mode: AI vs AI."
                elif mode == "human_vs_human":
                    self.white_is_human = True
                    self.black_is_human = True
                    self.feedback_message = "Mode: Human vs Human. Both sides are manual."
                # After changing mode, let AI move if needed (e.g., AI vs AI and it's AI turn)
                self._maybe_ai_move()
            return self.get_state()

        if action_type == "select_square":
            from states import engine as ChessEngine
            sq_name = payload.get("square")
            row = 8 - int(sq_name[1])
            col = ord(sq_name[0]) - ord('a')

            # If it's not a human turn in current mode, ignore clicks
            if not self._is_human_turn():
                self.feedback_message = "It's AI's turn right now."
                return self.get_state()
            
            if not self.selected_sq:
                # First click
                piece = self.gs.board[row][col]
                if piece != "--" and piece[0] == ('w' if self.gs.whiteToMove else 'b'):
                    self.selected_sq = (row, col)
                    self.feedback_message = f"Selected {sq_name}. Now click target square."
                else:
                    self.feedback_message = "Select one of your pieces first."
            else:
                # Second click - try to move
                move = ChessEngine.Move(self.selected_sq, (row, col), self.gs.board)
                valid_moves = self.gs.getValidMoves()
                
                if move in valid_moves:
                    self.gs.makeMove(move)
                    self.selected_sq = None
                    self.feedback_message = "Move played."
                    # After a human move, let AI respond if needed
                    self._maybe_ai_move()
                else:
                    # Invalid move or re-selecting same piece
                    piece = self.gs.board[row][col]
                    if piece != "--" and piece[0] == ('w' if self.gs.whiteToMove else 'b'):
                        self.selected_sq = (row, col)
                        self.feedback_message = f"Selected {sq_name}."
                    else:
                        self.selected_sq = None
                        self.feedback_message = "Invalid move."
                        self.is_correct = False
        
        elif action_type == "next":
            # In AI vs AI mode, advance the game by one AI move (or pair of moves)
            self._maybe_ai_move()
        
        elif action_type == "hint":
            self.feedback_message = "General tip: control the center, develop your minor pieces, and keep your king safe."
            self.is_correct = None

        if self.gs.checkmate:
            winner = "Black" if self.gs.whiteToMove else "White"
            self.feedback_message = f"Checkmate! {winner} wins."
        elif self.gs.stalemate:
            self.feedback_message = "Stalemate!"
            
        return self.get_state()


# ---- Board Setup Lesson ----

class BoardSetupLesson(BaseLesson):
    """Teaches how to set up the board."""

    def __init__(self, module_id: str = "board_setup"):
        super().__init__(module_id)
        self.board = chess.Board()
        self.board.clear()
        self.correct_board = chess.Board()
        
        self.pieces_to_place = [
            (chess.PAWN, chess.WHITE, "Place all white pawns on the 2nd rank."),
            (chess.ROOK, chess.WHITE, "Place white rooks in the corners (a1 and h1)."),
            (chess.KNIGHT, chess.WHITE, "Place white knights next to rooks (b1 and g1)."),
            (chess.BISHOP, chess.WHITE, "Place white bishops next to knights (c1 and f1)."),
            (chess.QUEEN, chess.WHITE, "Place the white queen on her color (d1)."),
            (chess.KING, chess.WHITE, "Place the white king on e1."),
        ]
        self.current_step = 0
        self.feedback_message = self.pieces_to_place[0][2]
        self.is_correct = None

    def get_state(self) -> ExerciseState:
        module_completed = self.current_step >= len(self.pieces_to_place)
        return ExerciseState(
            module_id=self.module_id,
            board_fen=self.board.fen(),
            instructions=self.feedback_message if not module_completed else "Board setup complete!",
            feedback_message=self.feedback_message,
            is_correct=self.is_correct,
            progress_current=min(self.current_step, len(self.pieces_to_place)),
            progress_total=len(self.pieces_to_place),
            module_completed=module_completed
        )

    def handle_action(self, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        if action_type == "select_square":
            sq_name = payload.get("square")
            sq = chess.parse_square(sq_name)
            expected_piece = self.correct_board.piece_at(sq)
            
            # Step-specific logic
            step_piece_type, step_color, _ = self.pieces_to_place[self.current_step]
            
            if expected_piece and expected_piece.piece_type == step_piece_type and \
               expected_piece.color == step_color:
                if not self.board.piece_at(sq):
                    self.board.set_piece_at(sq, expected_piece)
                    self.is_correct = True
                    
                    # Verify if all pieces of this type/color are placed
                    missing = False
                    for s in chess.SQUARES:
                        cp = self.correct_board.piece_at(s)
                        if cp and cp.piece_type == step_piece_type and cp.color == step_color:
                            if not self.board.piece_at(s):
                                missing = True
                                break
                    
                    if not missing:
                        self.current_step += 1
                        if self.current_step < len(self.pieces_to_place):
                            self.feedback_message = f"Great! {self.pieces_to_place[self.current_step][2]}"
                        else:
                            self.feedback_message = "Excellent! You've set up all white pieces correctly."
                    else:
                        self.feedback_message = "Good! Keep placing the remaining pieces for this step."
                else:
                    self.feedback_message = "This piece is already placed."
            else:
                self.is_correct = False
                self.feedback_message = "That's not where that piece goes."
        
        elif action_type == "hint":
            step_piece_type, _, text = self.pieces_to_place[self.current_step]
            piece_label = {
                chess.PAWN: "pawns",
                chess.ROOK: "rooks",
                chess.KNIGHT: "knights",
                chess.BISHOP: "bishops",
                chess.QUEEN: "queen",
                chess.KING: "king",
            }.get(step_piece_type, "pieces")
            self.feedback_message = f"Hint: {text} Look where the {piece_label} start in a normal game."
            self.is_correct = None
                
        return self.get_state()


# ---- Special Moves Lesson ----

class SpecialMovesLesson(BaseLesson):
    """Teaches castling and en passant."""

    def __init__(self, module_id: str = "special_moves"):
        super().__init__(module_id)
        self.exercises = ["kingside_castle", "queenside_castle", "en_passant"]
        self.current_index = 0
        self.board = chess.Board()
        self.feedback_message = ""
        self.is_correct = None
        self._generate_exercise()

    def _generate_exercise(self) -> None:
        if self.current_index >= len(self.exercises):
            return

        ex = self.exercises[self.current_index]
        self.board = chess.Board()
        self.board.clear()
        
        if ex == "kingside_castle":
            self.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            self.board.set_piece_at(chess.H1, chess.Piece(chess.ROOK, chess.WHITE))
            self.instructions = "Castling: Move the White King to g1 to castle kingside."
            self.target_sq = chess.G1
        elif ex == "queenside_castle":
            self.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            self.board.set_piece_at(chess.A1, chess.Piece(chess.ROOK, chess.WHITE))
            self.instructions = "Castling: Move the White King to c1 to castle queenside."
            self.target_sq = chess.C1
        elif ex == "en_passant":
            self.board.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.WHITE))
            self.board.set_piece_at(chess.D5, chess.Piece(chess.PAWN, chess.BLACK))
            # We need to set en passant square in python-chess
            self.board.ep_square = chess.D6
            self.instructions = "En Passant: The black pawn just moved two squares. Capture it by moving your pawn to d6."
            self.target_sq = chess.D6

    def get_state(self) -> ExerciseState:
        module_completed = self.current_index >= len(self.exercises)
        return ExerciseState(
            module_id=self.module_id,
            board_fen=self.board.fen(),
            instructions=self.instructions if not module_completed else "Special moves mastered!",
            feedback_message=self.feedback_message,
            is_correct=self.is_correct,
            progress_current=min(self.current_index, len(self.exercises)),
            progress_total=len(self.exercises),
            module_completed=module_completed
        )

    def handle_action(self, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        if action_type == "select_square":
            sq_name = payload.get("square")
            sq = chess.parse_square(sq_name)
            if sq == self.target_sq:
                self.is_correct = True
                self.feedback_message = "Correct! You performed the special move."
                self.current_index += 1
                self._generate_exercise()
            else:
                self.is_correct = False
                self.feedback_message = "Try again. Move to the correct square."
        
        elif action_type == "hint":
            self.feedback_message = "Remember: castling moves the king two squares towards the rook, and en passant captures a pawn that just moved two squares."
            self.is_correct = None
        return self.get_state()


# ---- Checkmate and Stalemate Lesson ----

class CheckmateStalemateLesson(BaseLesson):
    """Teaches identification of checkmate and stalemate."""

    def __init__(self, module_id: str = "checkmate_stalemate"):
        super().__init__(module_id)
        self.exercises = ["checkmate", "stalemate"]
        self.current_index = 0
        self.board = chess.Board()
        self.feedback_message = ""
        self.is_correct = None
        self._generate_exercise()

    def _generate_exercise(self) -> None:
        if self.current_index >= len(self.exercises):
            return

        ex = self.exercises[self.current_index]
        self.board = chess.Board()
        self.board.clear()
        
        if ex == "checkmate":
            # Fool's mate style
            self.board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
            self.board.set_piece_at(chess.H4, chess.Piece(chess.QUEEN, chess.BLACK))
            self.board.set_piece_at(chess.F2, chess.Piece(chess.PAWN, chess.WHITE))
            self.board.set_piece_at(chess.G2, chess.Piece(chess.PAWN, chess.WHITE))
            self.instructions = "Is this checkmate? Click 'Next' if yes."
        elif ex == "stalemate":
            # Simple stalemate
            self.board.set_piece_at(chess.A8, chess.Piece(chess.KING, chess.BLACK))
            self.board.set_piece_at(chess.C7, chess.Piece(chess.QUEEN, chess.WHITE))
            self.board.set_piece_at(chess.C1, chess.Piece(chess.KING, chess.WHITE))
            self.instructions = "Is this stalemate? Click 'Next' if yes."

    def get_state(self) -> ExerciseState:
        module_completed = self.current_index >= len(self.exercises)
        return ExerciseState(
            module_id=self.module_id,
            board_fen=self.board.fen(),
            instructions=self.instructions if not module_completed else "Mastered!",
            feedback_message=self.feedback_message,
            is_correct=self.is_correct,
            progress_current=min(self.current_index, len(self.exercises)),
            progress_total=len(self.exercises),
            module_completed=module_completed
        )

    def handle_action(self, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        # Check if module is already completed
        module_completed = self.current_index >= len(self.exercises)
        
        if action_type in {"next", "skip"}:
            # Don't process if already completed
            if module_completed:
                self.feedback_message = "Lesson completed! Go back to select another lesson."
                return self.get_state()
                
            self.current_index += 1
            self._generate_exercise()
            self.is_correct = True
        
        elif action_type == "hint":
            if self.current_index == 0:
                self.feedback_message = "Checkmate: the king is in check and has no legal moves."
            else:
                self.feedback_message = "Stalemate: the player has no legal moves but is not in check."
            self.is_correct = None
        return self.get_state()


# ---- Session manager ----

class LessonSession:
    def __init__(self, module_id: str, lesson: BaseLesson):
        self.session_id: str = str(uuid.uuid4())
        self.module_id: str = module_id
        self.lesson: BaseLesson = lesson
        self.state: SessionState = SessionState(
            session_id=self.session_id,
            module_id=module_id,
            current_exercise_index=0,
            total_exercises=0,
            correct_moves=0,
            total_attempts=0,
            completed=False,
        )

    def get_exercise_state(self) -> ExerciseState:
        return self.lesson.get_state()

    def apply_action(self, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        return self.lesson.handle_action(action_type, payload)


class LessonSessionManager:
    """In-memory session manager for all chess lessons."""

    def __init__(self):
        self.sessions: Dict[str, LessonSession] = {}

    def create_session(self, module_id: str) -> LessonSession:
        lesson: BaseLesson
        
        if module_id == "pawn_movement":
            lesson = PawnLesson()
        elif module_id == "identify_pieces":
            lesson = IdentifyPiecesLesson()
        elif module_id == "board_setup":
            lesson = BoardSetupLesson()
        elif module_id == "rook_movement":
            lesson = PieceMovementLesson(chess.ROOK, module_id)
        elif module_id == "knight_movement":
            lesson = PieceMovementLesson(chess.KNIGHT, module_id)
        elif module_id == "bishop_movement":
            lesson = PieceMovementLesson(chess.BISHOP, module_id)
        elif module_id == "queen_movement":
            lesson = PieceMovementLesson(chess.QUEEN, module_id)
        elif module_id == "king_movement":
            lesson = PieceMovementLesson(chess.KING, module_id)
        elif module_id == "play_vs_ai":
            lesson = PlayVsAILesson()
        elif module_id == "special_moves":
            lesson = SpecialMovesLesson()
        elif module_id == "checkmate_stalemate":
            lesson = CheckmateStalemateLesson()
        else:
            # Fallback
            lesson = PawnLesson(module_id)

        session = LessonSession(module_id, lesson)
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[LessonSession]:
        return self.sessions.get(session_id)

    def complete_session(self, session_id: str) -> Optional[SessionState]:
        session = self.sessions.get(session_id)
        if not session:
            return None
        session.state.completed = True
        return session.state


# ---- Module registry (metadata only) ----

MODULES: List[ModuleInfo] = [
    ModuleInfo(
        id="identify_pieces",
        name="Identify Pieces",
        description="Learn to recognize each chess piece",
        icon="pawn",
    ),
    ModuleInfo(
        id="board_setup",
        name="Board Setup",
        description="Learn how to set up the chess board",
        icon="rook",
    ),
    ModuleInfo(
        id="pawn_movement",
        name="Pawn Movement",
        description="Master how pawns move and capture",
        icon="pawn",
    ),
    ModuleInfo(
        id="knight_movement",
        name="Knight Movement",
        description="Learn the knight's special L-shaped move",
        icon="knight",
    ),
    ModuleInfo(
        id="rook_movement",
        name="Rook Movement",
        description="Learn the rook's straight-line power",
        icon="rook",
    ),
    ModuleInfo(
        id="bishop_movement",
        name="Bishop Movement",
        description="Practice bishop diagonals",
        icon="bishop",
    ),
    ModuleInfo(
        id="queen_movement",
        name="Queen Movement",
        description="Combine rook and bishop powers with the queen",
        icon="queen",
    ),
    ModuleInfo(
        id="king_movement",
        name="King Movement",
        description="Learn how the king moves and handles check",
        icon="king",
    ),
    ModuleInfo(
        id="special_moves",
        name="Special Moves",
        description="Castling, en passant, and promotion",
        icon="pawn",
    ),
    ModuleInfo(
        id="checkmate_stalemate",
        name="Checkmate and Stalemate",
        description="Understand check, checkmate, and stalemate",
        icon="king",
    ),
    ModuleInfo(
        id="play_vs_ai",
        name="Game Play",
        description="Play a simple game vs AI",
        icon="king",
    ),
]


def get_module_by_id(module_id: str) -> Optional[ModuleInfo]:
    for m in MODULES:
        if m.id == module_id:
            return m
    return None
