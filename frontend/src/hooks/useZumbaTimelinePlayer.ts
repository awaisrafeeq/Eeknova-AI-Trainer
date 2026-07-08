'use client';

// Drives Zumba timeline playback off the song audio clock.
//
// The song audio element is the single source of truth for timing: move changes
// are resolved from `audio.currentTime`, so the avatar stays in sync with the
// music. A move "group" spans several 8-count blocks of the same step; we only
// switch the avatar at group boundaries (Idle In -> Main flow), and let Main
// loop across the blocks within a group so nothing restarts abruptly.

import { useCallback, useEffect, useRef, useState } from 'react';
import type { RefObject } from 'react';
import type { ZumbaAvatarPlayerHandle } from '@/components/ZumbaAvatarPlayer';
import type { ZumbaTimelineBlock, ZumbaTimelineMeta } from '@/lib/zumbaTimelineTypes';

type UseZumbaTimelinePlayerParams = {
  timeline: ZumbaTimelineBlock[];
  /** Beat-alignment meta from the client's corrected sheet (null = legacy timing). */
  meta?: ZumbaTimelineMeta | null;
  playerRef: RefObject<ZumbaAvatarPlayerHandle | null>;
  audioRef: RefObject<HTMLAudioElement | null>;
  onComplete?: () => void;
};

/** One avatar switch, recorded for on-screen beat verification. */
export type ZumbaSwitchLogEntry = {
  group: number;
  move: string;
  /** Sheet time the move should start (ms). */
  expectedMs: number;
  /** Timeline time the switch actually fired (ms). */
  actualMs: number;
  latencyMs: number;
  speedScale: number | null;
  plannedLoops: number | null;
};

type UseZumbaTimelinePlayerResult = {
  isRunning: boolean;
  currentBlock: ZumbaTimelineBlock | null;
  nextBlock: ZumbaTimelineBlock | null;
  timelineMs: number;
  /** Every move switch of the current/last run — drives the Beat Test panel. */
  switchLog: ZumbaSwitchLogEntry[];
  start: () => Promise<boolean>;
  stop: () => void;
};

function findBlockIndexAtTime(timeline: ZumbaTimelineBlock[], ms: number, fromIndex: number): number {
  // Time only moves forward, so start scanning at the last known index.
  for (let i = Math.max(0, fromIndex); i < timeline.length; i += 1) {
    const block = timeline[i];
    if (ms >= block.startMs && ms < block.endMs) return i;
    if (ms < block.startMs) return -1; // gap before this block
  }
  return -1;
}

