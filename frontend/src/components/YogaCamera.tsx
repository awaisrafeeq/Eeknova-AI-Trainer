'use client';
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  YogaPoseWebSocket,
  TTSFeedback,
  updateSessionPose,
  drawSkeleton,
  PoseAnalysisResult,
  SessionSummary,
} from '@/lib/yogaApi';

let globalTTS: TTSFeedback | null = null;
let globalLastSpoken: { text: string; atMs: number } | null = null;
let globalTTSHandlersInstalled = false;
const globalCallbacks = {
  onSpeaking: null as null | ((speaking: boolean) => void),
  onText: null as null | ((text: string) => void),
  onGuidedEnd: null as null | (() => void),
  onReleaseEnd: null as null | (() => void),
  shouldIgnoreSpeakingFalse: null as null | (() => boolean),
  clearIgnoreSpeakingFalse: null as null | (() => void),
  isGuidedPending: null as null | (() => boolean),
  clearGuidedPending: null as null | (() => void),
  isReleasePending: null as null | (() => boolean),
  clearReleasePending: null as null | (() => void),
};

interface YogaCameraProps {
  selectedPose: string;
  shouldAnalyze: boolean;
  playGuidedInstructions: boolean;
  playReleaseInstructions: boolean;
  onSessionEnd: (summary: SessionSummary | null) => void;
  onAccuracyUpdate: (accuracy: number) => void;
  onCorrectionsUpdate: (corrections: string[]) => void;
  onPhaseChange?: (phase: 'in' | 'hold' | 'out' | 'idle', timeLeft: number) => void;
  currentPhase?: 'in' | 'hold' | 'out';
  onTTSSpeakingChange?: (speaking: boolean) => void;
  onTTSTextChange?: (text: string) => void;
  onGuidedInstructionsEnd?: () => void;
  onReleaseInstructionsEnd?: () => void;
  tolerance?: number;
  mirrorMode?: boolean;
  // When true, suppress correction feedback (UI + TTS). Used for the last few
  // seconds of the hold phase so the pose ends quietly.
  suppressFeedback?: boolean;
}

