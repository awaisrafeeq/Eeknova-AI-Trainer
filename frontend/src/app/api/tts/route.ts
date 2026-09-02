import { NextResponse } from 'next/server';

type CacheEntry = { bytes: Uint8Array };

type TtsCache = {
  map: Map<string, CacheEntry>;
  bytes: number;
};

// Yoga/chess coaching lines repeat every single session, and pose corrections
// repeat many times inside one session. Regenerating them costs a full OpenAI
// round-trip each time, which is what made the voice land long after the
// subtitle/animation. Keep the rendered audio in memory so a repeat is instant.
// Lives on globalThis so Next's dev-mode module reloads don't drop it.
const MAX_CACHE_ENTRIES = 400;
const MAX_CACHE_BYTES = 64 * 1024 * 1024;

const globalForTts = globalThis as typeof globalThis & { __ttsCache?: TtsCache };
const cache: TtsCache = (globalForTts.__ttsCache ??= { map: new Map(), bytes: 0 });

function cacheGet(key: string): Uint8Array | null {
  const hit = cache.map.get(key);
  if (!hit) return null;
  // Refresh recency.
  cache.map.delete(key);
  cache.map.set(key, hit);
  return hit.bytes;
}

function cacheSet(key: string, bytes: Uint8Array): void {
  if (bytes.byteLength === 0) return;
  const existing = cache.map.get(key);
  if (existing) {
    cache.bytes -= existing.bytes.byteLength;
    cache.map.delete(key);
  }
  cache.map.set(key, { bytes });
  cache.bytes += bytes.byteLength;

  while (cache.map.size > MAX_CACHE_ENTRIES || cache.bytes > MAX_CACHE_BYTES) {
    const oldestKey = cache.map.keys().next().value;
    if (oldestKey === undefined) break;
    const oldest = cache.map.get(oldestKey);
    cache.map.delete(oldestKey);
    if (oldest) cache.bytes -= oldest.bytes.byteLength;
  }
}

export async function POST(req: Request) {
  try {
    const { text, voice } = (await req.json()) as { text?: string; voice?: string };

    if (!text || typeof text !== 'string') {
      return NextResponse.json({ error: 'Missing text' }, { status: 400 });
    }

    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'OPENAI_API_KEY is not set' }, { status: 500 });
    }

    const resolvedVoice = voice || 'nova';
    const normalizedText = text.replace(/\s+/g, ' ').trim();
    const cacheKey = `${resolvedVoice}:${normalizedText}`;

    const cached = cacheGet(cacheKey);
    if (cached) {
      return new Response(cached.slice().buffer as ArrayBuffer, {
        headers: {
          'Content-Type': 'audio/mpeg',
          'Content-Length': String(cached.byteLength),
          'Cache-Control': 'no-store',
          'X-TTS-Cache': 'hit',
        },
      });
    }

    // `tts-1` is the low-latency model. `tts-1-hd` sounds marginally richer but
    // takes roughly twice as long to generate, which is far too slow for live
    // coaching cues that have to land in step with the avatar.
    const makeSpeechRequest = async (model: 'tts-1' | 'tts-1-hd') =>
      fetch('https://api.openai.com/v1/audio/speech', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model,
          voice: resolvedVoice,
          input: text,
          response_format: 'mp3',
          speed: 1.0,
        }),
      });

    let openaiRes = await makeSpeechRequest('tts-1');

    // OpenAI TTS can intermittently return 5xx. Retry once on the same model first.
    if (openaiRes.status >= 500) {
      openaiRes = await makeSpeechRequest('tts-1');
    }

    // If the fast model keeps failing server-side, fall back to HD.
    if (openaiRes.status >= 500) {
      openaiRes = await makeSpeechRequest('tts-1-hd');
    }

    if (!openaiRes.ok) {
      const errText = await openaiRes.text().catch(() => '');
      return NextResponse.json(
        { error: 'OpenAI TTS failed', details: errText },
        { status: openaiRes.status }
      );
    }

    if (!openaiRes.body) {
      const audioBuffer = await openaiRes.arrayBuffer();
      cacheSet(cacheKey, new Uint8Array(audioBuffer));
      return new Response(audioBuffer, {
        headers: {
          'Content-Type': 'audio/mpeg',
          'Cache-Control': 'no-store',
          'X-TTS-Cache': 'miss',
        },
      });
    }

    // Forward bytes to the browser as OpenAI produces them instead of buffering
    // the whole file here first, and fill the cache off the second branch.
    const [toClient, toCache] = openaiRes.body.tee();

    void (async () => {
      try {
        const chunks: Uint8Array[] = [];
        let total = 0;
        const reader = toCache.getReader();
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value) {
            chunks.push(value);
            total += value.byteLength;
          }
        }
        const merged = new Uint8Array(total);
        let offset = 0;
        for (const chunk of chunks) {
          merged.set(chunk, offset);
          offset += chunk.byteLength;
        }
        cacheSet(cacheKey, merged);
      } catch {
        // A failed cache fill must never affect the response already in flight.
      }
    })();

    return new Response(toClient, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Cache-Control': 'no-store',
        'X-TTS-Cache': 'miss',
      },
    });
  } catch {
    return NextResponse.json({ error: 'Unexpected error' }, { status: 500 });
  }
}
