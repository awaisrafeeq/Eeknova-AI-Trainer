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
import type { ZumbaTimelineBlock } from '@/lib/zumbaTimelineTypes';

type UseZumbaTimelinePlayerParams = {
  timeline: ZumbaTimelineBlock[];
  playerRef: RefObject<ZumbaAvatarPlayerHandle | null>;
  audioRef: RefObject<HTMLAudioElement | null>;
  onComplete?: () => void;
};

type UseZumbaTimelinePlayerResult = {
  isRunning: boolean;
  currentBlock: ZumbaTimelineBlock | null;
  nextBlock: ZumbaTimelineBlock | null;
  timelineMs: number;
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
  playerRef,
  audioRef,
  onComplete,
}: UseZumbaTimelinePlayerParams): UseZumbaTimelinePlayerResult {
  const [isRunning, setIsRunning] = useState(false);
  const [currentBlock, setCurrentBlock] = useState<ZumbaTimelineBlock | null>(null);
  const [nextBlock, setNextBlock] = useState<ZumbaTimelineBlock | null>(null);
  const [timelineMs, setTimelineMs] = useState(0);

  const rafRef = useRef<number | null>(null);
  const startPerfRef = useRef(0);
  const currentIndexRef = useRef(-1);
  const currentGroupRef = useRef<number | null>(null);
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
    setCurrentBlock(null);
    setNextBlock(null);
    setTimelineMs(0);

    const lastEndMs = timeline[timeline.length - 1].endMs;

    const finish = () => {
      stop();
      onCompleteRef.current?.();
    };

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

      if (currentMs >= lastEndMs) {
        finish();
        return;
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
          playerRef.current?.playIntro(block.moveKey);

          if (process.env.NODE_ENV !== 'production') {
            console.debug('[zumba-timeline]', {
              expectedMoveAtMs: block.startMs,
              actualSwitchAtMs: Math.round(currentMs),
              switchLatencyMs: Math.round(currentMs - block.startMs),
              move: block.moveName,
              group: block.moveGroupIndex,
            });
          }
        }
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return true;
  }, [timeline, playerRef, audioRef, detachEnded, stop]);

  // Clean up on unmount.
  useEffect(() => () => {
    if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    detachEnded();
  }, [detachEnded]);

  return { isRunning, currentBlock, nextBlock, timelineMs, start, stop };
}
