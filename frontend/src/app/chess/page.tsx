'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import AuthGuard from '@/components/AuthGuard';
import Avatar3D from '@/components/Avatar3D';
import { getChessModules, createChessSession, sendChessAction, ChessModule, ChessExerciseState } from '@/lib/chessApi';
import { TTSFeedback } from '@/lib/yogaApi';
import EnhancedChessBoard from '@/components/EnhancedChessBoard';

interface UserProfile {
  username: string;
  email: string;
  full_name?: string;
  age?: number;
  height?: number;
  weight?: number;
  fitness_level?: string;
  preferences?: Record<string, any>;
}

interface SessionSummary {
  duration_seconds: number;
  frames_processed: number;
  average_accuracy: number;
  corrections_given: number;
}

/**
 * Pause between the player's move appearing on the board and the AI's reply.
 * The backend plays both inside one request, so without this the answer lands
 * in the same frame and the player never sees their own move.
 */
const AI_MOVE_REVEAL_MS = 1200;

/** How long the AI's origin and destination squares stay marked afterwards. */
const AI_MOVE_HIGHLIGHT_MS = 2600;

const GAME_MODES = [
  { id: 'human_vs_ai', icon: '🧑 vs 🤖', label: 'Human vs AI' },
  { id: 'ai_vs_ai', icon: '🤖 vs 🤖', label: 'AI vs AI' },
  { id: 'human_vs_human', icon: '🧑 vs 🧑', label: 'Human vs Human' },
] as const;

/**
 * Difficulty only means something when an AI is playing, so picking a level
 * while in two-player mode implies a game against the computer.
 */
const aiGameMode = (mode: string): string => (mode === 'human_vs_human' ? 'human_vs_ai' : mode);

function Particles() {
  return (
    <div aria-hidden className="particles pointer-events-none fixed inset-0 -z-10">
      <div
        className="absolute left-[10%] top-[10%] h-[420px] w-[420px] rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(25,227,255,.5), transparent 60%)',
          animation: 'drift 48s ease-in-out infinite',
        }}
      />
      <div
        className="absolute right-[5%] top-[30%] h-[520px] w-[520px] rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(106,93,255,.4), transparent 60%)',
          animation: 'drift 56s ease-in-out infinite',
        }}
      />
    </div>
  );
}