export default function YogaCamera({
  selectedPose,
  shouldAnalyze,
  playGuidedInstructions,
  playReleaseInstructions,
  onSessionEnd,
  onAccuracyUpdate,
  onCorrectionsUpdate,
  onPhaseChange,
  currentPhase,
  onTTSSpeakingChange,
  onTTSTextChange,
  onGuidedInstructionsEnd,
  onReleaseInstructionsEnd,
  tolerance = 10.0,
  mirrorMode = true,
  suppressFeedback = false,
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
  const [instructionSet, setInstructionSet] = useState<{ entry: string[]; release: string[] } | null>(null);
  const entryPlayedRef = useRef(false);
  const releasePlayedRef = useRef(false);
  const instructionPoseRef = useRef<string | null>(null);
  const suppressSessionEndRef = useRef(false);
  const ignoreSpeakingFalseRef = useRef(false);
  const isGuidedPhaseRef = useRef(false);
  const pendingGuidedEndRef = useRef(false);
  const pendingReleaseEndRef = useRef(false);
  const releaseEarliestEndAtRef = useRef(0);
  const releaseEndTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const guidedTimeoutsRef = useRef<Array<ReturnType<typeof setTimeout>>>([]);
  const prevPhaseRef = useRef<'in' | 'hold' | 'out' | 'idle' | null>(null);
  const correctionsGivenRef = useRef(0);
  const lastCorrectionSpokenRef = useRef<{ text: string; atMs: number } | null>(null);
  const prevPlayGuidedRef = useRef(false);
  const prevPlayReleaseRef = useRef(false);

  const onTTSSpeakingChangeRef = useRef<YogaCameraProps['onTTSSpeakingChange']>(onTTSSpeakingChange);
  const onTTSTextChangeRef = useRef<YogaCameraProps['onTTSTextChange']>(onTTSTextChange);
  const onGuidedInstructionsEndRef = useRef<YogaCameraProps['onGuidedInstructionsEnd']>(onGuidedInstructionsEnd);
  const onReleaseInstructionsEndRef = useRef<YogaCameraProps['onReleaseInstructionsEnd']>(onReleaseInstructionsEnd);
  const ttsInitializedRef = useRef(false);

  const playGuidedInstructionsRef = useRef(playGuidedInstructions);
  const playReleaseInstructionsRef = useRef(playReleaseInstructions);
  const suppressFeedbackRef = useRef(suppressFeedback);

  useEffect(() => {
    playGuidedInstructionsRef.current = playGuidedInstructions;
  }, [playGuidedInstructions]);

  useEffect(() => {
    playReleaseInstructionsRef.current = playReleaseInstructions;
  }, [playReleaseInstructions]);

  useEffect(() => {
    suppressFeedbackRef.current = suppressFeedback;
  }, [suppressFeedback]);

  // When the suppression window opens (final seconds of hold), stop any correction
  // TTS that is already speaking. Guided/release instruction TTS is only active in
  // their own phases, so this is safe to call here.
  useEffect(() => {
    if (!suppressFeedback) return;
    if (playGuidedInstructionsRef.current || playReleaseInstructionsRef.current) return;
    try {
      if (ttsRef.current) {
        ignoreSpeakingFalseRef.current = true;
        ttsRef.current.stop();
      }
    } catch { }
    // Also clear any previously shown corrections in the parent UI.
    onCorrectionsUpdate([]);
  }, [suppressFeedback, onCorrectionsUpdate]);

  useEffect(() => {
    onTTSSpeakingChangeRef.current = onTTSSpeakingChange;
  }, [onTTSSpeakingChange]);

  useEffect(() => {
    onTTSTextChangeRef.current = onTTSTextChange;
  }, [onTTSTextChange]);

  useEffect(() => {
    onGuidedInstructionsEndRef.current = onGuidedInstructionsEnd;
  }, [onGuidedInstructionsEnd]);

  useEffect(() => {
    onReleaseInstructionsEndRef.current = onReleaseInstructionsEnd;
  }, [onReleaseInstructionsEnd]);

  useEffect(() => {
    // Keep singleton callbacks in sync with the latest refs for this mounted component.
    globalCallbacks.onSpeaking = (speaking: boolean) => onTTSSpeakingChangeRef.current?.(speaking);
    globalCallbacks.onText = (text: string) => onTTSTextChangeRef.current?.(text);
    globalCallbacks.onGuidedEnd = () => {
      console.log('[YogaCamera] Guided instructions ended');
      onGuidedInstructionsEndRef.current?.();
    };
    globalCallbacks.onReleaseEnd = () => {
      console.log('[YogaCamera] Release instructions ended');
      onReleaseInstructionsEndRef.current?.();
    };
    globalCallbacks.shouldIgnoreSpeakingFalse = () => ignoreSpeakingFalseRef.current;
    globalCallbacks.clearIgnoreSpeakingFalse = () => {
      ignoreSpeakingFalseRef.current = false;
    };
    globalCallbacks.isGuidedPending = () => pendingGuidedEndRef.current;
    globalCallbacks.clearGuidedPending = () => {
      pendingGuidedEndRef.current = false;
      isGuidedPhaseRef.current = false;
    };
    globalCallbacks.isReleasePending = () => pendingReleaseEndRef.current;
    globalCallbacks.clearReleasePending = () => {
      pendingReleaseEndRef.current = false;
      releaseEarliestEndAtRef.current = 0;
      if (releaseEndTimerRef.current) {
        clearTimeout(releaseEndTimerRef.current);
        releaseEndTimerRef.current = null;
      }
    };
  });

  const safeStopTTS = () => {
    try {
      if (ttsRef.current) {
        ignoreSpeakingFalseRef.current = true;
        ttsRef.current.stop();
      }
    } catch (error) {
      console.log('TTS stop error (safe):', error);
    }
  };

  // Initialize TTS
  useEffect(() => {
    if (ttsInitializedRef.current) {
      return;
    }
    ttsInitializedRef.current = true;

    if (!globalTTSHandlersInstalled) {
      const speakingHandler = (speaking: boolean) => {
        globalCallbacks.onSpeaking?.(speaking);

        if (speaking) {
          return;
        }

        // If we manually stopped TTS (cleanup / transition), don't treat it as "finished speaking".
        if (globalCallbacks.shouldIgnoreSpeakingFalse?.()) {
          globalCallbacks.clearIgnoreSpeakingFalse?.();
        }

        if (globalCallbacks.isGuidedPending?.()) {
          globalCallbacks.clearGuidedPending?.();
          globalCallbacks.onGuidedEnd?.();
          return;
        }

        if (globalCallbacks.isReleasePending?.()) {
          const now = Date.now();
          const earliestEndAt = releaseEarliestEndAtRef.current;
          const remainingMs = Math.max(0, earliestEndAt - now);
          if (remainingMs > 0) {
            if (releaseEndTimerRef.current) {
              clearTimeout(releaseEndTimerRef.current);
            }
            releaseEndTimerRef.current = setTimeout(() => {
              if (!globalCallbacks.isReleasePending?.()) {
                return;
              }
              globalCallbacks.clearReleasePending?.();
              globalCallbacks.onReleaseEnd?.();
            }, remainingMs);
            return;
          }
          globalCallbacks.clearReleasePending?.();
          globalCallbacks.onReleaseEnd?.();
        }
      };

      const textHandler = (text: string) => {
        globalCallbacks.onText?.(text);
      };

      if (!globalTTS) {
        globalTTS = new TTSFeedback(speakingHandler, textHandler);
        console.log('TTS initialized');
      }

      globalTTSHandlersInstalled = true;
    }

    // Always point this component's ref at the singleton
    ttsRef.current = globalTTS;

    // Ensure latest handlers are used after HMR / rerenders via refs
  }, []);

  useEffect(() => {
    return () => {
      safeStopTTS();
    };
  }, []);

  const clearGuidedTimeouts = () => {
    guidedTimeoutsRef.current.forEach((timeoutId) => clearTimeout(timeoutId));
    guidedTimeoutsRef.current = [];
  };

  const queueGuidedLines = (lines: string[]) => {
    if (!ttsRef.current) return;
    clearGuidedTimeouts();
    isGuidedPhaseRef.current = true;
    const combined = lines.map((l) => l.trim()).filter(Boolean).join(' ');
    if (!combined) {
      isGuidedPhaseRef.current = false;
      onGuidedInstructionsEndRef.current?.();
      return;
    }

    const now = Date.now();
    const last = globalLastSpoken;
    if (last && last.text === combined && now - last.atMs < 2000) {
      return;
    }
    globalLastSpoken = { text: combined, atMs: now };

    pendingGuidedEndRef.current = true;
    ttsRef.current.speak(combined, true);
  };

  const queueReleaseLines = (lines: string[]) => {
    if (!ttsRef.current) return;
    clearGuidedTimeouts();
    if (releaseEndTimerRef.current) {
      clearTimeout(releaseEndTimerRef.current);
      releaseEndTimerRef.current = null;
    }
    const combined = lines.map((l) => l.trim()).filter(Boolean).join(' ');
    if (!combined) {
      onReleaseInstructionsEndRef.current?.();
      return;
    }

    const now = Date.now();
    const last = globalLastSpoken;
    if (last && last.text === combined && now - last.atMs < 2000) {
      return;
    }
    globalLastSpoken = { text: combined, atMs: now };

    const wordCount = combined.split(/\s+/).filter(Boolean).length;
    const estimatedSpeechMs = Math.max(3500, wordCount * 420);
    releaseEarliestEndAtRef.current = now + estimatedSpeechMs;
    pendingReleaseEndRef.current = true;
    ttsRef.current.speak(combined, true);
  };

  // Load guided instructions for the selected pose
  useEffect(() => {
    if (!selectedPose) {
      setInstructionSet(null);
      return;
    }

    const poseChanged = instructionPoseRef.current !== selectedPose;
    if (poseChanged) {
      entryPlayedRef.current = false;
      releasePlayedRef.current = false;
      instructionPoseRef.current = selectedPose;
    }

    const fetchInstructions = async () => {
      try {
        const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8002';
        const response = await fetch(
          `${apiBaseUrl}/api/yoga/instructions/${encodeURIComponent(selectedPose)}`
        );
        if (!response.ok) {
          setInstructionSet(null);
          return;
        }
        const data = await response.json();
        setInstructionSet({
          entry: data.entry || [],
          release: data.release || [],
        });
      } catch (err) {
        setInstructionSet(null);
      }
    };

    fetchInstructions();
  }, [selectedPose]);

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
          duration_seconds:
            result.duration_seconds ||
            (sessionStartTime ? Math.floor((Date.now() - sessionStartTime) / 1000) : 0),
          frames_processed: result.frames_processed || 0,
          average_accuracy: result.average_accuracy || 0,
          corrections_given: Math.max(result.corrections_given || 0, correctionsGivenRef.current),
          pose_name: result.pose_name,
        };

        console.log('Session ended from WebSocket:', summary);
        onSessionEnd(summary);
        if (!(playGuidedInstructionsRef.current || playReleaseInstructionsRef.current)) {
          ttsRef.current?.speak('Session ended. Great workout!', true);
        }

        // Stop analysis without calling onSessionEnd again
        setIsAnalyzing(false);
        setIsConnected(false);
        setPoseDetected(false);
        setCurrentPose(null);
        setAccuracy(null);
        setSessionStartTime(null);

        // Disconnect WebSocket gracefully without sending close message
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

        if (result.corrections && result.corrections.length > 0 && !suppressFeedbackRef.current) {
          onCorrectionsUpdate(result.corrections);

          // Speak correction feedback (if enabled)
          // During guided/release instruction phases, suppress feedback TTS to avoid overlapping.
          if (ttsEnabled && !(playGuidedInstructionsRef.current || playReleaseInstructionsRef.current)) {
            if (result.accuracy !== null && result.accuracy !== undefined && result.accuracy < 80) {
              // Only speak the first correction to avoid overwhelming
              const correctionText = result.corrections[0];
              const voiceCorrection = correctionText
                .replace(/Adjust your/i, '')
                .replace(/:\s*/g, ': ')
                .replace(/\(by [\d\.]+°\)/g, '')
                .trim();

              // Count corrections based on what we actually speak (de-dupe repeated spam)
              const now = Date.now();
              const last = lastCorrectionSpokenRef.current;
              if (!last || last.text !== voiceCorrection || now - last.atMs > 3000) {
                correctionsGivenRef.current += 1;
                lastCorrectionSpokenRef.current = { text: voiceCorrection, atMs: now };
              }

              ttsRef.current?.speak(voiceCorrection);
            }
          }
        }

        if (result.session_stats) {
          setFrameCount(result.session_stats.frames_processed);
          setAvgAccuracy(result.session_stats.average_accuracy);
        }

        // Draw skeleton overlay
        if (result.keypoints && overlayCanvasRef.current) {
          const ctx = overlayCanvasRef.current.getContext('2d');
          if (ctx) {
            ctx.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height);
            drawSkeleton(ctx, result.keypoints, result.angle_status);
          }
        }
      } else {
        setPoseDetected(false);
        setCurrentPose(null);
        setAccuracy(null);

        // Clear overlay
        if (overlayCanvasRef.current) {
          const ctx = overlayCanvasRef.current.getContext('2d');
          if (ctx) {
            ctx.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height);
          }
        }
      }
    },
    [onAccuracyUpdate, onCorrectionsUpdate, onSessionEnd, sessionStartTime, ttsEnabled]
  );

  // Speak entry instructions once when guided instructions phase starts
  useEffect(() => {
    const shouldPlay = playGuidedInstructions && !!instructionSet && !!ttsRef.current;

    if (shouldPlay && !prevPlayGuidedRef.current) {
      entryPlayedRef.current = false;
      pendingGuidedEndRef.current = false;
      isGuidedPhaseRef.current = false;
      globalLastSpoken = null;
    }
    prevPlayGuidedRef.current = playGuidedInstructions;

    if (!shouldPlay) {
      clearGuidedTimeouts();
      isGuidedPhaseRef.current = false;
      return;
    }

    if (!entryPlayedRef.current && instructionSet!.entry.length > 0) {
      entryPlayedRef.current = true;
      safeStopTTS();
      queueGuidedLines(instructionSet!.entry);
    }
  }, [instructionSet, playGuidedInstructions]);

  // Speak release instructions once when release phase starts
  useEffect(() => {
    const shouldPlay = playReleaseInstructions && !!instructionSet && !!ttsRef.current;

    if (shouldPlay && !prevPlayReleaseRef.current) {
      releasePlayedRef.current = false;
      pendingReleaseEndRef.current = false;
      globalLastSpoken = null;
    }
    prevPlayReleaseRef.current = playReleaseInstructions;

    if (!shouldPlay) {
      return;
    }

    if (!releasePlayedRef.current && instructionSet!.release.length > 0) {
      releasePlayedRef.current = true;
      safeStopTTS();
      queueReleaseLines(instructionSet!.release);
    }
  }, [instructionSet, playReleaseInstructions]);
  // Start/Stop analysis based on shouldAnalyze prop
  useEffect(() => {
    if (shouldAnalyze && isCameraReady) {
      startAnalysis();
    } else if (!shouldAnalyze) {
      prevPhaseRef.current = null;
      if (!playGuidedInstructions && !playReleaseInstructions) {
        clearGuidedTimeouts();
        isGuidedPhaseRef.current = false;

        safeStopTTS();
      }
      
      stopAnalysis();
    }

    return () => {
      stopAnalysis();
    };
  }, [shouldAnalyze, isCameraReady, playGuidedInstructions]);

  // Handle pose changes during active session
  const prevSelectedPoseRef = useRef<string>('');
  
  useEffect(() => {
    // Only handle pose changes if session is active and pose actually changed
    if (shouldAnalyze && isCameraReady && wsRef.current?.isConnected() && 
        selectedPose && selectedPose !== prevSelectedPoseRef.current) {
      
      const apiPoseName = convertPoseNameToApi(selectedPose);
      wsRef.current.startAnalysis(apiPoseName, tolerance);
      ttsRef.current?.speak(`Switched to ${selectedPose} pose.`, true);
      
      prevSelectedPoseRef.current = selectedPose;
    }
  }, [selectedPose, shouldAnalyze, isCameraReady]);

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
      correctionsGivenRef.current = 0;
      lastCorrectionSpokenRef.current = null;

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
    // Always clear frame capture, even if not analyzing
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
    
    // Prevent multiple WebSocket calls
    if (!isAnalyzing) return;

    // Calculate final session duration before stopping
    const finalDuration = sessionStartTime ? Math.floor((Date.now() - sessionStartTime) / 1000) : 0;
    console.log('Final session duration:', finalDuration, 'seconds');

    // Stop WebSocket analysis
    if (wsRef.current) {
      try {
        wsRef.current.stopAnalysis();

        // Wait for WebSocket session end, if not received, create local summary
        setTimeout(() => {
          if (isAnalyzing) {
            const summary: SessionSummary = {
              session_id: 'local-session',
              duration_seconds: finalDuration,
              frames_processed: frameCount,
              average_accuracy: avgAccuracy,
              corrections_given: correctionsGivenRef.current,
              pose_name: selectedPose,
            };

            console.log('Final session summary (local):', summary);
            onSessionEnd(summary);
            if (!(playGuidedInstructionsRef.current || playReleaseInstructionsRef.current)) {
              ttsRef.current?.speak('Session ended. Great workout!', true);
            }
          }
        }, 1000);
      } catch (err) {
        console.error('Failed to stop session:', err);
        const summary: SessionSummary = {
          session_id: 'local-session',
          duration_seconds: finalDuration,
          frames_processed: frameCount,
          average_accuracy: avgAccuracy,
          corrections_given: correctionsGivenRef.current,
          pose_name: selectedPose,
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
    correctionsGivenRef.current = 0;
    lastCorrectionSpokenRef.current = null;

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
      {shouldAnalyze && (
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
