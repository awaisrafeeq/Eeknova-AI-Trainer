'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth, useAuthenticatedFetch } from '@/hooks/useAuth';
import { authRedirect } from '@/lib/auth';

import { useRouter } from 'next/navigation';

import Avatar3D from '@/components/Avatar3D';
import YogaCamera from '@/components/YogaCamera';
import { SessionSummary, TTSFeedback } from '@/lib/yogaApi';



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



const POSE_OPTIONS = [

  "Downward Dog",

  "Warrior Pose",

  "Mountain Pose",

  "Tree Pose",

  "Cat And Camel Pose",

  "Child Pose",

  "Cobra Pose",

  "Seated Forward",

  "Warrior 1"

];



const MET_VALUES: Record<string, number> = {

  "Mountain Pose": 2.0,

  "Tree Pose": 2.5,

  "Downward Dog": 3.0,

  "Warrior 1": 3.2,

  "Warrior Pose": 3.2,

  "Triangle": 3.0,

  "Child Pose": 1.8,

  "Cobra Pose": 2.5,

  "Cat And Camel Pose": 2.2,

  "Seated Forward": 2.4,

};



export default function YogaPage() {

  const { user, isLoading: authLoading, isAuthenticated } = useAuth();
  const authenticatedFetch = useAuthenticatedFetch();
  const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8000';
  const router = useRouter();

  // TTS reference for cleanup
  const ttsRef = useRef<TTSFeedback | null>(null);

  const [selectedPose, setSelectedPose] = useState<string>("Mountain Pose");

  const [isSessionStarted, setIsSessionStarted] = useState(false);

  const [isPaused, setIsPaused] = useState(false);

  const [flowStage, setFlowStage] = useState<'setup' | 'warmup' | 'pose' | 'cooldown'>('setup');

  const WARMUP_STEPS = [
    {
      label: 'Deep Breathing Cycle',
      path: '/warm-up/Deep Breathing Cycle_compressed.glb',
      seconds: 60, // 1 minute per step
    },
    {
      label: 'Neck Rolls',
      path: '/warm-up/NECK_ROLLS_compressed.glb',
      seconds: 60,
    },
    {
      label: 'Arm Circles',
      path: '/warm-up/Arm Circles_compressed.glb',
      seconds: 60,
      isPlaceholder: true,
    },
    {
      label: 'Leg Stretch Side-to-Side',
      path: '/warm-up/Leg Stretch Side-to-Side_compressed.glb',
      seconds: 60,
    },
  ] as const;

  const COOLDOWN_STEPS = [
    {
      label: 'Forward Fold Stretch',
      path: '/cool-down/Forward Fold Stretch_compressed.glb',
      seconds: 60,
    },
    {
      label: 'Deep Breathing Cycle',
      path: '/cool-down/Deep Breathing Cycle_compressed.glb',
      seconds: 60, // 1 minute per step
    },
    {
      label: 'Relax and Reset Pose',
      path: '/cool-down/RELAX_&_RESET_pose_compressed.glb',
      seconds: 60,
      isPlaceholder: true,
    },
  ] as const;

  const [warmupStepIndex, setWarmupStepIndex] = useState(0);
  const [cooldownStepIndex, setCooldownStepIndex] = useState(0);
  const [auxTimeLeft, setAuxTimeLeft] = useState(0);
  const [auxAnimKey, setAuxAnimKey] = useState(0);
  const [showWarmupSkipWarning, setShowWarmupSkipWarning] = useState(false);

  const [currentPoseIndex, setCurrentPoseIndex] = useState(2); // Mountain Pose index

  const [sessionStats, setSessionStats] = useState({

    duration: 0,

    calories: 0,

    accuracy: 0,

    streak: 0, // Will be loaded from localStorage

  });

  const [currentAccuracy, setCurrentAccuracy] = useState(0);

  const [corrections, setCorrections] = useState<string[]>([]);

  const [sessionSummary, setSessionSummary] = useState<SessionSummary | null>(null);

  const [energyLevel, setEnergyLevel] = useState(82);

  const [sessionPhase, setSessionPhase] = useState<'in' | 'hold' | 'out' | 'idle'>('idle');

  const [phaseTimeLeft, setPhaseTimeLeft] = useState(0);

  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  const [isTTSSpeaking, setIsTTSSpeaking] = useState(false);

  const [lastYogaDate, setLastYogaDate] = useState<string | null>(null);

  const [shouldPlayAnimation, setShouldPlayAnimation] = useState(false); // Control animation playback

  // Timer state for pose duration
  const [totalTime, setTotalTime] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [currentPhase, setCurrentPhase] = useState<'in' | 'hold' | 'out'>('in');

  // TTS feedback state
  const [currentTTSFeedback, setCurrentTTSFeedback] = useState<string>('');

  // Pose specifications for timing
  const POSE_SPEC: Record<string, { in: number; hold: number; out: number; total: number }> = {
    "Mountain Pose": { in: 4, hold: 24, out: 5, total: 33 },
    "Tree Pose": { in: 9, hold: 30, out: 7, total: 46 },
    "Downward Dog": { in: 9, hold: 30, out: 8, total: 47 },
    "Warrior 1": { in: 8, hold: 30, out: 6, total: 44 },
    "Warrior Pose": { in: 8, hold: 30, out: 6, total: 44 },
    "Triangle": { in: 4, hold: 25, out: 4, total: 33 },
    "Child Pose": { in: 10, hold: 33, out: 9, total: 52 },
    "Cobra Pose": { in: 9, hold: 21, out: 9, total: 39 },
    "Cat And Camel Pose": { in: 8, hold: 42, out: 10, total: 60 },
  };



  // Format time utility
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Timer effect for countdown and phase management
  useEffect(() => {
    if (!isSessionStarted || isPaused || timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          // TODO: Re-enable cool-down later - skip directly to session end
          // startCooldown();
          finalizeSessionEnd();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isSessionStarted, isPaused, timeLeft]);

  // Warm-up / Cool-down timer effect
  useEffect(() => {
    if (flowStage !== 'warmup' && flowStage !== 'cooldown') {
      return;
    }
    if (isPaused || auxTimeLeft <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setAuxTimeLeft((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [flowStage, isPaused, auxTimeLeft]);

  // Step advancement for warm-up / cool-down
  useEffect(() => {
    if (flowStage === 'warmup' && auxTimeLeft === 0) {
      if (warmupStepIndex < WARMUP_STEPS.length - 1) {
        const nextIndex = warmupStepIndex + 1;
        setWarmupStepIndex(nextIndex);
        setAuxTimeLeft(WARMUP_STEPS[nextIndex].seconds);
        setAuxAnimKey((k) => k + 1);
      } else {
        startPoseSession();
      }
    }
  }, [flowStage, auxTimeLeft, warmupStepIndex]);

  useEffect(() => {
    if (flowStage === 'cooldown' && auxTimeLeft === 0) {
      if (cooldownStepIndex < COOLDOWN_STEPS.length - 1) {
        const nextIndex = cooldownStepIndex + 1;
        setCooldownStepIndex(nextIndex);
        setAuxTimeLeft(COOLDOWN_STEPS[nextIndex].seconds);
        setAuxAnimKey((k) => k + 1);
      } else {
        finalizeSessionEnd();
      }
    }
  }, [flowStage, auxTimeLeft, cooldownStepIndex]);

  // Phase management effect
  useEffect(() => {
    if (!isSessionStarted || isPaused) return;

    const poseSpec = POSE_SPEC[selectedPose];
    if (!poseSpec) return;

    const elapsedTime = totalTime - timeLeft;
    
    if (elapsedTime < poseSpec.in) {
      setCurrentPhase('in');
    } else if (elapsedTime < poseSpec.in + poseSpec.hold) {
      setCurrentPhase('hold');
    } else {
      setCurrentPhase('out');
    }
  }, [timeLeft, totalTime, selectedPose, isSessionStarted, isPaused]);



  // TTS speaking state handler

  const handleTTSSpeakingChange = useCallback((speaking: boolean) => {

    setIsTTSSpeaking(speaking);

  }, []);

  // TTS text handler
  const handleTTSTextChange = useCallback((text: string) => {
    setCurrentTTSFeedback(text);
  }, []);


  // Fetch user profile on component mount

  const fetchUserProfile = async () => {

    try {

      // Use API route instead of direct backend call
      const response = await authenticatedFetch('/api/auth/me');

      if (response.ok) {

        const profile = await response.json();

        setUserProfile(profile);

      }

    } catch (error) {

      // Error fetching user profile, using defaults

    }

  };

  // Fetch user profile and streak data on component mount

  useEffect(() => {

    if (isAuthenticated) {
      fetchUserProfile();
      loadStreakData();
    }

  }, [isAuthenticated]);



  // Load streak data from database API

  const loadStreakData = async () => {
    console.log('loadStreakData called');
    try {

      // Use authenticated fetch instead of manual token handling
      const response = await authenticatedFetch('/api/auth/me');

      if (response.ok) {

        const profile = await response.json();

        const username = profile.username;



        // Get streak data from database
        const streakResponse = await authenticatedFetch(`${apiBaseUrl}/api/yoga/streak/${username}`);

        if (streakResponse.ok) {

          const streakResult = await streakResponse.json();

          console.log('streakResult:', streakResult);

          if (streakResult.success) {

            const streakData = streakResult.data;

            console.log('Setting streak to:', streakData.current_streak);

            setSessionStats(prev => ({ 

              ...prev, 

              streak: streakData.current_streak 

            }));

            setLastYogaDate(streakData.last_practice_date);

          }

        }

      }

    } catch (error) {

      console.error('Error loading streak data:', error);

    }

  };



  // Handle Start button

  const handleStart = () => {
    // TODO: Re-enable warm-up later - skip directly to pose session
    // startWarmup();
    startPoseSession();
  };

  const startWarmup = () => {
    setSessionSummary(null);
    setCorrections([]);
    setCurrentAccuracy(0);
    setIsPaused(false);

    setWarmupStepIndex(0);
    setAuxTimeLeft(WARMUP_STEPS[0].seconds);
    setAuxAnimKey(1);
    setFlowStage('warmup');

    // Ensure pose session is not running during warm-up
    setIsSessionStarted(false);
    setShouldPlayAnimation(false);
  };

  const startPoseSession = () => {
    setShowWarmupSkipWarning(false);
    setFlowStage('pose');
    setIsSessionStarted(true);
    setIsPaused(false);
    setShouldPlayAnimation(true);

    const poseSpec = POSE_SPEC[selectedPose];
    if (poseSpec) {
      setTotalTime(poseSpec.total);
      setTimeLeft(poseSpec.total);
      setCurrentPhase('in');
    }

    const currentPose = selectedPose;
    setSelectedPose("");
    setTimeout(() => {
      setSelectedPose(currentPose);
    }, 200);
  };

  const startCooldown = () => {
    setIsSessionStarted(false);
    setShouldPlayAnimation(false);
    setIsPaused(false);

    setCooldownStepIndex(0);
    setAuxTimeLeft(COOLDOWN_STEPS[0].seconds);
    setAuxAnimKey(1);
    setFlowStage('cooldown');
  };

  const finalizeSessionEnd = () => {
    console.log('🔄 Finalizing session end - resetting all states');
    setFlowStage('setup');
    setIsSessionStarted(false);
    setIsPaused(false);
    setShouldPlayAnimation(false);
    setTimeLeft(0);
    setCurrentPhase('in');
    setPhaseTimeLeft(0);
    setSessionPhase('idle');
    // Don't reset sessionSummary here - let it show
  };

  // Effect to handle session end and ensure proper UI state
  useEffect(() => {
    if (sessionSummary && flowStage === 'setup') {
      console.log('🎯 Session summary detected, ensuring proper setup state');
      // Double-check all states are properly reset
      setIsSessionStarted(false);
      setShouldPlayAnimation(false);
      setTimeLeft(0);
      setCurrentPhase('in');
      setPhaseTimeLeft(0);
      setSessionPhase('idle');
    }
  }, [sessionSummary, flowStage]);

  // Update streak in database when session completes

  const updateStreak = async () => {

    try {

      // Use authenticated fetch instead of manual token handling
      const response = await authenticatedFetch('/api/auth/me');

      if (response.ok) {

        const profile = await response.json();

        const username = profile.username;



        // Create yoga session record (this will automatically update streak)

        const sessionData = {

          username: username,

          duration_seconds: sessionStats.duration * 60, // Convert minutes to seconds

          pose_name: selectedPose,

          average_accuracy: sessionStats.accuracy,

          calories_burned: sessionStats.calories,

          corrections_given: corrections.length,

          frames_processed: 0, // Would be filled by actual session

          completed: true

        };



        const sessionResponse = await authenticatedFetch(`${apiBaseUrl}/api/yoga/session`, {
          method: 'POST',
          body: JSON.stringify(sessionData)
        });



        if (sessionResponse.ok) {

          const result = await sessionResponse.json();

          if (result.success) {

            // Reload streak data to get updated values

            loadStreakData();

          }

          return result;

        } else {
          const details = await sessionResponse.text().catch(() => '');
          console.error('Failed to create yoga session for streak update:', {
            status: sessionResponse.status,
            details,
          });
          return { success: false, status: sessionResponse.status, details };
        }

      }

      const details = await response.text().catch(() => '');
      console.error('Failed to load profile for streak update:', { status: response.status, details });
      return { success: false, status: response.status, details };

    } catch (error) {

      console.error('Error updating streak:', error);

      return { success: false, error: String((error as any)?.message || error) };

    }

  };



  // Handle pose selection change

  const handlePoseChange = (e: React.ChangeEvent<HTMLSelectElement>) => {

    const newPose = e.target.value;

    setSelectedPose(newPose);

    setCurrentPoseIndex(POSE_OPTIONS.indexOf(newPose));



    // If session is running, we need to restart with new pose

    if (isSessionStarted) {

      setIsSessionStarted(false);

      setTimeout(() => setIsSessionStarted(true), 100);

    }

  };



  // Handle Pause/Resume button

  const handlePause = () => {

    setIsPaused(!isPaused);

  };



  // Handle Next Pose button

  const handleNextPose = () => {

    const nextIndex = (currentPoseIndex + 1) % POSE_OPTIONS.length;

    setCurrentPoseIndex(nextIndex);

    setSelectedPose(POSE_OPTIONS[nextIndex]);

    setCorrections([]);



    // Don't restart session when changing poses during active session

    // The YogaCamera component will automatically handle pose changes

  };



  // Handle End Session button

  const handleEndSession = () => {
    // TODO: Re-enable cool-down later - skip directly to session end
    // startCooldown();
    finalizeSessionEnd();
  };



  // Handle session end callback

  const handleSessionEnd = useCallback((summary: SessionSummary | null) => {

    setSessionSummary(summary);

    // Auto-scroll to session summary when session ends
    if (summary) {
      setTimeout(() => {
        const summaryElement = document.getElementById('session-summary');
        if (summaryElement) {
          summaryElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    }

    // Stop TTS gracefully when session ends
    try {
      if (ttsRef.current) {
        ttsRef.current.stop();
        console.log('TTS stopped gracefully at session end');
      }
    } catch (error) {
      console.log('TTS stop error at session end:', error);
    }

    if (summary) {

      const durationMinutes = summary.duration_seconds / 60;

      const metValue = MET_VALUES[selectedPose] || 2.5;

      // Use user's weight from profile or default to 70kg

      const weight = userProfile?.weight || 70;

      const calories = Math.round(

        metValue * weight * (summary.duration_seconds / 3600) * 

        (0.7 + 0.3 * (summary.average_accuracy / 100))

      );

      

      setSessionStats((prev) => ({

        ...prev,

        duration: Math.round(durationMinutes),

        accuracy: Math.round(summary.average_accuracy),

        calories: calories,

      }));



      // Update streak when session completes successfully
      console.log('Updating streak...');
      updateStreak()
        .then((res) => console.log('updateStreak response:', res))
        .then(() => {
          console.log('Reloading streak...');
          loadStreakData();
        })
        .catch((e) => console.error('updateStreak error:', e));

    }

  }, [selectedPose, userProfile?.weight, lastYogaDate, sessionStats.streak]);

  const currentAuxStep = flowStage === 'warmup'
    ? WARMUP_STEPS[warmupStepIndex]
    : COOLDOWN_STEPS[cooldownStepIndex];

  const formatAuxTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };



  // Handle accuracy update

  const handleAccuracyUpdate = useCallback((accuracy: number) => {

    setCurrentAccuracy(accuracy);

    // Update energy level based on performance

    setEnergyLevel(Math.min(100, Math.max(0, 50 + accuracy * 0.5)));

  }, []);



  // Handle corrections update

  const handleCorrectionsUpdate = useCallback((newCorrections: string[]) => {

    setCorrections(newCorrections);

  }, []);



  // Handle phase change callback

  const handlePhaseChange = useCallback((phase: 'in' | 'hold' | 'out' | 'idle', timeLeft: number) => {

    setSessionPhase(phase);

    setPhaseTimeLeft(timeLeft);

  }, []);



  return (

    <main

      className="min-h-screen w-full overflow-hidden text-[var(--ink-hi)]"

      style={{

        background: 'var(--bg-gradient)',

        fontFamily: 'var(--font-ui)',

      }}

    >

      <Particles />



      <div className="mx-auto max-w-[1400px] px-6 md:px-8 py-6 md:py-8 relative">

        {/* Back Button */}

        <button

          onClick={() => router.push('/dashboard')}

          className="absolute left-4 top-6 z-20 rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] px-5 py-2 text-[18px] font-semibold text-[var(--brand-neo)] transition-all hover:shadow-[var(--glow-neo)]"

        >

          ← Back

        </button>



        <section className="relative grid grid-cols-12 gap-4 md:gap-6 mt-8">

          {/* Avatar Section - Dynamic Positioning */}

          <div className={`col-span-12 relative transition-all duration-700 ease-in-out ${

            isSessionStarted 

              ? 'lg:col-span-12 lg:col-start-1' 

              : 'lg:col-span-5'

          }`}>

            <div

              className={`avatar-wrap relative rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] transition-all duration-700 ease-in-out ${

                isSessionStarted 

                  ? 'h-[55vh] lg:mx-auto lg:max-w-xl mt-2 scale-105' 

                  : 'h-[50vh] mt-8'

              }`}

              style={{

                background:

                  'linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02))',

                backdropFilter: 'blur(12px)',

              }}

            >

              {flowStage === 'warmup' || flowStage === 'cooldown' ? (
                <Avatar3D
                  selectedPose={selectedPose}
                  staticMode={true}
                  playAnimationPath={currentAuxStep.path}
                  playAnimationKey={auxAnimKey}
                  isPaused={isPaused}
                />
              ) : (
                <Avatar3D 
                  selectedPose={selectedPose} 
                  onlyInAnimation={shouldPlayAnimation} 
                  staticMode={!shouldPlayAnimation}
                  isTTSSpeaking={isTTSSpeaking} 
                  isPaused={isPaused} 
                  onSessionEnd={finalizeSessionEnd}
                />
              )}

              <div

                className="pointer-events-none absolute left-1/2 -translate-x-1/2 bottom-[42px] h-[18px] w-[60%]"

                style={{

                  filter: 'blur(10px)',

                  background:

                    'radial-gradient(closest-side, rgba(25,227,255,.35), transparent)',

                }}

              />

            </div>

            {!isSessionStarted && flowStage === 'setup' && (

              <div className="text-center mt-2 text-[var(--ink-med)] text-sm">

                Reference: {selectedPose}

              </div>

            )}

          </div>



          {/* Main Content Section - Dynamic Positioning */}

          <div className={`col-span-12 relative transition-all duration-700 ease-in-out ${

            isSessionStarted 

              ? 'lg:col-span-12 lg:col-start-1' 

              : 'lg:col-span-7'

          }`}>

            {flowStage === 'warmup' && (
              <div className="mb-4 mt-2">
                <div className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] bg-[var(--glass)] p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-[18px] font-semibold text-[var(--brand-neo)]">Warm-Up {warmupStepIndex + 1}/{WARMUP_STEPS.length}</div>
                      <div className="text-[14px] text-[var(--ink-med)]">{currentAuxStep.label}{(currentAuxStep as any).isPlaceholder ? ' (placeholder)' : ''}</div>
                    </div>
                    <div className="text-[24px] font-bold text-[var(--brand-neo)] tabular-nums" style={{ fontFamily: 'var(--font-future)' }}>
                      {formatAuxTime(auxTimeLeft)}
                    </div>
                  </div>
                  <div className="mt-3 flex gap-3 justify-center">
                    <ControlButton label={isPaused ? '▶ Resume' : '⏸ Pause'} onClick={handlePause} />
                    <ControlButton label="Skip Warm-Up" danger onClick={() => setShowWarmupSkipWarning(true)} />
                  </div>
                </div>
              </div>
            )}

            {flowStage === 'cooldown' && (
              <div className="mb-4 mt-2">
                <div className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] bg-[var(--glass)] p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-[18px] font-semibold text-[var(--brand-neo)]">Cool-Down {cooldownStepIndex + 1}/{COOLDOWN_STEPS.length}</div>
                      <div className="text-[14px] text-[var(--ink-med)]">{currentAuxStep.label}{(currentAuxStep as any).isPlaceholder ? ' (placeholder)' : ''}</div>
                    </div>
                    <div className="text-[24px] font-bold text-[var(--brand-neo)] tabular-nums" style={{ fontFamily: 'var(--font-future)' }}>
                      {formatAuxTime(auxTimeLeft)}
                    </div>
                  </div>
                  <div className="mt-3 flex gap-3 justify-center">
                    <ControlButton label={isPaused ? '▶ Resume' : '⏸ Pause'} onClick={handlePause} />
                    <ControlButton
                      label="Skip"
                      disabled={cooldownStepIndex === COOLDOWN_STEPS.length - 1}
                      onClick={() => {
                        if (cooldownStepIndex < COOLDOWN_STEPS.length - 1) {
                          const nextIndex = cooldownStepIndex + 1;
                          setCooldownStepIndex(nextIndex);
                          setAuxTimeLeft(COOLDOWN_STEPS[nextIndex].seconds);
                          setAuxAnimKey((k) => k + 1);
                        }
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {!isSessionStarted && flowStage === 'setup' && (
              <div className="mb-4">
                <h2
                  className="text-[28px] font-bold leading-tight text-[var(--brand-neo)] text-center"
                  style={{ fontFamily: 'var(--font-future)' }}
                >
                  Live Detection
                </h2>
              </div>
            )}

            {/* Session Timer & Phase - Show During Session */}
            {isSessionStarted && flowStage === 'pose' && (
              <div className="mb-4 mt-2">
                <div className="flex flex-col items-center space-y-3">
                  <div className="text-3xl font-bold text-[var(--brand-neo)]" style={{ fontFamily: 'var(--font-future)' }}>
                    {formatTime(timeLeft)}
                  </div>
                  <div className="flex items-center space-x-4 text-xs">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      currentPhase === 'in' ? 'bg-blue-500 text-white' : 
                      currentPhase === 'hold' ? 'bg-green-500 text-white' : 
                      'bg-orange-500 text-white'
                    }`}>
                      {currentPhase.toUpperCase()}
                    </span>
                    <span className="text-[var(--ink-med)]">Total: {formatTime(totalTime)}</span>
                  </div>
                  {/* TTS Speaking Indicator */}
                  {isTTSSpeaking && currentTTSFeedback && (
                    <div className="flex flex-col items-center space-y-1 text-xs animate-pulse">
                      <div className="flex items-center space-x-2 text-[var(--brand-neo)]">
                        <div className="w-2 h-2 bg-[var(--brand-neo)] rounded-full animate-ping"></div>
                        <span>Speaking...</span>
                      </div>
                      <div className="text-[var(--ink-med)] text-center max-w-[200px] px-2">
                        {currentTTSFeedback}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Session Timer & Phase - Hide During Session */}

            {!isSessionStarted && flowStage === 'setup' && sessionPhase !== 'idle' && (
              <GlassCard title="Current Phase">
                <div className="flex flex-col items-center justify-center p-2">
                  <div className="text-[20px] font-bold text-[var(--brand-neo)] capitalize mb-1">
                    {sessionPhase === 'in' ? 'Transitioning In' : sessionPhase === 'hold' ? 'Holding Pose' : 'Transitioning Out'}
                  </div>
                  <div className="text-[42px] font-black text-white tabular-nums">
                    {phaseTimeLeft}s
                  </div>
                  <div className="w-full h-1 bg-white/10 rounded-full mt-2 overflow-hidden">
                    <div
                      className="h-full bg-[var(--brand-neo)] transition-all duration-1000"
                      style={{
                        width: `${(phaseTimeLeft / 30) * 100}%`,
                        transitionTimingFunction: 'linear'
                      }}
                    />
                  </div>
                </div>
              </GlassCard>
            )}

            {/* Pose Selector - Hide During Session */}
            {!isSessionStarted && flowStage === 'setup' && (
              <div className="mt-4">
                <GlassCard title="Pose Selector">
                  <div className="space-y-3">
                    <select
                      value={selectedPose}
                      onChange={handlePoseChange}
                      disabled={isSessionStarted}
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-[var(--ink-hi)] text-[16px] focus:outline-none focus:ring-2 focus:ring-[var(--brand-neo)] focus:border-transparent transition-all disabled:opacity-50"
                      style={{
                        background: 'linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))',
                        backdropFilter: 'blur(12px)',
                        colorScheme: 'dark',
                      }}
                    >
                      {POSE_OPTIONS.map((pose) => (
                        <option key={pose} value={pose} className="bg-[#0B132B] text-white">
                          {pose}
                        </option>
                      ))}
                    </select>
                    <div className="text-center text-[14px] text-[var(--ink-med)]">
                      Target pose: <span className="text-[var(--brand-neo)] font-semibold">{selectedPose}</span>
                    </div>
                  </div>
                </GlassCard>
              </div>
            )}

            {/* Control Buttons - Always Visible */}
            <div className={`flex flex-wrap gap-3 justify-center transition-all duration-700 ease-in-out ${

              isSessionStarted 

                ? 'fixed bottom-8 left-1/2 -translate-x-1/2 z-20' 

                : 'mt-4'

            }`}>
              {!isSessionStarted && flowStage === 'setup' ? (
                <ControlButton
                  label="▶ Start"
                  active
                  onClick={handleStart}
                />
              ) : (
                <ControlButton
                  label={isPaused ? "▶ Resume" : "⏸ Pause"}
                  onClick={handlePause}
                />
              )}
              {flowStage === 'pose' && (
                <ControlButton
                  label="⏭ Next Pose"
                  onClick={handleNextPose}
                />
              )}
              <ControlButton
                label="⏹ End Session"
                danger
                onClick={handleEndSession}
                disabled={flowStage !== 'pose'}
              />
            </div>

            {/* Hidden Camera Component - Background Processing */}
            <div className="hidden">
              <YogaCamera
                selectedPose={selectedPose}
                isStarted={flowStage === 'pose' && isSessionStarted && !isPaused}
                onSessionEnd={handleSessionEnd}
                onAccuracyUpdate={setCurrentAccuracy}
                onCorrectionsUpdate={setCorrections}
                onTTSSpeakingChange={handleTTSSpeakingChange}
                onTTSTextChange={handleTTSTextChange}
                currentPhase={currentPhase}
                onPhaseChange={handlePhaseChange}
                tolerance={10.0}
                mirrorMode={true}
              />
            </div>

            {/* Session Stats - Hide During Session */}
            {!isSessionStarted && flowStage === 'setup' && (
              <>
                <GlassCard title="Session Stats" className="mt-4">
                  <ul className="space-y-1 text-[16px] text-[var(--ink-med)]">
                    <li>Duration <span className="float-right font-semibold">{sessionStats.duration} min</span></li>
                    <li>Calories burned <span className="float-right font-semibold">{sessionStats.calories} cl</span></li>
                    <li>Avg Accuracy <span className="float-right font-semibold text-[var(--brand-neo)]">{sessionStats.accuracy}%</span></li>
                    <li>Streak <span className="float-right font-semibold text-[var(--brand-neo)]">{sessionStats.streak} days</span></li>
                    {userProfile?.weight && (
                      <li className="text-xs text-[var(--ink-low)]">Weight: {userProfile.weight}kg</li>
                    )}
                  </ul>
                </GlassCard>

                {/* Streak Status Indicator */}
                <GlassCard title="Streak Status" className="mt-4">
                  <div className="text-center">
                    <div className="text-[48px] font-black text-[var(--brand-neo)] mb-2">
                      🔥 {sessionStats.streak}
                    </div>
                    <div className="text-[14px] text-[var(--ink-med)]">
                      {sessionStats.streak === 0 ? (
                        <span>Start your yoga journey today!</span>
                      ) : sessionStats.streak === 1 ? (
                        <span>Great start! Keep it going!</span>
                      ) : sessionStats.streak < 7 ? (
                        <span>{sessionStats.streak} day streak - Building momentum!</span>
                      ) : sessionStats.streak < 30 ? (
                        <span>{sessionStats.streak} day streak - On fire! 🔥</span>
                      ) : (
                        <span>{sessionStats.streak} day streak - Yoga Master! 🏆</span>
                      )}
                    </div>
                    {lastYogaDate && (
                      <div className="text-[12px] text-[var(--ink-low)] mt-2">
                        Last practice: {new Date(lastYogaDate).toLocaleDateString()}
                      </div>
                    )}
                    {lastYogaDate === new Date().toISOString().split('T')[0] && (
                      <div className="text-[12px] text-green-400 mt-2">
                        ✅ Today's practice complete!
                      </div>
                    )}
                  </div>
                </GlassCard>
              </>
            )}

            {/* Session Summary (when ended) */}
            {sessionSummary && !isSessionStarted && flowStage === 'setup' && (
              <div id="session-summary">
                <GlassCard title="Session Summary" className="mt-4">
                <ul className="space-y-1 text-[14px] text-[var(--ink-med)]">
                  <li>Total Duration <span className="float-right font-semibold">{Math.round(sessionSummary.duration_seconds)}s</span></li>

                  <li>Frames Analyzed <span className="float-right font-semibold">{sessionSummary.frames_processed}</span></li>

                  <li>Avg Accuracy <span className="float-right font-semibold text-[var(--brand-neo)]">{sessionSummary.average_accuracy.toFixed(1)}%</span></li>

                  <li>Corrections Given <span className="float-right font-semibold">{sessionSummary.corrections_given}</span></li>

                </ul>

              </GlassCard>

              </div>
            )}

          </div>

        </section>

        {showWarmupSkipWarning && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] bg-[var(--glass)] p-6 max-w-[420px] mx-6">
              <h3 className="text-[20px] font-semibold mb-2 text-[var(--brand-neo)]">Skip Warm-Up?</h3>
              <div className="text-[14px] text-[var(--ink-med)]">
                Skipping warm-up may reduce flexibility and increase injury risk.
              </div>
              <div className="mt-4 flex gap-3">
                <ControlButton label="Cancel" onClick={() => setShowWarmupSkipWarning(false)} />
                <ControlButton
                  label="Skip Warm-Up"
                  danger
                  onClick={() => {
                    setShowWarmupSkipWarning(false);
                    startPoseSession();
                  }}
                />
              </div>
            </div>
          </div>
        )}

      </div>

    </main>

  );

}



/* ================= Glass Card ================= */

function GlassCard({

  title,

  children,

  className = "",

}: {

  title: string;

  children: React.ReactNode;

  className?: string;

}) {

  return (

    <div

      className={`rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-4 btn-glass ${className}`}

      style={{

        background:

          'linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))',

      }}

    >

      <h3 className="text-[20px] font-semibold mb-2 text-[var(--brand-neo)]">

        {title}

      </h3>

      {children}

    </div>

  );

}



/* ================= Control Buttons ================= */

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

      className={`rounded-[var(--radius-md)] border border-[var(--glass-stroke)] px-5 py-2 text-[16px] font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed ${danger

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



/* ================= Decorative Particles ================= */

function Particles() {

  return (

    <div aria-hidden className="particles pointer-events-none fixed inset-0 -z-10">

      <div

        className="absolute left-[10%] top-[10%] h-[420px] w-[420px] rounded-full"

        style={{

          background:

            'radial-gradient(circle, rgba(25,227,255,.5), transparent 60%)',

          animation: 'drift 48s ease-in-out infinite',

        }}

      />

      <div

        className="absolute right-[5%] top-[30%] h-[520px] w-[520px] rounded-full"

        style={{

          background:

            'radial-gradient(circle, rgba(106,93,255,.4), transparent 60%)',

          animation: 'drift 56s ease-in-out infinite',

        }}

      />

    </div>

  );

}

