'use client';
import React, { useRef, useState, useEffect, useCallback } from 'react';
import {
  YogaPoseWebSocket,
  TTSFeedback,
  startSession,
  stopSession,
  analyzeFrame,
  updateSessionPose,
  drawSkeleton,
  PoseAnalysisResult,
  SessionSummary,
} from '@/lib/yogaApi';

interface YogaCameraProps {
  selectedPose: string;
  isStarted: boolean;
  onSessionEnd: (summary: SessionSummary | null) => void;
  onAccuracyUpdate: (accuracy: number) => void;
  onCorrectionsUpdate: (corrections: string[]) => void;
  onPhaseChange?: (phase: 'in' | 'hold' | 'out' | 'idle', timeLeft: number) => void;
  onTTSSpeakingChange?: (speaking: boolean) => void;
  onTTSTextChange?: (text: string) => void;
  tolerance?: number;
  mirrorMode?: boolean;
}

export default function YogaCamera({
  selectedPose,
  isStarted,
  onSessionEnd,
  onAccuracyUpdate,
  onCorrectionsUpdate,
  onPhaseChange,
  onTTSSpeakingChange,
  onTTSTextChange,
  tolerance = 10.0,
  mirrorMode = true,
}: YogaCameraProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<YogaPoseWebSocket | null>(null);
  const ttsRef = useRef<TTSFeedback | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const frameIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [isCameraReady, setIsCameraReady] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentPose, setCurrentPose] = useState<string | null>(null);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [poseDetected, setPoseDetected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [lastResult, setLastResult] = useState<PoseAnalysisResult | null>(null);
  const [frameCount, setFrameCount] = useState(0);
  const [avgAccuracy, setAvgAccuracy] = useState(0);
  const [sessionStartTime, setSessionStartTime] = useState<number | null>(null);

  // Initialize TTS
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      ttsRef.current = new TTSFeedback(onTTSSpeakingChange, onTTSTextChange);
      console.log('TTS initialized');
    } else {
      console.warn('TTS not supported in this browser');
    }
  }, [onTTSSpeakingChange, onTTSTextChange]);

  useEffect(() => {
    return () => {
      ttsRef.current?.stop();
    };
  }, []);

  // Update TTS enabled state
  useEffect(() => {
    ttsRef.current?.setEnabled(ttsEnabled);
  }, [ttsEnabled]);

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
            setError(null);
          };
        }
      } catch (err) {
        console.error('Camera access error:', err);
        setError('Unable to access camera. Please grant camera permissions.');
        setIsCameraReady(false);
      }
    };

    initCamera();

    return () => {
      // Cleanup camera
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Handle WebSocket messages
  const handlePoseResult = useCallback(
    (result: PoseAnalysisResult) => {
      setLastResult(result);

      // Handle session stopped message from WebSocket
      if (result.type === 'analysis_stopped') {
        const summary: SessionSummary | null = result.summary || {
          session_id: result.session_id || 'websocket-session',
          duration_seconds: result.duration_seconds || (sessionStartTime ? Math.floor((Date.now() - sessionStartTime) / 1000) : 0),
          frames_processed: result.frames_processed || 0,
          average_accuracy: result.average_accuracy || 0,
          corrections_given: result.corrections_given || 0,
          pose_name: result.pose_name
        };
        
        console.log('Session ended from WebSocket:', summary);
        onSessionEnd(summary);
        ttsRef.current?.speak('Session ended. Great workout!', true);
        
        // Stop analysis without calling onSessionEnd again
        setIsAnalyzing(false);
        setIsConnected(false);
        setPoseDetected(false);
        setCurrentPose(null);
        setAccuracy(null);
        setSessionStartTime(null);
        
        // Disconnect WebSocket
        if (wsRef.current) {
          wsRef.current.disconnect();
          wsRef.current = null;
        }
        return;
      }

      if (result.pose_detected) {
        setPoseDetected(true);
        setCurrentPose(result.pose_name || null);

        if (result.accuracy !== null && result.accuracy !== undefined) {
          setAccuracy(result.accuracy);
          onAccuracyUpdate(result.accuracy);
        }

        // Handle corrections and TTS
        if (result.corrections && result.corrections.length > 0) {
          onCorrectionsUpdate(result.corrections);
          console.log('Speaking corrections:', result.corrections);
          // Add delay to avoid TTS conflicts
          setTimeout(() => {
            ttsRef.current?.speakCorrections(result.corrections || []);
          }, 200);
        } else if (result.accuracy && result.accuracy >= 80) {
          // Good pose feedback (less frequent)
          if (Math.random() < 0.1) {
            console.log('Speaking good feedback');
            setTimeout(() => {
              ttsRef.current?.speak('Great form! Keep it up!');
            }, 300);
          }
        }

        // Update session stats
        if (result.session_stats) {
          setFrameCount(result.session_stats.frames_processed);
          setAvgAccuracy(result.session_stats.average_accuracy);
        }

        // Draw skeleton overlay
        if (result.keypoints && overlayCanvasRef.current) {
          const ctx = overlayCanvasRef.current.getContext('2d');
          if (ctx) {
            ctx.clearRect(
              0,
              0,
              overlayCanvasRef.current.width,
              overlayCanvasRef.current.height
            );
            drawSkeleton(ctx, result.keypoints, result.angle_status);
          }
        }
      } else {
        setPoseDetected(false);
        setCurrentPose(null);

        // Clear overlay
        if (overlayCanvasRef.current) {
          const ctx = overlayCanvasRef.current.getContext('2d');
          if (ctx) {
            ctx.clearRect(
              0,
              0,
              overlayCanvasRef.current.width,
              overlayCanvasRef.current.height
            );
          }
        }
      }
    },
    [onAccuracyUpdate, onCorrectionsUpdate, onSessionEnd]
  );

  // Start/Stop analysis based on isStarted prop
  useEffect(() => {
    if (isStarted && isCameraReady) {
      startAnalysis();
    } else if (!isStarted) {
      stopAnalysis();
    }

    return () => {
      stopAnalysis();
    };
  }, [isStarted, isCameraReady]);

  // Handle pose changes during active session
  const prevSelectedPoseRef = useRef<string>('');
  
  useEffect(() => {
    // Only handle pose changes if session is active and pose actually changed
    if (isStarted && isCameraReady && wsRef.current?.isConnected() && 
        selectedPose && selectedPose !== prevSelectedPoseRef.current) {
      
      const apiPoseName = convertPoseNameToApi(selectedPose);
      wsRef.current.startAnalysis(apiPoseName, tolerance);
      ttsRef.current?.speak(`Switched to ${selectedPose} pose.`, true);
      
      prevSelectedPoseRef.current = selectedPose;
    }
  }, [selectedPose, isStarted, isCameraReady]);

  // Convert pose name to API format
  const convertPoseNameToApi = (poseName: string): string => {
    // Convert "Mountain Pose" to "mountain_pose" format
    return poseName.toLowerCase().replace(/\s+/g, '_');
  };

  // Start analysis
  const startAnalysis = async () => {
    if (!isCameraReady) {
      setError('Camera not ready');
      return;
    }

    try {
      // Clear any existing session
      if (sessionIdRef.current) {
        wsRef.current?.stopAnalysis();
        sessionIdRef.current = null;
      }

      // Initialize WebSocket
      wsRef.current = new YogaPoseWebSocket(
        // Handle pose results
        handlePoseResult,
        // Handle errors
        (error: string) => {
          console.error('WebSocket error:', error);
          setError(error);
        },
        // Handle connection
        () => {
          setIsConnected(true);
          console.log('WebSocket connected');
        },
        // Handle disconnection
        () => {
          setIsConnected(false);
          console.log('WebSocket disconnected');
        }
      );

      // Connect to WebSocket
      await wsRef.current.connect();
      
      // Wait a moment for connection to stabilize
      await new Promise(resolve => setTimeout(resolve, 100));

      // Start analysis via WebSocket
      const apiPoseName = convertPoseNameToApi(selectedPose);
      wsRef.current.startAnalysis(apiPoseName, tolerance);

      // Announce the start
      ttsRef.current?.speak(`Starting ${selectedPose} detection. Get into position.`, true);

      // Start sending frames via WebSocket
      startFrameCapture();
      
      // Set session start time
      setSessionStartTime(Date.now());
      setIsAnalyzing(true);
    } catch (err) {
      console.error('Failed to start analysis:', err);
      setError('Failed to connect to the yoga server. Make sure the backend is running.');
      setIsAnalyzing(false);
    }
  };

  // Stop analysis
  const stopAnalysis = async () => {
    // Prevent multiple calls
    if (!isAnalyzing) return;
    
    // Stop frame capture
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }

    // Calculate final session duration before stopping
    const finalDuration = sessionStartTime ? Math.floor((Date.now() - sessionStartTime) / 1000) : 0;
    console.log('Final session duration:', finalDuration, 'seconds');

  // Stop WebSocket analysis
    if (wsRef.current) {
      try {
        wsRef.current.stopAnalysis();
        
        // Wait for WebSocket session end, if not received, create local summary
        setTimeout(() => {
          if (isAnalyzing) { // Only if WebSocket didn't end the session
            const summary: SessionSummary = {
              session_id: 'local-session',
              duration_seconds: finalDuration,
              frames_processed: frameCount,
              average_accuracy: avgAccuracy,
              corrections_given: (lastResult as any)?.corrections?.length || 0,
              pose_name: selectedPose
            };
            
            console.log('Final session summary (local):', summary);
            onSessionEnd(summary);
            ttsRef.current?.speak('Session ended. Great workout!', true);
          }
        }, 1000);
        
      } catch (err) {
        console.error('Failed to stop session:', err);
        // Still provide summary even on error
        const summary: SessionSummary = {
          session_id: 'local-session',
          duration_seconds: finalDuration,
          frames_processed: frameCount,
          average_accuracy: avgAccuracy,
          corrections_given: (lastResult as any)?.corrections?.length || 0,
          pose_name: selectedPose
        };
        onSessionEnd(summary);
      }
      
      // Disconnect WebSocket after a delay
      setTimeout(() => {
        if (wsRef.current) {
          wsRef.current.disconnect();
          wsRef.current = null;
        }
      }, 2000);
    }

    setIsAnalyzing(false);
    setIsConnected(false);
    setPoseDetected(false);
    setCurrentPose(null);
    setAccuracy(null);
    setSessionStartTime(null);

    // Clear overlay
    if (overlayCanvasRef.current) {
      const ctx = overlayCanvasRef.current.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height);
      }
    }
  };

  // Capture and send frames
  const startFrameCapture = () => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
    }

    // Capture frames every 500ms (2 FPS for smooth analysis without overloading)
    frameIntervalRef.current = setInterval(async () => {
      if (!videoRef.current || !canvasRef.current || !wsRef.current) return;

      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');

      if (!ctx) return;

      // Set canvas size to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Also update overlay canvas size
      if (overlayCanvasRef.current) {
        overlayCanvasRef.current.width = video.videoWidth;
        overlayCanvasRef.current.height = video.videoHeight;
      }

      // Draw video frame to canvas
      if (mirrorMode) {
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
      }
      ctx.drawImage(video, 0, 0);
      if (mirrorMode) {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
      }

      // Convert to base64
      const frameData = canvas.toDataURL('image/jpeg', 0.7);

      try {
        // Send frame for analysis via WebSocket
        if (wsRef.current?.isConnected()) {
          wsRef.current.sendFrame(frameData);
          console.log('Frame sent for analysis');
        } else {
          console.log('WebSocket not connected, skipping frame');
        }
      } catch (err) {
        console.error('Frame analysis error:', err);
      }
    }, 500);
  };

  return (
    <div className="relative w-full">
      {/* Camera container */}
      <div className="relative rounded-[var(--radius-lg)] overflow-hidden border border-[var(--glass-stroke)]">
        {/* Video element */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-auto"
          style={{
            transform: mirrorMode ? 'scaleX(-1)' : 'none',
            maxHeight: '400px',
            objectFit: 'cover',
          }}
        />

        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Overlay canvas for skeleton */}
        <canvas
          ref={overlayCanvasRef}
          className="absolute top-0 left-0 w-full h-full pointer-events-none"
          style={{
            transform: mirrorMode ? 'scaleX(-1)' : 'none',
          }}
        />

        {/* Status overlays */}
        {!isCameraReady && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/70">
            <div className="text-center">
              <div className="text-[var(--brand-neo)] text-xl mb-2">
                Initializing Camera...
              </div>
              <div className="text-[var(--ink-med)]">
                Please allow camera access
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-red-900/70">
            <div className="text-center text-white p-4">
              <div className="text-xl mb-2">Error</div>
              <div>{error}</div>
            </div>
          </div>
        )}

        {/* Pose detection status */}
        {isAnalyzing && (
          <div className="absolute top-3 left-3 right-3 flex justify-between items-start">
            {/* Current pose indicator */}
            <div
              className={`px-3 py-1 rounded-full text-sm font-semibold ${poseDetected
                  ? 'bg-green-500/80 text-white'
                  : 'bg-orange-500/80 text-white'
                }`}
            >
              {poseDetected
                ? `Detecting: ${selectedPose}`
                : 'Get into position...'}
            </div>

            {/* TTS toggle */}
            <button
              onClick={() => setTtsEnabled(!ttsEnabled)}
              className={`px-3 py-1 rounded-full text-sm font-semibold transition-all ${ttsEnabled
                  ? 'bg-[var(--brand-neo)]/80 text-black'
                  : 'bg-gray-500/80 text-white'
                }`}
            >
              {ttsEnabled ? '🔊 Voice On' : '🔇 Voice Off'}
            </button>
          </div>
        )}

        {/* Accuracy display */}
        {isAnalyzing && accuracy !== null && (
          <div className="absolute bottom-3 left-3 right-3">
            <div className="bg-black/60 rounded-lg p-3">
              <div className="flex justify-between items-center mb-2">
                <span className="text-white text-sm">Accuracy</span>
                <span
                  className={`text-lg font-bold ${accuracy >= 80
                      ? 'text-green-400'
                      : accuracy >= 50
                        ? 'text-yellow-400'
                        : 'text-red-400'
                    }`}
                >
                  {accuracy.toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${accuracy >= 80
                      ? 'bg-green-500'
                      : accuracy >= 50
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                  style={{ width: `${Math.min(100, accuracy)}%` }}
                />
              </div>
              {/* Session stats */}
              <div className="flex justify-between text-xs text-gray-400 mt-2">
                <span>Frames: {frameCount}</span>
                <span>Avg: {avgAccuracy.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Analysis status bar */}
      {isStarted && (
        <div className="mt-2 flex justify-center">
          <div className="flex items-center gap-2 text-sm text-[var(--ink-med)]">
            <div
              className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                }`}
            />
            <span>
              {isConnected ? 'Connected' : 'Connecting...'}
            </span>
            {isAnalyzing && (
              <>
                <span className="mx-1">•</span>
                <span>Analyzing...</span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
