'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import Avatar3D from '@/components/Avatar3D';
import ZumbaCamera from '@/components/ZumbaCamera';
import { getZumbaMoves, ZumbaAnalysisResult, ZumbaSessionSummary } from '@/lib/zumbaApi';
import { useAuth } from '@/hooks/useAuth';

type ZumbaVisualPhase = 'in' | 'main' | 'out';

type ZumbaAnimationSet = {
  in: string;
  main: string;
  out: string;
};

const ZUMBA_ANIMATIONS: Record<string, ZumbaAnimationSet> = {
  body_rolls: {
    in: '/zumba pose/Body Rolls/Idle in Body Rolls_compressed.glb',
    main: '/zumba pose/Body Rolls/Main Body Rolls_compressed.glb',
    out: '/zumba pose/Body Rolls/Idle out Body Rolls_compressed.glb',
  },
  cumbia_step: {
    in: '/zumba pose/Cumbia Step/Idle In Cumbia Step_compressed.glb',
    main: '/zumba pose/Cumbia Step/Main Cumbia Step_compressed.glb',
    out: '/zumba pose/Cumbia Step/Idle Out Cumbia Step_compressed.glb',
  },
  grape_vine: {
    in: '/zumba pose/Grape Vine/Idle In Grape Vine_compressed.glb',
    main: '/zumba pose/Grape Vine/Main Grape Vine_compressed.glb',
    out: '/zumba pose/Grape Vine/Idle Out Grape Vine_compressed.glb',
  },
  heel_taps: {
    in: '/zumba pose/Heel Taps/Idle in Heel Taps_compressed.glb',
    main: '/zumba pose/Heel Taps/Main Heel Taps_compressed.glb',
    out: '/zumba pose/Heel Taps/Idle out Heel Taps_compressed.glb',
  },
  jumping_jacks: {
    in: '/zumba pose/Jumping Jacks/Idle In Jumping Jacks_compressed.glb',
    main: '/zumba pose/Jumping Jacks/Main Jumping Jacks_compressed.glb',
    out: '/zumba pose/Jumping Jacks/Idle Out Jumping Jacks_compressed.glb',
  },
  knee_lifts: {
    in: '/zumba pose/Knee Lifts/Idle in Knee Lift_compressed.glb',
    main: '/zumba pose/Knee Lifts/Main Knee Lift_compressed.glb',
    out: '/zumba pose/Knee Lifts/Idle out Knee Lift_compressed.glb',
  },
  lunge_with_punches: {
    in: '/zumba pose/Lunge with Punches/Idle in Lunge with Punches_compressed.glb',
    main: '/zumba pose/Lunge with Punches/Main Lunge with Punches_compressed.glb',
    out: '/zumba pose/Lunge with Punches/Idle out Lunge with Punches_compressed.glb',
  },
  mambo_step: {
    in: '/zumba pose/Mambo/Idle in Mambo_compressed.glb',
    main: '/zumba pose/Mambo/Main Mambo_compressed.glb',
    out: '/zumba pose/Mambo/Idle out Mambo_compressed.glb',
  },
  march_in_place: {
    in: '/zumba pose/March in Place/Idle in March in place_compressed.glb',
    main: '/zumba pose/March in Place/Main March in place_compressed.glb',
    out: '/zumba pose/March in Place/Idle out March in place_compressed.glb',
  },
  merengue_march: {
    in: '/zumba pose/Merengue March/Idle In Merengue March_compressed.glb',
    main: '/zumba pose/Merengue March/Main Merengue March_compressed.glb',
    out: '/zumba pose/Merengue March/Idle Out Merengue March_compressed.glb',
  },
  reggaeton_stomp: {
    in: '/zumba pose/Reggaeton Stomp/Idle in Reggaeton stomp_compressed.glb',
    main: '/zumba pose/Reggaeton Stomp/Main Reggaeton stomp_compressed.glb',
    out: '/zumba pose/Reggaeton Stomp/Idle out Reggaeton stomp_compressed.glb',
  },
  shimmy: {
    in: '/zumba pose/Shimmy/Idle in Shimmy_compressed.glb',
    main: '/zumba pose/Shimmy/Main Shimmy_compressed.glb',
    out: '/zumba pose/Shimmy/Idle out Shimmy_compressed.glb',
  },
  side_punches: {
    in: '/zumba pose/Side Punches/Idle in Side punches_compressed.glb',
    main: '/zumba pose/Side Punches/Main Side punches_compressed.glb',
    out: '/zumba pose/Side Punches/Idle out Side punches_compressed.glb',
  },
  squat_with_clap: {
    in: '/zumba pose/Squat With Clap/Idle In Squat With Clap_compressed.glb',
    main: '/zumba pose/Squat With Clap/Main Squat With Clap_compressed.glb',
    out: '/zumba pose/Squat With Clap/Idle Out Squat With Clap_compressed.glb',
  },
  step_clap: {
    in: '/zumba pose/Step Clap/Idle in Step clap_compressed.glb',
    main: '/zumba pose/Step Clap/Main Step clap_compressed.glb',
    out: '/zumba pose/Step Clap/Idle out Step clap_compressed.glb',
  },
  step_touch: {
    in: '/zumba pose/Step Touch/Idle in Step touch_compressed.glb',
    main: '/zumba pose/Step Touch/Main Step touch_compressed.glb',
    out: '/zumba pose/Step Touch/Idle out Step touch_compressed.glb',
  },
  twist_step: {
    in: '/zumba pose/Twist Step/Idle in Twist Step_compressed.glb',
    main: '/zumba pose/Twist Step/Main Twist Step_compressed.glb',
    out: '/zumba pose/Twist Step/Idle out Twist Step_compressed.glb',
  },
  'zumba_turn_(pivot)': {
    in: '/zumba pose/Zumba Turn(Pivot)/Idle in Zumba turn (pivot)_compressed.glb',
    main: '/zumba pose/Zumba Turn(Pivot)/Main Zumba turn (pivot)_compressed.glb',
    out: '/zumba pose/Zumba Turn(Pivot)/Idle out Zumba turn (pivot)_compressed.glb',
  },
};

