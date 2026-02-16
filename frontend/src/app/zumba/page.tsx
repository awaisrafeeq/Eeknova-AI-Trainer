'use client';
import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Avatar3D from '@/components/Avatar3D';
import ZumbaCamera from '@/components/ZumbaCamera';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';
import { getZumbaMoves, ZumbaSessionSummary } from '@/lib/zumbaApi';
import { useAuth, useAuthenticatedFetch } from '@/hooks/useAuth';

/**
 * Zumba Module page with real-time camera integration
 * Features:
 * - Live camera feed with pose detection
 * - Real-time feedback and accuracy tracking
 * - Session management and progress tracking
 * - Move selection and settings
 */

export default function ZumbaPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const authenticatedFetch = useAuthenticatedFetch();

  // State management
  const [availableMoves, setAvailableMoves] = useState<string[]>([]);
  const [selectedMove, setSelectedMove] = useState<string>('');
  const [isStarted, setIsStarted] = useState(false);
  const [currentAccuracy, setCurrentAccuracy] = useState(0);
  const [currentFeedback, setCurrentFeedback] = useState<string[]>([]);
  const [sessionSummary, setSessionSummary] = useState<ZumbaSessionSummary | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Session types with state
  const [sessions, setSessions] = useState([
    { id: 'warmup', title: 'Warm-Up', state: 'completed' as 'completed' | 'ongoing' | 'locked', progress: 100 },
    { id: 'main', title: 'Main Routine', state: 'ongoing' as 'completed' | 'ongoing' | 'locked', progress: 45 },
    { id: 'power', title: 'Power Finish', state: 'locked' as 'completed' | 'ongoing' | 'locked', progress: 0 },
  ]);

  // Load available moves
  useEffect(() => {
    if (!isAuthenticated) return; // Only load if authenticated
    
    const loadMoves = async () => {
      try {
        const moves = await getZumbaMoves();
        setAvailableMoves(moves);
        if (moves.length > 0 && !selectedMove) {
          setSelectedMove(moves[0]);
        }
      } catch (error) {
        console.error('Failed to load Zumba moves:', error);
        setError('Failed to load available moves');
      } finally {
        setIsLoading(false);
      }
    };

    loadMoves();
  }, [selectedMove, isAuthenticated]);

  // Toggle session state on click
  function toggleSessionState(id: string) {
    setSessions(prev =>
      prev.map(s => {
        if (s.id !== id) return s;
        if (s.state === 'locked') return s;
        return { ...s, state: s.state === 'completed' ? 'ongoing' : 'completed' };
      })
    );
  }

  // Handle session end
  const handleSessionEnd = (summary: ZumbaSessionSummary | null) => {
    setSessionSummary(summary);
    setShowResults(true);
    setIsStarted(false);
  };

  // Handle accuracy update
  const handleAccuracyUpdate = (accuracy: number) => {
    setCurrentAccuracy(accuracy);
  };

  // Handle feedback update
  const handleFeedbackUpdate = (feedback: string[]) => {
    setCurrentFeedback(feedback);
  };

  // Start/Stop session
  const toggleAnalysisSession = () => {
    if (!selectedMove) {
      setError('Please select a Zumba move first');
      return;
    }
    setIsStarted(!isStarted);
    if (!isStarted) {
      setShowResults(false);
      setSessionSummary(null);
      setCurrentFeedback([]);
      setCurrentAccuracy(0);
    }
  };

  // Go back to dashboard
  const handleBack = () => {
    if (isStarted) {
      setIsStarted(false);
    }
    router.push('/dashboard');
  };

  if (isLoading) {
    return (
      <main className="min-h-screen w-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <div>Loading Zumba moves...</div>
        </div>
      </main>
    );
  }

  return (
    <main
      className="min-h-screen w-full overflow-hidden text-[var(--ink-hi)]"
      style={{ background: 'var(--bg-gradient)', fontFamily: 'var(--font-ui)' }}
    >
      <Particles />

      <div className="mx-auto max-w-[1080px] px-6 md:px-8 py-6 md:py-8 relative">
        {/* Back Button */}
        <button
          onClick={handleBack}
          className="absolute left-4 top-6 z-30 rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] px-4 py-2 text-[16px] font-semibold text-[var(--brand-neo)] transition-all hover:shadow-[var(--glow-neo)]"
        >
          ← Back
        </button>

        <section className="relative grid grid-cols-12 gap-4 md:gap-6 mt-6">
          {/* Camera Section */}
          <div className="col-span-12 lg:col-span-7 xl:col-span-7 relative">
            <div
              className="camera-wrap relative h-[72vh] rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] overflow-hidden"
              style={{
                background: 'linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02))',
                backdropFilter: 'blur(12px)',
              }}
            >
              <ZumbaCamera
                selectedMove={selectedMove}
                isStarted={isStarted}
                onSessionEnd={handleSessionEnd}
                onAccuracyUpdate={handleAccuracyUpdate}
                onFeedbackUpdate={handleFeedbackUpdate}
                onError={setError}
              />
              
              {/* Camera Controls Overlay */}
              <div className="absolute bottom-4 left-4 right-4 flex justify-between items-end">
                <div className="flex gap-3">
                  {/* Move Selector */}
                  <select
                    value={selectedMove}
                    onChange={(e) => setSelectedMove(e.target.value)}
                    disabled={isStarted}
                    className="bg-black/50 backdrop-blur-sm text-white rounded-lg px-3 py-2 text-sm border border-white/20 disabled:opacity-50"
                  >
                    <option value="">Select Move</option>
                    {availableMoves.map((move) => (
                      <option key={move} value={move}>
                        {move.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Start/Stop Button */}
                <button
                  onClick={toggleAnalysisSession}
                  disabled={!selectedMove}
                  className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                    isStarted
                      ? 'bg-red-500 hover:bg-red-600 text-white'
                      : 'bg-green-500 hover:bg-green-600 text-white disabled:opacity-50 disabled:cursor-not-allowed'
                  }`}
                >
                  {isStarted ? 'Stop Session' : 'Start Session'}
                </button>
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="hidden lg:block col-span-1 relative">
            <div className="absolute inset-y-6 left-1/2 w-px -translate-x-1/2 bg-gradient-to-b from-[rgba(25,227,255,.0)] via-[rgba(25,227,255,.75)] to-[rgba(25,227,255,.0)] shadow-[0_0_16px_rgba(25,227,255,.65),0_0_48px_rgba(25,227,255,.28)]" />
          </div>

          {/* Right Panel */}
          <aside className="col-span-12 lg:col-span-4 xl:col-span-4 content-center">
            <div className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-6 btn-glass" style={{ background: 'linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.01))' }}>
              {/* Logo + Title */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] grid place-items-center shadow-[var(--glow-neo)]">
                    <Image src="/logo.png" alt="Logo" width={36} height={36} />
                  </div>
                  <div>
                    <div className="text-[18px] font-semibold text-[var(--brand-neo)]">Eeknova</div>
                    <div className="text-[12px] text-[var(--ink-med)]">AITrainer</div>
                  </div>
                </div>

                {/* Accuracy Display */}
                <div className="text-right">
                  <div className="text-[20px] font-bold text-[var(--brand-neo)]">
                    {currentAccuracy.toFixed(1)}%
                  </div>
                  <div className="text-[12px] text-[var(--ink-med)]">Accuracy</div>
                </div>
              </div>

              <h2 className="text-[28px] font-extrabold text-[var(--brand-neo)] mb-2">ZUMBA</h2>
              <p className="text-[14px] text-[var(--ink-med)] mb-6">
                Real-time dance analysis with AI-powered feedback
              </p>

              {/* Current Status */}
              <div className="mb-6">
                <h3 className="text-[14px] font-semibold text-[var(--brand-neo)] mb-3">CURRENT STATUS</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-[var(--ink-med)]">Move:</span>
                    <span className="text-white font-medium">
                      {selectedMove ? selectedMove.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Not Selected'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[var(--ink-med)]">Session:</span>
                    <span className={`font-medium ${isStarted ? 'text-green-400' : 'text-yellow-400'}`}>
                      {isStarted ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[var(--ink-med)]">Accuracy:</span>
                    <span className="text-white font-medium">{currentAccuracy.toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              {/* Live Feedback */}
              {currentFeedback.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-[14px] font-semibold text-[var(--brand-neo)] mb-3">LIVE FEEDBACK</h3>
                  <div className="bg-black/30 rounded-lg p-3 max-h-32 overflow-y-auto">
                    {currentFeedback.map((feedback, index) => (
                      <div key={index} className="text-xs text-yellow-300 mb-1">
                        • {feedback}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Session Types */}
              <div className="mb-6">
                <h3 className="text-[14px] font-semibold text-[var(--brand-neo)] mb-3">SESSION TYPES</h3>
                <div className="space-y-2">
                  {sessions.map(s => (
                    <motion.button
                      key={s.id}
                      onClick={() => toggleSessionState(s.id)}
                      whileTap={{ scale: s.state === 'locked' ? 1 : 0.98 }}
                      className={`w-full text-left rounded-lg border px-3 py-2 flex items-center justify-between transition-all text-sm
                        ${s.state === 'completed' ? 'border-[rgba(25,227,255,.18)] bg-[rgba(25,227,255,.02)]' : ''}
                        ${s.state === 'ongoing' ? 'border-[var(--brand-neo)] shadow-[0_0_10px_rgba(25,227,255,.22)]' : ''}
                        ${s.state === 'locked' ? 'opacity-70 bg-[rgba(255,255,255,.01)] pointer-events-auto' : ''}
                      `}
                      style={{ borderColor: s.state === 'ongoing' ? 'var(--brand-neo)' : undefined }}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`w-5 h-5 grid place-items-center rounded-md text-xs ${s.state === 'completed' ? 'bg-[rgba(25,227,255,.12)]' : ''}`}>
                          {s.state === 'completed' ? '✔' : s.state === 'locked' ? '🔒' : '▶'}
                        </span>
                        <div>
                          <div className={`text-xs font-semibold ${s.state === 'ongoing' ? 'text-[var(--brand-neo)]' : ''}`}>{s.title}</div>
                          <div className="text-[11px] text-[var(--ink-med)]">
                            {s.state === 'locked' ? 'Locked' : s.state === 'ongoing' ? 'Ongoing' : 'Completed'}
                          </div>
                        </div>
                      </div>

                      <div className="text-right text-[11px">
                        <div className="text-[11px] text-[var(--brand-neo)] font-semibold">{s.progress}%</div>
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mb-4">
                  <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
                    <div className="text-red-300 text-sm font-semibold mb-1">Error</div>
                    <div className="text-red-200 text-xs">{error}</div>
                  </div>
                </div>
              )}
            </div>
          </aside>
        </section>
      </div>

      {/* Results Modal */}
      <AnimatePresence>
        {showResults && sessionSummary && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50"
            onClick={() => setShowResults(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-[var(--glass)] border border-[var(--glass-stroke)] rounded-[var(--radius-lg)] p-6 max-w-md w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-[24px] font-bold text-[var(--brand-neo)] mb-4">Session Complete!</h3>
              
              <div className="space-y-3 mb-6">
                <div className="flex justify-between">
                  <span className="text-[var(--ink-med)]">Move:</span>
                  <span className="text-white font-medium">{sessionSummary.target_move}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--ink-med)]">Frames Processed:</span>
                  <span className="text-white font-medium">{sessionSummary.frames_processed}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--ink-med)]">Average Accuracy:</span>
                  <span className="text-[var(--brand-neo)] font-bold">{sessionSummary.average_accuracy.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--ink-med)]">Feedback Count:</span>
                  <span className="text-white font-medium">{sessionSummary.feedback_count}</span>
                </div>
              </div>

              <button
                onClick={() => setShowResults(false)}
                className="w-full bg-[var(--brand-neo)] text-white rounded-lg py-3 font-semibold hover:opacity-90 transition-opacity"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}

/* ================= Progress Ring Component =================
   Animated SVG circle that fills to `percentage`. */
function ProgressRing({ size = 72, stroke = 8, percentage = 0 }: { size?: number; stroke?: number; percentage: number }) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = (percentage / 100) * circumference;

  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    // animate to target dash
    const target = circumference - dash;
    // small animation using requestAnimationFrame
    let rafId = 0;
    const duration = 700;
    const start = performance.now();
    const from = offset;
    const animate = (t: number) => {
      const elapsed = Math.min(1, (t - start) / duration);
      const value = from + (target - from) * elapsed;
      setOffset(value);
      if (elapsed < 1) rafId = requestAnimationFrame(animate);
    };
    rafId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [percentage]);

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <defs>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* background circle */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="rgba(255,255,255,0.06)"
        strokeWidth={stroke}
        fill="transparent"
      />

      {/* progress circle */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="var(--brand-neo)"
        strokeWidth={stroke}
        strokeLinecap="round"
        fill="transparent"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 0.2s linear' }}
        filter="url(#glow)"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />

      {/* percentage text */}
      <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" fontSize={14} fontWeight={700} fill="var(--brand-neo)">
        {percentage}%
      </text>
    </svg>
  );
}

/* ================= Particles (re-used) ================= */
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