export function useZumbaTimelinePlayer({
  timeline,
  meta = null,
  playerRef,
  audioRef,
  onComplete,
}: UseZumbaTimelinePlayerParams): UseZumbaTimelinePlayerResult {
  const [isRunning, setIsRunning] = useState(false);
  const [currentBlock, setCurrentBlock] = useState<ZumbaTimelineBlock | null>(null);
  const [nextBlock, setNextBlock] = useState<ZumbaTimelineBlock | null>(null);
  const [timelineMs, setTimelineMs] = useState(0);
  const [switchLog, setSwitchLog] = useState<ZumbaSwitchLogEntry[]>([]);

  const rafRef = useRef<number | null>(null);
  const startPerfRef = useRef(0);
  const currentIndexRef = useRef(-1);
  const currentGroupRef = useRef<number | null>(null);
  const outroTriggeredRef = useRef(false);
  const endedHandlerRef = useRef<(() => void) | null>(null);
  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  const detachEnded = useCallback(() => {
    const audio = audioRef.current;
    if (audio && endedHandlerRef.current) {
      audio.removeEventListener('ended', endedHandlerRef.current);
    }
    endedHandlerRef.current = null;
  }, [audioRef]);

  const stop = useCallback(() => {
    if (rafRef.current != null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    detachEnded();
    const audio = audioRef.current;
    if (audio && !audio.paused) {
      try { audio.pause(); } catch { /* noop */ }
    }
    setIsRunning(false);
  }, [audioRef, detachEnded]);

  const start = useCallback(async () => {
    if (timeline.length === 0) return false;
    if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    detachEnded();

    const audio = audioRef.current;
    currentIndexRef.current = -1;
    currentGroupRef.current = null;
    outroTriggeredRef.current = false;
    setCurrentBlock(null);
    setNextBlock(null);
    setTimelineMs(0);
    setSwitchLog([]);

    const corrected = Boolean(meta?.corrected);
    const lastBlock = timeline[timeline.length - 1];
    // Corrected sheets add an "Idle Out / End Hold" tail after the last block;
    // the session runs until the tail finishes so the music isn't cut short.
    const sessionEndMs = corrected && meta?.outroEndMs ? meta.outroEndMs : lastBlock.endMs;
    const outroStartMs = corrected && meta?.outroStartMs ? meta.outroStartMs : null;

    const finish = () => {
      stop();
      onCompleteRef.current?.();
    };

    // Beat lead-in ("Idle In / Beat Lead-In" row): hold ready until the song's
    // count 1 (beatPhaseOffsetMs); the first group then starts on the beat.
    if (corrected && timeline[0]) {
      playerRef.current?.playLeadIn(timeline[0].moveKey);
    }

    if (audio) {
      try {
        audio.currentTime = 0;
        audio.muted = false;
        await audio.play();
      } catch { /* play may be blocked; clock falls back to performance.now */ }
      const onEnded = () => finish();
      endedHandlerRef.current = onEnded;
      audio.addEventListener('ended', onEnded);
    }

    startPerfRef.current = performance.now();
    setIsRunning(true);

    const getTimelineMs = () => {
      if (audio && audio.currentTime > 0) return audio.currentTime * 1000;
      return performance.now() - startPerfRef.current;
    };

    const tick = () => {
      const currentMs = getTimelineMs();
      setTimelineMs(currentMs);

      if (currentMs >= sessionEndMs) {
        finish();
        return;
      }

      // Audio tail after the final full 8-count block: the avatar exits with
      // Idle Out while the music finishes (corrected sheets only).
      if (outroStartMs != null && !outroTriggeredRef.current && currentMs >= outroStartMs) {
        outroTriggeredRef.current = true;
        playerRef.current?.playOutro(lastBlock.moveKey);
      }

      const idx = findBlockIndexAtTime(timeline, currentMs, currentIndexRef.current);
      if (idx !== -1 && idx !== currentIndexRef.current) {
        const block = timeline[idx];
        currentIndexRef.current = idx;
        setCurrentBlock(block);
        setNextBlock(timeline[idx + 1] ?? null);

        // Only switch the avatar when the MOVE GROUP changes. Blocks within a
        // group are the same step, so Main keeps looping (no abrupt restart).
        if (block.moveGroupIndex !== currentGroupRef.current) {
          currentGroupRef.current = block.moveGroupIndex;

          if (corrected) {
            // Beat-aligned playback: the corrected sheet's loop math assumes
            // Main starts exactly at the group boundary, so switch straight to
            // Main with the sheet's speed scale (no mid-song Idle In).
            playerRef.current?.playMove(block.moveKey, {
              side: block.side,
              timeScale: block.animationSpeedScale ?? 1,
            });
          } else {
            // Legacy timing (song not yet corrected by the client).
            playerRef.current?.playIntro(block.moveKey);
          }

          const entry: ZumbaSwitchLogEntry = {
            group: block.moveGroupIndex,
            move: block.moveName,
            expectedMs: block.startMs,
            actualMs: Math.round(currentMs),
            latencyMs: Math.round(currentMs - block.startMs),
            speedScale: corrected ? block.animationSpeedScale ?? 1 : null,
            plannedLoops: corrected ? block.plannedLoops ?? null : null,
          };
          setSwitchLog((log) => [...log, entry]);
          if (process.env.NODE_ENV !== 'production') {
            // info (not debug) so it is visible without the Verbose filter.
            console.info('[zumba-timeline]', entry);
          }
        }
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return true;
  }, [timeline, meta, playerRef, audioRef, detachEnded, stop]);

  // Clean up on unmount.
  useEffect(() => () => {
    if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    detachEnded();
  }, [detachEnded]);

  return { isRunning, currentBlock, nextBlock, timelineMs, switchLog, start, stop };
}
