# chess_api.py - Complete Chess API Endpoints for Yoga Project
# This provides all pygame chess functionality as REST API endpoints

from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from chess_engine import (
    chess_engine, lesson_engine, ChessEngine, LessonEngine,
    ExerciseState, BoardPosition, ChessPiece, ChessSquare,
    PieceType, PieceColor
)
import chess

# ---- Pydantic Models for API ----

class ChessModuleInfo(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    total_exercises: int
    unlocked: bool

class ChessBoardLayout(BaseModel):
    squares: List[Dict[str, Any]]
    pieces: List[Dict[str, Any]]
    labels: Dict[str, List[str]]
    colors: Dict[str, str]

class ChessExerciseResponse(BaseModel):
    session_id: str
    exercise_id: str
    module_id: str
    exercise_type: str
    board_layout: ChessBoardLayout
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

class ChessActionRequest(BaseModel):
    type: str
    payload: Dict[str, Any] = {}

class ChessSessionCreateRequest(BaseModel):
    module_id: str

class ChessSessionSummary(BaseModel):
    session_id: str
    module_id: str
    completed: bool
    total_exercises: int
    completed_exercises: int
    accuracy: float

# ---- Session Management ----

class ChessSessionManager:
    """Manages chess learning sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.lesson_engine = LessonEngine()
    
    def create_session(self, module_id: str) -> str:
        """Create a new chess learning session"""
        session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "module_id": module_id,
            "current_exercise": 0,
            "total_exercises": self._get_total_exercises(module_id),
            "completed_exercises": 0,
            "correct_answers": 0,
            "total_attempts": 0,
            "current_exercise_state": None,
            "completed": False
        }
        
        self.sessions[session_id] = session_data
        
        # Create first exercise
        self._create_next_exercise(session_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.sessions.get(session_id)
    
    def _get_total_exercises(self, module_id: str) -> int:
        """Get total exercises for a module"""
        exercise_counts = {
            "identify_pieces": 12,
            "board_setup": 1,
            "pawn_movement": 15,
            "rook_movement": 9,
            "knight_movement": 9,
            "bishop_movement": 9,
            "queen_movement": 9,
            "king_movement": 9,
            "special_moves": 12,
            "check_checkmate_stalemate": 5,
            "gameplay": 3
        }
        return exercise_counts.get(module_id, 5)
    
    def _create_next_exercise(self, session_id: str) -> None:
        """Create the next exercise for a session"""
        session = self.sessions[session_id]
        module_id = session["module_id"]
        exercise_num = session["current_exercise"]
        
        # Stop creating exercises if module is completed
        if session.get("completed", False):
            return
        
        # Stop creating exercises when completed
        if session.get("completed_exercises", 0) >= session.get("total_exercises", 0):
            session["completed"] = True
            return
        
        try:
            if module_id == "identify_pieces":
                # Stop after 12 exercises (0-11)
                if exercise_num >= 12:
                    session["completed"] = True
                    return
                exercise = self.lesson_engine.create_identify_pieces_exercise(exercise_num)
                if exercise is None:
                    # Fallback to a simple exercise if creation fails
                    print(f"Warning: create_identify_pieces_exercise returned None for exercise_num {exercise_num}")
                    exercise = self.lesson_engine.create_pawn_exercise("basic_forward", 0)
                    exercise.module_id = "identify_pieces"
                    exercise.exercise_type = "identify_pieces"
                    exercise.exercise_id = f"identify_pieces_{exercise_num}"
                    exercise.progress_current = exercise_num
                    exercise.progress_total = 12
            elif module_id == "board_setup":
                exercise = self.lesson_engine.create_board_setup_exercise()
            elif module_id == "pawn_movement":
                # Cycle through pawn exercise types
                exercise_types = ["basic_forward", "initial_double", "capture", "blocked", "en_passant"]
                exercise_type = exercise_types[exercise_num % len(exercise_types)]
                exercise = self.lesson_engine.create_pawn_exercise(exercise_type, exercise_num)
            elif module_id == "knight_movement":
                # Cycle through knight exercise types
                exercise_types = ["basic", "capture"]
                exercise_type = exercise_types[exercise_num % len(exercise_types)]
                exercise = self.lesson_engine.create_knight_exercise(exercise_type, exercise_num)
            elif module_id == "rook_movement":
                # Cycle through rook exercise types
                exercise_types = ["basic"]
                exercise_type = exercise_types[exercise_num % len(exercise_types)]
                exercise = self.lesson_engine.create_rook_exercise(exercise_type, exercise_num)
            elif module_id == "bishop_movement":
                # Cycle through bishop exercise types
                exercise_types = ["basic", "capture"]
                exercise_type = exercise_types[exercise_num % len(exercise_types)]
                exercise = self.lesson_engine.create_bishop_exercise(exercise_type, exercise_num)
            elif module_id == "queen_movement":
                # Cycle through queen exercise types
                exercise_types = ["basic", "capture"]
                exercise_type = exercise_types[exercise_num % len(exercise_types)]
                exercise = self.lesson_engine.create_queen_exercise(exercise_type, exercise_num)
            elif module_id == "king_movement":
                # Cycle through king exercise types
                exercise_types = ["basic", "castling"]
                exercise_type = exercise_types[exercise_num % len(exercise_types)]
                exercise = self.lesson_engine.create_king_exercise(exercise_type, exercise_num)
            elif module_id == "special_moves":
                # Cycle through special moves exercise types
                exercise_types = ["castling", "promotion", "en_passant"]
                exercise_type = exercise_types[exercise_num % len(exercise_types)]
                exercise = self.lesson_engine.create_special_moves_exercise(exercise_type, exercise_num)
            elif module_id == "check_checkmate_stalemate":
                # Cycle through check/checkmate/stalemate exercise types
                exercise_types = ["check", "checkmate", "stalemate"]
                exercise_type = exercise_types[exercise_num % len(exercise_types)]
                exercise = self.lesson_engine.create_check_checkmate_stalemate_exercise(exercise_type, exercise_num)
            elif module_id == "gameplay":
                # Cycle through game modes
                game_modes = ["human_vs_ai", "ai_vs_ai", "human_vs_human"]
                game_mode = game_modes[exercise_num % len(game_modes)]
                exercise = self.lesson_engine.create_gameplay_exercise(game_mode, exercise_num)
            else:
                # Default to basic exercise for other modules
                exercise = self.lesson_engine.create_pawn_exercise("basic_forward", exercise_num)
            
            # Ensure exercise is not None before setting
            if exercise is None:
                print(f"Error: Exercise creation returned None for module {module_id}, exercise_num {exercise_num}")
                exercise = self.lesson_engine.create_pawn_exercise("basic_forward", 0)
            
            session["current_exercise_state"] = exercise
            
        except Exception as e:
            print(f"Error creating exercise for module {module_id}: {e}")
            import traceback
            traceback.print_exc()
            exercise = self.lesson_engine.create_pawn_exercise("basic_forward", 0)
            session["current_exercise_state"] = exercise
    
    def apply_action(self, session_id: str, action_type: str, payload: Dict[str, Any]) -> ExerciseState:
        """Apply an action to a session"""
        session = self.sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        exercise = session["current_exercise_state"]
        if not exercise:
            raise HTTPException(status_code=400, detail="No active exercise")
        
        session["total_attempts"] += 1
        
        if action_type == "set_game_mode":
            game_mode = payload.get("game_mode")
            if game_mode in ["human_vs_ai", "ai_vs_ai", "human_vs_human"]:
                # Update the exercise type to the specific game mode
                exercise.exercise_type = game_mode
                exercise.instructions = self._get_game_mode_instructions(game_mode)
                exercise.is_correct = True
                exercise.feedback_message = f"Game mode set to {game_mode.replace('_', ' ')}"
            else:
                exercise.is_correct = False
                exercise.feedback_message = "Invalid game mode"
        
        elif action_type == "start_gameplay":
            # Start gameplay with specific mode and difficulty
            game_mode = payload.get("game_mode", "human_vs_ai")
            difficulty = payload.get("difficulty", "beginner")
            
            # Create gameplay exercise with difficulty
            exercise = self.lesson_engine.create_gameplay_exercise(game_mode, 0, difficulty)
            
            # Initialize session state
            session["current_exercise"] = exercise
            session["current_exercise_state"] = exercise
            session["exercise_type"] = game_mode
            session["difficulty"] = difficulty
            session["completed_exercises"] = 0
            session["total_exercises"] = 3
            session["correct_answers"] = 0
            session["completed"] = False
            
            print(f"🎮 Started {game_mode} at {difficulty} difficulty level")
            
        elif action_type == "resign":
            # Player resigns
            current_turn = 'White' if self.lesson_engine.engine.board.turn else 'Black'
            winner = 'Black' if current_turn == 'White' else 'White'
            exercise.exercise_completed = True
            exercise.module_completed = True
            session["completed"] = True
            exercise.feedback_message = f"{current_turn} resigned! {winner} wins! 🏳️"
        
        elif action_type == "new_game":
            # Start a new game
            self.lesson_engine.engine.board.reset()
            exercise.board_position = self.lesson_engine.engine.get_board_position()
            exercise.selected_square = None
            exercise.exercise_completed = False
            exercise.module_completed = False
            session["completed"] = False
            exercise.feedback_message = "New game started! Good luck! 🎮"
        
        elif action_type == "select_square":
            square = payload.get("square")
            if square:
                # For gameplay, actually make the move on the board
                if exercise.module_id == "gameplay":
                    # Make the actual move
                    from_square = exercise.selected_square
                    if from_square:
                        # Check if it's a different square (not same square)
                        if from_square != square:
                            # Check if this is a pawn promotion move
                            from_rank = chess.square_rank(chess.parse_square(from_square))
                            to_rank = chess.square_rank(chess.parse_square(square))
                            piece = self.lesson_engine.engine.board.piece_at(chess.parse_square(from_square))
                            
                            is_promotion = False
                            if piece and piece.piece_type == chess.PAWN:
                                if (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0):
                                    is_promotion = True
                            
                            if is_promotion:
                                # Create promotion move with queen (most common)
                                move = chess.Move.from_uci(f"{from_square}{square}q")
                            else:
                                move = chess.Move.from_uci(f"{from_square}{square}")
                                
                            if move in self.lesson_engine.engine.board.legal_moves:
                                # Additional validation: prevent king captures
                                piece = self.lesson_engine.engine.board.piece_at(chess.parse_square(square))
                                if piece and piece.piece_type == chess.KING:
                                    exercise.is_correct = False
                                    exercise.feedback_message = "❌ Illegal move! Cannot capture the king directly!"
                                else:
                                    self.lesson_engine.engine.board.push(move)
                                    exercise.board_position = self.lesson_engine.engine.get_board_position()
                                    # Clear selected piece after move
                                    exercise.selected_square = None
                                    exercise.is_correct = True
                                    
                                    if is_promotion:
                                        exercise.feedback_message = "Move successful! Pawn promoted to Queen! 👑"
                                    else:
                                        exercise.feedback_message = "Move successful!"
                            else:
                                exercise.is_correct = False
                                exercise.feedback_message = "Illegal move!"
                        else:
                            # Same square clicked - deselect the piece
                            exercise.selected_square = None
                            exercise.is_correct = True
                            exercise.feedback_message = "Piece deselected."
                    else:
                        # First move - select the piece
                        piece = self.lesson_engine.engine.board.piece_at(chess.parse_square(square))
                        if piece:
                            # Check if it's the correct player's piece
                            current_turn = 'white' if self.lesson_engine.engine.board.turn else 'black'
                            piece_color = 'white' if piece.color else 'black'
                            
                            if piece_color == current_turn:
                                # Auto-deselect previous piece and select new one
                                exercise.selected_square = square
                                exercise.is_correct = True
                                exercise.feedback_message = f"Selected {piece_color} {piece.symbol}. Make your move."
                            else:
                                # If clicking on opponent's piece while having a piece selected, 
                                # it might be a capture attempt - let the move logic handle it
                                if exercise.selected_square:
                                    # Try to make the capture move
                                    from_square = exercise.selected_square
                                    move = chess.Move.from_uci(f"{from_square}{square}")
                                    
                                    if move in self.lesson_engine.engine.board.legal_moves:
                                        # Make the capture move
                                        self.lesson_engine.engine.board.push(move)
                                        exercise.board_position = self.lesson_engine.engine.get_board_position()
                                        exercise.selected_square = None
                                        exercise.is_correct = True
                                        exercise.feedback_message = "Capture successful!"
                                    else:
                                        exercise.is_correct = False
                                        exercise.feedback_message = "Illegal capture!"
                
                elif exercise.module_id == "special_moves":
                    if exercise.exercise_type == "castling":
                        from_square = exercise.selected_square
                        if from_square:
                            if from_square == "e1" and square in ["g1", "c1"]:
                                move = chess.Move.from_uci(f"{from_square}{square}")
                                
                                if move in self.lesson_engine.engine.board.legal_moves:
                                    
                                    self.lesson_engine.engine.board.push(move)
                                    
                                    exercise.board_position = self.lesson_engine.engine.get_board_position()
                                    
                                    exercise.selected_square = None
                                    
                                    exercise.is_correct = True
                                    
                                    exercise.feedback_message = "Castling successful! 🏰 King and rook moved to safety!"
                                    
                                    exercise.exercise_completed = True
                                    
                                    exercise.progress_current = exercise.progress_total
                                    
                                    session["completed_exercises"] += 1
                                    
                                    session["current_exercise"] += 1
                                    
                                    if session["completed_exercises"] >= 5:  
                                        exercise.module_completed = True
                                        session["completed"] = True
                                        session["current_exercise_state"].module_completed = True
                                    else:
                                        self._create_next_exercise(session_id)
                                else:
                                    exercise.is_correct = False
                                    exercise.feedback_message = "Castling is not legal in this position!"
                            else:
                                exercise.is_correct = False
                                exercise.feedback_message = "That's not the correct square. Try again!"
                        else:
                            # First move - select the king
                            piece = self.lesson_engine.engine.board.piece_at(chess.parse_square(square))
                            if piece and piece.piece_type == chess.KING and piece.color == chess.WHITE:
                                exercise.selected_square = square
                                exercise.is_correct = True
                                exercise.feedback_message = "King selected. Choose castling destination (g1 or c1)."
                                
                                # Show castling squares as highlights
                                castling_squares = []
                                if square == "e1":
                                    # Check for kingside castling
                                    if self.lesson_engine.engine.board.has_kingside_castling_rights(chess.WHITE):
                                        castling_squares.append("g1")
                                    # Check for queenside castling  
                                    if self.lesson_engine.engine.board.has_queenside_castling_rights(chess.WHITE):
                                        castling_squares.append("c1")
                                exercise.highlighted_squares = castling_squares
                            else:
                                exercise.is_correct = False
                                exercise.feedback_message = "Please select the white king on e1 to start castling."
                    
                    # Handle promotion exercises
                    elif exercise.exercise_type == "promotion":
                        from_square = exercise.selected_square
                        if from_square:
                            # Check if this is a promotion move
                            from_rank = chess.square_rank(chess.parse_square(from_square))
                            to_rank = chess.square_rank(chess.parse_square(square))
                            piece = self.lesson_engine.engine.board.piece_at(chess.parse_square(from_square))
                            
                            if piece and piece.piece_type == chess.PAWN:
                                if (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0):
                                    move = chess.Move.from_uci(f"{from_square}{square}q")
                                    
                                    if move in self.lesson_engine.engine.board.legal_moves:
                                        
                                        self.lesson_engine.engine.board.push(move)
                                        
                                        exercise.board_position = self.lesson_engine.engine.get_board_position()
                                        
                                        exercise.selected_square = None
                                        
                                        exercise.is_correct = True
                                        
                                        exercise.feedback_message = "Promotion successful! Pawn promoted to Queen! 👑"
                                        
                                        exercise.exercise_completed = True
                                        
                                        exercise.progress_current = exercise.progress_total
                                        
                                        session["completed_exercises"] += 1
                                        
                                        session["current_exercise"] += 1
                                        
                                        if session["completed_exercises"] >= 5:  
                                            exercise.module_completed = True
                                            session["completed"] = True
                                            session["current_exercise_state"].module_completed = True
                                        else:
                                            self._create_next_exercise(session_id)
                                    
                                    else:
                                        exercise.is_correct = False
                                        exercise.feedback_message = "Promotion is not legal in this position!"
                                else:
                                    exercise.is_correct = False
                                    exercise.feedback_message = "That's not a promotion move! Move the pawn to the end rank."
                            else:
                                exercise.is_correct = False
                                exercise.feedback_message = "Please select a pawn to promote."
                        else:
                            # First move - select the pawn
                            piece = self.lesson_engine.engine.board.piece_at(chess.parse_square(square))
                            if piece and piece.piece_type == chess.PAWN:
                                exercise.selected_square = square
                                exercise.is_correct = True
                                exercise.feedback_message = "Pawn selected. Move to the end rank to promote!"
                                
                                # Show promotion square as highlight
                                promotion_square = None
                                if piece.color == chess.WHITE and chess.square_rank(chess.parse_square(square)) == 6:
                                    promotion_square = chess.square_name(chess.parse_square(square) + 8)
                                exercise.highlighted_squares = [promotion_square] if promotion_square else []
                            else:
                                exercise.is_correct = False
                                exercise.feedback_message = "Please select a pawn to promote."
                    
                    elif exercise.exercise_type == "en_passant":
                        from_square = exercise.selected_square
                        if from_square:
                            if square in exercise.target_squares:
                                exercise.is_correct = True
                                exercise.feedback_message = "En passant capture successful! ♟️"
                                exercise.exercise_completed = True
                                exercise.progress_current = exercise.progress_total
                                
                                session["completed_exercises"] += 1
                                
                                session["current_exercise"] += 1
                                
                                if session["completed_exercises"] >= 5:  
                                    exercise.module_completed = True
                                    session["completed"] = True
                                    session["current_exercise_state"].module_completed = True
                                else:
                                    self._create_next_exercise(session_id)
                            else:
                                exercise.is_correct = False
                                exercise.feedback_message = "That's not the correct en passant square. Try again!"
                        else:
                            # First move - select the white pawn
                            piece = self.lesson_engine.engine.board.piece_at(chess.parse_square(square))
                            if piece and piece.piece_type == chess.PAWN and piece.color == chess.WHITE:
                                exercise.selected_square = square
                                exercise.is_correct = True
                                exercise.feedback_message = "White pawn selected. Choose the en passant capture square."
                                
                                # Show en_passant target square as highlight
                                exercise.highlighted_squares = exercise.target_squares
                            else:
                                exercise.is_correct = False
                                exercise.feedback_message = "Please select the white pawn for en passant."

                elif exercise.module_id == "board_setup":
                    # For board setup, handle piece placement
                    if exercise.current_piece_type:
                        # Place the selected piece
                        exercise = self.lesson_engine.handle_board_setup_placement(exercise, square)
                    else:
                        # No piece selected, show message
                        exercise.feedback_message = "Please select a piece type first!"
                        exercise.is_correct = False

                elif exercise.module_id == "check_checkmate_stalemate":
                    if not exercise.selected_square:
                        piece = self.lesson_engine.engine.board.piece_at(chess.parse_square(square))
                        if piece and piece.color == chess.WHITE:  # Use chess.WHITE for lessons instead of board.turn
                            exercise.selected_square = square
                            exercise.is_correct = True
                            exercise.feedback_message = "Piece selected. Now choose the correct move."
                            
                            # Show specific target moves as highlighted squares (only check/checkmate/stalemate moves)
                            target_moves = []
                            for move in self.lesson_engine.engine.board.legal_moves:
                                if move.from_square == chess.parse_square(square):
                                    test_board = self.lesson_engine.engine.board.copy()
                                    test_board.push(move)
                                    
                                    if exercise.exercise_type == "check" and test_board.is_check() and not test_board.is_checkmate():
                                        target_moves.append(move)
                                    elif exercise.exercise_type == "checkmate" and test_board.is_checkmate():
                                        target_moves.append(move)
                                    elif exercise.exercise_type == "stalemate" and test_board.is_stalemate():
                                        target_moves.append(move)
                            
                            exercise.highlighted_squares = [chess.square_name(move.to_square) for move in target_moves]
                        else:
                            exercise.is_correct = False
                            exercise.feedback_message = "Select a white piece to move."
                    else:
                        from_square = exercise.selected_square
                        if square == from_square:
                            exercise.selected_square = None
                            exercise.is_correct = True
                            exercise.feedback_message = "Piece deselected. Select another piece."
                        else:
                            move = chess.Move.from_uci(f"{from_square}{square}")
                            board = self.lesson_engine.engine.board

                            if move in board.legal_moves:
                                test_board = board.copy()
                                test_board.push(move)

                                is_check = test_board.is_check()
                                is_checkmate = test_board.is_checkmate()
                                is_stalemate = test_board.is_stalemate()

                                if exercise.exercise_type == "check" and is_check and not is_checkmate:
                                    board.push(move)
                                    exercise.board_position = self.lesson_engine.engine.get_board_position()
                                    exercise.selected_square = None
                                    exercise.is_correct = True
                                    exercise.feedback_message = "Correct! This move gives check."
                                    exercise.exercise_completed = True
                                    session["completed_exercises"] = min(session["completed_exercises"] + 1, session["total_exercises"])
                                    session["current_exercise"] += 1
                                    if session["completed_exercises"] >= session["total_exercises"]:
                                        exercise.module_completed = True
                                        session["completed"] = True
                                elif exercise.exercise_type == "checkmate" and is_checkmate:
                                    board.push(move)
                                    exercise.board_position = self.lesson_engine.engine.get_board_position()
                                    exercise.selected_square = None
                                    exercise.is_correct = True
                                    exercise.feedback_message = "Correct! This is checkmate."
                                    exercise.exercise_completed = True
                                    session["completed_exercises"] = min(session["completed_exercises"] + 1, session["total_exercises"])
                                    session["current_exercise"] += 1
                                    if session["completed_exercises"] >= session["total_exercises"]:
                                        exercise.module_completed = True
                                        session["completed"] = True
                                elif exercise.exercise_type == "stalemate" and is_stalemate:
                                    board.push(move)
                                    exercise.board_position = self.lesson_engine.engine.get_board_position()
                                    exercise.selected_square = None
                                    exercise.is_correct = True
                                    exercise.feedback_message = "Correct! This is stalemate."
                                    exercise.exercise_completed = True
                                    session["completed_exercises"] = min(session["completed_exercises"] + 1, session["total_exercises"])
                                    session["current_exercise"] += 1
                                    if session["completed_exercises"] >= session["total_exercises"]:
                                        exercise.module_completed = True
                                        session["completed"] = True
                                else:
                                    exercise.is_correct = False
                                    exercise.feedback_message = "That's not the correct square. Try again!"
                            else:
                                exercise.is_correct = False
                                exercise.feedback_message = "Illegal move! Try again."
                
                elif exercise.module_id in ["pawn_movement", "rook_movement", "knight_movement", "bishop_movement", "queen_movement", "king_movement", "special_moves", "check_checkmate_stalemate"]:
                    # Handle piece selection and movement for lessons
                    print(f"🔍 DEBUG: Handling piece selection for {exercise.module_id}")
                    if not exercise.selected_square:
                        # First click - select the piece
                        print(f"🔍 DEBUG: First click - selecting piece at {square}")
                        piece = self.lesson_engine.engine.board.piece_at(chess.parse_square(square))
                        print(f"🔍 DEBUG: Piece at {square}: {piece}")
                        if piece and piece.color == chess.WHITE:  # Only allow selecting white pieces for lessons
                            exercise.selected_square = square
                            exercise.is_correct = True
                            exercise.feedback_message = f"Selected {piece.symbol}. Now click where it can move."
                            
                            # Show possible moves as highlighted squares
                            legal_moves = list(self.lesson_engine.engine.board.legal_moves)
                            highlighted_moves = [m.to_square for m in legal_moves if m.from_square == chess.parse_square(square)]
                            exercise.highlighted_squares = [chess.square_name(sq) for sq in highlighted_moves]
                            print(f"🔍 DEBUG: Highlighted moves: {exercise.highlighted_squares}")
                        else:
                            exercise.is_correct = False
                            exercise.feedback_message = "Please select a white piece to move."
                    else:
                        # Second click - try to move to the selected square
                        print(f"🔍 DEBUG: Second click - moving from {exercise.selected_square} to {square}")
                        from_square = exercise.selected_square
                        
                        # Check if the target square is in highlighted squares (legal moves)
                        target_square_int = chess.parse_square(square)
                        highlighted_squares_int = [chess.parse_square(sq) for sq in exercise.highlighted_squares]
                        
                        if target_square_int in highlighted_squares_int:
                            # Valid move - complete the exercise
                            move = chess.Move.from_uci(f"{from_square}{square}")
                            if move in self.lesson_engine.engine.board.legal_moves:
                                self.lesson_engine.engine.board.push(move)
                                exercise.board_position = self.lesson_engine.engine.get_board_position()
                                
                                exercise.selected_square = None
                                exercise.highlighted_squares = []  # Clear highlights
                                exercise.is_correct = True
                                exercise.feedback_message = "Correct move!"
                                exercise.exercise_completed = True
                                
                                # Update progress
                                session["completed_exercises"] += 1
                                session["current_exercise"] += 1
                                
                                if session["completed_exercises"] >= session["total_exercises"]:
                                    exercise.module_completed = True
                                    session["completed"] = True
                        else:
                            exercise.is_correct = False
                            exercise.feedback_message = "That's not a valid move for this piece."
                            
                            # Clear selection on invalid move
                            exercise.selected_square = None
                            exercise.highlighted_squares = []
        
        elif action_type == "select_option":
            option_index = payload.get("index")
            if exercise.exercise_type == "identify_pieces" and option_index is not None:
                options = exercise.instructions.split("|")[1].split(",")
                if 0 <= option_index < len(options):
                    answer = options[option_index]
                    is_correct = self.lesson_engine.check_answer(exercise, answer)
                    exercise.is_correct = is_correct
                    exercise.exercise_completed = is_correct
                    session["correct_answers"] += 1 if is_correct else 0
                    
                    if is_correct:
                        exercise.feedback_message = f"Correct! Well done! That is a {answer}."
                        session["completed_exercises"] += 1
                    else:
                        exercise.feedback_message = f"Wrong. That is not a {answer}."
        
        elif action_type == "submit_answer":
            answer = payload.get("answer")
            if exercise.exercise_type == "identify_pieces" and answer:
                if exercise.exercise_completed:
                    return exercise
                
                is_correct = self.lesson_engine.check_answer(exercise, answer)
                exercise.is_correct = is_correct
                exercise.exercise_completed = is_correct
                session["correct_answers"] += 1 if is_correct else 0
                
                if is_correct:
                    exercise.feedback_message = f"Correct! Well done! That is a {answer}."
                    session["completed_exercises"] += 1
                    session["current_exercise"] += 1
                    
                    # Update progress_current for identify_pieces
                    exercise.progress_current = session["completed_exercises"]
                    
                    if session["completed_exercises"] >= self._get_total_exercises(session["module_id"]):
                        exercise.module_completed = True
                        session["completed"] = True
                    # Note: Don't create next exercise here for identify_pieces - let frontend show feedback first
                else:
                    exercise.feedback_message = f"Wrong. That is not a {answer}."
        
        elif action_type == "hint":
            exercise.feedback_message = f"Hint: {self._get_hint_for_exercise(exercise)}"
            exercise.is_correct = None
        
        elif action_type == "skip":
            exercise.feedback_message = "Skipping to next exercise."
            exercise.exercise_completed = True
            session["completed_exercises"] += 1
            
            session["current_exercise"] += 1
            if session["current_exercise"] >= session["total_exercises"]:
                exercise.module_completed = True
                session["completed"] = True
            else:
                self._create_next_exercise(session_id)
        
        elif action_type == "next":
            if exercise.exercise_completed:
                self._create_next_exercise(session_id)
        
        elif action_type == "select_piece":
            piece_type = payload.get("piece_type")
            if exercise.exercise_type == "board_setup" and piece_type:
                exercise = self.lesson_engine.handle_board_setup_piece_selection(exercise, piece_type)
        
        elif action_type == "place_piece":
            square = payload.get("square")
            if exercise.exercise_type == "board_setup" and square:
                exercise = self.lesson_engine.handle_board_setup_placement(exercise, square)
        
        elif action_type == "remove_piece":
            square = payload.get("square")
            if exercise.exercise_type == "board_setup" and square:
                exercise = self.lesson_engine.handle_board_setup_remove_piece(exercise, square)
        
        if exercise.exercise_type != "board_setup":
            exercise.progress_current = min(session["completed_exercises"], session.get("total_exercises", 0))
        
        if exercise.module_id == "gameplay":
            board = self.lesson_engine.engine.board
            
            exercise.board_position = self.lesson_engine.engine.get_board_position()
            
            if board.is_checkmate():
                if board.turn:  
                    winner = 'Black'
                    winner_color = '⚫'
                    exercise.feedback_message = f"🏆 BLACK WINS! Checkmate! White king is checkmated!"
                else:  
                    winner = 'White'
                    winner_color = '⚪'
                    exercise.feedback_message = f"🏆 WHITE WINS! Checkmate! Black king is checkmated!"
                
                exercise.exercise_completed = True
                exercise.module_completed = True
                session["completed"] = True
                
                print(f"🎉 GAME OVER: {winner} wins by checkmate!")
                print(f"Final position FEN: {board.fen()}")
                
            elif board.is_stalemate():
                print("Stalemate detected!")
                exercise.exercise_completed = True
                exercise.module_completed = True
                session["completed"] = True
                exercise.feedback_message = "🤝 STALEMATE! The game is a draw! No legal moves available!"
                
            elif board.is_insufficient_material():
                print("Insufficient material detected!")
                exercise.exercise_completed = True
                exercise.module_completed = True
                session["completed"] = True
                exercise.feedback_message = "🤝 DRAW! Insufficient material to checkmate!"
                
            elif board.can_claim_draw():
                print("Draw can be claimed!")
                exercise.feedback_message = "🤝 Draw can be claimed! Game is likely drawn."
                
            elif board.is_check():
                if board.turn:  
                    exercise.feedback_message = "⚠️ CHECK! White king is in check!"
                else:
                    exercise.feedback_message = "⚠️ CHECK! Black king is in check!"
                
                print("Check detected! Still checking for AI turn...")
                
            else:
                print("No check, no checkmate, continuing to AI check")
                    
            is_ai_turn = self.lesson_engine.is_ai_turn(exercise.exercise_type)
            print(f"After check detection - Exercise type: {exercise.exercise_type}, Board turn: {board.turn}, Is AI turn: {is_ai_turn}")
            
            if exercise.exercise_completed:
                print("Game is already over, skipping AI move")
            elif is_ai_turn:
                # Make AI move automatically
                print("Making AI move...")
                ai_success = self.lesson_engine.make_ai_move()
                print(f"AI move success: {ai_success}")
                if ai_success:
                    exercise.board_position = self.lesson_engine.engine.get_board_position()
                    # Clear selected piece after AI move
                    exercise.selected_square = None
                    exercise.feedback_message = "🤖 AI made its move!"
                else:
                    exercise.feedback_message = "❌ AI has no valid moves!"
                    print("AI move failed - no valid moves or error occurred")
        else:
            # Only update progress_current for non-board_setup exercises
            if exercise.exercise_type != "board_setup":
                exercise.progress_current = session["completed_exercises"]
        
        return session["current_exercise_state"]
    
    def _get_game_mode_instructions(self, game_mode: str) -> str:
        """Get instructions for different game modes"""
        if game_mode == "human_vs_ai":
            return "You are playing as White against the AI. Make your move and wait for the AI's response."
        elif game_mode == "ai_vs_ai":
            return "AI vs AI: Watch the computer play against itself. Turn: AI"
        elif game_mode == "human_vs_human":
            return "Two-player mode: Both players play on the same device. White moves first."
        else:
            return "Unknown game mode"

    def _get_hint_for_exercise(self, exercise: ExerciseState) -> str:
        """Get hint message for an exercise"""
        # Pawn movement lesson types
        if exercise.exercise_type == "basic_forward":
            return "Pawns move forward one square toward the opponent."
        elif exercise.exercise_type == "initial_double":
            return "From the starting position, pawns can move one or two squares forward."
        elif exercise.exercise_type == "capture":
            return "Pawns capture diagonally forward, not straight ahead."
        elif exercise.exercise_type == "blocked":
            return "A pawn cannot move forward if another piece blocks its path."
        elif exercise.exercise_type == "en_passant":
            return "En passant is a special capture when an enemy pawn moves two squares."

        # Piece identification
        elif exercise.exercise_type == "identify_pieces":
            return "Look at the shape and position of the highlighted piece."

        # Board setup
        elif exercise.exercise_type == "board_setup":
            return "Remember: Rooks in corners, knights next to them, then bishops, queen on her color."

        # Movement modules often use generic exercise_type values like "basic" / "capture".
        # Use module_id to provide accurate hints.
        if exercise.module_id == "rook_movement":
            return "Rooks move any number of squares in straight lines (up, down, left, right). They cannot jump over pieces."
        if exercise.module_id == "knight_movement":
            return "Knights move in an L-shape (2 squares then 1). Knights CAN jump over pieces."
        if exercise.module_id == "bishop_movement":
            return "Bishops move diagonally any number of squares. They stay on the same color squares and cannot jump over pieces."
        if exercise.module_id == "queen_movement":
            return "The queen moves like a rook + bishop combined: straight lines or diagonals, any number of squares."
        if exercise.module_id == "king_movement":
            return "The king moves exactly 1 square in any direction. Don’t move into check."

        # Special moves module
        if exercise.module_id == "special_moves":
            if exercise.exercise_type == "castling":
                return "Castling: move the king two squares toward the rook, then the rook jumps next to the king. It’s only allowed if neither piece moved and the king doesn’t pass through check."
            if exercise.exercise_type == "promotion":
                return "Promotion: when a pawn reaches the last rank, it must be promoted (usually to a queen)."
            return "Special moves include castling, en passant, and pawn promotion."

        # Check / checkmate / stalemate module
        if exercise.module_id == "check_checkmate_stalemate":
            if exercise.exercise_type == "check":
                return "Check means the king is under attack. The player must respond by moving the king, capturing the attacker, or blocking the attack."
            if exercise.exercise_type == "checkmate":
                return "Checkmate means the king is in check and there is no legal move to escape."
            if exercise.exercise_type == "stalemate":
                return "Stalemate means the player is NOT in check but has no legal moves. It’s a draw."
            return "Focus on king safety: check, checkmate, and stalemate depend on legal moves available."

        else:
            return "Think about how this piece normally moves in chess."
    
    def complete_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Complete a session and return summary"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        session["completed"] = True
        
        accuracy = (session["correct_answers"] / session["total_attempts"] * 100) if session["total_attempts"] > 0 else 0
        
        return {
            "session_id": session_id,
            "module_id": session["module_id"],
            "completed": True,
            "total_exercises": session["total_exercises"],
            "completed_exercises": session["completed_exercises"],
            "accuracy": accuracy
        }

# Global session manager
chess_session_manager = ChessSessionManager()

# ---- API Helper Functions ----

def exercise_state_to_response(exercise: ExerciseState, session_id: str) -> ChessExerciseResponse:
    """Convert ExerciseState to API response"""
    
    return ChessExerciseResponse(
        session_id=session_id,
        exercise_id=exercise.exercise_id,
        module_id=exercise.module_id,
        exercise_type=exercise.exercise_type,
        board_layout=chess_engine.get_board_layout(),
        board_position=exercise.board_position,
        highlighted_squares=exercise.highlighted_squares,
        target_squares=exercise.target_squares,
        invalid_squares=exercise.invalid_squares,
        selected_square=exercise.selected_square,
        instructions=exercise.instructions,
        feedback_message=exercise.feedback_message,
        is_correct=exercise.is_correct,
        progress_current=exercise.progress_current,
        progress_total=exercise.progress_total,
        hint_available=exercise.hint_available,
        exercise_completed=exercise.exercise_completed,
        module_completed=exercise.module_completed,
        # Board setup specific properties
        pieces_inventory=exercise.pieces_inventory,
        placed_pieces=exercise.placed_pieces,
        current_piece_type=exercise.current_piece_type
    )

def board_position_to_model(position: BoardPosition) -> BoardPosition:
    """Convert BoardPosition to Pydantic model"""
    return BoardPosition(
        fen=position.fen,
        pieces=[
            ChessPiece(
                type=piece.type,
                color=piece.color,
                square=piece.square
            ) for piece in position.pieces
        ],
        legal_moves=position.legal_moves,
        is_check=position.is_check,
        is_checkmate=position.is_checkmate,
        is_stalemate=position.is_stalemate,
        turn=position.turn,
        fullmove_number=position.fullmove_number,
        halfmove_clock=position.halfmove_clock
    )

# ---- Module Definitions ----

CHESS_MODULES = [
    {
        "id": "identify_pieces",
        "name": "Identify Pieces",
        "description": "Learn to identify all chess pieces",
        "icon": "♟",
        "total_exercises": 12,
        "unlocked": True
    },
    {
        "id": "board_setup",
        "name": "Board Setup",
        "description": "Learn how to set up the chess board correctly",
        "icon": "♞",
        "total_exercises": 1,
        "unlocked": True
    },
    {
        "id": "pawn_movement",
        "name": "Pawn Movement",
        "description": "Master pawn movement including special moves",
        "icon": "♙",
        "total_exercises": 15,
        "unlocked": True
    },
    {
        "id": "rook_movement",
        "name": "Rook Movement",
        "description": "Learn rook movement patterns",
        "icon": "♖",
        "total_exercises": 9,
        "unlocked": True
    },
    {
        "id": "knight_movement",
        "name": "Knight Movement",
        "description": "Master the knight's L-shaped moves",
        "icon": "♘",
        "total_exercises": 9,
        "unlocked": True
    },
    {
        "id": "bishop_movement",
        "name": "Bishop Movement",
        "description": "Learn bishop diagonal movement",
        "icon": "♗",
        "total_exercises": 9,
        "unlocked": True
    },
    {
        "id": "queen_movement",
        "name": "Queen Movement",
        "description": "Master the queen's powerful moves",
        "icon": "♕",
        "total_exercises": 9,
        "unlocked": True
    },
    {
        "id": "king_movement",
        "name": "King Movement",
        "description": "Learn king movement and check concepts",
        "icon": "♔",
        "total_exercises": 9,
        "unlocked": True
    },
    {
        "id": "special_moves",
        "name": "Special Moves",
        "description": "Learn castling, en passant, and promotion",
        "icon": "♚",
        "total_exercises": 12,
        "unlocked": True
    },
    {
        "id": "check_checkmate_stalemate",
        "name": "Check & Checkmate",
        "description": "Understand check, checkmate, and stalemate",
        "icon": "♛",
        "total_exercises": 10,
        "unlocked": True
    },
    {
        "id": "gameplay",
        "name": "Gameplay",
        "description": "Play chess with different game modes",
        "icon": "♜",
        "total_exercises": 3,
        "unlocked": True
    }
]

def get_module_by_id(module_id: str) -> Optional[Dict[str, Any]]:
    """Get module by ID"""
    for module in CHESS_MODULES:
        if module["id"] == module_id:
            return module
    return None
