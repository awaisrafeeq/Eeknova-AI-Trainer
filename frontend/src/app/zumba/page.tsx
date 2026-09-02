'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import ZumbaAvatarPlayer, {
  ZumbaAvatarPlayerHandle,
  ZUMBA_TEMPO_STORAGE_KEY,
  ZUMBA_MODE_TEMPO,
  setZumbaActiveMode,
} from '@/components/ZumbaAvatarPlayer';
import ZumbaCamera from '@/components/ZumbaCamera';
import ZumbaSummary from '@/components/ZumbaSummary';
import { ZumbaAnalysisResult, ZumbaSessionSummary } from '@/lib/zumbaApi';
import {
  getBackendMoveKey,
  getModesForSong,
  getSongAudio,
  getSongTitles,
  getTimeline,
  getTimelineMeta,
  getUniqueMoveKeys,
  loadZumbaMappings,
} from '@/lib/zumbaAnimationManifest';
import type {
  ZumbaMappingsJson,
  ZumbaMode,
  ZumbaPreloadStatus,
  ZumbaTimelineBlock,
} from '@/lib/zumbaTimelineTypes';
import { useZumbaTimelinePlayer, type ZumbaSwitchLogEntry } from '@/hooks/useZumbaTimelinePlayer';
import { useAuth } from '@/hooks/useAuth';
import { TTSFeedback } from '@/lib/yogaApi';

// A switch within this window of the sheet's time counts as on-beat.
const BEAT_PASS_MS = 120;

// How long before a step change the "coming up" clip and countdown appear.
const NEXT_STEP_COUNTDOWN_SECONDS = 5;

// Coaching pace, set against the choreography: moves run about 15 seconds each.
// Analysis returns several messages ~3 times a second, so it is thinned to at
// most one spoken line per move, placed in the middle of it - after the dancer
// has settled into the step, and before the countdown to the next one starts.
const ZUMBA_FEEDBACK_GAP_MS = 6000;
const ZUMBA_FEEDBACK_REPEAT_MS = 15000;

// The song IS the session clock (the timeline reads audio.currentTime), so it
// can never be paused for a line - it is dipped instead, and ramped rather than
// stepped so the change is not audible as a click mid-track.
const ZUMBA_MUSIC_DUCK_RATIO = 0.18;
const ZUMBA_MUSIC_FADE_MS = 220;

/**
 * Turns a raw analysis message into something worth saying out loud.
 *
 * The analyser emits lines like
 *   "!!!CRITICAL Raise your left arm higher from the shoulder (too low by 2 value)"
 * where the severity marker and the trailing measurement are internal detail.
 * Generic filler ("Keep moving with the selected dance step.") is dropped so the
 * corrections get the airtime.
 */
