// zumbaApi.ts - Zumba Dance Analysis API Client
// Connects to the unified backend for real-time Zumba dance analysis

const API_BASE_URL = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8002';
const WS_BASE_URL = process.env.NEXT_PUBLIC_YOGA_WS_URL || 'ws://localhost:8002';

export interface ZumbaSessionStartRequest {
  target_move: string;
  settings?: {
    tolerance?: number;
    feedback_interval?: number;
    min_feedback_gap?: number;
    // Timeline session context for post-session analytics (beat sync,
    // calories, per-move breakdown). All optional for backward compatibility.
    mode?: string;
    song_title?: string;
    username?: string;
    weight_kg?: number | null;
    /** 8-count block start times (ms) — the "key beats" for Beat Sync. */
    key_beats_ms?: number[];
    /** Backend move key expected at each key beat (parallel array). */
    key_beat_moves?: string[];
  };
}

export interface ZumbaSessionResponse {
  session_id: string;
  target_move: string;
  settings: Record<string, unknown>;
  created_at: string;
  status: string;
}

export interface ZumbaAnalysisResult {
  session_id: string;
  pose_detected: boolean;
  target_move?: string;
  angles?: Record<string, number>;
  feedback_messages: string[];
  corrections: string[];
  accuracy?: number;
  motion_score?: number;
  active_movement?: boolean;
  processed_frame?: string;
  timestamp: string;
  performance_metrics: {
    good_frames: number;
    total_frames: number;
    detected_frames?: number;
    comparable_frames?: number;
    active_frames?: number;
    feedback_count: number;
  };
  message?: string;
}

// ---- Post-session analytics (AITrainer Zumba Post-Session Stats Guide) ----

export interface ZumbaMoveScore {
  key: string;
  name: string;
  frames: number;
  accuracy: number | null;
  rhythm: number | null;
  energy: number;
  completion: number;
  body_parts: Record<string, number | null>;
}

export interface ZumbaScores {
  overall: number;
  pose_accuracy: number;
  beat_sync: number;
  completion: number;
  energy: number;
  consistency: number;
  beat_sync_detail: {
    matched: number;
    total: number;
    avg_delay_ms: number | null;
    bands: { excellent: number; good: number; average: number; off: number };
  };
  body_parts: { arms: number | null; legs: number | null; core: number | null; balance: number | null; rhythm: number };
  calories: { value?: number; range?: [number, number] };
  met: number;
  active_time_seconds: number;
  best_move: { key: string; name: string; accuracy: number } | null;
  needs_practice: { key: string; name: string; accuracy: number } | null;
  moves: ZumbaMoveScore[];
  tip: string;
  mode: string;
  song_title: string;
}

export interface ZumbaSessionSummary {
  session_id: string;
  target_move: string;
  duration_seconds: number;
  frames_processed: number;
  average_accuracy: number;
  feedback_count: number;
  created_at: string;
  status: string;
  song_title?: string | null;
  mode?: string | null;
  username?: string | null;
  /** Full post-session score object; null for legacy single-move sessions. */
  scores?: ZumbaScores | null;
}

// Get auth token from localStorage
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
};

// API Headers with auth
const getHeaders = (): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// Get available Zumba moves
export const getZumbaMoves = async (): Promise<string[]> => {
  const response = await fetch(`${API_BASE_URL}/api/zumba/moves`, {
    method: 'GET',
    headers: getHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to get Zumba moves: ${response.statusText}`);
  }

  return response.json();
};

// Start a new Zumba session
export const startZumbaSession = async (request: ZumbaSessionStartRequest): Promise<ZumbaSessionResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/zumba/session`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to start Zumba session: ${response.statusText}`);
  }

  return response.json();
};

// Analyze a single frame
export const analyzeZumbaFrame = async (request: {
  session_id: string;
  frame_data: string;
}): Promise<ZumbaAnalysisResult> => {
  const response = await fetch(`${API_BASE_URL}/api/zumba/analyze-frame`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to analyze Zumba frame: ${response.statusText}`);
  }

  return response.json();
};