/**
 * Zumba module UI aligned with the Yoga page:
 * display area first, controls and stats below, camera processing hidden.
 */
export default function ZumbaPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const [availableMoves, setAvailableMoves] = useState<string[]>([]);
  const [selectedMove, setSelectedMove] = useState<string>('');
  const [isStarted, setIsStarted] = useState(false);
  const [isSessionViewActive, setIsSessionViewActive] = useState(false);
  const [visualPhase, setVisualPhase] = useState<ZumbaVisualPhase>('main');
  const [visualAnimKey, setVisualAnimKey] = useState(0);
  const [currentAccuracy, setCurrentAccuracy] = useState(0);
  const [framesProcessed, setFramesProcessed] = useState(0);
  const [validFrames, setValidFrames] = useState(0);
  const [activeFrames, setActiveFrames] = useState(0);
  const [poseDetected, setPoseDetected] = useState(false);
  const [activeMovement, setActiveMovement] = useState(false);
  const [currentFeedback, setCurrentFeedback] = useState<string[]>([]);
  const [sessionSummary, setSessionSummary] = useState<ZumbaSessionSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const selectedAnimationSet = selectedMove ? ZUMBA_ANIMATIONS[selectedMove] : undefined;
  const visualAnimationPath = selectedAnimationSet?.[isSessionViewActive ? visualPhase : 'main'];
  const shouldLoopVisualAnimation = !isSessionViewActive || visualPhase === 'main';

  useEffect(() => {
    if (!isSessionViewActive) {
      setVisualPhase('main');
      setVisualAnimKey((key) => key + 1);
    }
  }, [selectedMove, isSessionViewActive]);

  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;

    const loadMoves = async () => {
      try {
        const moves = await getZumbaMoves();
        if (cancelled) return;

        setAvailableMoves(moves);
        setSelectedMove((current) => current || moves[0] || '');
      } catch (error) {
        console.error('Failed to load Zumba moves:', error);
        if (!cancelled) {
          setError('Failed to load available moves');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    loadMoves();

    return () => {
      cancelled = true;
    };
  }, [authLoading, isAuthenticated]);

  const handleSessionEnd = useCallback((summary: ZumbaSessionSummary | null) => {
    if (summary && summary.frames_processed > 0) {
      setSessionSummary(summary);
    } else {
      setSessionSummary(null);
      setError('Session ended before any frames were analyzed. Please keep camera access enabled and try again.');
    }
    setIsStarted(false);
  }, []);

  const handleAccuracyUpdate = useCallback((accuracy: number) => {
    setCurrentAccuracy(accuracy);
  }, []);

  const handleFeedbackUpdate = useCallback((feedback: string[]) => {
    setCurrentFeedback(feedback);
  }, []);

  const handleFrameProcessed = useCallback((result: ZumbaAnalysisResult) => {
    const metrics = result.performance_metrics;
    setFramesProcessed(metrics?.total_frames || 0);
    setValidFrames(metrics?.comparable_frames || 0);
    setActiveFrames(metrics?.active_frames || 0);
    setPoseDetected(Boolean(result.pose_detected));
    setActiveMovement(Boolean(result.active_movement));
  }, []);

  const handleVisualAnimationEnd = useCallback(() => {
    if (!isSessionViewActive) return;

    if (visualPhase === 'in') {
      setVisualPhase('main');
      setVisualAnimKey((key) => key + 1);
      return;
    }

    if (visualPhase === 'out') {
      setIsSessionViewActive(false);
      setVisualPhase('main');
      setVisualAnimKey((key) => key + 1);
    }
  }, [isSessionViewActive, visualPhase]);

  const toggleAnalysisSession = () => {
    if (isSessionViewActive && !isStarted) {
      setIsSessionViewActive(false);
      return;
    }

    if (!selectedMove) {
      setError('Please select a Zumba move first');
      return;
    }

    if (!isStarted) {
      setSessionSummary(null);
      setCurrentFeedback([]);
      setCurrentAccuracy(0);
      setFramesProcessed(0);
      setValidFrames(0);
      setActiveFrames(0);
      setPoseDetected(false);
      setActiveMovement(false);
      setError(null);
      setIsSessionViewActive(true);
      setVisualPhase(selectedAnimationSet ? 'in' : 'main');
      setVisualAnimKey((key) => key + 1);
      setIsStarted(true);
      return;
    }

    setIsStarted(false);
    if (selectedAnimationSet) {
      setIsSessionViewActive(true);
      setVisualPhase('out');
      setVisualAnimKey((key) => key + 1);
    } else {
      setIsSessionViewActive(false);
    }
  };

  const handleBack = () => {
    if (isStarted) {
      setIsStarted(false);
    }
    setIsSessionViewActive(false);
    router.push('/dashboard');
  };

  if (authLoading || isLoading) {
    return (
      <main
        className="min-h-screen w-full flex items-center justify-center text-[var(--ink-hi)]"
        style={{ background: 'var(--bg-gradient)', fontFamily: 'var(--font-ui)' }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--brand-neo)] mx-auto mb-4" />
          <div>Loading Zumba moves...</div>
        </div>
      </main>
    );
  }

  return (
    <main
      className="min-h-screen w-full overflow-hidden text-[var(--ink-hi)]"
      style={{
        background: isSessionViewActive ? 'transparent' : 'var(--bg-gradient)',
        fontFamily: 'var(--font-ui)',
        transition: 'background 0.5s ease',
      }}
    >
      {!isSessionViewActive && <Particles />}

      <div className={`mx-auto relative ${
        isSessionViewActive ? 'w-full max-w-none p-0' : 'max-w-[1400px] px-6 md:px-8 pb-6 md:pb-8'
      }`}>
        {!isSessionViewActive && (
          <button
            onClick={handleBack}
            className="absolute left-4 top-6 z-20 rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] px-5 py-2 text-[18px] font-semibold text-[var(--brand-neo)] transition-all hover:shadow-[var(--glow-neo)]"
          >
            Back
          </button>
        )}

        <section className={`${
          isSessionViewActive ? 'fixed inset-0 flex flex-col z-10' : 'relative grid grid-cols-12 gap-4 md:gap-6'
        }`}>
          <div className={`${
            isSessionViewActive ? 'absolute inset-x-0 bottom-0 h-screen' : 'col-span-12 h-[50vh]'
          } transition-all duration-700 ease-in-out`}>
            <div className="flex h-full w-full items-end justify-center">
              <div className={`relative flex ${
                isSessionViewActive ? 'h-[80vh]' : 'h-[50vh]'
              } w-full items-end justify-center overflow-hidden`}>
                <div
                  className={`absolute ${
                    isSessionViewActive ? 'inset-x-[18%] bottom-[6%] h-[78%]' : 'inset-x-[8%] bottom-0 h-[82%]'
                  } rounded-[var(--radius-lg)] border border-[rgba(25,227,255,.18)]`}
                  style={{
                    background:
                      isSessionViewActive
                        ? 'linear-gradient(180deg, rgba(255,255,255,.03), rgba(25,227,255,.02) 54%, rgba(4,13,35,.04))'
                        : 'linear-gradient(180deg, rgba(25,227,255,.05), rgba(106,93,255,.05) 54%, rgba(4,13,35,.08))',
                    boxShadow:
                      'inset 0 0 48px rgba(25,227,255,.08), 0 0 28px rgba(25,227,255,.08)',
                  }}
                />

                <div className={`relative z-10 h-full w-full ${visualAnimationPath ? '' : 'flex flex-col items-center justify-center text-center'}`}>
                  {visualAnimationPath ? (
                    <Avatar3D
                      key={`zumba-avatar-${selectedMove}-${isSessionViewActive ? visualPhase : 'preview'}-${visualAnimKey}`}
                      selectedPose=""
                      staticMode={false}
                      playAnimationPath={visualAnimationPath}
                      playAnimationKey={visualAnimKey}
                      loopCustomAnimation={shouldLoopVisualAnimation}
                      cameraManualDistanceFactor={isSessionViewActive ? 1.65 : 1.75}
                      cameraManualTargetYOffsetFactor={isSessionViewActive ? 0.04 : 0.02}
                      lockCamera={true}
                      freezeCameraFit={isSessionViewActive}
                      onCustomAnimationEnd={handleVisualAnimationEnd}
                    />
                  ) : (
                    <div className={`relative z-10 flex flex-col items-center text-center ${isSessionViewActive ? 'mb-[12vh]' : 'mb-6'}`}>
                      <div className={`mb-5 grid ${isSessionViewActive ? 'h-32 w-32' : 'h-24 w-24'} place-items-center rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] shadow-[var(--glow-neo)]`}>
                        <Image src="/logo.png" alt="Eeknova AI Trainer" width={68} height={68} priority />
                      </div>
                      <div
                        className={`font-black leading-none text-[var(--brand-neo)] ${isSessionViewActive ? 'text-[58px]' : 'text-[42px]'}`}
                        style={{ fontFamily: 'var(--font-future)' }}
                      >
                        Zumba
                      </div>
                      <div className={`${isSessionViewActive ? 'mt-4 text-[24px]' : 'mt-2 text-[18px]'} font-semibold text-white`}>
                        {isSessionViewActive ? 'Live dance detection is active' : 'Ready for AI dance analysis'}
                      </div>
                      <div className={`${isSessionViewActive ? 'mt-3 max-w-[680px] text-[18px]' : 'mt-2 max-w-[520px] text-[15px]'} text-[var(--ink-med)]`}>
                        {selectedMove
                          ? `Selected move: ${formatMove(selectedMove)}`
                          : 'Select a move below to start your session.'}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className={`${
            isSessionViewActive ? 'fixed inset-x-0 bottom-0 z-20 pointer-events-none' : 'col-span-12 relative h-[50vh]'
          }`}>
            <div className="mb-4">
              {!isSessionViewActive && (
                <h2
                  className="text-[28px] font-bold leading-tight text-[var(--brand-neo)] text-center"
                  style={{ fontFamily: 'var(--font-future)' }}
                >
                  Live Detection
                </h2>
              )}
            </div>

            {!isSessionViewActive && (
            <div className="mt-7">
              <GlassCard title="Move Selector">
                <div className="space-y-3">
                  <select
                    value={selectedMove}
                    onChange={(event) => setSelectedMove(event.target.value)}
                    disabled={isStarted}
                    className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-[var(--ink-hi)] text-[16px] focus:outline-none focus:ring-2 focus:ring-[var(--brand-neo)] focus:border-transparent transition-all disabled:opacity-50"
                    style={{
                      background: 'linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))',
                      backdropFilter: 'blur(12px)',
                      colorScheme: 'dark',
                    }}
                  >
                    <option value="">Select Move</option>
                    {availableMoves.map((move) => (
                      <option key={move} value={move} className="bg-[#0B132B] text-white">
                        {formatMove(move)}
                      </option>
                    ))}
                  </select>
                  <div className="text-center text-[14px] text-[var(--ink-med)]">
                    Target move:{' '}
                    <span className="text-[var(--brand-neo)] font-semibold">
                      {selectedMove ? formatMove(selectedMove) : 'Not selected'}
                    </span>
                  </div>
                </div>
              </GlassCard>
            </div>
            )}

            <div className={`flex flex-wrap gap-3 justify-center transition-all duration-700 ease-in-out pointer-events-auto ${
              isSessionViewActive ? 'fixed bottom-8 left-1/2 -translate-x-1/2 z-30' : 'mt-7'
            }`}>
              <ControlButton
                label={isSessionViewActive ? 'End Session' : 'Start'}
                active={!isSessionViewActive}
                danger={isSessionViewActive}
                disabled={!selectedMove}
                onClick={toggleAnalysisSession}
              />
            </div>

            <div className="fixed left-[-10000px] top-0 h-[240px] w-[320px] overflow-hidden pointer-events-none">
              <ZumbaCamera
                selectedMove={selectedMove}
                isStarted={isStarted}
                onSessionEnd={handleSessionEnd}
                onAccuracyUpdate={handleAccuracyUpdate}
                onFeedbackUpdate={handleFeedbackUpdate}
                onFrameProcessed={handleFrameProcessed}
                onError={setError}
              />
            </div>

            {!isSessionViewActive && (
            <GlassCard title="Session Stats" className="mt-7">
              <ul className="space-y-1 text-[16px] text-[var(--ink-med)]">
                <li>
                  Move
                  <span className="float-right font-semibold text-white">
                    {selectedMove ? formatMove(selectedMove) : 'Not selected'}
                  </span>
                </li>
                <li>
                  Session
                  <span className={`float-right font-semibold ${isStarted ? 'text-green-400' : 'text-yellow-400'}`}>
                    {isStarted ? 'Active' : 'Inactive'}
                  </span>
                </li>
                <li>
                  Avg Accuracy
                  <span className="float-right font-semibold text-[var(--brand-neo)]">
                    {validFrames > 0 ? `${currentAccuracy.toFixed(1)}%` : '--'}
                  </span>
                </li>
                <li>
                  Frames
                  <span className="float-right font-semibold">{framesProcessed}</span>
                </li>
                <li>
                  Valid Frames
                  <span className="float-right font-semibold">{validFrames}</span>
                </li>
                <li>
                  Active Frames
                  <span className="float-right font-semibold">{activeFrames}</span>
                </li>
                <li>
                  Pose Detected
                  <span className={`float-right font-semibold ${poseDetected ? 'text-green-400' : 'text-[var(--ink-med)]'}`}>
                    {poseDetected ? 'Yes' : 'No'}
                  </span>
                </li>
                <li>
                  Active Movement
                  <span className={`float-right font-semibold ${activeMovement ? 'text-green-400' : 'text-yellow-400'}`}>
                    {activeMovement ? 'Yes' : 'No'}
                  </span>
                </li>
                <li>
                  User
                  <span className="float-right font-semibold">
                    {user?.full_name || user?.username || user?.name || user?.email || 'Guest'}
                  </span>
                </li>
              </ul>
            </GlassCard>
            )}

            {!isSessionViewActive && (
            <GlassCard title="Live Feedback" className="mt-7">
              {currentFeedback.length > 0 ? (
                <div className="space-y-2 text-[14px] text-yellow-300">
                  {currentFeedback.slice(0, 5).map((feedback, index) => (
                    <div key={`${feedback}-${index}`} className="rounded-lg border border-yellow-300/20 bg-yellow-300/5 px-3 py-2">
                      {feedback}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-[14px] text-[var(--ink-med)] text-center py-2">
                  {isStarted ? 'Analyzing your movement...' : 'Feedback will appear during the session.'}
                </div>
              )}
            </GlassCard>
            )}

            {error && (
              <GlassCard title="Error" className="mt-7 border-red-500/50">
                <div className="text-[14px] text-red-200">{error}</div>
              </GlassCard>
            )}

            {sessionSummary && !isSessionViewActive && (
              <div id="zumba-session-summary">
                <GlassCard title="Session Summary" className="mt-7">
                  <ul className="space-y-1 text-[14px] text-[var(--ink-med)]">
                    <li>
                      Move
                      <span className="float-right font-semibold text-white">
                        {formatMove(sessionSummary.target_move)}
                      </span>
                    </li>
                    <li>
                      Frames Processed
                      <span className="float-right font-semibold">{sessionSummary.frames_processed}</span>
                    </li>
                    <li>
                      Avg Accuracy
                      <span className="float-right font-semibold text-[var(--brand-neo)]">
                        {sessionSummary.average_accuracy.toFixed(1)}%
                      </span>
                    </li>
                    <li>
                      Feedback Count
                      <span className="float-right font-semibold">{sessionSummary.feedback_count}</span>
                    </li>
                  </ul>
                </GlassCard>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function formatMove(move: string) {
  return move
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function GlassCard({
  title,
  children,
  className = '',
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-4 btn-glass ${className}`}
      style={{
        background: 'linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))',
      }}
    >
      <h3 className="text-[20px] font-semibold mb-2 text-[var(--brand-neo)]">{title}</h3>
      {children}
    </div>
  );
}

function ControlButton({
  label,
  active,
  danger,
  disabled,
  onClick,
}: {
  label: string;
  active?: boolean;
  danger?: boolean;
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`rounded-[var(--radius-md)] border border-[var(--glass-stroke)] px-5 py-2 text-[16px] font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
        danger
          ? 'bg-red-500/80 text-white hover:bg-red-600/80'
          : active
            ? 'bg-[var(--brand-neo)] text-black shadow-[0_0_18px_rgba(25,227,255,.55)]'
            : 'bg-[var(--glass)] text-[var(--brand-neo)] hover:shadow-[var(--glow-neo)]'
      }`}
    >
      {label}
    </button>
  );
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