function tidyZumbaFeedback(message: string): string {
  return String(message || '')
    .replace(/^!+\s*(critical|warning|info)\s*/i, '')
    .replace(/\s*\((?:too (?:low|high|far|close)|off) by [\d.]+\s*\w*\)\s*/gi, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

function cleanZumbaFeedback(message: string): string {
  const text = tidyZumbaFeedback(message);
  if (!text) return '';
  if (/^keep moving with the selected dance step/i.test(text)) return '';
  return text;
}

/**
 * Zumba module UI aligned with the Yoga page. The avatar canvas stays mounted
 * for the whole page lifetime; moves are switched via preloaded buffers on the
 * timeline clock so there is no loading delay between dance steps.
 */
export default function ZumbaPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const [mapping, setMapping] = useState<ZumbaMappingsJson | null>(null);
  const [selectedSong, setSelectedSong] = useState<string>('');
  const [selectedMode, setSelectedMode] = useState<ZumbaMode | ''>('');
  const [preloadStatus, setPreloadStatus] = useState<ZumbaPreloadStatus>({
    state: 'idle', total: 0, loaded: 0, failed: [],
  });

  const [isStarted, setIsStarted] = useState(false);
  const [isSessionViewActive, setIsSessionViewActive] = useState(false);
  const [analysisReady, setAnalysisReady] = useState(false);

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

  const playerRef = useRef<ZumbaAvatarPlayerHandle>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const startingTimelineRef = useRef(false);
  const endingSessionRef = useRef(false);

  const songTitles = useMemo(() => (mapping ? getSongTitles(mapping) : []), [mapping]);
  const selectedSongAudio = useMemo(
    () => (mapping && selectedSong ? getSongAudio(mapping, selectedSong) : undefined),
    [mapping, selectedSong],
  );
  const availableModes = useMemo(
    () => (mapping && selectedSong ? getModesForSong(mapping, selectedSong) : []),
    [mapping, selectedSong],
  );
  const timeline = useMemo(
    () => (mapping && selectedSong && selectedMode ? getTimeline(mapping, selectedSong, selectedMode) : []),
    [mapping, selectedSong, selectedMode],
  );
  const timelineMeta = useMemo(
    () => (mapping && selectedSong && selectedMode ? getTimelineMeta(mapping, selectedSong, selectedMode) : null),
    [mapping, selectedSong, selectedMode],
  );
  const uniqueMoveKeys = useMemo(() => getUniqueMoveKeys(timeline), [timeline]);

  const closeSessionView = useCallback(() => {
    setIsStarted(false);
    setIsSessionViewActive(false);
    setAnalysisReady(false);
    startingTimelineRef.current = false;
    endingSessionRef.current = false;
  }, []);

  const playOutroThenClose = useCallback((moveKey?: string) => {
    if (endingSessionRef.current) return;
    endingSessionRef.current = true;

    if (!moveKey) {
      closeSessionView();
      return;
    }

    let timeoutId: number | null = null;
    let completed = false;
    const complete = () => {
      if (completed) return;
      completed = true;
      if (timeoutId != null) window.clearTimeout(timeoutId);
      closeSessionView();
    };

    const played = playerRef.current?.playOutro(moveKey, complete) ?? false;
    if (!played) {
      complete();
      return;
    }
    timeoutId = window.setTimeout(complete, 2200);
  }, [closeSessionView]);

  // Called when the song finishes: end the session cleanly and play the exit.
  const handleComplete = useCallback(() => {
    playOutroThenClose(timeline[timeline.length - 1]?.moveKey);
  }, [playOutroThenClose, timeline]);

  const { isRunning, currentBlock, timelineMs, switchLog, start, stop } = useZumbaTimelinePlayer({
    timeline,
    meta: timelineMeta,
    playerRef,
    audioRef,
    onComplete: handleComplete,
  });
  const [showBeatTest, setShowBeatTest] = useState(false);
  // Where the player drew the "coming up" clip, so the label lines up with it.
  const [previewRect, setPreviewRect] = useState<
    { left: number; top: number; width: number; height: number } | null
  >(null);

  // Spoken coaching. The analysis was already coming back correctly, but during
  // a session nothing rendered it (the camera lives off-screen and the feedback
  // card only shows outside the session) and nothing spoke it.
  const ttsRef = useRef<TTSFeedback | null>(null);
  const [coachLine, setCoachLine] = useState('');
  const lastSpokenFeedbackRef = useRef<{ text: string; atMs: number }>({ text: '', atMs: 0 });
  // Seconds until the step changes, mirrored into a ref because the feedback
  // handler must keep a stable identity (ZumbaCamera reconnects its WebSocket
  // whenever that callback changes).
  const secondsToStepChangeRef = useRef<number | null>(null);
  // Music level around a spoken line.
  const musicFadeRef = useRef<number | null>(null);
  const musicBaseVolumeRef = useRef(1);
  const musicDuckedRef = useRef(false);

  const fadeMusicTo = useCallback((target: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    if (musicFadeRef.current != null) {
      cancelAnimationFrame(musicFadeRef.current);
      musicFadeRef.current = null;
    }
    const from = audio.volume;
    if (Math.abs(from - target) < 0.01) {
      audio.volume = target;
      return;
    }
    const startedAt = performance.now();
    const step = () => {
      const t = Math.min(1, (performance.now() - startedAt) / ZUMBA_MUSIC_FADE_MS);
      audio.volume = Math.max(0, Math.min(1, from + (target - from) * t));
      musicFadeRef.current = t < 1 ? requestAnimationFrame(step) : null;
    };
    step();
  }, []);

  useEffect(() => {
    const tts = new TTSFeedback(
      (speaking) => {
        if (speaking) {
          // Remember the level to come back to, but only on the way down -
          // re-reading it mid-duck would latch the ducked value as the base.
          if (!musicDuckedRef.current) {
            musicDuckedRef.current = true;
            const audio = audioRef.current;
            if (audio) musicBaseVolumeRef.current = audio.volume;
          }
          fadeMusicTo(musicBaseVolumeRef.current * ZUMBA_MUSIC_DUCK_RATIO);
        } else {
          musicDuckedRef.current = false;
          fadeMusicTo(musicBaseVolumeRef.current);
        }
      },
      (text) => setCoachLine(text),
    );
    ttsRef.current = tts;
    return () => {
      tts.stop();
      ttsRef.current = null;
      if (musicFadeRef.current != null) {
        cancelAnimationFrame(musicFadeRef.current);
        musicFadeRef.current = null;
      }
      musicDuckedRef.current = false;
      const audio = audioRef.current;
      if (audio) audio.volume = musicBaseVolumeRef.current;
    };
  }, [fadeMusicTo]);

  // A line about the step that just ended is no longer useful, so it is cut off
  // at the switch and the pacing clock restarts for the new move.
  useEffect(() => {
    if (!isSessionViewActive) return;
    ttsRef.current?.stop();
    lastSpokenFeedbackRef.current = { text: '', atMs: Date.now() };
  }, [currentBlock?.moveKey, isSessionViewActive]);

  // Nothing to coach once the session is over.
  useEffect(() => {
    if (isSessionViewActive) return;
    ttsRef.current?.stop();
    lastSpokenFeedbackRef.current = { text: '', atMs: 0 };
    setCoachLine('');
  }, [isSessionViewActive]);

  // Stable backend move key used to create the camera session.
  const sessionTargetMove = useMemo(
    () => (mapping && timeline.length > 0 ? getBackendMoveKey(mapping, timeline[0].moveKey) : ''),
    [mapping, timeline],
  );
  const currentBackendMoveKey = useMemo(
    () => (mapping && currentBlock ? getBackendMoveKey(mapping, currentBlock.moveKey) : sessionTargetMove),
    [mapping, currentBlock, sessionTargetMove],
  );

  // Session analytics context: the key-beat grid (8-count block starts) drives
  // the backend Beat Sync score; song/mode/user feed calories and history.
  const sessionInfo = useMemo(() => {
    if (!mapping || timeline.length === 0) return undefined;
    return {
      mode: selectedMode || undefined,
      songTitle: selectedSong || undefined,
      username: user?.username || user?.email || undefined,
      weightKg: user?.weight ?? null,
      keyBeatsMs: timeline.map((b) => b.startMs),
      keyBeatMoves: timeline.map((b) => getBackendMoveKey(mapping, b.moveKey)),
    };
  }, [mapping, timeline, selectedMode, selectedSong, user]);

  // Load the mapping JSON once after auth resolves.
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- auth state is an external async source.
      setIsLoading(false);
      return;
    }
    let cancelled = false;
    loadZumbaMappings()
      .then((data) => {
        if (cancelled) return;
        setMapping(data);
        const songs = getSongTitles(data);
        // Restore the last chosen song across refreshes.
        const savedSong = window.localStorage.getItem('zumba.selectedSong');
        setSelectedSong((cur) => cur || (savedSong && songs.includes(savedSong) ? savedSong : songs[0] || ''));
      })
      .catch((err) => {
        console.error('Failed to load Zumba mappings:', err);
        if (!cancelled) setError('Failed to load Zumba choreography data');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [authLoading, isAuthenticated]);

  // Default mode when the song changes: keep current, else the saved one, else first.
  useEffect(() => {
    if (availableModes.length > 0) {
      const savedMode = window.localStorage.getItem('zumba.selectedMode') as ZumbaMode | null;
      // eslint-disable-next-line react-hooks/set-state-in-effect -- selected mode is derived from the loaded workbook.
      setSelectedMode((cur) =>
        cur && availableModes.includes(cur)
          ? cur
          : savedMode && availableModes.includes(savedMode)
            ? savedMode
            : availableModes[0],
      );
    } else {
      setSelectedMode('');
    }
  }, [availableModes]);

  // Remember the selection across refreshes.
  useEffect(() => {
    if (selectedSong) window.localStorage.setItem('zumba.selectedSong', selectedSong);
  }, [selectedSong]);
  useEffect(() => {
    if (selectedMode) window.localStorage.setItem('zumba.selectedMode', selectedMode);
  }, [selectedMode]);

  // The avatar player uses the current mode to pick its default animation tempo.
  useEffect(() => {
    setZumbaActiveMode(selectedMode || '');
  }, [selectedMode]);

  // Preload all GLBs for the selected song/mode whenever the timeline changes.
  useEffect(() => {
    if (isStarted) return; // never re-preload mid-session
    if (timeline.length === 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- reflects external preload state for an empty timeline.
      setPreloadStatus({ state: 'idle', total: 0, loaded: 0, failed: [] });
      return;
    }
    const player = playerRef.current;
    if (!player) return;
    setPreloadStatus({ state: 'loading', total: 0, loaded: 0, failed: [] });
    void player.preloadTimeline(timeline, { corrected: Boolean(timelineMeta?.corrected) });
  }, [timeline, timelineMeta, isStarted]);

  useEffect(() => {
    if (!isStarted || !analysisReady || isRunning || startingTimelineRef.current) return;
    startingTimelineRef.current = true;
    void start().then((started) => {
      if (!started) startingTimelineRef.current = false;
    });
  }, [analysisReady, isRunning, isStarted, start]);

  // Show a preview of the first move once assets are ready — once per song/mode
  // selection, so a post-session exit animation isn't immediately overridden.
  const previewedKeyRef = useRef('');
  useEffect(() => {
    const key = `${selectedSong}|${selectedMode}`;
    if (
      preloadStatus.state === 'ready' &&
      !isStarted &&
      timeline.length > 0 &&
      previewedKeyRef.current !== key
    ) {
      previewedKeyRef.current = key;
      playerRef.current?.playMove(timeline[0].moveKey);
    }
  }, [preloadStatus.state, isStarted, timeline, selectedSong, selectedMode]);

  const handleSessionEnd = useCallback((summary: ZumbaSessionSummary | null) => {
    if (summary && summary.frames_processed > 0) {
      setSessionSummary(summary);
    } else {
      setSessionSummary(null);
    }
    setIsStarted(false);
    setAnalysisReady(false);
  }, []);

  const handleAccuracyUpdate = useCallback((accuracy: number) => setCurrentAccuracy(accuracy), []);
  const handleFeedbackUpdate = useCallback((feedback: string[]) => {
    setCurrentFeedback(feedback);

    // Analysis runs at ~3 fps and returns several messages per frame, so this
    // has to be thinned right down: one coached line at a time, and only after
    // the previous one has had room to be heard.
    const coachable = feedback.map(cleanZumbaFeedback).find(Boolean);
    if (!coachable) return;

    // Hold off once the countdown is on screen: those last seconds belong to the
    // "coming up" clip and the 5-4-3-2-1, and a correction about the step being
    // left behind would only pull attention away from the switch.
    const toChange = secondsToStepChangeRef.current;
    if (toChange != null && toChange <= NEXT_STEP_COUNTDOWN_SECONDS) return;

    const now = Date.now();
    const last = lastSpokenFeedbackRef.current;
    if (now - last.atMs < ZUMBA_FEEDBACK_GAP_MS) return;
    if (last.text === coachable && now - last.atMs < ZUMBA_FEEDBACK_REPEAT_MS) return;

    lastSpokenFeedbackRef.current = { text: coachable, atMs: now };
    ttsRef.current?.speak(coachable, true);
  }, []);
  const handleFrameProcessed = useCallback((result: ZumbaAnalysisResult) => {
    const metrics = result.performance_metrics;
    setFramesProcessed(metrics?.total_frames || 0);
    setValidFrames(metrics?.comparable_frames || 0);
    setActiveFrames(metrics?.active_frames || 0);
    setPoseDetected(Boolean(result.pose_detected));
    setActiveMovement(Boolean(result.active_movement));
  }, []);

  const canStart =
    !authLoading &&
    !!mapping &&
    !!selectedSong &&
    !!selectedMode &&
    timeline.length > 0 &&
    preloadStatus.state === 'ready';

  const startSession = () => {
    if (!canStart) {
      setError('Please wait for animations to finish preparing.');
      return;
    }
    setSessionSummary(null);
    setCurrentFeedback([]);
    setCurrentAccuracy(0);
    setFramesProcessed(0);
    setValidFrames(0);
    setActiveFrames(0);
    setPoseDetected(false);
    setActiveMovement(false);
    setError(null);
    setAnalysisReady(false);
    startingTimelineRef.current = false;
    endingSessionRef.current = false;
    const audio = audioRef.current;
    if (audio) {
      try {
        audio.currentTime = 0;
        audio.muted = true;
        void audio.play().then(() => {
          audio.pause();
          audio.currentTime = 0;
          audio.muted = false;
        }).catch(() => {
          audio.muted = false;
        });
      } catch {
        audio.muted = false;
      }
    }
    // Hold on the ready pose while the camera/backend connect; the timeline
    // then starts Main exactly on the song's count 1 (no silent dancing).
    if (timeline[0]) playerRef.current?.playLeadIn(timeline[0].moveKey);
    setIsSessionViewActive(true);
    setIsStarted(true);
  };

  const endSession = () => {
    stop();
    playOutroThenClose(currentBlock?.moveKey ?? timeline[0]?.moveKey);
  };

  const toggleAnalysisSession = () => {
    if (isSessionViewActive || isStarted) {
      endSession();
    } else {
      startSession();
    }
  };

  const handleBack = () => {
    if (isStarted) {
      stop();
      setIsStarted(false);
      setAnalysisReady(false);
    }
    setIsSessionViewActive(false);
    router.push('/dashboard');
  };

  // The next block whose step actually differs from the current one. Blocks
  // inside a move group repeat the same step, so counting down to the next
  // *block* would run a countdown for a step that is not changing at all.
  const upcomingChangeBlock = useMemo(() => {
    if (!currentBlock) return null;
    const currentIndex = timeline.indexOf(currentBlock);
    if (currentIndex === -1) return null;
    for (let i = currentIndex + 1; i < timeline.length; i += 1) {
      if (timeline[i].moveKey !== currentBlock.moveKey) return timeline[i];
    }
    return null; // current step runs to the end of the song
  }, [timeline, currentBlock]);

  // Seconds until the step actually changes.
  const changeInSeconds = upcomingChangeBlock && isRunning
    ? Math.max(0, (upcomingChangeBlock.startMs - timelineMs) / 1000)
    : null;

  useEffect(() => {
    secondsToStepChangeRef.current = changeInSeconds;
  }, [changeInSeconds]);

  // The corner clip runs only inside the countdown window, so it draws attention
  // exactly when the switch is imminent rather than competing with the dancing
  // for the whole song.
  const previewMoveKey =
    isSessionViewActive &&
    upcomingChangeBlock &&
    changeInSeconds != null &&
    changeInSeconds <= NEXT_STEP_COUNTDOWN_SECONDS
      ? upcomingChangeBlock.moveKey
      : null;

  if (authLoading || isLoading) {
    return (
      <main
        className="min-h-screen w-full flex items-center justify-center text-[var(--ink-hi)]"
        style={{ background: 'var(--bg-gradient)', fontFamily: 'var(--font-ui)' }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--brand-neo)] mx-auto mb-4" />
          <div>Loading Zumba choreography...</div>
        </div>
      </main>
    );
  }

  return (
    <main
      className={`min-h-screen w-full overflow-x-hidden text-[var(--ink-hi)] ${
        isSessionViewActive ? 'overflow-y-hidden' : ''
      }`}
      style={{
        background: isSessionViewActive ? 'transparent' : 'var(--bg-gradient)',
        fontFamily: 'var(--font-ui)',
        transition: 'background 0.5s ease',
      }}
    >
      {!isSessionViewActive && <Particles />}

      {/* Current move + upcoming step preview. Fixed to the viewport (rather
          than the avatar container, which is bottom-aligned) so they sit at
          the true top of the screen. */}
      {isSessionViewActive && currentBlock && (
        <div className="pointer-events-none fixed left-1/2 top-4 z-40 -translate-x-1/2 rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-black/40 px-6 py-3 text-center backdrop-blur-md">
          <div className="text-[13px] uppercase tracking-wide text-[var(--ink-med)]">Current</div>
          <div className="text-[24px] font-bold text-[var(--brand-neo)]">
            {currentBlock.moveName}{currentBlock.side ? ` (${currentBlock.side})` : ''}
          </div>
        </div>
      )}
      {isSessionViewActive && (
        <NextStepCountdown
          block={upcomingChangeBlock}
          secondsLeft={changeInSeconds}
          previewRect={previewRect}
        />
      )}

      {/* Live coaching, as a subtitle. Sits above the End Session button. */}
      {isSessionViewActive && coachLine && (
        <div className="pointer-events-none fixed bottom-28 left-1/2 z-40 w-[min(860px,92vw)] -translate-x-1/2 px-4">
          <p className="rounded-2xl border border-[var(--glass-stroke)] bg-black/60 px-7 py-4 text-center text-[26px] font-semibold leading-snug text-white shadow-[0_10px_40px_rgba(0,0,0,.35)] backdrop-blur-md">
            {coachLine}
          </p>
        </div>
      )}

      {/* Beat verification: on-screen proof that switches land on the sheet's
          times — no console needed. Toggle stays available in every state. */}
      <button
        onClick={() => setShowBeatTest((v) => !v)}
        className="fixed bottom-4 left-4 z-50 rounded-full border border-[var(--glass-stroke)] bg-black/60 px-4 py-1.5 text-[13px] font-semibold text-[var(--brand-neo)] backdrop-blur-md transition-all hover:shadow-[var(--glow-neo)]"
      >
        {showBeatTest ? 'Hide Beat Test' : 'Beat Test'}
      </button>
      {showBeatTest && (
        <BeatTestPanel
          entries={switchLog}
          isRunning={isRunning}
          corrected={Boolean(timelineMeta?.corrected)}
          mode={selectedMode || ''}
        />
      )}

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
                <div className="relative z-10 h-full w-full">
                  {mapping ? (
                    <>
                      <ZumbaAvatarPlayer
                        ref={playerRef}
                        mapping={mapping}
                        onPreloadStatus={setPreloadStatus}
                        previewMoveKey={previewMoveKey}
                        onPreviewRectChange={setPreviewRect}
                        cameraDistanceFactor={isSessionViewActive ? 1.3 : 1.75}
                        cameraTargetYOffsetFactor={isSessionViewActive ? 0.0 : 0.02}
                      />
                      {!isSessionViewActive && preloadStatus.state !== 'ready' && (
                        <ZumbaAvatarLoading status={preloadStatus} />
                      )}
                    </>
                  ) : (
                    <div className="relative z-10 flex h-full flex-col items-center justify-center text-center">
                      <div className="mb-5 grid h-24 w-24 place-items-center rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] shadow-[var(--glow-neo)]">
                        <Image src="/logo.png" alt="Eeknova AI Trainer" width={68} height={68} priority />
                      </div>
                      <div
                        className="font-black leading-none text-[var(--brand-neo)] text-[42px]"
                        style={{ fontFamily: 'var(--font-future)' }}
                      >
                        Zumba
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
                <GlassCard title="Song & Mode">
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                    <select
                      value={selectedSong}
                      onChange={(event) => setSelectedSong(event.target.value)}
                      disabled={isStarted}
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-[var(--ink-hi)] text-[16px] focus:outline-none focus:ring-2 focus:ring-[var(--brand-neo)] focus:border-transparent transition-all disabled:opacity-50"
                      style={{
                        background: 'linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))',
                        backdropFilter: 'blur(12px)',
                        colorScheme: 'dark',
                      }}
                    >
                      <option value="">Select Song</option>
                      {songTitles.map((song) => (
                        <option key={song} value={song} className="bg-[#0B132B] text-white">
                          {song}
                        </option>
                      ))}
                    </select>

                    <select
                      value={selectedMode}
                      onChange={(event) => setSelectedMode(event.target.value as ZumbaMode)}
                      disabled={isStarted || !selectedSong}
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-[var(--ink-hi)] text-[16px] focus:outline-none focus:ring-2 focus:ring-[var(--brand-neo)] focus:border-transparent transition-all disabled:opacity-50"
                      style={{
                        background: 'linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))',
                        backdropFilter: 'blur(12px)',
                        colorScheme: 'dark',
                      }}
                    >
                      <option value="">Select Mode</option>
                      {availableModes.map((mode) => (
                        <option key={mode} value={mode} className="bg-[#0B132B] text-white">
                          {mode}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mt-3 text-center text-[14px] text-[var(--ink-med)]">
                    {timeline.length > 0 ? (
                      <>
                        {uniqueMoveKeys.length} moves · {timeline.length} blocks ·{' '}
                        <span className="text-[var(--brand-neo)] font-semibold">{renderPreload(preloadStatus)}</span>
                      </>
                    ) : (
                      'Select a song and mode to prepare your session.'
                    )}
                  </div>

                  {preloadStatus.failed.length > 0 && (
                    <div className="mt-2 text-[13px] text-red-300">
                      Missing animation: {preloadStatus.failed[0]}
                    </div>
                  )}
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
                disabled={!isSessionViewActive && !canStart}
                onClick={toggleAnalysisSession}
              />
            </div>

            {/* Song audio: drives the timeline clock and is what the user dances to. */}
            <audio ref={audioRef} src={selectedSongAudio} preload="auto" className="hidden" />

            <div className="fixed left-[-10000px] top-0 h-[240px] w-[320px] overflow-hidden pointer-events-none">
              <ZumbaCamera
                selectedMove={sessionTargetMove}
                currentMoveKey={currentBackendMoveKey}
                currentMoveName={currentBlock?.moveName}
                currentTimelineMs={timelineMs}
                sessionInfo={sessionInfo}
                isStarted={isStarted}
                onReadyChange={setAnalysisReady}
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
                    Song
                    <span className="float-right font-semibold text-white">
                      {selectedSong || 'Not selected'}
                    </span>
                  </li>
                  <li>
                    Mode
                    <span className="float-right font-semibold text-white">
                      {selectedMode || 'Not selected'}
                    </span>
                  </li>
                  <li>
                    Animations
                    <span className={`float-right font-semibold ${preloadStatus.state === 'ready' ? 'text-green-400' : 'text-yellow-400'}`}>
                      {renderPreload(preloadStatus)}
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
                        {/* The analyser's severity marker and measurement are
                            internal detail, not something to show a dancer. */}
                        {tidyZumbaFeedback(feedback)}
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
              <div id="zumba-session-summary" className="mt-7">
                <ZumbaSummary
                  summary={sessionSummary}
                  songTitle={selectedSong}
                  mode={selectedMode || undefined}
                  userName={user?.full_name || user?.username || user?.name || undefined}
                />
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

/**
 * Top-right "coming up" preview for the next dance step.
 *
 * `block` is the next block whose step actually CHANGES, so a step repeating
 * across several 8-count blocks never triggers a countdown. While dancing it is
 * hard to read a move name, so the last few seconds count down as a single
 * large digit (5, 4, 3, 2, 1), which is readable peripherally.
 */
function NextStepCountdown({
  block,
  secondsLeft,
  previewRect,
}: {
  block: ZumbaTimelineBlock | null;
  secondsLeft: number | null;
  previewRect: { left: number; top: number; width: number; height: number } | null;
}) {
  if (!block || secondsLeft == null) return null;

  const COUNTDOWN_FROM = NEXT_STEP_COUNTDOWN_SECONDS;
  const isCountingDown = secondsLeft <= COUNTDOWN_FROM;
  // 5.0s -> "5", 0.4s -> "1": the digit shown is the second being counted.
  const digit = Math.max(1, Math.min(COUNTDOWN_FROM, Math.ceil(secondsLeft)));
  // Fills up as the switch approaches.
  const progress = Math.max(0, Math.min(100, (1 - secondsLeft / COUNTDOWN_FROM) * 100));

  // The clip itself is drawn by the 3D canvas underneath, so this card sits on
  // top of it: a transparent framed window over the clip, with the label below.
  // Without a rect (clip not being drawn yet) it falls back to the old corner.
  const anchored = previewRect
    ? { left: previewRect.left, top: previewRect.top, width: previewRect.width }
    : null;

  return (
    <div
      className="pointer-events-none fixed z-40 transition-all duration-300"
      style={
        anchored
          ? { left: anchored.left, top: anchored.top, width: anchored.width }
          : { right: 16, top: 16, width: 'min(240px, 42vw)' }
      }
    >
      {previewRect && (
        <div
          className={`rounded-[var(--radius-md)] border ${
            isCountingDown
              ? 'border-[var(--brand-neo)] shadow-[0_0_28px_rgba(25,227,255,.35)]'
              : 'border-[var(--glass-stroke)]'
          }`}
          // Transparent on purpose - the live clip is rendered behind it.
          style={{ height: previewRect.height }}
        >
          <div className="m-2 w-fit rounded-full bg-black/55 px-2 py-0.5 text-[10px] uppercase tracking-[0.18em] text-[var(--ink-med)] backdrop-blur-sm">
            Coming up
          </div>
        </div>
      )}

      <div
        className={`rounded-[var(--radius-md)] border bg-black/55 px-4 py-3 text-right backdrop-blur-md ${
          previewRect ? 'mt-2' : ''
        } ${
          isCountingDown
            ? 'border-[var(--brand-neo)] shadow-[0_0_28px_rgba(25,227,255,.35)]'
            : 'border-[var(--glass-stroke)]'
        }`}
      >
        {!previewRect && (
          <div className="text-[12px] uppercase tracking-[0.18em] text-[var(--ink-med)]">Coming up</div>
        )}
        <div className="text-[20px] font-bold leading-tight text-white">
          {block.moveName}
          {block.side ? <span className="text-[var(--ink-med)]"> ({block.side})</span> : null}
        </div>

        {isCountingDown ? (
          <div className="mt-1 flex items-baseline justify-end gap-2">
            <span className="text-[13px] text-[var(--ink-med)]">in</span>
            <span
              key={digit}
              className="text-[48px] font-black leading-none text-[var(--brand-neo)]"
              style={{ fontFamily: 'var(--font-future)', animation: 'zumba-count-pop 0.45s ease-out' }}
            >
              {digit}
            </span>
          </div>
        ) : (
          <div className="mt-2 text-[15px] text-[var(--ink-med)]">
            in {secondsLeft.toFixed(1)}s
          </div>
        )}

        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-[var(--brand-neo)]"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <style>{`
        @keyframes zumba-count-pop {
          0%   { transform: scale(1.5); opacity: 0.35; }
          100% { transform: scale(1);   opacity: 1; }
        }
      `}</style>
    </div>
  );
}

function formatMs(ms: number): string {
  const total = Math.max(0, ms) / 1000;
  const minutes = Math.floor(total / 60);
  const seconds = total - minutes * 60;
  return `${minutes}:${seconds.toFixed(3).padStart(6, '0')}`;
}

const TEMPO_CHOICES = [0.8, 0.85, 0.9, 1.0];

function BeatTestPanel({
  entries,
  isRunning,
  corrected,
  mode,
}: {
  entries: ZumbaSwitchLogEntry[];
  isRunning: boolean;
  corrected: boolean;
  mode: string;
}) {
  const passed = entries.filter((e) => Math.abs(e.latencyMs) <= BEAT_PASS_MS).length;
  // null = "Auto": use the per-mode default; a number = manual A/B override.
  const [override, setOverride] = useState<number | null>(() => {
    if (typeof window === 'undefined') return null;
    const raw = window.localStorage.getItem(ZUMBA_TEMPO_STORAGE_KEY);
    const v = raw ? Number.parseFloat(raw) : NaN;
    return Number.isFinite(v) ? v : null;
  });
  const modeDefault = ZUMBA_MODE_TEMPO[mode] ?? 0.85;
  const effective = override ?? modeDefault;
  const pickTempo = (value: number | null) => {
    if (value == null) window.localStorage.removeItem(ZUMBA_TEMPO_STORAGE_KEY);
    else window.localStorage.setItem(ZUMBA_TEMPO_STORAGE_KEY, String(value));
    setOverride(value);
  };

  return (
    <div className="fixed bottom-16 left-4 z-50 w-[min(560px,92vw)] rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-black/75 p-3 text-[12px] backdrop-blur-md">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-semibold text-[var(--brand-neo)]">
          Beat Test {corrected ? '(beat-corrected sheet)' : '(legacy timing)'}
        </span>
        <span className={`font-bold ${passed === entries.length ? 'text-green-400' : 'text-yellow-300'}`}>
          {entries.length > 0 ? `${passed} / ${entries.length} on beat (±${BEAT_PASS_MS}ms)` : isRunning ? 'waiting for first switch…' : 'start a session'}
        </span>
      </div>

      {/* Live tempo A/B: lets a tester compare animation speeds without a
          rebuild. Takes effect at the NEXT move switch. Auto = mode default. */}
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-[var(--ink-med)]">Speed tempo:</span>
        <button
          onClick={() => pickTempo(null)}
          className={`rounded px-2 py-0.5 font-semibold transition-all ${
            override == null
              ? 'bg-[var(--brand-neo)] text-black'
              : 'border border-[var(--glass-stroke)] text-[var(--brand-neo)] hover:bg-white/10'
          }`}
        >
          Auto ({modeDefault.toFixed(2)}×{mode ? ` · ${mode}` : ''})
        </button>
        {TEMPO_CHOICES.map((value) => (
          <button
            key={value}
            onClick={() => pickTempo(value)}
            className={`rounded px-2 py-0.5 font-semibold transition-all ${
              override === value
                ? 'bg-[var(--brand-neo)] text-black'
                : 'border border-[var(--glass-stroke)] text-[var(--brand-neo)] hover:bg-white/10'
            }`}
          >
            {value.toFixed(2)}×
          </button>
        ))}
        <span className="text-[var(--ink-med)]">now: {effective.toFixed(2)}× (from next move)</span>
      </div>
      {entries.length > 0 && (
        <div className="max-h-[240px] overflow-y-auto">
          <table className="w-full text-left">
            <thead className="sticky top-0 bg-black/80 text-[var(--ink-med)]">
              <tr>
                <th className="py-1 pr-2 font-medium">Grp</th>
                <th className="py-1 pr-2 font-medium">Move</th>
                <th className="py-1 pr-2 font-medium">Expected</th>
                <th className="py-1 pr-2 font-medium">Actual</th>
                <th className="py-1 pr-2 font-medium">Latency</th>
                <th className="py-1 pr-2 font-medium">Speed</th>
                <th className="py-1 font-medium">OK</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => {
                const pass = Math.abs(e.latencyMs) <= BEAT_PASS_MS;
                return (
                  <tr key={`${e.group}-${e.expectedMs}`} className="border-t border-white/10">
                    <td className="py-1 pr-2">{e.group}</td>
                    <td className="py-1 pr-2 font-semibold text-white">{e.move}</td>
                    <td className="py-1 pr-2">{formatMs(e.expectedMs)}</td>
                    <td className="py-1 pr-2">{formatMs(e.actualMs)}</td>
                    <td className={`py-1 pr-2 font-semibold ${pass ? 'text-green-400' : 'text-red-300'}`}>
                      {e.latencyMs >= 0 ? '+' : ''}{e.latencyMs}ms
                    </td>
                    <td className="py-1 pr-2">{e.speedScale != null ? `${e.speedScale.toFixed(3)}×${e.plannedLoops != null ? ` (${e.plannedLoops} loops)` : ''}` : '--'}</td>
                    <td className={`py-1 font-bold ${pass ? 'text-green-400' : 'text-red-300'}`}>{pass ? 'PASS' : 'FAIL'}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function renderPreload(status: ZumbaPreloadStatus): string {
  switch (status.state) {
    case 'idle':
      return 'Not prepared';
    case 'loading':
      return `Preparing ${status.loaded} / ${status.total} new animations`;
    case 'ready':
      return 'Ready';
    case 'error':
      return 'Failed to prepare animations';
    default:
      return '';
  }
}

function ZumbaAvatarLoading({ status }: { status: ZumbaPreloadStatus }) {
  const progress =
    status.total > 0 ? Math.min(100, Math.round((status.loaded / status.total) * 100)) : 0;

  return (
    <div className="pointer-events-none absolute inset-0 z-20 flex items-center justify-center">
      <div className="w-[min(360px,82vw)] rounded-[var(--radius-md)] border border-white/10 bg-black/45 px-5 py-4 text-center shadow-[0_18px_48px_rgba(0,0,0,.32)] backdrop-blur-md">
        <div className="mx-auto mb-4 h-11 w-11 rounded-full border-2 border-white/15 border-t-[var(--brand-neo)] animate-spin" />
        <div className="text-[18px] font-semibold text-white">Preparing avatar</div>
        <div className="mt-1 text-[13px] text-[var(--ink-med)]">
          {status.total > 0 ? `${status.loaded} / ${status.total} new animations` : 'Loading choreography'}
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full bg-[var(--brand-neo)] transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
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
