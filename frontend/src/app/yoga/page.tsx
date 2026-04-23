'use client';

import React, { useState, useEffect, useCallback, useRef, useLayoutEffect } from 'react';
import { useAuth, useAuthenticatedFetch } from '@/hooks/useAuth';
import { authRedirect } from '@/lib/auth';

import { useRouter } from 'next/navigation';

import Avatar3D from '@/components/Avatar3D';
import YogaCamera from '@/components/YogaCamera';
import { SessionSummary, TTSFeedback } from '@/lib/yogaApi';

const useClientLayoutEffect = typeof window !== 'undefined' ? useLayoutEffect : useEffect;



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
  "Triangle Pose",

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

  "Triangle Pose": 3.0,

  "Child Pose": 1.8,

  "Cobra Pose": 2.5,

  "Cat And Camel Pose": 2.2,

  "Seated Forward": 2.4,

};

// POSE_ANIMATIONS mapping for pose preview
const POSE_ANIMATIONS: Record<string, { inPath: string; mainPath: string; outPath: string }> = {
  "Downward Dog": {
    inPath: "/Downward Dog Pose/in_compressed.glb",
    mainPath: "/Downward Dog Pose/main_compressed.glb",
    outPath: "/Downward Dog Pose/out_compressed.glb",
  },
  "Triangle Pose": {
    inPath: "/Triangle/in_compressed.glb",
    mainPath: "/Triangle/main_compressed.glb",
    outPath: "/Triangle/out_compressed.glb",
  },
  "Warrior Pose": {
    inPath: "/Warrior Pose/in_compressed.glb",
    mainPath: "/Warrior Pose/main_compressed.glb",
    outPath: "/Warrior Pose/out_compressed.glb",
  },
  "Mountain Pose": {
    inPath: "/Mountain Pose/in_compressed.glb",
    mainPath: "/Mountain Pose/main_compressed.glb",
    outPath: "/Mountain Pose/out_compressed.glb",
  },
  "Tree Pose": {
    inPath: "/Tree Pose/in_compressed.glb",
    mainPath: "/Tree Pose/main_compressed.glb",
    outPath: "/Tree Pose/out_compressed.glb",
  },
  "Cat And Camel Pose": {
    inPath: "/Cat And Camel Pose/in_compressed.glb",
    mainPath: "/Cat And Camel Pose/main_compressed.glb",
    outPath: "/Cat And Camel Pose/out_compressed.glb",
  },
  "Child Pose": {
    inPath: "/Child Pose/in_compressed.glb",
    mainPath: "/Child Pose/main_compressed.glb",
    outPath: "/Child Pose/out_compressed.glb",
  },
  "Cobra Pose": {
    inPath: "/Cobra Pose/in_compressed.glb",
    mainPath: "/Cobra Pose/main_compressed.glb",
    outPath: "/Cobra Pose/out_compressed.glb",
  },
  "Seated Forward": {
    inPath: "/Seated Forward Pose/in_compressed.glb",
    mainPath: "/Seated Forward Pose/main_compressed.glb",
    outPath: "/Seated Forward Pose/out_compressed.glb",
  },
  "Warrior 1": {
    inPath: "/Warrior 1 Pose/warrior_1_in_compressed.glb",
    mainPath: "/Warrior 1 Pose/warrior_1_main_compressed.glb",
    outPath: "/Warrior 1 Pose/warrior_1_out_compressed.glb",
  },
};



