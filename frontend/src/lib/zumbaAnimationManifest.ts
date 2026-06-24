// Manifest + loader for the generated Zumba mapping JSON.
//
// The JSON file (public/zumba-mappings-18steps.json) is the single source of
// truth for move asset paths and timelines. This module loads it once, caches
// it, and exposes typed helpers. We intentionally do NOT hard-code GLB paths
// here to avoid drift between the converter output and the frontend.

import type {
  ZumbaMappingsJson,
  ZumbaMode,
  ZumbaMoveAsset,
  ZumbaMoveKey,
  ZumbaTimelineBlock,
} from './zumbaTimelineTypes';

export type { ZumbaMoveKey, ZumbaMode } from './zumbaTimelineTypes';

export const ZUMBA_MAPPING_URL = '/zumba-mappings-18steps.json';

let mappingPromise: Promise<ZumbaMappingsJson> | null = null;

export async function loadZumbaMappings(): Promise<ZumbaMappingsJson> {
  if (!mappingPromise) {
    mappingPromise = fetch(ZUMBA_MAPPING_URL)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Failed to load Zumba mappings: ${res.status} ${res.statusText}`);
        }
        return res.json() as Promise<ZumbaMappingsJson>;
      })
      .catch((err) => {
        // Reset so a later retry can succeed.
        mappingPromise = null;
        throw err;
      });
  }
  return mappingPromise;
}

export function getSongTitles(mapping: ZumbaMappingsJson): string[] {
  return Object.keys(mapping.songs);
}

export function getModesForSong(mapping: ZumbaMappingsJson, song: string): ZumbaMode[] {
  const songEntry = mapping.songs[song];
  if (!songEntry) return [];
  return mapping.modes.filter((m) => m in songEntry);
}

export function getSongAudio(mapping: ZumbaMappingsJson, song: string): string | undefined {
  return mapping.audio?.[song];
}

export function getTimeline(
  mapping: ZumbaMappingsJson,
  song: string,
  mode: ZumbaMode,
): ZumbaTimelineBlock[] {
  return mapping.songs[song]?.[mode] ?? [];
}

export function getMoveAsset(
  mapping: ZumbaMappingsJson,
  key: ZumbaMoveKey | string,
): ZumbaMoveAsset | undefined {
  return mapping.moves[key];
}

/** Unique move keys used by a timeline, in first-seen order. */
export function getUniqueMoveKeys(blocks: ZumbaTimelineBlock[]): ZumbaMoveKey[] {
  const seen = new Set<ZumbaMoveKey>();
  const out: ZumbaMoveKey[] = [];
  for (const b of blocks) {
    if (!seen.has(b.moveKey)) {
      seen.add(b.moveKey);
      out.push(b.moveKey);
    }
  }
  return out;
}

/** Map a frontend move key to the backend reference key (target_move). */
export function getBackendMoveKey(
  mapping: ZumbaMappingsJson,
  key: ZumbaMoveKey | string,
): string {
  return mapping.moves[key]?.backendKey ?? key;
}