// Get session summary
export const getZumbaSessionSummary = async (sessionId: string): Promise<ZumbaSessionSummary> => {
  const response = await fetch(`${API_BASE_URL}/api/zumba/session/${sessionId}/summary`, {
    method: 'GET',
    headers: getHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to get Zumba session summary: ${response.statusText}`);
  }

  return response.json();
};

// End Zumba session
export const endZumbaSession = async (sessionId: string): Promise<ZumbaSessionSummary> => {
  const response = await fetch(`${API_BASE_URL}/api/zumba/session/${sessionId}/end`, {
    method: 'POST',
    headers: getHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to end Zumba session: ${response.statusText}`);
  }

  return response.json();
};

// Per-frame timeline context sent alongside each pose frame.
export interface ZumbaFrameMeta {
  targetMove?: string;
  targetMoveName?: string;
  timelineMs?: number;
}

// WebSocket class for real-time Zumba analysis
export class ZumbaWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private shouldReconnect = true;

  constructor(
    private onResult: (result: ZumbaAnalysisResult) => void,
    private onError: (error: string) => void,
    private onConnect: () => void,
    private onDisconnect: () => void
  ) {}

  async connect(sessionId: string): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;
    this.shouldReconnect = true;
    this.sessionId = sessionId;

    try {
      const wsUrl = `${WS_BASE_URL}/ws/pose-analysis`;
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('Zumba WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.onConnect();
      };

      this.ws.onmessage = (event) => {
        try {
          // Check if event.data exists and is not empty
          if (!event.data) {
            console.warn('Received empty WebSocket message');
            return;
          }
          
          const data = JSON.parse(event.data);
          
          if (data.type === 'zumba_analysis') {
            // Validate data structure before processing
            if (data && typeof data === 'object') {
              this.onResult(data as ZumbaAnalysisResult);
            } else {
              console.warn('Invalid analysis data structure:', data);
            }
          } else if (data.type === 'error') {
            this.onError(data.message || 'Unknown error occurred');
          } else if (data.type === 'connected') {
            console.log('WebSocket connection confirmed');
          } else {
            console.warn('Unknown message type:', data.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          console.error('Raw message:', event.data);
          this.onError('Failed to parse server response');
        }
      };

      this.ws.onclose = (event) => {
        console.log('Zumba WebSocket disconnected', event.code, event.reason);
        this.isConnecting = false;
        this.onDisconnect();
        
        // Don't reconnect if it was a normal closure
        if (!this.shouldReconnect || event.code === 1000) {
          return;
        }
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
          
          setTimeout(() => {
            if (this.sessionId) {
              this.connect(this.sessionId);
            }
          }, this.reconnectDelay * this.reconnectAttempts);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.onError('WebSocket connection error');
      };

    } catch (error) {
      this.isConnecting = false;
      throw new Error(`Failed to connect WebSocket: ${error}`);
    }
  }

  sendFrame(frameData: string, meta?: ZumbaFrameMeta): void {
    if (!this.isConnected()) {
      throw new Error('WebSocket not connected or session not established');
    }

    if (!this.sessionId) {
      throw new Error('Session not established');
    }

    // Every frame is self-describing: it carries the move the timeline expects
    // right now, so the backend can switch comparison target without a new session.
    const message: Record<string, unknown> = {
      type: 'pose_frame',
      session_id: this.sessionId,
      session_type: 'zumba',
      data: frameData,
    };
    if (meta?.targetMove) message.target_move = meta.targetMove;
    if (meta?.targetMoveName) message.target_move_name = meta.targetMoveName;
    if (typeof meta?.timelineMs === 'number') message.timeline_ms = meta.timelineMs;

    this.ws?.send(JSON.stringify(message));
  }

  disconnect(): void {
    if (this.ws) {
      this.shouldReconnect = false;
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Utility function to convert canvas/frame to base64
export const canvasToBase64 = (canvas: HTMLCanvasElement): string => {
  return canvas.toDataURL('image/jpeg', 0.7); // Using YogaCamera's quality
};
