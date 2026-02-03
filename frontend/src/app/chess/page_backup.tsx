'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import AuthGuard from '@/components/AuthGuard';
import Avatar3D from '@/components/Avatar3D';
import { getChessModules, createChessSession, sendChessAction, ChessModule, ChessExerciseState } from '@/lib/chessApi';
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
  const [lastYogaDate, setLastYogaDate] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('beginner'); // Default to beginner
  const [view, setView] = useState<'list' | 'lesson'>('list');
  const [moduleProgress, setModuleProgress] = useState<Record<string, number>>({});

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
    try {
      if (typeof window === 'undefined') return;
      const stored = window.localStorage.getItem('chessModuleProgress');
      if (stored) {
        const parsed = JSON.parse(stored) as Record<string, number>;
        setModuleProgress(parsed);
      }
    } catch {
      // ignore localStorage errors
    }
  }, []);

  const selectedModule = useMemo(
    () => modules.find((m) => m.id === selectedModuleId) || null,
    [modules, selectedModuleId]
  );

  const updateModuleProgressForExercise = (state: ChessExerciseState) => {
    const total = state.progress_total || 0;
    const current = state.progress_current || 0;
    const percent = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
    
    setModuleProgress((prev) => {
      const next = { ...prev, [state.module_id]: Math.max(prev[state.module_id] || 0, percent) };
      try {
        if (typeof window !== 'undefined') {
          window.localStorage.setItem('chessModuleProgress', JSON.stringify(next));
        }
      } catch {
        // ignore storage errors
      }
      return next;
    });
  };

  const startGameplayMode = async (gameMode: string) => {
    setLoading(true);
    setError(null);
    setSessionId(null);
    setExercise(null);
    
    console.log('Starting gameplay mode:', gameMode);
    
    try {
      const state = await createChessSession('gameplay');
      console.log('Created gameplay session:', state);
      
      // Update the exercise to use the specific game mode
      const updatedState = await sendChessAction(state.session_id, 'set_game_mode', { game_mode: gameMode });
      
      setSelectedModuleId('gameplay');
      setSessionId(updatedState.session_id);
      setExercise(updatedState);
      updateModuleProgressForExercise(updatedState);
      setView('lesson');
    } catch (e: any) {
      console.error('Error starting gameplay mode:', e);
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
    
    console.log('Starting gameplay mode:', gameMode, 'with difficulty:', difficulty);
    
    try {
      const state = await createChessSession('gameplay');
      console.log('Created gameplay session:', state);
      
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
      console.error('Error starting gameplay with difficulty:', e);
      setError(e.message || 'Failed to start gameplay mode');
    } finally {
      setLoading(false);
    }
  };

  const startLesson = async (moduleId: string) => {
    setLoading(true);
    setError(null);
    setSessionId(null);
    setExercise(null);
    
    console.log('Starting lesson for module:', moduleId);
    
    try {
      const state = await createChessSession(moduleId);
      console.log('Created session state:', state);
      console.log('Session ID:', state.session_id);
      console.log('Exercise ID:', state.exercise_id);
      console.log('Exercise type:', state.exercise_type);
      
      setSelectedModuleId(moduleId);
      setSessionId(state.session_id);
      setExercise(state);
      updateModuleProgressForExercise(state);
      setView('lesson');
    } catch (e: any) {
      console.error('Error starting lesson:', e);
      setError(e.message || 'Failed to start lesson');
    } finally {
      setLoading(false);
    }
  };

  const handleSquareClick = async (square: string) => {
    if (!sessionId) {
      console.error('No session ID available');
      return;
    }
    console.log('Sending action for square:', square);
    console.log('Session ID:', sessionId);
    
    try {
      const state = await sendChessAction(sessionId, 'select_square', { square });
      console.log('Received state:', state);
      console.log('Exercise completed:', state.exercise_completed);
      console.log('Is correct:', state.is_correct);
      console.log('Feedback:', state.feedback_message);
      setExercise(state);
      updateModuleProgressForExercise(state);
      
      // Auto-progress if exercise is completed
      if (state.exercise_completed && !state.module_completed) {
        setTimeout(() => {
          handleAction('next');
        }, 1500); // Small delay before next exercise
      }
    } catch (e: any) {
      console.error('Error in handleSquareClick:', e);
      console.error('Error details:', e.message);
      console.error('Error stack:', e.stack);
      setError(e.message || 'Failed to apply move');
    }
  };

  const handleAction = async (type: string, payload?: any) => {
    if (!sessionId) return;
    try {
      const state = await sendChessAction(sessionId, type, payload);
      setExercise(state);
      updateModuleProgressForExercise(state);
      
      // Auto-progress if exercise is completed
      if (state.exercise_completed && !state.module_completed) {
        setTimeout(() => {
          handleAction('next');
        }, 1500); // Small delay before next exercise
      }
    } catch (e: any) {
      setError(e.message || 'Failed to apply action');
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

        <section className="relative grid grid-cols-12 gap-4 md:gap-6 mt-6">
          {/* Avatar Section */}
          <div className="col-span-12 lg:col-span-5 xl:col-span-5 relative">
            <div
              className="avatar-wrap relative h-[72vh] rounded-[var(--radius-lg)] border border-[var(--glass-stroke)]"
              style={{
                background: 'linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02))',
                backdropFilter: 'blur(12px)',
              }}
            >
              <Avatar3D onlyInAnimation={false} staticMode={true} />
              <div
                className="pointer-events-none absolute left-1/2 -translate-x-1/2 bottom-[42px] h-[18px] w-[60%]"
                style={{
                  filter: 'blur(10px)',
                  background: 'radial-gradient(closest-side, rgba(25,227,255,.35), transparent)',
                }}
              />
            </div>
          </div>

          {/* Divider */}
          <div className="hidden lg:block col-span-1 relative">
            <div className="absolute inset-y-6 left-1/2 w-px -translate-x-1/2 bg-gradient-to-b from-[rgba(25,227,255,.0)] via-[rgba(25,227,255,.75)] to-[rgba(25,227,255,.0)] shadow-[0_0_16px_rgba(25,227,255,.65),0_0_48px_rgba(25,227,255,.28)]" />
          </div>

          {/* Chess Lessons Panel */}
          <aside className="col-span-12 lg:col-span-6 xl:col-span-6 content-center space-y-4">
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
                  {modules.map((m) => {
                    const progress = moduleProgress[m.id] || 0;
                    return (
                      <button
                        key={m.id}
                        type="button"
                        onClick={() => startLesson(m.id)}
                        className="w-full rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[var(--glass)] px-3 py-3 text-left transition hover:border-[var(--brand-neo)] hover:shadow-[var(--glow-neo)]"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[14px] font-semibold text-[var(--ink-hi)]">
                            {m.name}
                          </span>
                          <span className="text-[11px] text-[var(--ink-med)]">{progress}%</span>
                        </div>
                        <p className="text-[12px] text-[var(--ink-med)] line-clamp-2">{m.description}</p>
                        <div className="mt-2 h-1.5 w-full rounded-full bg-[var(--glass-stroke)]/40 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-[var(--brand-neo)] transition-all"
                            style={{ width: `${progress}%` }}
                          />
                        </div>
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
                            startGameplayWithDifficulty('human_vs_ai', 'beginner');
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
                            startGameplayWithDifficulty('human_vs_ai', 'intermediate');
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
                            startGameplayWithDifficulty('human_vs_ai', 'advanced');
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
                        <button
                          type="button"
                          onClick={() => startGameplayWithDifficulty('human_vs_ai', selectedDifficulty)}
                          className="px-3 py-2 rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[var(--glass)] text-[12px] text-[var(--ink-hi)] hover:border-[var(--brand-neo)] hover:bg-[var(--glass-stroke)]/20 transition-all"
                        >
                          <div className="font-semibold">🧑 vs 🤖</div>
                          <div className="text-[10px] opacity-80 ">Human vs AI</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => startGameplayWithDifficulty('ai_vs_ai', selectedDifficulty)}
                          className="px-3 py-2 rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[var(--glass)] text-[12px] text-[var(--ink-hi)] hover:border-[var(--brand-neo)] hover:bg-[var(--glass-stroke)]/20 transition-all"
                        >
                          <div className="font-semibold">🤖 vs 🤖</div>
                          <div className="text-[10px] opacity-80">AI vs AI</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => startGameplayMode('human_vs_human')}
                          className="px-3 py-2 rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[var(--glass)] text-[12px] text-[var(--ink-hi)] hover:border-[var(--brand-neo)] hover:bg-[var(--glass-stroke)]/20 transition-all"
                        >
                          <div className="font-semibold">🧑 vs 🧑</div>
                          <div className="text-[10px] opacity-80">Human vs Human</div>
                        </button>
                      </div>
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
                      />
                    </div>

                    {/* Feedback message */}
                    {exercise.feedback_message && (
                      <div
                        className={`text-[14px] mt-2 ${exercise.is_correct === true
                          ? 'text-green-400'
                          : exercise.is_correct === false
                            ? 'text-red-400'
                            : 'text-[var(--ink-med)]'
                          }`}
                      >
                        {exercise.feedback_message}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="mt-3">
                    <button
                      type="button"
                      onClick={() => startLesson(selectedModule.id)}
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
