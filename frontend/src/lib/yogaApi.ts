// Yoga Pose Detection API Client
// Connects to the FastAPI backend for real-time pose analysis

const API_BASE_URL = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8002';
const WS_BASE_URL = process.env.NEXT_PUBLIC_YOGA_WS_URL || 'ws://localhost:8002';

export interface SessionStartRequest {
  pose_name?: string;
  tolerance?: number;
}

export interface SessionResponse {
  session_id: string;
  settings: {
    pose_name?: string;
    tolerance: number;
    timestamp: string;
  };
}

export interface PoseAnalysisResult {
  type?: string;
  pose_detected: boolean;
  pose_name?: string;
  confidence?: number;
  accuracy?: number | null;
  correct_angles?: number;
  total_angles?: number;
  keypoints?: number[][];
  angles?: Record<string, number | null>;
  corrections?: string[];
  angle_status?: Record<string, { within_tolerance: boolean; difference: number | null }>;
  // DEBUG: Backend debug traces for captured vs reference angle matching.
  debug_captured_angles?: Record<string, number | null>;
  debug_reference_angles?: Record<string, number | null> | null;
  debug_comparison_results?: Record<
    string,
    {
      calculated?: number | null;
      ground_truth?: number | null;
      difference?: number | null;
      within_tolerance: boolean;
    }
  >;
  debug_corrections?: string[];
  session_stats?: {
    frames_processed: number;
    average_accuracy: number;
  };
  message?: string;
  error?: string;
  timestamp?: string;
  // For session stopped messages
  session_id?: string;
  duration_seconds?: number;
  frames_processed?: number;
  average_accuracy?: number;
  corrections_given?: number;
  summary?: SessionSummary;
}

export interface SessionSummary {
  session_id: string;
  duration_seconds: number;
  frames_processed: number;
  average_accuracy: number;
  corrections_given: number;
  pose_name?: string;
}

export interface PoseInfo {
  name: string;
  display_name: string;
  description: string;
}

