'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';

type AssistantLanguage = 'auto' | 'en' | 'te' | 'hi' | 'ta' | 'kn';

type RealtimeStatus = 'idle' | 'connecting' | 'connected' | 'error';

const LANGUAGE_OPTIONS: Array<{ value: AssistantLanguage; label: string }> = [
  { value: 'auto', label: 'Auto' },
  { value: 'en', label: 'English' },
  { value: 'te', label: 'తెలుగు' },
  { value: 'hi', label: 'हिंदी' },
  { value: 'ta', label: 'தமிழ்' },
  { value: 'kn', label: 'ಕನ್ನಡ' },
];

export default function AssistantShell() {
  const USE_REALTIME = true;

  const [open, setOpen] = useState(false);
  const openRef = useRef(false);
  const [language, setLanguage] = useState<AssistantLanguage>('auto');
  const startedAtRef = useRef<number | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<BlobPart[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const vadRafRef = useRef<number | null>(null);
  const speechStartedRef = useRef(false);
  const lastVoiceAtRef = useRef<number>(0);
  const recordingStartedAtRef = useRef<number>(0);

  const rtcRef = useRef<RTCPeerConnection | null>(null);
  const rtcDataRef = useRef<RTCDataChannel | null>(null);
  const rtcRemoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const rtcStatsIntervalRef = useRef<number | null>(null);
  const rtcAudioSenderRef = useRef<RTCRtpSender | null>(null);
  const remoteAudioCtxRef = useRef<AudioContext | null>(null);
  const remoteAudioAnalyserRef = useRef<AnalyserNode | null>(null);
  const remoteAudioRafRef = useRef<number | null>(null);

  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [reply, setReply] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [realtimeStatus, setRealtimeStatus] = useState<RealtimeStatus>('idle');
  const [micDevices, setMicDevices] = useState<Array<{ deviceId: string; label: string }>>([]);
  const [selectedMicDeviceId, setSelectedMicDeviceId] = useState<string>('');
  const [debugText, setDebugText] = useState('Hello Eeknova');
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const [micLevel, setMicLevel] = useState(0);
  const [useRawMic, setUseRawMic] = useState(false);
  const [wakeWordEnabled, setWakeWordEnabled] = useState(true);
  const [micMonitorEnabled, setMicMonitorEnabled] = useState(false);
  const speechRecRef = useRef<any>(null);
  const speechRecShouldRunRef = useRef(false);
  const speechRecIsRunningRef = useRef(false);
  const realtimeAttemptRef = useRef(0);
  const startRealtimeSessionRef = useRef<(() => Promise<void>) | null>(null);
  const startRecordingRef = useRef<(() => Promise<void>) | null>(null);
  const closeAssistantRef = useRef<(() => void) | null>(null);
  const [wakeStatus, setWakeStatus] = useState<'idle' | 'starting' | 'listening' | 'error'>('idle');
  const [wakeLastHeard, setWakeLastHeard] = useState('');
  const [wakeLastError, setWakeLastError] = useState<string>('');
  const [micMonitorPausedForWake, setMicMonitorPausedForWake] = useState(false);
  const lastWakeTriggerAtRef = useRef<number>(0);
  const lastExitTriggerAtRef = useRef<number>(0);
  const [realtimeLastHeard, setRealtimeLastHeard] = useState('');
  const [assistantAudioLevel, setAssistantAudioLevel] = useState(0);
  const [assistantIsSpeaking, setAssistantIsSpeaking] = useState(false);
  const micMeterAudioCtxRef = useRef<AudioContext | null>(null);
  const micMeterAnalyserRef = useRef<AnalyserNode | null>(null);
  const micMeterRafRef = useRef<number | null>(null);
  const micMeterLastLogAtRef = useRef<number>(0);
  const micMonitorStreamRef = useRef<MediaStream | null>(null);

  const publish = useCallback(
    (nextOpen: boolean, nextLanguage: AssistantLanguage) => {
      if (typeof window === 'undefined') return;
      window.dispatchEvent(
        new CustomEvent('eeknova-assistant-mode', {
          detail: {
            active: nextOpen,
            language: nextLanguage,
          },
        })
      );
    },
    []
  );

  useEffect(() => {
    publish(open, language);
    openRef.current = open;
    if (typeof document !== 'undefined') {
      if (open) {
        document.body.dataset.eeknovaAssistantActive = 'true';
      } else {
        delete (document.body.dataset as any).eeknovaAssistantActive;
      }
    }
  }, [open, language, publish]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = window.localStorage.getItem('eeknova_useRawMic');
    if (saved === 'true') setUseRawMic(true);
    if (saved === 'false') setUseRawMic(false);
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = window.localStorage.getItem('eeknova_selectedMicDeviceId');
    if (saved) setSelectedMicDeviceId(saved);
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('eeknova_useRawMic', useRawMic ? 'true' : 'false');
  }, [useRawMic]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!selectedMicDeviceId) return;
    window.localStorage.setItem('eeknova_selectedMicDeviceId', selectedMicDeviceId);
  }, [selectedMicDeviceId]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = window.localStorage.getItem('eeknova_micMonitorEnabled');
    if (saved === 'true') setMicMonitorEnabled(true);
    if (saved === 'false') setMicMonitorEnabled(false);
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('eeknova_micMonitorEnabled', micMonitorEnabled ? 'true' : 'false');
  }, [micMonitorEnabled]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = window.localStorage.getItem('eeknova_wakeWordEnabled');
    // User requested wake-word to be enabled by default without manual checking.
    // If it was previously stored as false, we still enable it.
    if (saved === null || saved === 'true' || saved === 'false') {
      setWakeWordEnabled(true);
      window.localStorage.setItem('eeknova_wakeWordEnabled', 'true');
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem('eeknova_wakeWordEnabled', wakeWordEnabled ? 'true' : 'false');
  }, [wakeWordEnabled]);

  const stopMicMeter = useCallback(() => {
    if (micMeterRafRef.current) {
      cancelAnimationFrame(micMeterRafRef.current);
      micMeterRafRef.current = null;
    }
    if (micMeterAnalyserRef.current) {
      try {
        micMeterAnalyserRef.current.disconnect();
      } catch {}
    }
    micMeterAnalyserRef.current = null;
    if (micMeterAudioCtxRef.current) {
      try {
        micMeterAudioCtxRef.current.close();
      } catch {}
    }
    micMeterAudioCtxRef.current = null;
    setMicLevel(0);
  }, []);

  const startMicMeter = useCallback(async (stream: MediaStream) => {
    stopMicMeter();
    try {
      const ctx = new AudioContext();
      micMeterAudioCtxRef.current = ctx;
      await ctx.resume().catch(() => undefined);
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      micMeterAnalyserRef.current = analyser;
      src.connect(analyser);

      const buf = new Float32Array(analyser.fftSize);
      const tick = () => {
        try {
          if (ctx.state !== 'running') {
            void ctx.resume().catch(() => undefined);
          }
          analyser.getFloatTimeDomainData(buf);
          let sum = 0;
          let peak = 0;
          for (let i = 0; i < buf.length; i++) {
            const v = buf[i];
            sum += v * v;
            const av = Math.abs(v);
            if (av > peak) peak = av;
          }
          const rms = Math.sqrt(sum / Math.max(1, buf.length));
          const lvl = Math.max(0, Math.min(1, Math.max(rms * 8, peak * 4)));
          setMicLevel(lvl);

          const now = Date.now();
          if (now - micMeterLastLogAtRef.current > 2500) {
            micMeterLastLogAtRef.current = now;
            console.log('[MicMeter]', { ctxState: ctx.state, rms, peak, level: lvl });
          }
        } catch {}
        micMeterRafRef.current = requestAnimationFrame(tick);
      };
      micMeterRafRef.current = requestAnimationFrame(tick);
    } catch {
      setMicLevel(0);
    }
  }, [stopMicMeter]);

  const stopMicMonitor = useCallback(() => {
    if (micMonitorStreamRef.current) {
      micMonitorStreamRef.current.getTracks().forEach((t) => t.stop());
    }
    micMonitorStreamRef.current = null;
    stopMicMeter();
  }, [stopMicMeter]);

  const startMicMonitor = useCallback(async () => {
    if (typeof navigator === 'undefined') return;
    if (!micMonitorEnabled) return;
    if (open || realtimeStatus === 'connecting' || realtimeStatus === 'connected') return;
    // Avoid mic contention with SpeechRecognition wake-word listener.
    if (wakeWordEnabled && (wakeStatus === 'starting' || wakeStatus === 'listening')) return;

    let desiredDeviceId = selectedMicDeviceId;
    const shouldConstrainDevice =
      !!desiredDeviceId && desiredDeviceId !== 'default' && desiredDeviceId !== 'communications';

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        deviceId: shouldConstrainDevice ? { exact: desiredDeviceId } : undefined,
        echoCancellation: useRawMic ? false : true,
        noiseSuppression: useRawMic ? false : true,
        autoGainControl: useRawMic ? false : true,
      },
    });
    micMonitorStreamRef.current = stream;
    await startMicMeter(stream);
  }, [micMonitorEnabled, open, realtimeStatus, selectedMicDeviceId, startMicMeter, useRawMic, wakeStatus, wakeWordEnabled]);

  const restartMicMonitor = useCallback(async () => {
    if (!micMonitorEnabled) return;
    if (open || realtimeStatus === 'connecting' || realtimeStatus === 'connected') return;
    if (wakeWordEnabled && (wakeStatus === 'starting' || wakeStatus === 'listening')) return;
    stopMicMonitor();
    await startMicMonitor();
  }, [micMonitorEnabled, open, realtimeStatus, startMicMonitor, stopMicMonitor, wakeStatus, wakeWordEnabled]);

  const openAssistant = useCallback(() => {
    startedAtRef.current = Date.now();
    setTranscript('');
    setReply('');
    setRealtimeLastHeard('');
    setError(null);
    setOpen(true);
  }, []);

  const startWakeWord = useCallback(() => {
    if (typeof window === 'undefined') return;
    
    // Prevent multiple rapid starts
    if (speechRecIsRunningRef.current) {
      console.log('[WakeWord] Already running, ignoring start call');
      return;
    }
    
    const SR: any = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) {
      setError('Wake word not supported in this browser. Use Chrome/Edge.');
      setWakeWordEnabled(false);
      return;
    }

    setWakeStatus('starting');
    setWakeLastError('');

    speechRecShouldRunRef.current = true;
    if (!speechRecRef.current) {
      console.log('[WakeWord] Creating NEW SpeechRecognition instance');
      const rec = new SR();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-US';

      rec.onstart = () => {
        console.log('[WakeWord] SpeechRecognition STARTED');
        speechRecIsRunningRef.current = true;
        setWakeStatus('listening');
        setWakeLastError('');
      };

      rec.onresult = (event: any) => {
        try {
          // If wake word detection is disabled, just log and return
          if (!wakeWordEnabled) {
            console.log('[WakeWord] Detection disabled, ignoring result');
            return;
          }

          let text = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const res = event.results[i];
            const t = res?.[0]?.transcript;
            if (typeof t === 'string') text += ` ${t}`;
          }
          const norm = text.trim().toLowerCase();
          if (!norm) return;
          setWakeLastHeard(norm.slice(-120));

          // normalize common mis-hearings
          const norm2 = norm
            .replace(/ek\s+a\s*nova/g, 'eeknova')
            .replace(/an\s*ova/g, 'eeknova')
            .replace(/ek ?nova/g, 'eeknova')
            .replace(/eek nova/g, 'eeknova')
            .replace(/iknova/g, 'eeknova')
            .replace(/ignova/g, 'eeknova')
            .replace(/eekn0va/g, 'eeknova');

          const wantsOpen = /\b(hi|hey|hello|hay|he)\b/.test(norm2);
          const wantsClose = /\b(bye|by|exit)\b/.test(norm2);

          const hasName = /\beeknova\b/.test(norm2) || /\bnova\b/.test(norm2);

          if (wantsClose && openRef.current) {
            const now = Date.now();
            if (now - lastExitTriggerAtRef.current < 2500) return;
            lastExitTriggerAtRef.current = now;
            console.log('[WakeWord] Exit command detected, closing assistant');
            closeAssistantRef.current?.();
            return;
          }

          const isHello = /\bhello\b/.test(norm2);
          const isHiHey = /\b(hi|hey)\b/.test(norm2);
          // Wake rules:
          // - "hello" alone is enough
          // - otherwise require "hi/hey" + name (eeknova/nova)
          if (!(isHello || (isHiHey && hasName))) return;
          const now = Date.now();
          if (now - lastWakeTriggerAtRef.current < 8000) return;
          lastWakeTriggerAtRef.current = now;
          if (!openRef.current) {
            console.log('[WakeWord] Wake command detected, opening assistant');
            openAssistant();
          }
          if (USE_REALTIME) {
            void startRealtimeSessionRef.current?.();
          } else {
            void startRecordingRef.current?.();
          }
        } catch {}
      };

      rec.onerror = (e: any) => {
        const err = String(e?.error || 'unknown');
        console.log('[WakeWord] SpeechRecognition ERROR:', { error: err, event: e });
        if (err === 'no-speech') {
          // Common benign event; keep listening/restarting silently
          setWakeStatus('listening');
          setWakeLastError('');
        } else {
          setWakeStatus('error');
          setWakeLastError(err);
        }
        if (err !== 'no-speech') {
          console.log('[WakeWord] error:', e);
        }
        // Some errors need user gesture / permission. We won't spin in a tight loop.
        speechRecShouldRunRef.current = wakeWordEnabled;
        try {
          rec.stop();
        } catch {}
      };

      rec.onend = () => {
        console.log('[WakeWord] SpeechRecognition ENDED - shouldRun:', speechRecShouldRunRef.current);
        speechRecIsRunningRef.current = false;
        if (!speechRecShouldRunRef.current) return;
        // Restart after a short delay to avoid rapid loops
        window.setTimeout(() => {
          if (!speechRecShouldRunRef.current || speechRecIsRunningRef.current) return;
          console.log('[WakeWord] Auto-restarting SpeechRecognition');
          try {
            rec.start();
          } catch (e) {
            console.error('[WakeWord] Failed to restart:', e);
          }
        }, 350);
      };

      speechRecRef.current = rec;
    } else {
      console.log('[WakeWord] Reusing existing SpeechRecognition instance');
    }

    try {
      console.log('[WakeWord] Starting SpeechRecognition');
      speechRecRef.current.start();
    } catch {}
  }, [USE_REALTIME, open, openAssistant, wakeWordEnabled]);

  useEffect(() => {
    // SpeechRecognition is more reliable when no other getUserMedia stream is holding the mic.
    // Pause the global mic monitor while wake-word is enabled.
    if (!wakeWordEnabled) return;
    if (micMonitorEnabled && !open && realtimeStatus !== 'connected' && realtimeStatus !== 'connecting') {
      stopMicMonitor();
      setMicMonitorPausedForWake(true);
    }
  }, [micMonitorEnabled, open, realtimeStatus, stopMicMonitor, wakeWordEnabled]);

  useEffect(() => {
    // Clear paused flag when wake-word is off or assistant is open/connected.
    if (!wakeWordEnabled) {
      setMicMonitorPausedForWake(false);
      return;
    }
    if (open || realtimeStatus === 'connecting' || realtimeStatus === 'connected') {
      setMicMonitorPausedForWake(false);
      return;
    }
    if (wakeStatus !== 'starting' && wakeStatus !== 'listening') {
      setMicMonitorPausedForWake(false);
    }
  }, [open, realtimeStatus, wakeStatus, wakeWordEnabled]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!wakeWordEnabled) return;

    // Some browsers require a user gesture before SpeechRecognition can start reliably.
    // We try eagerly in the main effect, but also retry on the first pointer interaction.
    const onFirstGesture = () => {
      if (!wakeWordEnabled) return;
      if (wakeStatus === 'listening') return;
      if (USE_REALTIME && open && realtimeStatus === 'connected') return;
      try {
        startWakeWord();
      } catch {}
    };

    window.addEventListener('pointerdown', onFirstGesture, { once: true });
    return () => window.removeEventListener('pointerdown', onFirstGesture);
  }, [USE_REALTIME, open, realtimeStatus, startWakeWord, wakeStatus, wakeWordEnabled]);

  const stopWakeWord = useCallback(() => {
    speechRecShouldRunRef.current = false;
    setWakeStatus('idle');
    try {
      speechRecRef.current?.stop();
    } catch {}
  }, []);

  useEffect(() => {
    if (!wakeWordEnabled) {
      stopWakeWord();
      return;
    }
    // Keep SpeechRecognition running even while Realtime is connected so we can still
    // detect voice-exit locally if Realtime transcription is unavailable (e.g. quota/token issues).
    startWakeWord();
    return () => stopWakeWord();
  }, [USE_REALTIME, open, realtimeStatus, startWakeWord, stopWakeWord, wakeWordEnabled]);

  useEffect(() => {
    if (typeof navigator === 'undefined') return;
    const loadDevices = async () => {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const mics = devices
          .filter((d) => d.kind === 'audioinput')
          .map((d) => ({ deviceId: d.deviceId, label: d.label || 'Microphone' }));
        setMicDevices(mics);

        const preferred =
          mics.find((m) => m.deviceId !== 'default' && m.deviceId !== 'communications') ||
          mics.find((m) => m.label && m.label !== 'Microphone') ||
          mics[0];
        if (preferred && !selectedMicDeviceId) {
          setSelectedMicDeviceId(preferred.deviceId);
        }
      } catch {
        // ignore
      }
    };

    const onDeviceChange = () => {
      void loadDevices();
    };
    navigator.mediaDevices?.addEventListener?.('devicechange', onDeviceChange);
    void loadDevices();
    return () => navigator.mediaDevices?.removeEventListener?.('devicechange', onDeviceChange);
  }, [selectedMicDeviceId]);

  useEffect(() => {
    // When user changes the mic dropdown while idle, restart the monitor so the selection actually takes effect.
    void restartMicMonitor().catch(() => undefined);
  }, [restartMicMonitor, selectedMicDeviceId]);

  useEffect(() => {
    if (!micMonitorEnabled) {
      stopMicMonitor();
      return;
    }
    // If wake-word is listening, don't start monitor (avoids mic contention).
    if (wakeWordEnabled && (wakeStatus === 'starting' || wakeStatus === 'listening') && !open) {
      return;
    }
    void startMicMonitor().catch(() => undefined);
    return () => stopMicMonitor();
  }, [micMonitorEnabled, open, startMicMonitor, stopMicMonitor, wakeStatus, wakeWordEnabled]);

  const startRealtimePcmInput = useCallback(async (_dc: RTCDataChannel) => {
    return;
  }, []);

  const closeAssistant = useCallback(() => {
    realtimeAttemptRef.current += 1;
    if (vadRafRef.current) {
      cancelAnimationFrame(vadRafRef.current);
      vadRafRef.current = null;
    }
    speechStartedRef.current = false;
    lastVoiceAtRef.current = 0;

    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch {}
    }
    audioContextRef.current = null;
    analyserRef.current = null;

    stopMicMeter();

    if (rtcDataRef.current) {
      try {
        rtcDataRef.current.close();
      } catch {}
    }
    rtcDataRef.current = null;

    if (rtcStatsIntervalRef.current) {
      window.clearInterval(rtcStatsIntervalRef.current);
      rtcStatsIntervalRef.current = null;
    }

    if (remoteAudioRafRef.current) {
      cancelAnimationFrame(remoteAudioRafRef.current);
      remoteAudioRafRef.current = null;
    }
    if (remoteAudioAnalyserRef.current) {
      try {
        remoteAudioAnalyserRef.current.disconnect();
      } catch {}
    }
    remoteAudioAnalyserRef.current = null;
    if (remoteAudioCtxRef.current) {
      try {
        remoteAudioCtxRef.current.close();
      } catch {}
    }
    remoteAudioCtxRef.current = null;
    try {
      window.dispatchEvent(
        new CustomEvent('eeknova-assistant-audio', {
          detail: { level: 0, isSpeaking: false, source: 'realtime' },
        })
      );
    } catch {}

    if (rtcRef.current) {
      try {
        rtcRef.current.close();
      } catch {}
    }
    rtcRef.current = null;

    if (rtcRemoteAudioRef.current) {
      try {
        rtcRemoteAudioRef.current.pause();
      } catch {}
    }
    rtcRemoteAudioRef.current = null;
    setRealtimeStatus('idle');
    setRealtimeLastHeard('');

    try {
      mediaRecorderRef.current?.stop();
    } catch {}
    mediaRecorderRef.current = null;

    if (audioStreamRef.current) {
      console.log('[Realtime] Stopping mic tracks - before stop:');
      audioStreamRef.current.getTracks().forEach((t) => {
        console.log('[Realtime] track state:', { kind: t.kind, enabled: t.enabled, readyState: t.readyState, muted: (t as any).muted });
      });
      audioStreamRef.current.getTracks().forEach((t) => t.stop());
    }
    audioStreamRef.current = null;
    recordedChunksRef.current = [];
    setIsRecording(false);

    if (currentAudioRef.current) {
      try {
        currentAudioRef.current.pause();
      } catch {}
      currentAudioRef.current = null;
    }

    setOpen(false);
    // If global mic monitor is enabled, resume it after closing assistant.
    window.setTimeout(() => {
      void startMicMonitor().catch(() => undefined);
    }, 250);
  }, [startMicMonitor, stopMicMeter]);

  useEffect(() => {
    closeAssistantRef.current = closeAssistant;
  }, [closeAssistant]);

  const getLanguageInstruction = useCallback((lang: AssistantLanguage) => {
    if (lang === 'auto') {
      return [
        'Reply in the same language the user is speaking/writing.',
        'Do NOT ask the user to choose a language (do not offer options like English/Urdu/Hindi).',
        'If the user explicitly says things like "speak in Hindi / Telugu / English" then lock to that language and continue replying in that language until the assistant session is closed.',
      ].join(' ');
    }
    if (lang === 'en') return 'Reply in English.';
    if (lang === 'hi') return 'Reply in Hindi.';
    if (lang === 'te') return 'Reply in Telugu.';
    if (lang === 'ta') return 'Reply in Tamil.';
    if (lang === 'kn') return 'Reply in Kannada.';
    return 'Reply in English.';
  }, []);

  const startRealtimeSession = useCallback(async () => {
    if (realtimeStatus === 'connecting' || realtimeStatus === 'connected') {
      return;
    }

    const attemptId = realtimeAttemptRef.current + 1;
    realtimeAttemptRef.current = attemptId;

    const isPcClosed = (p: RTCPeerConnection) => {
      try {
        return (p as any).signalingState === 'closed' || (p as any).connectionState === 'closed';
      } catch {
        return true;
      }
    };

    setError(null);
    setRealtimeStatus('connecting');

    const tokenRes = await fetch('/api/realtime/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'gpt-4o-mini-realtime-preview', voice: 'alloy' }),
    });

    if (realtimeAttemptRef.current !== attemptId) return;

    if (!tokenRes.ok) {
      const t = await tokenRes.text().catch(() => '');
      const msg = t || `Realtime token failed (${tokenRes.status})`;
      setRealtimeStatus('error');
      setIsProcessing(false);
      setError(msg);
      return;
    }

    const tokenJson = (await tokenRes.json()) as { token: string; model?: string };
    const token = tokenJson.token;
    const model = tokenJson.model || 'gpt-4o-realtime-preview';

    const pc = new RTCPeerConnection();
    rtcRef.current = pc;

    if (realtimeAttemptRef.current !== attemptId) {
      try {
        pc.close();
      } catch {}
      return;
    }

    // We want to both send mic audio and receive assistant audio.
    // Keep a handle so we can attach the user's mic track via replaceTrack (more reliable than addTrack here).
    const audioTransceiver = pc.addTransceiver('audio', { direction: 'sendrecv' });
    rtcAudioSenderRef.current = audioTransceiver.sender;

    pc.oniceconnectionstatechange = () => {
      console.log('[Realtime] iceConnectionState:', pc.iceConnectionState);
    };
    pc.onicecandidateerror = (e) => {
      console.log('[Realtime] icecandidateerror', e);
    };
    pc.onconnectionstatechange = () => {
      console.log('[Realtime] connectionState:', pc.connectionState);
    };
    pc.onsignalingstatechange = () => {
      console.log('[Realtime] signalingState:', pc.signalingState);
    };

    const remoteAudio = new Audio();
    remoteAudio.autoplay = true;
    rtcRemoteAudioRef.current = remoteAudio;

    pc.ontrack = (e) => {
      console.log('[Realtime] remote track received:', e.track.kind);
      const track = e.track;
      if (track && track.kind === 'audio') {
        const stream = new MediaStream([track]);
        remoteAudio.srcObject = stream;
        remoteAudio.muted = false;
        remoteAudio.volume = 1;
        (remoteAudio as any).playsInline = true;
        void remoteAudio.play().catch(() => undefined);

        console.log('[Realtime] remote audio track info:', {
          label: track.label,
          enabled: track.enabled,
          readyState: track.readyState,
          muted: (track as any).muted,
        });

        try {
          if (remoteAudioRafRef.current) {
            cancelAnimationFrame(remoteAudioRafRef.current);
            remoteAudioRafRef.current = null;
          }
          if (remoteAudioCtxRef.current) {
            try {
              remoteAudioCtxRef.current.close();
            } catch {}
          }
          remoteAudioCtxRef.current = null;
          remoteAudioAnalyserRef.current = null;

          const ctx = new AudioContext();
          remoteAudioCtxRef.current = ctx;
          void ctx.resume().catch(() => undefined);

          const src = ctx.createMediaStreamSource(stream);
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 1024;
          src.connect(analyser);
          remoteAudioAnalyserRef.current = analyser;

          const buf = new Float32Array(analyser.fftSize);
          let lastSpeakAt = 0;
          let lastLogAt = 0;
          const tick = () => {
            try {
              if (ctx.state !== 'running') {
                void ctx.resume().catch(() => undefined);
              }
              analyser.getFloatTimeDomainData(buf);
              let sum = 0;
              let peak = 0;
              for (let i = 0; i < buf.length; i++) {
                const v = buf[i];
                sum += v * v;
                const av = Math.abs(v);
                if (av > peak) peak = av;
              }
              const rms = Math.sqrt(sum / Math.max(1, buf.length));
              const lvl = Math.max(0, Math.min(1, Math.max(rms * 12, peak * 6)));
              const now = Date.now();
              if (lvl > 0.045) lastSpeakAt = now;
              const isSpeaking = now - lastSpeakAt < 180;
              setAssistantAudioLevel(lvl);
              setAssistantIsSpeaking(isSpeaking);

              if (now - lastLogAt > 3000) {
                lastLogAt = now;
                console.log('[Realtime] remote audio meter:', { ctxState: ctx.state, level: lvl, isSpeaking });
              }

              window.dispatchEvent(
                new CustomEvent('eeknova-assistant-audio', {
                  detail: { level: lvl, isSpeaking, source: 'realtime' },
                })
              );
            } catch {}
            remoteAudioRafRef.current = requestAnimationFrame(tick);
          };
          remoteAudioRafRef.current = requestAnimationFrame(tick);
        } catch {}
      }
    };

    const dc = pc.createDataChannel('oai-events');
    rtcDataRef.current = dc;

    const sendResponseCreate = () => {
      try {
        if (dc.readyState !== 'open') return;
        dc.send(
          JSON.stringify({
            type: 'response.create',
            response: { modalities: ['text', 'audio'] },
          })
        );
        setIsProcessing(true);
      } catch {}
    };

    const sendUserText = (text: string) => {
      try {
        if (dc.readyState !== 'open') return;
        dc.send(
          JSON.stringify({
            type: 'conversation.item.create',
            item: {
              type: 'message',
              role: 'user',
              content: [{ type: 'input_text', text }],
            },
          })
        );
        sendResponseCreate();
      } catch {}
    };

    // expose for UI handlers
    (window as any).__eeknovaRealtimeSendResponseCreate = sendResponseCreate;
    (window as any).__eeknovaRealtimeSendUserText = sendUserText;

    dc.onopen = () => {
      console.log('[Realtime] datachannel open');
      setRealtimeStatus('connected');
      setIsProcessing(false);
    };
    dc.onclose = () => {
      console.log('[Realtime] datachannel close, readyState:', dc.readyState);
      setRealtimeStatus('error');
      setIsProcessing(false);
    };
    dc.onerror = (e) => {
      console.log('[Realtime] datachannel error', e);
      setRealtimeStatus('error');
      setIsProcessing(false);
    };

    dc.onmessage = (ev) => {
      try {
        const raw = String(ev.data);
        console.log('[Realtime] raw:', raw);
        const msg = JSON.parse(raw) as any;
        if (msg?.type) {
          console.log('[Realtime] event:', msg.type);
        }
        if (msg?.type === 'input_audio_buffer.speech_started') {
          setIsUserSpeaking(true);
        }
        if (msg?.type === 'input_audio_buffer.speech_stopped' || msg?.type === 'input_audio_buffer.speech_ended') {
          setIsUserSpeaking(false);
          setIsProcessing(true);
        }
        if (msg?.type === 'response.text.delta' && typeof msg.delta === 'string') {
          setReply((prev) => prev + msg.delta);
        }
        if (msg?.type === 'response.audio_transcript.delta' && typeof msg.delta === 'string') {
          setReply((prev) => prev + msg.delta);
        }
        if (msg?.type === 'response.audio_transcript.done' && typeof msg.transcript === 'string') {
          setReply(msg.transcript);
        }
        const maybeHandleExitFromTranscript = (t: string) => {
          try {
            const norm = String(t).trim().toLowerCase();
            if (!norm) return;
            setTranscript(String(t));
            setRealtimeLastHeard(String(t));
            const norm2 = norm
              .replace(/ek\s+a\s*nova/g, 'eeknova')
              .replace(/an\s*ova/g, 'eeknova')
              .replace(/ek ?nova/g, 'eeknova')
              .replace(/eek nova/g, 'eeknova')
              .replace(/iknova/g, 'eeknova')
              .replace(/ignova/g, 'eeknova');
            if (!/\b(bye|by|exit)\b/.test(norm2)) return;
            const now = Date.now();
            if (now - lastExitTriggerAtRef.current < 2500) return;
            lastExitTriggerAtRef.current = now;
            console.log('[ExitWord] closing from transcript:', norm2);
            closeAssistantRef.current?.();
          } catch {}
        };

        if (msg?.type === 'conversation.item.input_audio_transcription.completed') {
          const t =
            typeof msg?.transcript === 'string'
              ? msg.transcript
              : typeof msg?.item?.transcript === 'string'
                ? msg.item.transcript
                : '';
          if (t) maybeHandleExitFromTranscript(String(t));
        }

        if (msg?.type === 'input_audio_transcription.completed') {
          const t = typeof msg?.transcript === 'string' ? msg.transcript : '';
          if (t) maybeHandleExitFromTranscript(String(t));
        }

        if (msg?.type === 'input_audio_transcription.segment') {
          const t = typeof msg?.text === 'string' ? msg.text : '';
          if (t) setRealtimeLastHeard(String(t));
        }

        // Some streams deliver transcript via conversation.item.created/updated
        if (msg?.type === 'conversation.item.created' || msg?.type === 'conversation.item.updated') {
          const item = msg?.item;
          if (item?.role === 'user') {
            const content0 = Array.isArray(item?.content) ? item.content[0] : null;
            const t =
              typeof content0?.transcript === 'string'
                ? content0.transcript
                : typeof content0?.text === 'string'
                  ? content0.text
                  : '';
            if (t) maybeHandleExitFromTranscript(String(t));
          }
        }
        if (msg?.type === 'response.done') {
          setIsProcessing(false);
        }
        if (msg?.type === 'response.completed') {
          setIsProcessing(false);
        }
      } catch {}
    };

    // Attach microphone track to WebRTC
    let desiredDeviceId = selectedMicDeviceId;
    if (!desiredDeviceId) {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const mics = devices
          .filter((d) => d.kind === 'audioinput')
          .map((d) => ({ deviceId: d.deviceId, label: d.label || 'Microphone' }));
        const preferred =
          mics.find((m) => m.deviceId !== 'default' && m.deviceId !== 'communications') ||
          mics.find((m) => m.label && m.label !== 'Microphone') ||
          mics[0];
        if (preferred?.deviceId) desiredDeviceId = preferred.deviceId;
      } catch {}
    }

    const shouldConstrainDevice =
      !!desiredDeviceId && desiredDeviceId !== 'default' && desiredDeviceId !== 'communications';

    const mic = await navigator.mediaDevices.getUserMedia({
      audio: {
        deviceId: shouldConstrainDevice ? { exact: desiredDeviceId } : undefined,
        echoCancellation: useRawMic ? false : true,
        noiseSuppression: useRawMic ? false : true,
        autoGainControl: useRawMic ? false : true,
      },
    });
    audioStreamRef.current = mic;
    const micTrack = mic.getAudioTracks()[0] || null;
    if (micTrack) {
      console.log('[Realtime] mic track:', {
        label: micTrack.label,
        enabled: micTrack.enabled,
        readyState: micTrack.readyState,
        muted: (micTrack as any).muted,
        desiredDeviceId,
      });
      console.log('[Realtime] mic settings:', micTrack.getSettings());
      try {
        await audioTransceiver.sender.replaceTrack(micTrack);
      } catch (e) {
        console.log('[Realtime] replaceTrack failed; falling back to addTrack', e);
        pc.addTrack(micTrack, mic);
      }
    } else {
      console.log('[Realtime] no mic audio track found');
    }

    // Local mic level meter (helps confirm if your voice is actually reaching the browser)
    stopMicMonitor();
    await startMicMeter(mic);

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    if (realtimeAttemptRef.current !== attemptId || isPcClosed(pc) || rtcRef.current !== pc) return;

    const sdpRes = await fetch(`https://api.openai.com/v1/realtime?model=${encodeURIComponent(model)}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/sdp',
      },
      body: offer.sdp || '',
    });

    if (realtimeAttemptRef.current !== attemptId || isPcClosed(pc) || rtcRef.current !== pc) return;

    if (!sdpRes.ok) {
      const details = await sdpRes.text().catch(() => '');
      setRealtimeStatus('error');
      setIsProcessing(false);
      setError(`SDP exchange failed (${sdpRes.status}): ${details}`);
      return;
    }

    const answerSdp = await sdpRes.text();
    if (realtimeAttemptRef.current !== attemptId || isPcClosed(pc) || rtcRef.current !== pc) return;
    try {
      await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });
    } catch (e) {
      if (isPcClosed(pc)) return;
      throw e;
    }

    if (rtcStatsIntervalRef.current) {
      window.clearInterval(rtcStatsIntervalRef.current);
      rtcStatsIntervalRef.current = null;
    }
    rtcStatsIntervalRef.current = window.setInterval(async () => {
      try {
        const stats = await pc.getStats();
        let outbound: any = null;
        let candidatePair: any = null;
        stats.forEach((r: any) => {
          if (r.type === 'outbound-rtp' && r.kind === 'audio') outbound = r;
          if (r.type === 'candidate-pair' && r.state === 'succeeded' && r.nominated) candidatePair = r;
        });
        if (outbound) {
          console.log('[Realtime] webrtc outbound audio:', {
            bytesSent: outbound.bytesSent,
            packetsSent: outbound.packetsSent,
            framesEncoded: outbound.framesEncoded,
          });
        }
        if (candidatePair) {
          console.log('[Realtime] webrtc candidate pair:', {
            currentRoundTripTime: candidatePair.currentRoundTripTime,
            availableOutgoingBitrate: candidatePair.availableOutgoingBitrate,
          });
        }
      } catch {}
    }, 2000);

    const instructions = [
      'You are Eeknova Assistant, a helpful in-app guide for the Eeknova experience.',
      'Scope: Eeknova app only. Your primary job is to help users use Eeknova modules and understand results: Yoga (poses, warm-up/cool-down, form feedback, accuracy/stats), Chess (learning modules + gameplay modes), Zumba (moves/steps, practice, feedback/stats).',
      'If the user asks something unrelated to Eeknova (e.g., cooking, general trivia), follow this exact pattern:',
      '1) Give a short helpful answer (1-3 lines, no deep detail).',
      '2) Immediately pivot back to Eeknova with: (a) a 1-line bridge, (b) 1-2 concrete next actions inside the app, (c) the kind of stats/feedback they will see.',
      'Example: If asked “how to fry an egg”, answer briefly, then say: “By the way, in Eeknova you can try a Yoga pose or a Chess lesson—want Yoga or Chess? You’ll see accuracy, corrections, and progress stats.”',
      'Never continue a long off-topic discussion. Always redirect back to Eeknova within the same message.',
      'If you are unsure about something specific, ask 1 short clarifying question and keep the conversation anchored to Eeknova.',
      'Reply in simple layman language.',
      'Use slow polite tone.',
      getLanguageInstruction(language),
    ].join(' ');

    const sendUpdate = () => {
      try {
        dc.send(
          JSON.stringify({
            type: 'session.update',
            session: {
              instructions,
              input_audio_transcription: { model: 'whisper-1' },
              // Let server VAD auto-create responses when user stops speaking
              turn_detection: {
                type: 'server_vad',
                threshold: 0.12,
                prefix_padding_ms: 500,
                silence_duration_ms: 1200,
                create_response: true,
              },
            },
          })
        );
        console.log('[Realtime] session.update sent');
      } catch {}
    };

    if (dc.readyState === 'open') {
      sendUpdate();
    } else {
      const existingOnOpen = dc.onopen;
      dc.onopen = (ev) => {
        if (typeof existingOnOpen === 'function') existingOnOpen.call(dc, ev as any);
        sendUpdate();
      };
    }
  }, [getLanguageInstruction, language, realtimeStatus, selectedMicDeviceId, useRawMic]);

  useEffect(() => {
    startRealtimeSessionRef.current = startRealtimeSession;
  }, [startRealtimeSession]);

  useEffect(() => {
    if (!USE_REALTIME) return;
    if (!open) return;
    if (realtimeStatus !== 'connected') return;
    // Restart session so new mic constraints take effect
    closeAssistant();
    setRealtimeStatus('connecting');
    setIsProcessing(true);
    void startRealtimeSession().catch((e) => {
      setRealtimeStatus('error');
      setIsProcessing(false);
      setError(e instanceof Error ? e.message : 'Realtime error');
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [useRawMic]);

  const startRecording = useCallback(async () => {
    if (USE_REALTIME) return;
    setError(null);
    setIsProcessing(false);

    if (isRecording) return;

    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
    audioStreamRef.current = stream;
    recordedChunksRef.current = [];

    speechStartedRef.current = false;
    lastVoiceAtRef.current = 0;
    recordingStartedAtRef.current = Date.now();

    // VAD setup
    const ctx = new AudioContext();
    audioContextRef.current = ctx;
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0.8;
    source.connect(analyser);
    analyserRef.current = analyser;

    const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e: BlobEvent) => {
      if (e.data && e.data.size > 0) {
        recordedChunksRef.current.push(e.data);
      }
    };

    recorder.onstop = async () => {
      try {
        setIsProcessing(true);
        const blob = new Blob(recordedChunksRef.current, { type: 'audio/webm' });
        recordedChunksRef.current = [];

        const fd = new FormData();
        fd.append('file', blob, 'audio.webm');
        fd.append('language', language);

        const sttRes = await fetch('/api/stt', { method: 'POST', body: fd });
        if (!sttRes.ok) {
          const t = await sttRes.text().catch(() => '');
          throw new Error(t || `STT failed (${sttRes.status})`);
        }
        const sttJson = (await sttRes.json()) as { text?: string };
        const nextTranscript = (sttJson.text || '').trim();
        setTranscript(nextTranscript);

        if (!nextTranscript) {
          setIsProcessing(false);
          return;
        }

        const assistantRes = await fetch('/api/assistant', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ transcript: nextTranscript, language }),
        });
        if (!assistantRes.ok) {
          const t = await assistantRes.text().catch(() => '');
          throw new Error(t || `Assistant failed (${assistantRes.status})`);
        }
        const assistantJson = (await assistantRes.json()) as { reply?: string };
        const nextReply = (assistantJson.reply || '').trim();
        setReply(nextReply);

        if (nextReply) {
          const ttsRes = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: nextReply, voice: 'nova' }),
          });
          if (!ttsRes.ok) {
            const t = await ttsRes.text().catch(() => '');
            throw new Error(t || `TTS failed (${ttsRes.status})`);
          }
          const audioBlob = await ttsRes.blob();
          const url = URL.createObjectURL(audioBlob);
          const audio = new Audio(url);
          currentAudioRef.current = audio;
          audio.onended = () => {
            URL.revokeObjectURL(url);
          };
          await audio.play();
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Unexpected error');
      } finally {
        setIsProcessing(false);
      }
    };

    // Chunking helps ensure we always get data even if user speaks briefly.
    recorder.start(250);
    setIsRecording(true);

    // Simple RMS VAD: stop after 900ms of silence once speech started.
    const SILENCE_MS = 900;
    const MAX_RECORDING_MS = 12_000;
    const VOICE_RMS_THRESHOLD = 0.018;

    const buf = new Float32Array(analyser.frequencyBinCount);

    const tick = () => {
      const a = analyserRef.current;
      if (!a || !audioContextRef.current) return;

      a.getFloatTimeDomainData(buf);
      let sumSq = 0;
      for (let i = 0; i < buf.length; i++) sumSq += buf[i] * buf[i];
      const rms = Math.sqrt(sumSq / buf.length);

      const now = Date.now();
      if (rms >= VOICE_RMS_THRESHOLD) {
        speechStartedRef.current = true;
        lastVoiceAtRef.current = now;
      }

      const elapsed = now - recordingStartedAtRef.current;
      const silentFor = lastVoiceAtRef.current ? now - lastVoiceAtRef.current : Infinity;

      if (elapsed >= MAX_RECORDING_MS) {
        stopRecording();
        return;
      }

      if (speechStartedRef.current && silentFor >= SILENCE_MS) {
        stopRecording();
        return;
      }

      vadRafRef.current = requestAnimationFrame(tick);
    };

    vadRafRef.current = requestAnimationFrame(tick);
  }, [isRecording, language]);

  const stopRecording = useCallback(() => {
    if (USE_REALTIME) return;
    if (!isRecording) return;

    if (vadRafRef.current) {
      cancelAnimationFrame(vadRafRef.current);
      vadRafRef.current = null;
    }

    try {
      mediaRecorderRef.current?.stop();
    } catch {}
    if (audioStreamRef.current) {
      console.log('[Recording] Stopping mic tracks - before stop:');
      audioStreamRef.current.getTracks().forEach((t) => {
        console.log('[Recording] track state:', { kind: t.kind, enabled: t.enabled, readyState: t.readyState, muted: (t as any).muted });
      });
      audioStreamRef.current.getTracks().forEach((t) => t.stop());
    }
    audioStreamRef.current = null;
    mediaRecorderRef.current = null;
    setIsRecording(false);

    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch {}
    }
    audioContextRef.current = null;
    analyserRef.current = null;
  }, [USE_REALTIME, isRecording, language]);

  useEffect(() => {
    startRecordingRef.current = startRecording;
  }, [startRecording]);

  const micButtonLabel = useMemo(() => {
    if (!open) return 'Ask Eeknova';
    return 'Exit';
  }, [open]);

  const handleMicClick = useCallback(() => {
    if (open) {
      closeAssistant();
      return;
    }

    openAssistant();
    if (USE_REALTIME) {
      setIsProcessing(true);
      void startRealtimeSession().catch((e) => {
        setRealtimeStatus('error');
        setIsProcessing(false);
        setError(e instanceof Error ? e.message : 'Realtime error');
      });
    } else {
      void startRecording().catch((e) => {
        setError(e instanceof Error ? e.message : 'Mic permission error');
      });
    }
  }, [USE_REALTIME, open, closeAssistant, openAssistant, startRealtimeSession, startRecording]);

  const handleDebugTestReply = useCallback(() => {
    try {
      (window as any).__eeknovaRealtimeSendResponseCreate?.();
    } catch {}
  }, []);

  const handleDebugSendText = useCallback(() => {
    try {
      (window as any).__eeknovaRealtimeSendUserText?.(debugText);
    } catch {}
  }, [debugText]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!open) return;
      if (e.key === 'Escape') {
        e.preventDefault();
        closeAssistant();
      }
    },
    [open, closeAssistant]
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <>
      <div
        data-eeknova-assistant-ui="true"
        className="fixed left-4 top-4 z-[80] rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[rgba(0,0,0,.28)] px-3 py-2 text-[12px] text-[var(--ink-med)] backdrop-blur-md"
      >
        <div>Mic monitor: {micMonitorEnabled ? 'on' : 'off'}</div>
        <div>Realtime: {realtimeStatus}</div>
        <div>Mic level: {Math.round(micLevel * 100)}%</div>
        <div>User: {isUserSpeaking ? 'speaking' : 'silent'}</div>
        <div>Wake: {wakeWordEnabled ? wakeStatus : 'off'}</div>
        {wakeWordEnabled ? <div>Heard: {wakeLastHeard || '-'}</div> : null}
        {(realtimeStatus === 'connecting' || realtimeStatus === 'connected') ? (
          <div>RT Heard: {realtimeLastHeard || '-'}</div>
        ) : null}
        {(realtimeStatus === 'connecting' || realtimeStatus === 'connected') ? (
          <div>AI audio: {Math.round(assistantAudioLevel * 100)}% ({assistantIsSpeaking ? 'speaking' : 'silent'})</div>
        ) : null}
        {micMonitorPausedForWake ? <div>Mic: paused for wake</div> : null}
        <label className="mt-2 flex items-center gap-2">
          <input
            type="checkbox"
            checked={micMonitorEnabled}
            onChange={(e) => setMicMonitorEnabled(e.target.checked)}
          />
          Mic monitor
        </label>
        <div className="mt-2">Mic devices: {micDevices.length || '0'}</div>
        <select
          value={selectedMicDeviceId}
          onChange={(e) => setSelectedMicDeviceId(e.target.value)}
          className="mt-1 w-[260px] max-w-[70vw] rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[rgba(0,0,0,.35)] px-2 py-1 text-[12px] text-white/90 outline-none"
        >
          {micDevices.length === 0 ? (
            <option value="" className="bg-black">
              Default
            </option>
          ) : (
            micDevices.map((d) => (
              <option key={d.deviceId} value={d.deviceId} className="bg-black">
                {d.label}
              </option>
            ))
          )}
        </select>
        {wakeLastError ? <div className="mt-1 text-red-200">Wake err: {wakeLastError}</div> : null}
        {error ? <div className="mt-1 text-red-200">Err: {error}</div> : null}
      </div>

      <button
        type="button"
        onClick={handleMicClick}
        data-eeknova-assistant-ui="true"
        className="fixed bottom-6 right-6 z-[60] rounded-full border border-[var(--glass-stroke)] bg-[rgba(255,255,255,.06)] px-5 py-3 text-[14px] font-semibold text-[var(--brand-neo)] shadow-[0_0_14px_rgba(25,227,255,.35)] backdrop-blur-md transition-all hover:shadow-[0_0_18px_rgba(25,227,255,.55)] active:scale-[0.98]"
      >
        {micButtonLabel}
      </button>
    </>
  );
}
