import { NextResponse } from 'next/server';

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

    const makeSpeechRequest = async (model: 'tts-1-hd' | 'tts-1') =>
      fetch('https://api.openai.com/v1/audio/speech', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model,
          voice: voice || 'nova',
          input: text,
          response_format: 'mp3',
          speed: 1.0,
        }),
      });

    let openaiRes = await makeSpeechRequest('tts-1-hd');

    // OpenAI TTS can intermittently return 5xx. Retry once on the same model first.
    if (openaiRes.status >= 500) {
      openaiRes = await makeSpeechRequest('tts-1-hd');
    }

    // If HD keeps failing server-side, fall back to the standard model.
    if (openaiRes.status >= 500) {
      openaiRes = await makeSpeechRequest('tts-1');
    }

    if (!openaiRes.ok) {
      const errText = await openaiRes.text().catch(() => '');
      return NextResponse.json(
        { error: 'OpenAI TTS failed', details: errText },
        { status: openaiRes.status }
      );
    }

    const audioBuffer = await openaiRes.arrayBuffer();

    return new Response(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Cache-Control': 'no-store',
      },
    });
  } catch (e) {
    return NextResponse.json({ error: 'Unexpected error' }, { status: 500 });
  }
}
