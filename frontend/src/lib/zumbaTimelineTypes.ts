// Types for the generated Zumba 18-step timeline JSON.
// Source of truth is scripts/build_zumba_mapping_json.py which writes
// frontend/public/zumba-mappings-18steps.json.

export type ZumbaMode = 'Beginner' | 'Easy' | 'Moderate' | 'High' | 'HIIT';

export type ZumbaMoveKey =
  | 'body_rolls'
  | 'cumbia_step'
  | 'grape_vine'
  | 'heel_taps'
  | 'jumping_jacks'
  | 'knee_lifts'
  | 'lunge_with_punches'
  | 'mambo'
  | 'march_in_place'
  | 'merengue_march'
  | 'reggaeton_stomp'
  | 'shimmy'
  | 'side_punches'
  | 'squat_with_clap'
  | 'step_clap'
  | 'step_touch'
  | 'twist_step'
  | 'zumba_turn_pivot';

export type ZumbaMoveAsset = {
  id: number;
  key: ZumbaMoveKey;
  /** Key the backend's reference_angles expects as `target_move`. */
  backendKey: string;
  name: string;
  folder: string;
  in: string;
  main: string;
  out: string;
};

export type ZumbaTimelineBlock = {
  songTitle: string;
  artist: string;
  mode: ZumbaMode;
  bpm: number;
  blockSizeCounts: number;
  startMs: number;
  endMs: number;
  durationMs: number;
  moveGroupIndex: number;
  moveGroupLengthBlocks: number;
  moveId: number;
  moveKey: ZumbaMoveKey;
  moveName: string;
  side: 'L' | 'R' | null;
  coachCue: string;
  /** Present only on client-corrected (beat-aligned) timelines. */
  glbMainDurationSec?: number;
  plannedLoops?: number;
  /** Playback speed multiplier so the Main loop fits the beat window exactly. */
  animationSpeedScale?: number;
};

/** Beat-alignment metadata for one song/mode timeline (from the corrected sheet). */
export type ZumbaTimelineMeta = {
  /** True when this timeline came from a client-corrected beat-aligned sheet. */
  corrected: boolean;
  /** Where the song's count 1 actually lands (ms). 0 for uncorrected timelines. */
  beatPhaseOffsetMs: number;
  /** End of the "hold/ready" lead-in before the first main move. */
  leadInEndMs: number | null;
  /** Audio tail after the last full 8-count block: play Idle Out here. */
  outroStartMs: number | null;
  outroEndMs: number | null;
};

export type ZumbaMappingsJson = {
  version: string;
  generatedAt: string;
  modes: ZumbaMode[];
  moves: Record<string, ZumbaMoveAsset>;
  /** One audio track per song title. */
  audio: Record<string, string>;
  /** Beat-alignment meta per song title per mode. */
  timelineMeta: Record<string, Record<string, ZumbaTimelineMeta>>;
  songs: Record<string, Record<string, ZumbaTimelineBlock[]>>;
};

export type ZumbaPreloadStatus = {
  state: 'idle' | 'loading' | 'ready' | 'error';
  total: number;
  loaded: number;
  failed: string[];
};
