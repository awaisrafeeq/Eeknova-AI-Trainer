import { NextResponse } from 'next/server';

type AssistantLanguage = 'auto' | 'en' | 'te' | 'hi' | 'ta' | 'kn';

function mapLanguage(lang: unknown): string | null {
  if (typeof lang !== 'string') return null;
  const v = lang as AssistantLanguage;
  if (v === 'auto') return null;
  if (v === 'en') return 'en';
  if (v === 'hi') return 'hi';
  if (v === 'te') return 'te';
  if (v === 'ta') return 'ta';
  // If unsupported by the STT backend, just omit language to let it auto-detect
  if (v === 'kn') return null;
  return null;
}

export async function POST(req: Request) {
  try {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'OPENAI_API_KEY is not set' }, { status: 500 });
    }

    const formData = await req.formData();
    const file = formData.get('file');
    const language = formData.get('language');

    if (!(file instanceof Blob)) {
      return NextResponse.json({ error: 'Missing audio file' }, { status: 400 });
    }

    const openAiForm = new FormData();
    // Use whisper-1 for maximum compatibility
    openAiForm.append('model', 'whisper-1');
    openAiForm.append('file', file, 'audio.webm');
    const mappedLang = mapLanguage(language);
    if (mappedLang) openAiForm.append('language', mappedLang);

    const openaiRes = await fetch('https://api.openai.com/v1/audio/transcriptions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
      body: openAiForm,
    });

    if (!openaiRes.ok) {
      const errText = await openaiRes.text().catch(() => '');
      return NextResponse.json(
        { error: 'OpenAI STT failed', details: errText },
        { status: openaiRes.status }
      );
    }

    const data = (await openaiRes.json()) as { text?: string };

    return NextResponse.json({ text: data.text || '' });
  } catch (e) {
    console.error('STT route unexpected error:', e);
    return NextResponse.json(
      { error: 'Unexpected error', details: e instanceof Error ? e.message : String(e) },
      { status: 500 }
    );
  }
}
