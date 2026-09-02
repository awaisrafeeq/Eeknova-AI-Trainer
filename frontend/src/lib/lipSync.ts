// Shared speech-shape model for every talking avatar in the app.
//
// Two things make this read as speech rather than a flapping jaw:
//
//  - Position through the line comes from the audio itself (elapsed / duration)
//    rather than an assumed speaking rate. A fixed rate drifts further out of
//    step the longer the sentence, so the mouth finishes before the voice does.
//  - Each shape eases into the following one instead of snapping. Real mouths
//    are already moving towards the next sound while finishing the current one,
//    and that overlap is most of what "natural" looks like.

export type TextViseme = {
  open: number;
  wide: number;
  round: number;
  close: number;
  lowerLip: number;
  energy: number;
};

export const IDLE_VISEME: TextViseme = {
  open: 0.26,
  wide: 0.08,
  round: 0.05,
  close: 0.08,
  lowerLip: 0,
  energy: 0.48,
};

const SPOKEN_DIGITS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'];

/**
 * Rewrites a line so its written length tracks how long it takes to say.
 * "Warrior 1" is nine characters but eleven sounds; without this the mouth runs
 * ahead of the voice from the first number onwards.
 */
function expandForSpeechShape(text: string): string {
  return text
    .toLowerCase()
    .replace(/[0-9]/g, (d) => ` ${SPOKEN_DIGITS[Number(d)]} `)
    .replace(/%/g, ' percent ')
    .replace(/&/g, ' and ')
    .replace(/\+/g, ' plus ')
    .replace(/°/g, ' degrees ')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

// The expansion runs once per line, not once per frame.
let cachedShapeSource = '';
let cachedShapeText = '';
export function speechShapeText(text: string): string {
  if (text === cachedShapeSource) return cachedShapeText;
  cachedShapeSource = text;
  cachedShapeText = expandForSpeechShape(text);
  return cachedShapeText;
}

/** Mouth shape for one sound, with no timing of its own. */
function visemeForChar(current: string, previous: string, next: string): TextViseme {
  if (/[\s,.;:!?]/.test(current)) {
    return { open: 0.02, wide: 0.01, round: 0.01, close: 0.68, lowerLip: 0, energy: 0.22 };
  }
  if ('mbp'.includes(current)) {
    return { open: 0.02, wide: 0.02, round: 0.02, close: 0.95, lowerLip: 0, energy: 0.35 };
  }
  if ('fv'.includes(current)) {
    return { open: 0.2, wide: 0.12, round: 0.02, close: 0.26, lowerLip: 0.72, energy: 0.62 };
  }
  if ('ouqw'.includes(current) || (current === 'o' && next === 'o')) {
    return { open: 0.34, wide: 0.02, round: 0.95, close: 0.02, lowerLip: 0.12, energy: 0.82 };
  }
  if ('ae'.includes(current)) {
    return { open: 0.78, wide: current === 'e' ? 0.48 : 0.28, round: 0.03, close: 0.01, lowerLip: 0.14, energy: 0.95 };
  }
  if ('iy'.includes(current)) {
    return { open: 0.34, wide: 0.92, round: 0.02, close: 0.02, lowerLip: 0.08, energy: 0.78 };
  }
  if ('lr'.includes(current)) {
    return { open: 0.4, wide: 0.22, round: previous === 'o' ? 0.42 : 0.12, close: 0.05, lowerLip: 0.08, energy: 0.72 };
  }
  if ('tdnszkgchj'.includes(current)) {
    return { open: 0.28, wide: 0.18, round: 0.03, close: 0.34, lowerLip: 0.03, energy: 0.62 };
  }
  return { open: 0.34, wide: 0.16, round: 0.08, close: 0.14, lowerLip: 0.05, energy: 0.66 };
}

export function mixViseme(a: TextViseme, b: TextViseme, t: number): TextViseme {
  return {
    open: a.open + (b.open - a.open) * t,
    wide: a.wide + (b.wide - a.wide) * t,
    round: a.round + (b.round - a.round) * t,
    close: a.close + (b.close - a.close) * t,
    lowerLip: a.lowerLip + (b.lowerLip - a.lowerLip) * t,
    energy: a.energy + (b.energy - a.energy) * t,
  };
}

/**
 * How far a mouth has already moved towards the following sound by the time it
 * finishes the current one. Real speech overlaps heavily - lips are rounding for
 * the "oo" while the tongue is still on the "t". Going the full way would smear
 * every sound into its neighbour, so it stops short.
 */
const COARTICULATION = 0.6;

/** Used only when the audio's duration is unknown (offline browser voice). */
const FALLBACK_CHARS_PER_SECOND = 13.5;

/** Mouth shape for a moment in a spoken line. */
export function getTextViseme(
  text: string | undefined,
  elapsedSeconds: number,
  durationSeconds: number,
): TextViseme {
  const sequence = speechShapeText(text || '');
  if (!sequence) return IDLE_VISEME;

  const count = sequence.length;
  const position = durationSeconds > 0
    ? Math.max(0, Math.min(1, elapsedSeconds / durationSeconds)) * count
    : elapsedSeconds * FALLBACK_CHARS_PER_SECOND;

  const index = Math.max(0, Math.min(count - 1, Math.floor(position)));
  const nextIndex = Math.min(count - 1, index + 1);
  const fraction = Math.max(0, Math.min(1, position - index));

  const current = visemeForChar(sequence[index] || '', sequence[index - 1] || '', sequence[index + 1] || '');
  if (nextIndex === index) return current;
  const upcoming = visemeForChar(sequence[nextIndex] || '', sequence[nextIndex - 1] || '', sequence[nextIndex + 1] || '');

  // Ease rather than ramp, so the shape settles into each sound before leaving it.
  const eased = fraction * fraction * (3 - 2 * fraction);
  return mixViseme(current, upcoming, eased * COARTICULATION);
}

/**
 * Frame-rate independent smoothing factor.
 *
 * A fixed per-frame lerp responds twice as fast at 120fps as at 60, so the same
 * face reads differently on different machines. `rate` is per second: the higher
 * it is, the quicker that articulator reaches its target.
 */
export function followFactor(rate: number, delta: number): number {
  return 1 - Math.exp(-rate * Math.max(0.0001, Math.min(0.1, delta)));
}

/**
 * Per-articulator response rates. These are what stop the mouth moving as one
 * rigid piece: the jaw is heavy and trails the lips, a p/b/m closure has to snap
 * shut, and an expression sits under the speech rather than flickering with it.
 */
export const LIP_SYNC_RATES = {
  jaw: 13,
  lips: 24,
  close: 38,
  expression: 9,
  /** A voice rises onto a syllable faster than it falls away from one. */
  envelopeAttack: 15,
  envelopeRelease: 7,
};
