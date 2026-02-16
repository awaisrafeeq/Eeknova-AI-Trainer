import { NextResponse } from 'next/server';

type AssistantLanguage = 'auto' | 'en' | 'te' | 'hi' | 'ta' | 'kn';

function languageLabel(lang: AssistantLanguage): string {
  switch (lang) {
    case 'en':
      return 'English';
    case 'te':
      return 'Telugu';
    case 'hi':
      return 'Hindi';
    case 'ta':
      return 'Tamil';
    case 'kn':
      return 'Kannada';
    default:
      return 'English';
  }
}

export async function POST(req: Request) {
  try {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'OPENAI_API_KEY is not set' }, { status: 500 });
    }

    const body = (await req.json()) as { transcript?: string; language?: AssistantLanguage };
    const transcript = (body.transcript || '').trim();
    const language = (body.language || 'auto') as AssistantLanguage;

    if (!transcript) {
      return NextResponse.json({ error: 'Missing transcript' }, { status: 400 });
    }

    const systemRules = [
      'Reply in simple layman language.',
      'Use slow polite tone.',
      language === 'auto'
        ? 'If user requested a native language, reply in that language; else reply in English.'
        : `Reply in ${languageLabel(language)}.`,
    ].join(' ');

    const openaiRes = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        temperature: 0.6,
        messages: [
          { role: 'system', content: systemRules },
          { role: 'user', content: transcript },
        ],
      }),
    });

    if (!openaiRes.ok) {
      const errText = await openaiRes.text().catch(() => '');
      return NextResponse.json(
        { error: 'OpenAI assistant failed', details: errText },
        { status: openaiRes.status }
      );
    }

    const data = (await openaiRes.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };

    const reply = data.choices?.[0]?.message?.content?.trim() || '';

    return NextResponse.json({ reply });
  } catch (e) {
    return NextResponse.json({ error: 'Unexpected error' }, { status: 500 });
  }
}