export default function ChessPage() {
  const router = useRouter();

  const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8002';

  const [modules, setModules] = useState<ChessModule[]>([]);
  const [selectedModuleId, setSelectedModuleId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [exercise, setExercise] = useState<ChessExerciseState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionSummary, setSessionSummary] = useState<SessionSummary | null>(null);
  const [energyLevel, setEnergyLevel] = useState(82);
  const [sessionPhase, setSessionPhase] = useState<'in' | 'hold' | 'out' | 'idle'>('idle');
  const [phaseTimeLeft, setPhaseTimeLeft] = useState(0);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isTTSSpeaking, setIsTTSSpeaking] = useState(false);
  // What the avatar is saying right now. Hints in particular were spoken but
  // never shown, so a learner who missed the audio had nothing to fall back on.
  const [avatarSpeech, setAvatarSpeech] = useState('');
  const [lastYogaDate, setLastYogaDate] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('beginner'); // Default to beginner
  const [view, setView] = useState<'list' | 'lesson'>('list');
  const [moduleProgress, setModuleProgress] = useState<Record<string, number>>({});
  // Lesson gating keys off saved progress, so a failed or still-pending load
  // must not lock every lesson. Locks only apply once progress really arrived.
  const [progressLoaded, setProgressLoaded] = useState(false);
  const [progressUpdateKey, setProgressUpdateKey] = useState(0); // Force re-render
  const [chessAnimKey, setChessAnimKey] = useState(0);
  const lastCorrectRef = useRef(false);
  const hasPlayedInitialRef = useRef(false); // Prevent initial animation on load
  const openingSpokenRef = useRef(false);
  const lastSpokenMessageRef = useRef<string>('');
  const aiRevealTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const aiMoveClearTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const completionSpokenRef = useRef<string | null>(null);
  // Squares the AI just moved between, so the board can show the piece travel.
  const [aiMove, setAiMove] = useState<{ from: string; to: string } | null>(null);
  // Which game mode the gameplay module is currently set to run.
  const [selectedGameMode, setSelectedGameMode] = useState<string>('human_vs_ai');

  const sanitizeTtsText = (text: string): string => {
    let t = String(text || '').trim();
    if (!t) return '';

    const pieceNameFromSymbol = (symRaw: string): string => {
      const sym = String(symRaw || '').trim();
      const isWhite = sym === sym.toUpperCase();
      const s = sym.toUpperCase();
      const name =
        s === 'P' ? 'pawn' :
        s === 'R' ? 'rook' :
        s === 'N' ? 'knight' :
        s === 'B' ? 'bishop' :
        s === 'Q' ? 'queen' :
        s === 'K' ? 'king' : 'piece';
      return `${isWhite ? 'white' : 'black'} ${name}`;
    };

    t = t.replace(
      /Selected\s+<bound method\s+Piece\.symbol\s+of\s+Piece\.from_symbol\('([^']+)'\)>/gi,
      (_m, sym) => `Selected ${pieceNameFromSymbol(sym)}.`
    );
    t = t.replace(/<bound method[^>]*>/gi, '');
    t = t.replace(/\.{2,}/g, '.');
    t = t.replace(/\s{2,}/g, ' ').trim();
    return t;
  };

  // TTS for chess feedback
  const ttsRef = useRef<TTSFeedback | null>(null);

  // AI vs AI automation
  useEffect(() => {
    if (view !== 'lesson' || !sessionId || !exercise || !exercise.instructions) return;
    
    // Check if this is a gameplay module
    const isGameplayModule = exercise.module_id === 'gameplay';
    const isAIVsAI = exercise.instructions.includes('AI vs AI');
    const isAITurn = exercise.instructions.includes('Turn: AI');
    const isHumanVsHuman = exercise.instructions.includes('Two-player mode');
    const isGameOver = exercise.module_completed;

    // Auto-progress for AI vs AI mode
    if (isGameplayModule && isAIVsAI && isAITurn && !isGameOver && !loading) {
      const timer = setTimeout(() => {
        handleAction('next');
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [view, sessionId, exercise]);

  // Initialize TTS for chess feedback
  useEffect(() => {
    ttsRef.current = new TTSFeedback((speaking) => {
      console.log('🎤 TTS speaking state changed:', speaking);
      setIsTTSSpeaking(speaking);
    }, (text) => {
      setAvatarSpeech(text);
    });

    // These lines are spoken constantly during a lesson and are always the same,
    // so render them up front instead of paying a synthesis round-trip the first
    // time each one comes up.
    ttsRef.current.prefetchMany([
      'Would you like to practice today?',
      'Perfect!',
      'Good move!',
      'Wrong position.',
    ]);

    return () => {
      if (ttsRef.current) {
        ttsRef.current.stop();
      }
      if (aiRevealTimerRef.current) {
        clearTimeout(aiRevealTimerRef.current);
        aiRevealTimerRef.current = null;
      }
      if (aiMoveClearTimerRef.current) {
        clearTimeout(aiMoveClearTimerRef.current);
        aiMoveClearTimerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (view !== 'lesson' || !sessionId) {
      openingSpokenRef.current = false;
      return;
    }

    if (!openingSpokenRef.current && ttsRef.current) {
      ttsRef.current.speak('Would you like to practice today?', true);
      openingSpokenRef.current = true;
    }
  }, [view, sessionId]);

  useEffect(() => {
    if (view !== 'lesson' || !exercise || !ttsRef.current) return;
    const msg = String(exercise.feedback_message || '').trim();
    if (!msg) return;

    const type = String((exercise as any).exercise_type || '').toLowerCase();
    if (exercise.is_correct === true && exercise.exercise_completed === true && (type === 'identify_pieces' || type === 'board_setup')) {
      return;
    }

    const normalized = msg.toLowerCase();
    const isHint = normalized.startsWith('hint:');
    let speakText = isHint ? msg.replace(/^hint:\s*/i, '').trim() : msg;
    speakText = sanitizeTtsText(speakText);

    if (isHint) {
      const pieceType = String((exercise as any).current_piece_type || '').toLowerCase();
      const isPawn = pieceType.includes('pawn');
      if (isPawn) {
        speakText = `Hint: Focus on the pawn's shape and its forward movement rules. ${speakText}`;
      } else {
        speakText = `Hint: ${speakText}`;
      }
    }

    if (!speakText) return;
    if (lastSpokenMessageRef.current === speakText) return;
    lastSpokenMessageRef.current = speakText;
    ttsRef.current.speak(speakText, true);
  }, [view, exercise?.feedback_message, exercise?.current_piece_type]);

  // Congratulate the learner by name when a lesson is finished, and point at
  // what that just opened up - lessons unlock in order, so the next one is the
  // most useful thing to tell them.
  useEffect(() => {
    if (view !== 'lesson' || !exercise?.module_completed || !ttsRef.current) return;
    if (completionSpokenRef.current === exercise.module_id) return;
    completionSpokenRef.current = exercise.module_id;

    const finishedIndex = modules.findIndex((m) => m.id === exercise.module_id);
    const finishedName = finishedIndex >= 0 ? modules[finishedIndex].name : null;
    if (!finishedName) return;

    const nextModule = modules[finishedIndex + 1];

    const line = nextModule
      ? `Well done! You have completed the ${finishedName} lesson. ${nextModule.name} is now unlocked, whenever you are ready.`
      : `Well done! You have completed the ${finishedName} lesson. That was the last one, you have finished every chess lesson.`;

    // Queued rather than priority so it follows the move feedback that is
    // usually still being spoken, instead of cutting it off.
    ttsRef.current.speak(line);
    setChessAnimKey((prev) => prev + 1);
  }, [view, exercise?.module_completed, exercise?.module_id, modules]);

  useEffect(() => {
    const loadModules = async () => {
      try {
        const mods = await getChessModules();
        setModules(mods);
        if (mods.length > 0) {
          setSelectedModuleId(mods[0].id);
        }
      } catch (e: any) {
        setError(e.message || 'Failed to load chess modules');
      }
    };
    loadModules();
  }, []);

  useEffect(() => {
    console.log('Animation check:', {
      isCorrect: exercise?.is_correct,
      lastCorrect: lastCorrectRef.current,
      hasPlayedInitial: hasPlayedInitialRef.current,
      exerciseId: exercise?.exercise_id,
      exerciseCompleted: exercise?.exercise_completed
    });
    
    // Reset lastCorrect when exercise changes
    if (exercise?.exercise_id) {
      lastCorrectRef.current = false;
    }
    
    // Only trigger animation for CORRECTLY COMPLETED exercises after initial load
    // This ensures animation plays only when piece moves to correct cell or correct answer is given
    if (exercise?.is_correct === true && exercise?.exercise_completed === true && !lastCorrectRef.current && hasPlayedInitialRef.current) {
      console.log('Triggering animation for correct completion!');
      
      // Trigger TTS IMMEDIATELY when correct move detected
      if (ttsRef.current) {
        const type = String(exercise.exercise_type || '').toLowerCase();
        const backendMsg = sanitizeTtsText(String((exercise as any).feedback_message || '').trim());

        // If backend already provides a correct feedback line (e.g. "Correct move!"), don't speak our own.
        if (!(type === 'identify_pieces' || type === 'board_setup') && backendMsg) {
          // Do nothing; feedback-message effect will speak it.
        } else {
          const phrase = (type === 'identify_pieces' || type === 'board_setup') ? 'Perfect!' : 'Good move!';
          ttsRef.current.speak(phrase, true); // Priority speak
        }
      }
      
      setChessAnimKey((prev: number) => prev + 1);
      lastCorrectRef.current = true;
    } else if (exercise?.is_correct === true && exercise?.exercise_completed === true) {
      lastCorrectRef.current = true;
    }
    
    // Set initial flag to true after first exercise loads
    if (exercise && !hasPlayedInitialRef.current) {
      hasPlayedInitialRef.current = true;
    }
  }, [exercise?.is_correct, exercise?.exercise_completed, exercise?.exercise_id]);

  // Load chess module progress from database
  useEffect(() => {
    const loadChessProgress = async () => {
      try {
        
        const token = localStorage.getItem('access_token');
        
        if (!token) {
          setModuleProgress({});
          return;
        }
        
        const profileResponse = await fetch(`${apiBaseUrl}/api/auth/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!profileResponse.ok) {
          setModuleProgress({});
          return;
        }

        const profile = await profileResponse.json();
        const username = profile.username;

        if (!username) {
          setModuleProgress({});
          return;
        }
        
        // First try module progress endpoint (where we actually save the data)
        const progressResponse = await fetch(`${apiBaseUrl}/api/module/progress/${username}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!progressResponse.ok) {
          // Try chess progress endpoint as fallback
          const chessProgressResponse = await fetch(`${apiBaseUrl}/api/chess/progress/${username}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });
         
          if (!chessProgressResponse.ok) {
            setModuleProgress({});
            return;
          }
          
          const chessData = await chessProgressResponse.json();
         
          // Process chess progress data
          const progressData: Record<string, number> = {};
          
          if (chessData.data) {
            
            if (Array.isArray(chessData.data)) {
              chessData.data.forEach((item: any, index: number) => {
                if (item.module_id && item.progress !== undefined) {
                  progressData[item.module_id] = Math.min(100, item.progress);
                } else {
                  console.log(`🔍 DEBUG: Item missing module_id or progress:`, item);
                }
              });
            } else if (typeof chessData.data === 'object') {
              Object.keys(chessData.data).forEach(key => {
                const value = chessData.data[key];
                if (typeof value === 'object' && value.module_id && value.progress !== undefined) {
                  progressData[value.module_id] = Math.min(100, value.progress);
                } else if (typeof value === 'number') {
                  progressData[key] = Math.min(100, value);
                }
              });
            }
          } else {
            console.log('🔍 DEBUG: No chessData.data found');
          }
          
          setModuleProgress(progressData);
          setProgressLoaded(true);
        } else {
          const moduleData = await progressResponse.json();
          
          // Process module progress data
          const progressData: Record<string, number> = {};
          
          if (moduleData.data) {
            
            if (Array.isArray(moduleData.data)) {
              moduleData.data.forEach((item: any, index: number) => {
                if (item.module_id && item.progress_percentage !== undefined) {
                  progressData[item.module_id] = Math.min(100, item.progress_percentage);
                  } else {
                  console.log(`🔍 DEBUG: Item missing module_id or progress_percentage:`, item);
                }
              });
            } else if (typeof moduleData.data === 'object') {
              Object.keys(moduleData.data).forEach(key => {
                const value = moduleData.data[key];
                console.log(`🔍 DEBUG: Object key ${key}:`, value);
                if (typeof value === 'object' && value.module_id && value.progress_percentage !== undefined) {
                  progressData[value.module_id] = Math.min(100, value.progress_percentage);
                } else if (typeof value === 'number') {
                  progressData[key] = Math.min(100, value);
                }
              });
            }
          } else {
            console.log('🔍 DEBUG: No moduleData.data found');
          }
          
          setModuleProgress(progressData);
          setProgressLoaded(true);
        }


      } catch (error) {
        setModuleProgress({});
      }
    };

    loadChessProgress();
  }, []);

  const selectedModule = useMemo(
    () => modules.find((m) => m.id === selectedModuleId) || null,
    [modules, selectedModuleId]
  );

  const updateModuleProgressForExercise = async (state: ChessExerciseState) => {
    const total = state.progress_total || 0;
    let current = state.progress_current || 0;
    
    // Fix progress calculation - if current is negative, use 0
    const actualCurrent = Math.max(0, current);
    let percent = total > 0 ? Math.min(100, Math.round((actualCurrent / total) * 100)) : 0;
    
    // Special debug for Board Setup
    if (state.exercise_type === 'board_setup') {
      
      // For Board Setup, ensure progress is based on placed pieces
      if (state.placed_pieces) {
        const placedCount = Object.keys(state.placed_pieces).length;
        const boardSetupPercent = total > 0 ? Math.min(100, Math.round((placedCount / total) * 100)) : 0;
        
        
        // Use the calculated progress from placed pieces
        if (boardSetupPercent !== percent) {
          percent = boardSetupPercent;
        }
      }
    }
    
    setModuleProgress((prev) => {
      const currentProgress = prev[state.module_id] || 0;
      
      // Don't update progress if module is already completed locally (100%)
      if (currentProgress >= 100) {
        return prev;
      }
      
      // Special case for Board Setup: Allow equal progress updates to ensure UI sync
      if (state.exercise_type === 'board_setup' && percent === currentProgress) {
        const next = { ...prev, [state.module_id]: percent };
        
        // Save progress to database
        saveProgressToDatabase(state.module_id, percent);
        
        return next;
      }
      
      // Only allow progress to increase, not decrease
      // Special case: If this is a new exercise (progress_current = -1), allow database progress to be used as starting point
      if (percent < currentProgress && currentProgress > 0) {
        if (state.progress_current === -1) {
          // Don't update for new exercises, keep database progress
          return prev;
        } else {
          return prev;
        }
      }
      
      const next = { ...prev, [state.module_id]: percent };
      
      // Save progress to database
      saveProgressToDatabase(state.module_id, percent);
      
      // Force re-render for Board Setup progress
      if (state.exercise_type === 'board_setup') {
        setProgressUpdateKey(prev => prev + 1);
      }
      
      return next;
    });
  }

  const saveProgressToDatabase = async (moduleId: string, progress: number) => {
    try {
      // Get current logged-in user token from existing auth system
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        return;
      }
      
      // Get username from token using existing auth system
      const profileResponse = await fetch(`${apiBaseUrl}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!profileResponse.ok) {
        return;
      }
      
      const profile = await profileResponse.json();
      const username = profile.username;
      
      if (!username) {
        return;
      }
      
      // Use the working endpoint with minimal data to avoid backend bug
      const queryParams = new URLSearchParams({
        module_id: moduleId,
        progress_percentage: progress.toString()
      });
      
      const requestBody = {
        progress: progress
      };
      
      const moduleProgressResponse = await fetch(`${apiBaseUrl}/api/module/progress/${username}?${queryParams}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
     
      if (moduleProgressResponse.ok) {
        const responseText = await moduleProgressResponse.text();
        try {
          const responseJson = JSON.parse(responseText);
          if (responseJson.success) {
            console.log(`🔍 DEBUG: ✅ Progress saved for ${moduleId}: ${progress}% for user ${username}`);
          } else {
            console.log(`🔍 DEBUG: ⚠️ Backend reported: ${responseJson.message}`);
            console.log('🔍 DEBUG: This is a backend database issue, frontend is working correctly');
          }
        } catch (e) {
          console.log('🔍 DEBUG: Response is not JSON:', responseText);
        }
      } else {
        const errorText = await moduleProgressResponse.text();
        console.log('🔍 DEBUG: Error response body:', errorText);
        console.error('🔍 DEBUG: Failed to save progress to database');
      }
    } catch (error) {
      console.error('🔍 DEBUG: Error saving progress to database:', error);
    }
  };

  const startGameplayMode = async (gameMode: string) => {
    setLoading(true);
    setError(null);
    setSessionId(null);
    setExercise(null);
    
    
    try {
      const state = await createChessSession('gameplay');
      
      // Update the exercise to use the specific game mode
      const updatedState = await sendChessAction(state.session_id, 'set_game_mode', { game_mode: gameMode });
      
      setSelectedModuleId('gameplay');
      setSessionId(updatedState.session_id);
      setExercise(updatedState);
      updateModuleProgressForExercise(updatedState);
      setView('lesson');
    } catch (e: any) {
      setError(e.message || 'Failed to start gameplay mode');
    } finally {
      setLoading(false);
    }
  };

  const startGameplayWithDifficulty = async (gameMode: string, difficulty: string) => {
    setLoading(true);
    setError(null);
    setSessionId(null);
    setExercise(null);
    
    
    try {
      const state = await createChessSession('gameplay');
      
      // Start gameplay with specific difficulty
      const updatedState = await sendChessAction(state.session_id, 'start_gameplay', { 
        game_mode: gameMode, 
        difficulty: difficulty 
      });
      
      setSelectedModuleId('gameplay');
      setSessionId(updatedState.session_id);
      setExercise(updatedState);
      updateModuleProgressForExercise(updatedState);
      setView('lesson');
    } catch (e: any) {
      setError(e.message || 'Failed to start gameplay mode');
    } finally {
      setLoading(false);
    }
  };

  /**
   * How long a finished exercise stays on screen before the next one loads.
   * Castling, en passant and promotion rearrange several pieces at once, so a
   * flat 1.5s moved the board on before the learner had seen what happened.
   */
  const autoAdvanceDelayMs = (state: ChessExerciseState): number => {
    if (state.module_id === 'special_moves') return 4500;
    if (state.exercise_type === 'identify_pieces') return 5000;
    return 1500;
  };

  /**
   * Commits a state from the backend. For gameplay the AI answers inside the
   * same request, so the response already carries both moves. When that happens
   * the player's own move is shown first and the AI's reply follows a beat
   * later, instead of the board jumping straight to the answer.
   */
  const applyExerciseState = (state: ChessExerciseState) => {
    if (aiRevealTimerRef.current) {
      clearTimeout(aiRevealTimerRef.current);
      aiRevealTimerRef.current = null;
    }
    if (aiMoveClearTimerRef.current) {
      clearTimeout(aiMoveClearTimerRef.current);
      aiMoveClearTimerRef.current = null;
    }
    setAiMove(null);

    const preAiPosition = state.pre_ai_board_position;
    if (!preAiPosition) {
      setExercise(state);
      updateModuleProgressForExercise(state);
      return;
    }

    setExercise({
      ...state,
      board_position: preAiPosition,
      feedback_message: state.pre_ai_feedback_message ?? null,
      selected_square: null,
      // The AI's reply is not on the board yet, so nothing about it should be
      // announced or highlighted during this beat.
      pre_ai_board_position: null,
      ai_move_san: null,
    });

    aiRevealTimerRef.current = setTimeout(() => {
      aiRevealTimerRef.current = null;
      setExercise(state);
      updateModuleProgressForExercise(state);

      // Hand the board the squares the AI moved between so it can slide the
      // piece across and mark where it came from.
      const uci = state.ai_move_uci;
      if (uci && uci.length >= 4) {
        setAiMove({ from: uci.slice(0, 2), to: uci.slice(2, 4) });
        if (aiMoveClearTimerRef.current) clearTimeout(aiMoveClearTimerRef.current);
        aiMoveClearTimerRef.current = setTimeout(() => {
          aiMoveClearTimerRef.current = null;
          setAiMove(null);
        }, AI_MOVE_HIGHLIGHT_MS);
      }
    }, AI_MOVE_REVEAL_MS);
  };

  const handleStartLesson = async (moduleId: string) => {
    setLoading(true);
    setError(null);
    setExercise(null);
    lastSpokenMessageRef.current = '';
    completionSpokenRef.current = null;

    console.log('🔍 DEBUG: Starting lesson for module:', moduleId);
    
    try {
      const state = await createChessSession(moduleId);
      
      console.log('🔍 DEBUG: Created session state:', state);
      console.log('🔍 DEBUG: Session ID:', state.session_id);
      console.log('🔍 DEBUG: Exercise ID:', state.exercise_id);
      console.log('🔍 DEBUG: Exercise type:', state.exercise_type);
      console.log('🔍 DEBUG: Expected board_setup, got:', state.exercise_type);
      
      setSelectedModuleId(moduleId);
      setSessionId(state.session_id);
      setExercise(state);
      updateModuleProgressForExercise(state);
      setView('lesson');
    } catch (e: any) {
      setError(e.message || 'Failed to start lesson');
      if (ttsRef.current) {
        ttsRef.current.speak(e.message || 'Failed to start lesson', true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSquareClick = async (square: string) => {
    if (!sessionId) {
      return;
    }
    
    // Don't allow clicks if module is already completed
    if (exercise?.module_completed) {
      return;
    }
    
    console.log('🔍 DEBUG: handleSquareClick called with square:', square);
    
    try {
      const state = await sendChessAction(sessionId, 'select_square', { square });
      console.log('🔍 DEBUG: Backend response:', {
        exercise_id: state.exercise_id,
        is_correct: state.is_correct,
        exercise_completed: state.exercise_completed,
        module_completed: state.module_completed,
        progress_current: state.progress_current,
        progress_total: state.progress_total,
        placed_pieces: state.placed_pieces
      });
      
      applyExerciseState(state);

      // Trigger TTS for bad move if incorrect
      if (state.is_correct === false && ttsRef.current) {
        const msg = String(state.feedback_message || '').trim();
        if (!msg) {
          ttsRef.current.speak('Wrong position.', true); // Priority speak
        }
      }

      // Auto-progress if exercise is completed BUT module is not completed
      if (state.exercise_completed && !state.module_completed && state.exercise_type !== 'identify_pieces') {
        setTimeout(() => {
          console.log('🔍 DEBUG: Auto-progressing to next exercise from select_square');
          handleAction('next');
        }, autoAdvanceDelayMs(state));
      }
    } catch (e: any) {
      setError(e.message || 'Failed to apply move');
      if (ttsRef.current) {
        ttsRef.current.speak(e.message || 'Failed to apply move', true);
      }
    }
  };

  const handleAction = async (type: string, payload?: any) => {
    if (!sessionId) return;
    
    console.log('🔍 DEBUG: handleAction called with type:', type, 'payload:', payload);
    
    // A finished module has no next exercise. "Next" at that point means the
    // next lesson - which is exactly the one this completion just unlocked.
    if (exercise?.module_completed && (type === 'skip' || type === 'next')) {
      if (type === 'next') {
        const finishedIndex = modules.findIndex((m) => m.id === exercise.module_id);
        const nextModule = finishedIndex >= 0 ? modules[finishedIndex + 1] : undefined;
        if (nextModule) {
          handleStartLesson(nextModule.id);
          return;
        }
        // Nothing left to move on to; return to the lesson list.
        ttsRef.current?.stop();
        setView('list');
        setSessionId(null);
        setExercise(null);
        return;
      }
      console.log('Module already completed, ignoring skip action');
      return;
    }


    try {
      const state = await sendChessAction(sessionId, type, payload);
      console.log('🔍 DEBUG: Backend response:', {
        exercise_id: state.exercise_id,
        is_correct: state.is_correct,
        exercise_completed: state.exercise_completed,
        module_completed: state.module_completed,
        progress_current: state.progress_current,
        progress_total: state.progress_total,
        placed_pieces: state.placed_pieces,
        current_piece_type: state.current_piece_type,
        pieces_inventory: state.pieces_inventory
      });
      
      applyExerciseState(state);

      // Auto-progress if exercise is completed BUT module is not completed
      if (state.exercise_completed && !state.module_completed && state.exercise_type !== 'identify_pieces') {
        setTimeout(() => {
          console.log('🔍 DEBUG: Auto-progressing to next exercise from handleAction');
          handleAction('next');
        }, autoAdvanceDelayMs(state));
      }
    } catch (e: any) {
      setError(e.message || 'Failed to apply action');
      if (ttsRef.current) {
        ttsRef.current.speak(e.message || 'Failed to apply action', true);
      }
    }
  };

  return (
    <AuthGuard>
      <main
        className="min-h-screen w-full overflow-hidden text-[var(--ink-hi)]"
        style={{ background: 'var(--bg-gradient)', fontFamily: 'var(--font-ui)' }}
      >
      <Particles />

      <div className="mx-auto max-w-[1080px] px-6 md:px-8 py-6 md:py-8 relative">
        {/* Back Button */}
        <button
          onClick={() => router.push('/dashboard')}
          className="absolute left-4 top-6 z-20 rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] px-5 py-2 text-[16px] font-semibold text-[var(--brand-neo)] transition-all hover:shadow-[var(--glow-neo)]"
        >
          ← Back
        </button>

        <section className="relative flex flex-col gap-6 mt-6">
          {/* Avatar Section - Top */}
          <div className="relative">
            <div
              className="avatar-wrap relative h-[30vh] overflow-hidden rounded-[var(--radius-lg)] border border-[var(--glass-stroke)]"
              style={{
                background: 'linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02))',
                backdropFilter: 'blur(12px)',
              }}
            >
              <Avatar3D
                onlyInAnimation={false}
                staticMode={true}
                staticModelPath="/Encouraging Gesture_compressed.glb"
                playAnimationPath="/Encouraging Gesture_compressed.glb"
                playAnimationKey={chessAnimKey}
                isTTSSpeaking={isTTSSpeaking}
                // Without the spoken text the lip-sync falls back to one fixed
                // mouth shape; with it the visemes follow the actual words.
                ttsText={avatarSpeech}
                // Frame the avatar from mid-belly up to just above the head.
                // The manual camera path is floor-anchored: the target sits at
                // 80% of the model's height and the distance sets how much of
                // the body fits around it. Only the distance is tuned here -
                // moving the target as well pulls the head out of frame, so
                // widening symmetrically is what keeps the head safe.
                cameraManualDistanceFactor={0.64}
                cameraManualTargetYOffsetFactor={0.3}
              />
              {/* Fake shadow removed to stop float illusion */}

              {/* What the avatar is saying, mirrored on screen. */}
              {avatarSpeech && (
                <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 px-4 pb-3">
                  <p
                    className="mx-auto w-fit max-w-[92%] rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-black/55 px-4 py-2 text-center text-[15px] font-medium leading-snug text-[var(--ink-hi)] backdrop-blur-sm"
                  >
                    {avatarSpeech}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Chess Lessons Panel - Bottom */}
          <aside className="flex-1 content-center space-y-4">
            <div className="mb-2 flex items-center justify-between">
              <h2
                className="text-[32px] font-bold leading-tight text-[var(--brand-neo)]"
                style={{ fontFamily: 'var(--font-future)' }}
              >
                Chess Lessons
              </h2>
              {view === 'lesson' && selectedModule && (
                <button
                  type="button"
                  onClick={() => {
                    if (aiRevealTimerRef.current) {
                      clearTimeout(aiRevealTimerRef.current);
                      aiRevealTimerRef.current = null;
                    }
                    ttsRef.current?.stop();
                    setView('list');
                    setSessionId(null);
                    setExercise(null);
                  }}
                  className="rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] px-3 py-1 text-[12px] font-semibold text-[var(--ink-hi)] hover:border-[var(--brand-neo)] hover:text-[var(--brand-neo)]"
                >
                  ← Back to lessons
                </button>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="rounded-[var(--radius-md)] border border-red-500/40 bg-red-900/40 text-red-100 text-[13px] px-3 py-2">
                {error}
              </div>
            )}

            {/* Lessons grid view */}
            {view === 'list' && (
              <div
                className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-4 btn-glass"
                style={{
                  background: 'linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))',
                }}
              >
                <h3 className="text-[18px] font-semibold mb-1 text-[var(--brand-neo)]">Choose a lesson</h3>
                <p className="text-[13px] text-[var(--ink-med)]">
                  Tap a lesson card to start practicing. Your progress is saved per lesson.
                </p>
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {(() => {
                    return null;
                  })()}
                  {modules.map((m, index) => {
                    const progress = moduleProgress[m.id] || 0;
                    // Lessons run in order: everything after the first stays
                    // locked until the one before it is finished.
                    const previousModule = index > 0 ? modules[index - 1] : null;
                    const locked = progressLoaded && previousModule
                      ? (moduleProgress[previousModule.id] || 0) < 100
                      : false;
                    return (
                      <button
                        key={`${m.id}-${progressUpdateKey}`} // Force re-render on progress update
                        type="button"
                        disabled={locked}
                        aria-disabled={locked}
                        onClick={() => {
                          if (locked) return;
                          handleStartLesson(m.id);
                        }}
                        className={`w-full rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[var(--glass)] px-3 py-3 text-left transition ${
                          locked
                            ? 'cursor-not-allowed opacity-45'
                            : 'hover:border-[var(--brand-neo)] hover:shadow-[var(--glow-neo)]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[14px] font-semibold text-[var(--ink-hi)]">
                            {locked ? '🔒 ' : ''}{m.name}
                          </span>
                          <span className="text-[11px] text-[var(--ink-med)]">{progress}%</span>
                        </div>
                        <p className="text-[12px] text-[var(--ink-med)] line-clamp-2">{m.description}</p>
                        <div className="mt-2 h-1.5 w-full rounded-full bg-[var(--glass-stroke)]/40 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-[var(--brand-neo)] transition-all duration-300"
                            style={{
                              width: `${progress}%`,
                              minWidth: progress > 0 ? '2px' : '0px'
                            }}
                          >
                            <span className="text-xs text-white">{progress > 0 ? progress : ''}</span>
                          </div>
                        </div>
                        {locked && previousModule && (
                          <p className="mt-2 text-[11px] text-[var(--ink-med)]">
                            Complete “{previousModule.name}” to unlock this lesson.
                          </p>
                        )}
                      </button>
                    );
                  })}
                  {modules.length === 0 && (
                    <p className="text-[13px] text-[var(--ink-med)]">No lessons available.</p>
                  )}
                </div>
              </div>
            )}

            {/* Current lesson view */}
            {view === 'lesson' && selectedModule && (
              <div
                className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-4 btn-glass space-y-3"
                style={{
                  background: 'linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,.01))',
                }}
              >
                <h3 className="text-[18px] font-semibold text-[var(--brand-neo)]">
                  {selectedModule.name}
                </h3>
                <p className="text-[13px] text-[var(--ink-med)]">{selectedModule.description}</p>

                {/* Game mode selection for gameplay module */}
                {selectedModule.id === 'gameplay' && (
                  <div className="mt-4 space-y-4">
                    {/* Current Difficulty Display */}
                    <div className="text-center p-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)]">
                      <p className="text-[12px] text-[var(--ink-med)] mb-1">Current Difficulty</p>
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-[18px] font-bold text-[var(--brand-neo)]">
                          {selectedDifficulty === 'beginner' && '🌱 Beginner'}
                          {selectedDifficulty === 'intermediate' && '🎯 Intermediate'}
                          {selectedDifficulty === 'advanced' && '🔥 Advanced'}
                        </span>
                        <span className="text-[11px] text-[var(--ink-low)]">
                          {selectedDifficulty === 'beginner' && 'Perfect for learning'}
                          {selectedDifficulty === 'intermediate' && 'Challenge yourself'}
                          {selectedDifficulty === 'advanced' && 'Test your mastery'}
                        </span>
                      </div>
                    </div>

                    {/* Difficulty Selection */}
                    <div>
                      <p className="text-[13px] text-[var(--ink-med)] mb-2">Select Difficulty Level:</p>
                      <div className="grid grid-cols-3 gap-2">
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedDifficulty('beginner');
                            const mode = aiGameMode(selectedGameMode);
                            setSelectedGameMode(mode);
                            startGameplayWithDifficulty(mode, 'beginner');
                          }}
                          className={`relative px-3 py-3 rounded-[var(--radius-md)] border text-[12px] transition-all ${
                            selectedDifficulty === 'beginner'
                              ? 'border-[var(--brand-neo)] bg-[var(--brand-neo)]/20 text-[var(--brand-neo)] shadow-[0_0_12px_rgba(25,227,255,.3)]'
                              : 'border-[var(--glass-stroke)] bg-[var(--glass)] text-[var(--ink-hi)] hover:border-[var(--brand-neo)]/50 hover:bg-[var(--glass-stroke)]/20'
                          }`}
                        >
                          <div className="font-semibold">🌱 Beginner</div>
                          {/* <div className="text-[10px] opacity-80">Easy AI • 2-3 depth</div> */}
                          {selectedDifficulty === 'beginner' && (
                            <div className="absolute -top-1 -right-1 w-2 h-2 bg-[var(--brand-neo)] rounded-full"></div>
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedDifficulty('intermediate');
                            const mode = aiGameMode(selectedGameMode);
                            setSelectedGameMode(mode);
                            startGameplayWithDifficulty(mode, 'intermediate');
                          }}
                          className={`relative px-3 py-3 rounded-[var(--radius-md)] border text-[12px] transition-all ${
                            selectedDifficulty === 'intermediate'
                              ? 'border-[var(--brand-neo)] bg-[var(--brand-neo)]/20 text-[var(--brand-neo)] shadow-[0_0_12px_rgba(25,227,255,.3)]'
                              : 'border-[var(--glass-stroke)] bg-[var(--glass)] text-[var(--ink-hi)] hover:border-[var(--brand-neo)]/50 hover:bg-[var(--glass-stroke)]/20'
                          }`}
                        >
                          <div className="font-semibold">🎯 Intermediate</div>
                          {/* <div className="text-[10px] opacity-80">Medium AI • 4-5 depth</div> */}
                          {selectedDifficulty === 'intermediate' && (
                            <div className="absolute -top-1 -right-1 w-2 h-2 bg-[var(--brand-neo)] rounded-full"></div>
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedDifficulty('advanced');
                            const mode = aiGameMode(selectedGameMode);
                            setSelectedGameMode(mode);
                            startGameplayWithDifficulty(mode, 'advanced');
                          }}
                          className={`relative px-3 py-3 rounded-[var(--radius-md)] border text-[12px] transition-all ${
                            selectedDifficulty === 'advanced'
                              ? 'border-[var(--brand-neo)] bg-[var(--brand-neo)]/20 text-[var(--brand-neo)] shadow-[0_0_12px_rgba(25,227,255,.3)]'
                              : 'border-[var(--glass-stroke)] bg-[var(--glass)] text-[var(--ink-hi)] hover:border-[var(--brand-neo)]/50 hover:bg-[var(--glass-stroke)]/20'
                          }`}
                        >
                          <div className="font-semibold">🔥 Advanced</div>
                          {/* <div className="text-[10px] opacity-80">Hard AI • 6+ depth</div> */}
                          {selectedDifficulty === 'advanced' && (
                            <div className="absolute -top-1 -right-1 w-2 h-2 bg-[var(--brand-neo)] rounded-full"></div>
                          )}
                        </button>
                      </div>
                    </div>
                    
                    {/* Game Mode Selection */}
                    <div>
                      <p className="text-[13px] text-[var(--ink-med)] mb-2">Game Mode:</p>
                      <div className="grid grid-cols-3 gap-2">
                        {GAME_MODES.map((mode) => {
                          const active = selectedGameMode === mode.id;
                          return (
                            <button
                              key={mode.id}
                              type="button"
                              onClick={() => {
                                setSelectedGameMode(mode.id);
                                if (mode.id === 'human_vs_human') {
                                  startGameplayMode(mode.id);
                                } else {
                                  startGameplayWithDifficulty(mode.id, selectedDifficulty);
                                }
                              }}
                              className={`relative px-3 py-2 rounded-[var(--radius-md)] border text-[12px] transition-all ${
                                active
                                  ? 'border-[var(--brand-neo)] bg-[var(--brand-neo)]/20 text-[var(--brand-neo)] shadow-[0_0_12px_rgba(25,227,255,.3)]'
                                  : 'border-[var(--glass-stroke)] bg-[var(--glass)] text-[var(--ink-hi)] hover:border-[var(--brand-neo)]/50 hover:bg-[var(--glass-stroke)]/20'
                              }`}
                            >
                              <div className="font-semibold">{mode.icon}</div>
                              <div className="text-[10px] opacity-80">{mode.label}</div>
                              {active && (
                                <div className="absolute -top-1 -right-1 w-2 h-2 bg-[var(--brand-neo)] rounded-full"></div>
                              )}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Spelled out, so there is never any doubt about which
                        game the buttons above just started. */}
                    <div className="rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[var(--glass)] px-3 py-2 text-center text-[12px] text-[var(--ink-med)]">
                      Now playing:{' '}
                      <span className="font-semibold text-[var(--brand-neo)]">
                        {GAME_MODES.find((m) => m.id === selectedGameMode)?.label || 'Human vs AI'}
                      </span>
                      {selectedGameMode !== 'human_vs_human' && (
                        <>
                          {' · '}
                          <span className="font-semibold text-[var(--brand-neo)] capitalize">
                            {selectedDifficulty}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                )}

                {exercise ? (
                  <div className="mt-2 space-y-3">
                    <div className="mt-2">
                      <EnhancedChessBoard
                        exercise={exercise}
                        onSquareClick={handleSquareClick}
                        onAction={handleAction}
                        aiMove={aiMove}
                      />
                    </div>
                    {/* Feedback is shown once, as the avatar's caption. It used
                        to be repeated here and inside the board as well. */}
                  </div>
                ) : (
                  <div className="mt-3">
                    <button
                      type="button"
                      onClick={() => handleStartLesson(selectedModule.id)}
                      disabled={loading}
                      className="px-4 py-2 rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[var(--brand-neo)] text-black text-[14px] font-semibold disabled:opacity-60"
                    >
                      {loading ? 'Starting…' : 'Start Lesson'}
                    </button>
                  </div>
                )}
              </div>
            )}
          </aside>
        </section>
      </div>
    </main>
    </AuthGuard>
  );
}
