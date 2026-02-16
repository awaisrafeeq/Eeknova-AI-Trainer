// chessApi.ts - Chess Learning API client

const CHESS_API_BASE_URL = process.env.NEXT_PUBLIC_YOGA_API_URL || process.env.NEXT_PUBLIC_CHESS_API_URL || 'http://localhost:8000';

export interface ChessModule {
  id: string;
  name: string;
  description: string;
  icon: string;
}

export interface ChessExerciseState {
  session_id: string;
  module_id: string;
  exercise_id: string;
  exercise_type: string;
  board_layout: {
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
  };
  board_position: {
    fen: string;
    pieces: Array<{
      type: string;
      color: string;
      square: string;
    }>;
    legal_moves: string[];
    is_check: boolean;
    is_checkmate: boolean;
    is_stalemate: boolean;
    turn: string;
    fullmove_number: number;
    halfmove_clock: number;
  };
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
  // Board setup specific properties
  pieces_inventory?: Record<string, {
    count: number;
    positions: Array<[number, number]>;
    symbol: string;
    color: string;
  }>;
  placed_pieces?: Record<string, {
    type: string;
    symbol: string;
    color: string;
    correct: boolean;
  }>;
  current_piece_type?: string | null;
}

export interface ChessSessionSummary {
  session_id: string;
  module_id: string;
  completed: boolean;
}

const getHeaders = (): HeadersInit => ({
  'Content-Type': 'application/json',
});

export const getChessModules = async (): Promise<ChessModule[]> => {
  const res = await fetch(`${CHESS_API_BASE_URL}/api/chess/modules`, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (!res.ok) {
    throw new Error('Failed to load chess modules');
  }
  return res.json();
};

export const createChessSession = async (
  moduleId: string
): Promise<ChessExerciseState> => {
  const res = await fetch(`${CHESS_API_BASE_URL}/api/chess/session`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ module_id: moduleId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to start chess session');
  }
  const data = await res.json();
  return { session_id: data.session_id, ...data };
};

export const getChessExercise = async (
  sessionId: string
): Promise<ChessExerciseState> => {
  const res = await fetch(`${CHESS_API_BASE_URL}/api/chess/session/${sessionId}`, {
    method: 'GET',
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to get exercise state');
  }
  const data = await res.json();
  return { session_id: sessionId, ...data };
};

export const sendChessAction = async (
  sessionId: string,
  type: string,
  payload: Record<string, unknown> = {}
): Promise<ChessExerciseState> => {
  const res = await fetch(`${CHESS_API_BASE_URL}/api/chess/session/${sessionId}/action`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ type, payload }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to apply action');
  }
  const data = await res.json();
  return { session_id: sessionId, ...data };
};

export const completeChessSession = async (
  sessionId: string
): Promise<ChessSessionSummary> => {
  const res = await fetch(`${CHESS_API_BASE_URL}/api/chess/session/${sessionId}/complete`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to complete chess session');
  }
  return res.json();
};
