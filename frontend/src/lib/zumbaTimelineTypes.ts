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
};

export type ZumbaMappingsJson = {
  version: string;
  generatedAt: string;
  modes: ZumbaMode[];
  moves: Record<string, ZumbaMoveAsset>;
  /** One audio track per song title. */
  audio: Record<string, string>;
  songs: Record<string, Record<string, ZumbaTimelineBlock[]>>;
};

export type ZumbaPreloadStatus = {
  state: 'idle' | 'loading' | 'ready' | 'error';
  total: number;
  loaded: number;
  failed: string[];
};