export default function YogaPage() {
  const { user, isLoading: authLoading, isAuthenticated } = useAuth();
  const authenticatedFetch = useAuthenticatedFetch();
  const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8002';
  const router = useRouter();

  // TTS reference for cleanup
  const ttsRef = useRef<TTSFeedback | null>(null);

  const [selectedPose, setSelectedPose] = useState<string>("Mountain Pose");
  const [poseRestartKey, setPoseRestartKey] = useState(0);

  const [isPortraitDisplay, setIsPortraitDisplay] = useState(true);
  const [layoutReady, setLayoutReady] = useState(false);

  useClientLayoutEffect(() => {
    if (typeof window === 'undefined') return;

    let rafId: number | null = null;
    let settleRafId: number | null = null;

    const compute = () => {
      const viewport = window.visualViewport;
      const w = viewport?.width || window.innerWidth || document.documentElement.clientWidth || 1;
      const h = viewport?.height || window.innerHeight || document.documentElement.clientHeight || 1;

      // Holobox/portrait displays are typically very tall (e.g. 2160x3840)
      setIsPortraitDisplay(h / w >= 1.6);
      setLayoutReady(true);
    };

    const scheduleCompute = () => {
      setLayoutReady(false);

      if (rafId !== null) window.cancelAnimationFrame(rafId);
      if (settleRafId !== null) window.cancelAnimationFrame(settleRafId);

      rafId = window.requestAnimationFrame(() => {
        compute();
        settleRafId = window.requestAnimationFrame(() => {
          compute();
          settleRafId = null;
        });
        rafId = null;
      });
    };

    scheduleCompute();

    window.addEventListener('resize', scheduleCompute);
    window.visualViewport?.addEventListener('resize', scheduleCompute);

    return () => {
      if (rafId !== null) window.cancelAnimationFrame(rafId);
      if (settleRafId !== null) window.cancelAnimationFrame(settleRafId);
      window.removeEventListener('resize', scheduleCompute);
      window.visualViewport?.removeEventListener('resize', scheduleCompute);
    };
  }, []);

  const [isSessionStarted, setIsSessionStarted] = useState(false);

  const [isPaused, setIsPaused] = useState(false);

  const [isStageTransitioning, setIsStageTransitioning] = useState(false);

  const [flowStage, setFlowStage] = useState<'setup' | 'instructions' | 'warmup' | 'pose' | 'release' | 'cooldown'>('setup');

  const isInstructionStage = flowStage === 'instructions' || flowStage === 'release';
  const isAvatarFullStage = flowStage !== 'setup';

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

  const [sessionSummary, setSessionSummary] = useState<any>(null);
  const pendingSessionSummaryRef = useRef<any>(null);

  const [energyLevel, setEnergyLevel] = useState(82);

  const [sessionPhase, setSessionPhase] = useState<'in' | 'hold' | 'out' | 'idle'>('idle');

  const [phaseTimeLeft, setPhaseTimeLeft] = useState(0);

  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  const [isTTSSpeaking, setIsTTSSpeaking] = useState(false);

  const [lastYogaDate, setLastYogaDate] = useState<string | null>(null);

  const [shouldPlayAnimation, setShouldPlayAnimation] = useState(false); // Control animation playback

  const [shouldAnalyze, setShouldAnalyze] = useState(false); // Control analysis

  const [playGuidedInstructions, setPlayGuidedInstructions] = useState(false); // Control guided instructions

  const [playReleaseInstructions, setPlayReleaseInstructions] = useState(false);
  const [useStaticSetupPreview, setUseStaticSetupPreview] = useState(false);
  const releaseFinalizedRef = useRef(false);
  const [releaseInstructionsDone, setReleaseInstructionsDone] = useState(false);
  const [releaseAnimationDone, setReleaseAnimationDone] = useState(false);

  const transitionToRelease = useCallback(() => {
    // Abort any ongoing TTS feedback before exit instructions start
    try {
      if (ttsRef.current) {
        ttsRef.current.stop();
        console.log('🛑 TTS feedback aborted - starting exit instructions');
      }
    } catch (error) {
      console.log('TTS stop error:', error);
    }

    setReleaseInstructionsDone(false);
    setReleaseAnimationDone(false);
    releaseFinalizedRef.current = false;
    
    setIsStageTransitioning(true);
    setTimeout(() => {
      setIsSessionStarted(false);
      setShouldAnalyze(false);
      setShouldPlayAnimation(false);
      setPlayGuidedInstructions(false);
      setPlayReleaseInstructions(true);
      setFlowStage('release');
      setTimeout(() => setIsStageTransitioning(false), 350);
    }, 220);
  }, [selectedPose]);

  // Timer state for pose duration
  const [totalTime, setTotalTime] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [currentPhase, setCurrentPhase] = useState<'in' | 'hold' | 'out'>('in');
  const [timerActive, setTimerActive] = useState(false); // Timer only active during MAIN phase

  // TTS feedback state
  const [currentTTSFeedback, setCurrentTTSFeedback] = useState<string>('');

  // Pose specifications for timing
  const POSE_SPEC: Record<string, { in: number; hold: number; out: number; total: number }> = {
    "Mountain Pose": { in: 4, hold: 24, out: 5, total: 33 },
    "Tree Pose": { in: 9, hold: 30, out: 7, total: 46 },
    "Downward Dog": { in: 9, hold: 30, out: 8, total: 47 },
    "Warrior 1": { in: 8, hold: 30, out: 6, total: 44 },
    "Warrior Pose": { in: 8, hold: 30, out: 6, total: 44 },
    "Triangle Pose": { in: 4, hold: 25, out: 4, total: 33 },
    "Child Pose": { in: 10, hold: 33, out: 9, total: 52 },
    "Cobra Pose": { in: 9, hold: 21, out: 9, total: 39 },
    "Cat And Camel Pose": { in: 8, hold: 42, out: 10, total: 60 },
    "Seated Forward": { in: 5, hold: 35, out: 5, total: 45 },
  };



  // Format time utility
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Timer effect for countdown - only runs during MAIN phase
  useEffect(() => {
    if (!isSessionStarted || isPaused || !timerActive || timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          transitionToRelease();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isSessionStarted, isPaused, timeLeft, transitionToRelease, timerActive]);

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

  // Phase management effect - handles timer activation for MAIN phase
  useEffect(() => {
    if (!isSessionStarted || isPaused) return;

    const poseSpec = POSE_SPEC[selectedPose];
    if (!poseSpec) return;

    // When currentPhase changes to 'hold', activate timer
    if (currentPhase === 'hold' && !timerActive) {
      setTimeLeft(poseSpec.hold); // Initialize timer for MAIN phase
      setTimerActive(true);
    }
  }, [currentPhase, selectedPose, isSessionStarted, isPaused, timerActive]);



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
    setSessionSummary(null);
    setCorrections([]);
    setCurrentAccuracy(0);
    setIsPaused(false);
    setShowWarmupSkipWarning(false);
    setUseStaticSetupPreview(false);

    setFlowStage('instructions');
    setIsSessionStarted(false);
    setShouldPlayAnimation(false);
    setShouldAnalyze(false);
    setPlayGuidedInstructions(true);
    setPlayReleaseInstructions(false);
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
    setShouldAnalyze(true);
    setPlayGuidedInstructions(false);
    setPlayReleaseInstructions(false);

    const poseSpec = POSE_SPEC[selectedPose];
    if (poseSpec) {
      // Timer only starts for MAIN (hold) phase, not IN
      setTotalTime(poseSpec.hold);
      setTimeLeft(0); // Timer not started yet
      setCurrentPhase('in');
      setTimerActive(false); // Will be activated when entering MAIN phase
    }

    setPoseRestartKey((k) => k + 1);
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
    if (releaseFinalizedRef.current) {
      return;
    }
    releaseFinalizedRef.current = true;
    console.log('🔄 Finalizing session end - resetting all states');
    setFlowStage('setup');
    setIsSessionStarted(false);
    setIsPaused(false);
    setShouldPlayAnimation(false);
    setShouldAnalyze(false);
    setPlayGuidedInstructions(false);
    setPlayReleaseInstructions(false);
    setTimeLeft(0);
    setCurrentPhase('in');
    setTimerActive(false); // Reset timer active state
    setPhaseTimeLeft(0);
    setSessionPhase('idle');
    setUseStaticSetupPreview(true);
    // Don't reset sessionSummary here - let it show
  };

  useEffect(() => {
    if (flowStage === 'release' && releaseInstructionsDone && releaseAnimationDone) {
      if (!sessionSummary && pendingSessionSummaryRef.current) {
        applySessionSummary(pendingSessionSummaryRef.current);
        pendingSessionSummaryRef.current = null;
      }
      finalizeSessionEnd();
    }
  }, [flowStage, releaseInstructionsDone, releaseAnimationDone, sessionSummary]);

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



  // Generate MAIN animation path for pose preview in setup stage
  const getMainPosePath = (poseName: string): string | undefined => {
    const poseKey = poseName as keyof typeof POSE_ANIMATIONS;
    const poseAnim = POSE_ANIMATIONS[poseKey];
    return poseAnim?.mainPath;
  };

  // Track pose changes for preview animation
  const [previewAnimKey, setPreviewAnimKey] = useState(0);

  // Get zoom level based on pose type
  // Standing poses: zoom in (1.6), Warrior/laying poses: zoom out (1.3)
  const getPoseZoom = (poseName: string, isPortrait: boolean): number => {
    const standingPoses = ['Mountain Pose', 'Tree Pose'];
    const widePoses = ['Warrior Pose', 'Warrior 1', 'Downward Dog', 'Child Pose', 'Cobra Pose', 'Cat And Camel Pose', 'Seated Forward', 'Triangle Pose'];
    
    if (standingPoses.includes(poseName)) {
      return isPortrait ? 1.6 : 1.5; // Zoom in for standing poses
    } else if (widePoses.includes(poseName)) {
      return isPortrait ? 1.3 : 1.2; // Zoom out for wide/laying poses
    }
    return isPortrait ? 1.45 : 1.35; // Default
  };

  // Handle pose selection change with preview
  const handlePoseChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newPose = e.target.value;
    setSelectedPose(newPose);
    setCurrentPoseIndex(POSE_OPTIONS.indexOf(newPose));
    // Trigger preview animation change
    setPreviewAnimKey(k => k + 1);

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



  const applySessionSummary = useCallback((summary: SessionSummary | null) => {
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

  // Handle session end callback
  const handleSessionEnd = useCallback(
    (summary: SessionSummary | null) => {
      // If we're in release stage, don't show/end yet. Wait until release TTS finishes.
      if (flowStage === 'release' || playReleaseInstructions) {
        pendingSessionSummaryRef.current = summary;
        return;
      }

      applySessionSummary(summary);
    },
    [applySessionSummary, flowStage, playReleaseInstructions]
  );

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

  const avatarLayoutMode = flowStage !== 'setup'
    ? 'full'
    : isPortraitDisplay ? 'portrait' : 'desktop';



  return (

    <main

      className="min-h-screen w-full overflow-hidden text-[var(--ink-hi)]"

      style={{

        background: flowStage !== 'setup' ? 'transparent' : 'var(--bg-gradient)',

        fontFamily: 'var(--font-ui)',

        transition: 'background 0.5s ease',

      }}

    >

      {flowStage === 'setup' && <Particles />}



      <div className={`mx-auto relative ${
        flowStage !== 'setup'
          ? 'w-full max-w-none p-0'
          : isPortraitDisplay
            ? 'w-full max-w-none px-3 md:px-4 pb-6 md:pb-8'
            : 'max-w-[1400px] px-6 md:px-8 pb-6 md:pb-8'
      }`}>

        {/* Back Button - Hidden during session for clean transparent view */}

        {flowStage === 'setup' && (
        <button

          onClick={() => router.push('/dashboard')}

          className="absolute left-4 top-6 z-20 rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] px-5 py-2 text-[18px] font-semibold text-[var(--brand-neo)] transition-all hover:shadow-[var(--glow-neo)]"

        >

          ← Back

        </button>
        )}



        <section className={`${
          flowStage !== 'setup'
            ? 'fixed inset-0 flex flex-col z-10'
            : 'relative grid grid-cols-12 gap-4 md:gap-6'
        }`}>

          {/* Avatar Section */}
          <div className={`${
            flowStage !== 'setup' ? 'absolute inset-x-0 bottom-0 h-screen' : 'col-span-12 h-[50vh]'
          } transition-all duration-700 ease-in-out`}>

            <div className={`flex ${
              flowStage !== 'setup' ? 'h-full items-end' : 'h-full items-end'
            } justify-center w-full ${isStageTransitioning ? 'opacity-0' : 'opacity-100'}`}
              style={{ background: 'transparent' }}>

              <div className={`${
                flowStage !== 'setup' ? 'h-[80vh] w-full' : 'h-[50vh] w-full'
              } flex items-end justify-center`}>
                {!layoutReady ? null : flowStage === 'warmup' || flowStage === 'cooldown' ? (
                  <Avatar3D
                    key={`aux-avatar-${currentAuxStep.path}-${auxAnimKey}-${avatarLayoutMode}`}
                    selectedPose={selectedPose}
                    staticMode={true}
                    playAnimationPath={currentAuxStep.path}
                    playAnimationKey={auxAnimKey}
                    isPaused={isPaused}
                    cameraZoom={1}
                  />
                ) : flowStage === 'setup' && !isSessionStarted ? (
                  <Avatar3D
                    key={`setup-avatar-${selectedPose}-${useStaticSetupPreview || !!sessionSummary ? 'static' : 'preview'}-${avatarLayoutMode}`}
                    selectedPose={selectedPose}
                    staticMode={useStaticSetupPreview || !!sessionSummary}
                    playAnimationPath={useStaticSetupPreview || sessionSummary ? undefined : getMainPosePath(selectedPose)}
                    playAnimationKey={useStaticSetupPreview || sessionSummary ? undefined : previewAnimKey}
                    isPaused={false}
                    cameraManualDistanceFactor={1.75}
                    cameraManualTargetYOffsetFactor={0.28}
                  />
                ) : flowStage === 'instructions' ? (
                  <Avatar3D
                    key={`instructions-avatar-${selectedPose}-${avatarLayoutMode}`}
                    selectedPose={selectedPose}
                    staticMode={true}
                    disablePoseMotion={true}
                    isTTSSpeaking={isTTSSpeaking}
                    isPaused={false}
                    cameraManualDistanceFactor={1.6}
                    cameraManualTargetYOffsetFactor={0.16}
                    lockCamera={true}
                  />
                ) : (
                  <Avatar3D
                    key={`session-avatar-${selectedPose}-${poseRestartKey}-${avatarLayoutMode}`}
                    selectedPose={selectedPose}
                    onlyInAnimation={flowStage === 'pose' && shouldPlayAnimation}
                    onlyOutAnimation={flowStage === 'release'}
                    staticMode={flowStage !== 'pose' && flowStage !== 'release'}
                    isTTSSpeaking={isTTSSpeaking}
                    isPaused={isPaused}
                    playAnimationKey={poseRestartKey}
                    cameraManualDistanceFactor={1.6}
                    cameraManualTargetYOffsetFactor={0.16}
                    lockCamera={true}
                    onPhaseChange={(phase) => {
                      setCurrentPhase(phase === 'main' ? 'hold' : phase);
                    }}
                    onSessionEnd={() => {
                      if (flowStage === 'pose') {
                        transitionToRelease();
                        return;
                      }

                      if (flowStage === 'release') {
                        setReleaseAnimationDone(true);
                      }
                    }}
                  />
                )}
              </div>

            </div>

          </div>



          {/* Main Content Section - Dynamic Positioning */}

          <div className={`transition-all duration-700 ease-in-out col-span-12 relative h-[50vh]`}>

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

            {/* Session Timer - Fixed above buttons during MAIN (hold) phase */}
            {isSessionStarted && flowStage === 'pose' && currentPhase === 'hold' && (
              <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-30 mb-2">
                <div className="flex flex-col items-center space-y-2">
                  <div className="text-3xl font-bold text-red-500" style={{ fontFamily: 'var(--font-future)' }}>
                    {formatTime(timeLeft)}
                  </div>
                  <div className="flex items-center space-x-4 text-xs">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-500 text-white">
                      HOLDING POSE
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
              <div className="mt-7">
                <GlassCard title="Pose Selector">
                  <div className="space-y-3">
                    <select
                      value={selectedPose}
                      onChange={(e) => {
                        setUseStaticSetupPreview(false);
                        handlePoseChange(e);
                      }}
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

            {/* Control Buttons - Visible only during detection/pose stage */}
            {!isInstructionStage && (
            <div className={`flex flex-wrap gap-3 justify-center transition-all duration-700 ease-in-out ${

              isSessionStarted 

                ? 'fixed bottom-8 left-1/2 -translate-x-1/2 z-20' 

                : 'mt-7'

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
                disabled={flowStage === 'setup'}
              />
            </div>
            )}

            {/* Hidden Camera Component - Background Processing */}
            <div className="hidden">
              <YogaCamera
                selectedPose={selectedPose}
                shouldAnalyze={flowStage === 'pose' && isSessionStarted && !isPaused && shouldAnalyze}
                playGuidedInstructions={flowStage === 'instructions' && playGuidedInstructions && !isPaused}
                playReleaseInstructions={flowStage === 'release' && playReleaseInstructions && !isPaused}
                onGuidedInstructionsEnd={() => {
                  // Smooth transition into detection/animation
                  setIsStageTransitioning(true);
                  setTimeout(() => {
                    setPlayGuidedInstructions(false);
                    startPoseSession();
                    setTimeout(() => setIsStageTransitioning(false), 350);
                  }, 220);
                }}
                onReleaseInstructionsEnd={() => {
                  setIsStageTransitioning(true);
                  setTimeout(() => {
                    setPlayReleaseInstructions(false);
                    setReleaseInstructionsDone(true);
                    setTimeout(() => setIsStageTransitioning(false), 350);
                  }, 220);
                }}
                onSessionEnd={handleSessionEnd}
                onAccuracyUpdate={setCurrentAccuracy}
                onCorrectionsUpdate={setCorrections}
                onTTSSpeakingChange={handleTTSSpeakingChange}
                onTTSTextChange={handleTTSTextChange}
                currentPhase={currentPhase}
                onPhaseChange={handlePhaseChange}
                tolerance={10.0}
                mirrorMode={true}
                suppressFeedback={
                  flowStage === 'pose' &&
                  timerActive &&
                  timeLeft > 0 &&
                  timeLeft <= 5
                }
              />
            </div>

            {/* Session Stats - Hide During Session */}
            {!isSessionStarted && flowStage === 'setup' && (
              <>
                <GlassCard title="Session Stats" className="mt-7">
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
                <GlassCard title="Streak Status" className="mt-7">
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
                <GlassCard title="Session Summary" className="mt-7">
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
