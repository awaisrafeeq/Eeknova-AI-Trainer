// TypeScript types for enhanced chess API
// Update your frontend types to match the new comprehensive chess API

export interface ChessSquare {
    file: string;
    rank: number;
    index: number;
}

export interface ChessPiece {
    type: 'pawn' | 'rook' | 'knight' | 'bishop' | 'queen' | 'king';
    color: 'white' | 'black';
    square: ChessSquare;
}

export interface BoardPosition {
    fen: string;
    pieces: ChessPiece[];
    legal_moves: string[];
    is_check: boolean;
    is_checkmate: boolean;
    is_stalemate: boolean;
    turn: 'white' | 'black';
    fullmove_number: number;
    halfmove_clock: number;
}

export interface ChessBoardLayout {
    squares: Array<{
        name: string;
        file: string;
        rank: string;
        color: string;
        is_light: boolean;
        is_highlighted: boolean;
        is_selected: boolean;
    }>;
    pieces: Array<{
        type: string;
        color: string;
        square: string;
        symbol: string;
    }>;
    labels: {
        files: string[];
        ranks: string[];
    };
    colors: {
        light_square: string;
        dark_square: string;
        highlight: string;
        selected: string;
    };
}

export interface ChessModule {
    id: string;
    name: string;
    description: string;
    icon: string;
    total_exercises: number;
    unlocked: boolean;
}

export interface ChessExerciseState {
    exercise_id: string;
    module_id: string;
    exercise_type: string;
    board_layout: ChessBoardLayout;
    board_position: BoardPosition;
    highlighted_squares: string[];
    target_squares: string[];
    invalid_squares: string[];
    selected_square: string | null;
    instructions: string;
    feedback_message: string | null;
    is_correct: boolean | null;
    progress_current: number;
    progress_total: number;
    hint_available: boolean;
    exercise_completed: boolean;
    module_completed: boolean;
}

export interface ChessSessionSummary {
    session_id: string;
    module_id: string;
    completed: boolean;
    total_exercises: number;
    completed_exercises: number;
    accuracy: number;
}

// API functions
export const getChessModules = async (): Promise<ChessModule[]> => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_YOGA_API_URL}/api/chess/modules`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error('Failed to load chess modules');
    return res.json();
};

export const createChessSession = async (moduleId: string): Promise<ChessExerciseState> => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_YOGA_API_URL}/api/chess/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module_id: moduleId }),
    });
    if (!res.ok) throw new Error('Failed to start chess session');
    return res.json();
};

export const getChessExercise = async (sessionId: string): Promise<ChessExerciseState> => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_YOGA_API_URL}/api/chess/session/${sessionId}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error('Failed to get exercise state');
    return res.json();
};

export const sendChessAction = async (
    sessionId: string,
    type: string,
    payload: Record<string, unknown> = {}
): Promise<ChessExerciseState> => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_YOGA_API_URL}/api/chess/session/${sessionId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, payload }),
    });
    if (!res.ok) throw new Error('Failed to apply action');
    return res.json();
};

export const completeChessSession = async (sessionId: string): Promise<ChessSessionSummary> => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_YOGA_API_URL}/api/chess/session/${sessionId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error('Failed to complete chess session');
    return res.json();
};