export interface ModelStatus {
  yolo_ready: boolean;
  classifier_ready: boolean;
  reference_angles_loaded: boolean;
  available_poses: number;
  reference_poses: number;
  timestamp: string;
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

// Start a new pose analysis session
export const startSession = async (request: SessionStartRequest): Promise<SessionResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/session/start`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to start session');
  }

  return response.json();
};

// Stop a pose analysis session
export const stopSession = async (sessionId: string): Promise<SessionSummary> => {
  const response = await fetch(`${API_BASE_URL}/api/session/stop/${sessionId}`, {
    method: 'POST',
    headers: getHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to stop session');
  }

  return response.json();
};

// Update pose for an active session
export const updateSessionPose = async (
  sessionId: string,
  poseName: string,
  tolerance: number = 10.0
): Promise<{ session_id: string; pose_name: string; tolerance: number; message: string }> => {
  const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/pose`, {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify({
      pose_name: poseName,
      tolerance: tolerance,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update pose');
  }

  return response.json();
};

// Get available poses
export const getAvailablePoses = async (): Promise<PoseInfo[]> => {
  const response = await fetch(`${API_BASE_URL}/api/poses/available`, {
    method: 'GET',
    headers: getHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to get available poses');
  }

  return response.json();
};

// Check model status
export const getModelStatus = async (): Promise<ModelStatus> => {
  const response = await fetch(`${API_BASE_URL}/api/model/status`, {
    method: 'GET',
    headers: getHeaders(),
  });

  if (!response.ok) {
    throw new Error('Failed to get model status');
  }

  return response.json();
};

// Analyze a single frame via HTTP (for slower analysis)
export const analyzeFrame = async (
  frameData: string,
  sessionId: string
): Promise<PoseAnalysisResult> => {
  const response = await fetch(`${API_BASE_URL}/api/analyze-frame`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({
      data: frameData,
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to analyze frame');
  }

  return response.json();
};

// WebSocket connection for real-time pose analysis
export class YogaPoseWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private onMessage: ((data: PoseAnalysisResult) => void) | null = null;
  private onError: ((error: string) => void) | null = null;
  private onConnect: (() => void) | null = null;
  private onDisconnect: (() => void) | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(
    onMessage?: (data: PoseAnalysisResult) => void,
    onError?: (error: string) => void,
    onConnect?: () => void,
    onDisconnect?: () => void
  ) {
    this.onMessage = onMessage || null;
    this.onError = onError || null;
    this.onConnect = onConnect || null;
    this.onDisconnect = onDisconnect || null;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${WS_BASE_URL}/ws/pose-analysis`);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.onConnect?.();
          
          // Start heartbeat to keep connection alive
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'connected') {
              console.log('WebSocket confirmed connection:', data.client_id);
            } else if (data.type === 'pong') {
              console.log('Received pong from server');
            } else if (data.type === 'analysis_started') {
              this.sessionId = data.session_id;
              console.log('Analysis session started:', this.sessionId);
            } else if (data.type === 'analysis_stopped') {
              console.log('Analysis session stopped:', data);
              this.sessionId = null;
            } else if (data.type === 'pose_analysis') {
              this.onMessage?.(data);
            } else if (data.type === 'error') {
              this.onError?.(data.message);
            }
          } catch (e) {
            console.error('Error parsing WebSocket message:', e);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.onError?.('WebSocket connection error');
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.onDisconnect?.();

          // Attempt to reconnect
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  startAnalysis(poseName: string, tolerance: number = 10.0): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'start_analysis',
        pose_name: poseName,
        tolerance: tolerance,
      }));
    } else {
      console.warn('WebSocket not ready, waiting for connection...');
      // Wait for connection and retry
      setTimeout(() => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.startAnalysis(poseName, tolerance);
        } else {
          this.onError?.('WebSocket connection failed');
        }
      }, 500);
    }
  }

  sendFrame(frameData: string): void {
    if (this.ws?.readyState === WebSocket.OPEN && this.sessionId) {
      this.ws.send(JSON.stringify({
        type: 'pose_frame',
        data: frameData,
        session_id: this.sessionId,
      }));
    }
  }

  stopAnalysis(): void {
    if (this.ws?.readyState === WebSocket.OPEN && this.sessionId) {
      this.ws.send(JSON.stringify({
        type: 'stop_analysis',
        session_id: this.sessionId,
      }));
      this.sessionId = null;
    }
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  disconnect(): void {
    this.stopHeartbeat(); // Stop heartbeat on disconnect
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.sessionId = null;
  }

  private startHeartbeat(): void {
    this.stopHeartbeat(); // Clear any existing heartbeat
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Send ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
}

// Text-to-Speech utility for feedback
export class TTSFeedback {
  private static readonly MAX_CACHE_ITEMS = 24;
  private lastSpokenTime: number = 0;
  private queue: string[] = [];
  private speaking: boolean = false;
  private enabled: boolean = true;
  private onSpeakingChange: ((isSpeaking: boolean) => void) | null = null;
  private onTextChange: ((text: string) => void) | null = null;
  private queueTimer: ReturnType<typeof setTimeout> | null = null;
  private currentText: string = '';
  private currentAudio: HTMLAudioElement | null = null;
  private abortController: AbortController | null = null;
  private playbackToken: number = 0;
  private audioCache: Map<string, Blob> = new Map();
  private prefetchRequests: Map<string, Promise<Blob>> = new Map();
  private ttsAudioContext: AudioContext | null = null;
  private ttsAudioFrame: number | null = null;

  constructor(onSpeakingChange?: (isSpeaking: boolean) => void, onTextChange?: (text: string) => void) {
    this.onSpeakingChange = onSpeakingChange || null;
    this.onTextChange = onTextChange || null;
  }

  setSpeakingChangeHandler(handler: (isSpeaking: boolean) => void): void {
    this.onSpeakingChange = handler;
  }

  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    if (!enabled) {
      this.stop();
    }
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  speak(text: string, priority: boolean = false): void {
    if (!this.enabled || !text) return;

    console.log('TTS speak called:', text, 'priority:', priority, 'queue length:', this.queue.length);

    if (priority) {
      this.queue.unshift(text);
      this.clearQueueTimer();
      this.processQueue();
    } else {
      if (this.queue.length < 5) {
        this.queue.push(text);
        // NO PREFETCH - Direct processing to eliminate delay
        this.processQueue();
      }
    }
  }

  prefetch(text: string | null | undefined): void {
    if (!this.enabled || !text) return;

    const key = this.getCacheKey(text);
    if (!key || this.audioCache.has(key) || this.prefetchRequests.has(key)) return;

    const request = this.requestSpeechBlob(text)
      .then((blob) => {
        this.cacheAudioBlob(key, blob);
        return blob;
      })
      .catch((error) => {
        console.warn('TTS prefetch failed:', error);
        throw error;
      })
      .finally(() => {
        this.prefetchRequests.delete(key);
      });

    this.prefetchRequests.set(key, request);
    void request.catch(() => undefined);
  }

  prefetchMany(texts: Array<string | null | undefined>): void {
    texts.forEach((text) => this.prefetch(text));
  }

  private clearQueueTimer(): void {
    if (this.queueTimer) {
      clearTimeout(this.queueTimer);
      this.queueTimer = null;
    }
  }

  private processQueue(): void {
    if (this.speaking || this.queue.length === 0) return;

    const next = this.queue.shift();
    if (next) {
      void this.speakNow(next);
    }
  }

  private async prefetchNext(): Promise<void> {
    const next = this.queue[0];
    if (next) {
      this.prefetch(next);
    }
    return Promise.resolve();
  }

  private getCacheKey(text: string): string {
    return text.replace(/\s+/g, ' ').trim();
  }

  private cacheAudioBlob(key: string, blob: Blob): void {
    if (!key) return;
    if (this.audioCache.has(key)) {
      this.audioCache.delete(key);
    }
    this.audioCache.set(key, blob);
    while (this.audioCache.size > TTSFeedback.MAX_CACHE_ITEMS) {
      const oldestKey = this.audioCache.keys().next().value;
      if (!oldestKey) break;
      this.audioCache.delete(oldestKey);
    }
  }

  private async requestSpeechBlob(text: string, signal?: AbortSignal): Promise<Blob> {
    const res = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, voice: 'nova' }),
      signal,
    });

    if (!res.ok) {
      const details = await res.text().catch(() => '');
      throw new Error(`TTS request failed: ${res.status} ${details ? `- ${details}` : ''}`);
    }

    return res.blob();
  }

  private async getSpeechBlob(text: string, signal?: AbortSignal): Promise<Blob> {
    const key = this.getCacheKey(text);
    const cached = this.audioCache.get(key);
    if (cached) {
      return cached;
    }

    const pending = this.prefetchRequests.get(key);
    if (pending) {
      const blob = await pending;
      this.cacheAudioBlob(key, blob);
      return blob;
    }

    const blob = await this.requestSpeechBlob(text, signal);
    this.cacheAudioBlob(key, blob);
    return blob;
  }

  private async speakNow(text: string): Promise<void> {
    this.stopCurrentPlayback();

    const token = ++this.playbackToken;
    this.speaking = true;
    this.currentText = text;
    this.onTextChange?.(text);
    this.lastSpokenTime = Date.now();

    try {
      this.abortController = new AbortController();
      const cacheKey = this.getCacheKey(text);
      if (!this.audioCache.has(cacheKey)) {
        console.log('⏳ Fetching TTS for:', text);
      }
      const blob = await this.getSpeechBlob(text, this.abortController.signal);
      if (token !== this.playbackToken || !this.speaking || this.currentText !== text) {
        return;
      }

      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.preload = 'auto';
      this.currentAudio = audio;

      await new Promise<void>((resolve, reject) => {
        if (audio.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
          resolve();
          return;
        }
        const timer = setTimeout(() => resolve(), 400);
        audio.oncanplay = () => {
          clearTimeout(timer);
          resolve();
        };
        audio.onerror = () => {
          clearTimeout(timer);
          reject(new Error('Audio preload error'));
        };
        audio.load();
      });

      if (token !== this.playbackToken || !this.speaking || this.currentText !== text) {
        URL.revokeObjectURL(url);
        return;
      }

      // Give React/Avatar3D one tiny frame to open lip-sync before the first syllable.
      this.onSpeakingChange?.(true);
      await new Promise((resolve) => setTimeout(resolve, 120));

      if (token !== this.playbackToken || !this.speaking || this.currentText !== text) {
        URL.revokeObjectURL(url);
        return;
      }

      await new Promise<void>((resolve, reject) => {
        audio.onended = () => resolve();
        audio.onerror = () => reject(new Error('Audio playback error'));
        audio.play().catch(reject);
        this.startTTSLevelEmitter(audio, text);
      });
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('TTS playback error:', e);
    } finally {
      if (token === this.playbackToken) {
        this.speaking = false;
        this.currentText = '';
        this.onSpeakingChange?.(false);
        this.onTextChange?.('');
        this.abortController = null;
        this.stopTTSLevelEmitter();

        void this.prefetchNext();
        this.processQueue();
      }
    }
  }

  private async startTTSLevelEmitter(audio: HTMLAudioElement, text: string): Promise<void> {
    this.stopTTSLevelEmitter(false);

    try {
      const AudioContextCtor =
        window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioContextCtor) return;

      const ctx = new AudioContextCtor();
      this.ttsAudioContext = ctx;
      if (ctx.state === 'suspended') {
        await ctx.resume().catch(() => undefined);
      }

      const source = ctx.createMediaElementSource(audio);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.35;
      source.connect(analyser);
      analyser.connect(ctx.destination);

      const data = new Uint8Array(analyser.fftSize);
      const tick = () => {
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i += 1) {
          const centered = (data[i] - 128) / 128;
          sum += centered * centered;
        }
        const rms = Math.sqrt(sum / data.length);
        const level = Math.min(1, Math.max(0, rms * 5.5));
        window.dispatchEvent(new CustomEvent('eeknova-tts-audio', {
          detail: {
            isSpeaking: true,
            level,
            text,
            currentTime: audio.currentTime,
            duration: Number.isFinite(audio.duration) ? audio.duration : 0,
          },
        }));

        if (!audio.paused && !audio.ended) {
          this.ttsAudioFrame = requestAnimationFrame(tick);
        }
      };

      tick();
    } catch (error) {
      console.warn('TTS audio level analyser unavailable:', error);
      window.dispatchEvent(new CustomEvent('eeknova-tts-audio', {
        detail: { isSpeaking: true, level: 0.45, text, currentTime: 0, duration: 0 },
      }));
    }
  }

  private stopTTSLevelEmitter(dispatchEnded: boolean = true): void {
    if (this.ttsAudioFrame !== null) {
      cancelAnimationFrame(this.ttsAudioFrame);
      this.ttsAudioFrame = null;
    }

    if (dispatchEnded) {
      window.dispatchEvent(new CustomEvent('eeknova-tts-audio', {
        detail: { isSpeaking: false, level: 0, text: '', currentTime: 0, duration: 0 },
      }));
    }

    const ctx = this.ttsAudioContext;
    this.ttsAudioContext = null;
    if (ctx) {
      void ctx.close().catch(() => undefined);
    }
  }

  private stopCurrentPlayback(): void {
    // Gracefully stop current playback without force abort
    if (this.currentAudio) {
      try {
        this.currentAudio.pause();
      } catch {}
      this.currentAudio = null;
    }
    this.stopTTSLevelEmitter();
    
    // Reset speaking state
    if (this.speaking) {
      this.speaking = false;
      this.currentText = '';
      this.onSpeakingChange?.(false);
      this.onTextChange?.('');
    }
  }

  stop(): void {
    this.playbackToken += 1;
    this.clearQueueTimer();
    this.queue = [];
    this.stopCurrentPlayback();

    if (this.speaking) {
      this.speaking = false;
      this.currentText = '';
      this.onSpeakingChange?.(false);
      this.onTextChange?.('');
    }
  }

  speakCorrections(corrections: string[]): void {
    if (!this.enabled || corrections.length === 0) return;

    const mainCorrection = corrections[0];
    const simplifiedMessage = this.simplifyCorrection(mainCorrection);
    this.speak(simplifiedMessage);
  }

  private simplifyCorrection(correction: string): string {
    let simplified = correction
      .replace(/\(by \d+\.\d+Â°\)/g, '')
      .replace(/\d+\.\d+Â°/g, '')
      .replace(/\(by \d+\.\d+°\)/g, '')
      .replace(/\d+\.\d+°/g, '')
      .trim();

    simplified = simplified
      .replace('Adjust your ', '')
      .replace(' more', '');

    return simplified;
  }
}
// Skeleton Drawing Utilities
export const SKELETON_CONNECTIONS = [
  [15, 13], [13, 11], [16, 14], [14, 12], [11, 12], [5, 11], [6, 12],
  [5, 6], [5, 7], [6, 8], [7, 9], [8, 10], [1, 2], [0, 1], [0, 2],
  [1, 3], [2, 4], [3, 5], [4, 6]
];

export const KEYPOINT_COLORS = [
  '#FF8000', '#FF9933', '#FFB266', '#E6E600', '#FF99FF', '#99CCFF',
  '#FF66FF', '#FF33FF', '#66B2FF', '#3399FF', '#FF9999', '#FF6666',
  '#FF3333', '#99FF99', '#66FF66', '#33FF33', '#00FF00'
];

export const drawSkeleton = (
  ctx: CanvasRenderingContext2D,
  keypoints: number[][],
  angleStatus?: Record<string, { within_tolerance: boolean; difference: number | null }>,
  confidenceThreshold: number = 0.5
): void => {
  if (!keypoints || keypoints.length !== 17) return;

  // Draw connections
  SKELETON_CONNECTIONS.forEach(([i, j], idx) => {
    const [x1, y1, conf1] = keypoints[i];
    const [x2, y2, conf2] = keypoints[j];

    if (conf1 > confidenceThreshold && conf2 > confidenceThreshold) {
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = KEYPOINT_COLORS[idx % KEYPOINT_COLORS.length];
      ctx.lineWidth = 3;
      ctx.stroke();
    }
  });

  // Draw keypoints
  keypoints.forEach(([x, y, conf], idx) => {
    if (conf > confidenceThreshold) {
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, 2 * Math.PI);
      ctx.fillStyle = KEYPOINT_COLORS[idx % KEYPOINT_COLORS.length];
      ctx.fill();
      ctx.strokeStyle = '#FFFFFF';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  });
};

export default {
  startSession,
  stopSession,
  getAvailablePoses,
  getModelStatus,
  analyzeFrame,
  YogaPoseWebSocket,
  TTSFeedback,
  drawSkeleton,
};







