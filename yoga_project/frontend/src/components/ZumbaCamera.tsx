// ZumbaCamera.tsx - Real-time Zumba dance analysis component
'use client';

import React, { useRef, useState, useEffect, useCallback } from 'react';
import {
  ZumbaWebSocket,
  startZumbaSession,
  endZumbaSession,
  analyzeZumbaFrame,
  getZumbaMoves,
  ZumbaSessionStartRequest,
  ZumbaAnalysisResult,
  ZumbaSessionSummary,
  canvasToBase64,
} from '@/lib/zumbaApi';

interface ZumbaCameraProps {
  selectedMove: string;
  isStarted: boolean;
  onSessionEnd: (summary: ZumbaSessionSummary | null) => void;
  onAccuracyUpdate: (accuracy: number) => void;
  onFeedbackUpdate: (feedback: string[]) => void;
  onFrameProcessed?: (result: ZumbaAnalysisResult) => void;
  onError?: (error: string) => void;
  tolerance?: number;
  mirrorMode?: boolean;
}

export default function ZumbaCamera({
  selectedMove,
  isStarted,
  onSessionEnd,
  onAccuracyUpdate,
  onFeedbackUpdate,
  onFrameProcessed,
  onError,
  tolerance = 15.0,
  mirrorMode = true,
}: ZumbaCameraProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<ZumbaWebSocket | null>(null);
  const frameIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [isCameraReady, setIsCameraReady] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentMove, setCurrentMove] = useState<string | null>(null);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [poseDetected, setPoseDetected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableMoves, setAvailableMoves] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [processedFrame, setProcessedFrame] = useState<string | null>(null);
  const [feedbackMessages, setFeedbackMessages] = useState<string[]>([]);

  // Load available moves on mount
  useEffect(() => {
    const loadMoves = async () => {
      try {
        const moves = await getZumbaMoves();
        setAvailableMoves(moves);
      } catch (error) {
        console.error('Failed to load Zumba moves:', error);
        setError('Failed to load available moves');
      }
    };
    loadMoves();
  }, []);

  // Initialize camera
  useEffect(() => {
    const initCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user',
          },
          audio: false,
        });

        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = () => {
            videoRef.current?.play();
            setIsCameraReady(true);
          };
        }
      } catch (error) {
        console.error('Camera initialization error:', error);
        setError('Failed to access camera');
      }
    };

    initCamera();

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    if (!sessionId) return;

    const ws = new ZumbaWebSocket(
      // onResult
      (result: ZumbaAnalysisResult) => {
        setPoseDetected(result.pose_detected || false);
        setAccuracy(result.accuracy || null);
        setFeedbackMessages(result.feedback_messages || []);
        setProcessedFrame(result.processed_frame || null);
        
        // Update parent components
        if (result.accuracy !== undefined) {
          onAccuracyUpdate(result.accuracy);
        }
        if (result.feedback_messages && result.feedback_messages.length > 0) {
          onFeedbackUpdate(result.feedback_messages);
        }
        if (onFrameProcessed) {
          onFrameProcessed(result);
        }
      },
      // onError
      (errorMessage: string) => {
        console.error('Zumba WebSocket error:', errorMessage);
        setError(errorMessage);
        if (onError) {
          onError(errorMessage);
        }
      },
      // onConnect
      () => {
        setIsConnected(true);
        console.log('Zumba WebSocket connected');
      },
      // onDisconnect
      () => {
        setIsConnected(false);
        console.log('Zumba WebSocket disconnected');
      }
    );

    ws.connect(sessionId);
    wsRef.current = ws;

    return () => {
      // Only disconnect if component is unmounting, not on re-render
      if (wsRef.current === ws) {
        ws.disconnect();
      }
    };
  }, [sessionId]);

  // Start/Stop analysis
  useEffect(() => {
    if (!isCameraReady || !selectedMove) return;

    if (isStarted && !sessionId) {
      // Start session
      const startSession = async () => {
        try {
          const sessionRequest: ZumbaSessionStartRequest = {
            target_move: selectedMove,
            settings: {
              tolerance,
              feedback_interval: 3.0,
              min_feedback_gap: 2.0,
            },
          };

          const session = await startZumbaSession(sessionRequest);
          setSessionId(session.session_id);
          setCurrentMove(selectedMove);
          setIsAnalyzing(true);
          setError(null);
        } catch (error) {
          console.error('Failed to start Zumba session:', error);
          setError('Failed to start analysis session');
        }
      };

      startSession();
    } else if (!isStarted && sessionId) {
      // Stop session
      const stopSession = async () => {
        // Immediately stop frame processing
        if (frameIntervalRef.current) {
          clearInterval(frameIntervalRef.current);
          frameIntervalRef.current = null;
        }
        
        try {
          const summary = await endZumbaSession(sessionId);
          onSessionEnd(summary);
        } catch (error) {
          console.error('Failed to end Zumba session:', error);
          onSessionEnd(null);
        } finally {
          setSessionId(null);
          setCurrentMove(null);
          setIsAnalyzing(false);
          setFeedbackMessages([]);
          setProcessedFrame(null);
        }
      };

      stopSession();
    }
  }, [isStarted, isCameraReady, selectedMove, sessionId, tolerance, onSessionEnd]);

  // Frame processing loop - using YogaCamera's smooth approach
  useEffect(() => {
    if (!isAnalyzing || !isConnected || !videoRef.current || !sessionId) return;

    let lastFrameTime = 0;
    const minFrameInterval = 300; // 3 FPS max for integrated GPU

    const startFrameCapture = () => {
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
      }

      // Check frames frequently but only process at controlled rate
      frameIntervalRef.current = setInterval(async () => {
        if (!videoRef.current || !canvasRef.current || !wsRef.current) return;

        // Skip frames if processing too fast
        const now = Date.now();
        if (now - lastFrameTime < minFrameInterval) {
          return;
        }

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        if (!ctx) return;

        // Set canvas size to optimized size for integrated GPU
        // But keep video display large
        canvas.width = 160;  // Very small for integrated GPU
        canvas.height = 120; // 4:3 aspect ratio
        
        // Draw video frame to canvas (scaled down for processing)
        if (mirrorMode) {
          ctx.translate(canvas.width, 0);
          ctx.scale(-1, 1);
        }
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        if (mirrorMode) {
          ctx.setTransform(1, 0, 0, 1, 0, 0);
        }

        // Convert to base64 with optimized quality for 30 FPS
        const frameData = canvas.toDataURL('image/jpeg', 0.3); // Further reduced for speed

        try {
          // Send frame for analysis via WebSocket
          if (wsRef.current?.isConnected()) {
            wsRef.current.sendFrame(frameData);
            lastFrameTime = now;
          }
        } catch (err) {
          console.error('Frame analysis error:', err);
        }
      }, 33); // Check every 33ms but only process if enough time passed
    };

    // Start frame capture immediately
    startFrameCapture();

    return () => {
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
      }
    };
  }, [isAnalyzing, isConnected, sessionId, mirrorMode]);

  // Draw processed frame on overlay canvas
  useEffect(() => {
    if (!processedFrame || !overlayCanvasRef.current) return;

    const canvas = overlayCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      
      if (mirrorMode) {
        ctx.scale(-1, 1);
        ctx.drawImage(img, -canvas.width, 0, canvas.width, canvas.height);
      } else {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      }
    };
    img.src = processedFrame;
  }, [processedFrame, mirrorMode]);

  return (
    <div className="relative w-full h-full">
      {/* Camera/Video Feed */}
      <div className="relative w-full h-full">
        <video
          ref={videoRef}
          className={`absolute inset-0 w-full h-full object-cover ${mirrorMode ? 'scale-x-[-1]' : ''}`}
          autoPlay
          playsInline
          muted
        />
        
        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />
        
        {/* Processed Frame Overlay */}
        {processedFrame && (
          <canvas
            ref={overlayCanvasRef}
            className={`absolute inset-0 w-full h-full object-cover ${mirrorMode ? 'scale-x-[-1]' : ''}`}
          />
        )}
      </div>

      {/* Status Overlay */}
      <div className="absolute top-4 left-4 right-4 flex justify-between items-start">
        <div className="bg-black/50 backdrop-blur-sm rounded-lg p-3 text-white">
          <div className="text-sm font-semibold">
            {isAnalyzing ? 'Analyzing' : 'Ready'}
          </div>
          {currentMove && (
            <div className="text-xs opacity-80">
              Move: {currentMove}
            </div>
          )}
          {poseDetected && (
            <div className="text-xs text-green-400">
              Pose Detected ✓
            </div>
          )}
        </div>

        {accuracy !== null && (
          <div className="bg-black/50 backdrop-blur-sm rounded-lg p-3 text-white">
            <div className="text-sm font-semibold">
              Accuracy: {accuracy.toFixed(1)}%
            </div>
          </div>
        )}
      </div>

      {/* Feedback Messages */}
      {feedbackMessages && feedbackMessages.length > 0 && (
        <div className="absolute bottom-4 left-4 right-4">
          <div className="bg-black/50 backdrop-blur-sm rounded-lg p-3 text-white max-h-32 overflow-y-auto">
            <div className="text-sm font-semibold mb-2">Feedback:</div>
            {feedbackMessages.map((message, index) => (
              <div key={index} className="text-xs mb-1">
                • {message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connection Status */}
      <div className="absolute top-4 right-4">
        <div className={`w-3 h-3 rounded-full ${
          isConnected ? 'bg-green-500' : 'bg-red-500'
        }`} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="absolute inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center">
          <div className="bg-red-500 text-white rounded-lg p-4 max-w-md">
            <div className="font-semibold mb-2">Error</div>
            <div className="text-sm">{error}</div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {!isCameraReady && (
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center">
          <div className="text-white text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
            <div>Initializing camera...</div>
          </div>
        </div>
      )}
    </div>
  );
}
