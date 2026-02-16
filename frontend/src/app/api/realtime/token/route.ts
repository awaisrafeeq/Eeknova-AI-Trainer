import { NextResponse } from 'next/server';

const REALTIME_VOICES = new Set([
  'alloy',
  'ash',
  'ballad',
  'coral',
  'echo',
  'sage',
  'shimmer',
  'verse',
  'marin',
  'cedar',
]);

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function POST(req: Request) {
  try {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'OPENAI_API_KEY is not set' }, { status: 500 });
    }

    const body = (await req.json().catch(() => ({}))) as { model?: string; voice?: string };
    const cheapDefaultModel = 'gpt-4o-mini-realtime-preview';
    const fallbackModel = 'gpt-4o-realtime-preview';
    let model = body.model || cheapDefaultModel;
    const requestedVoice = body.voice || 'alloy';
    const voice = REALTIME_VOICES.has(requestedVoice) ? requestedVoice : 'alloy';

    const maxAttempts = 3;
    let openaiRes: Response | null = null;
    let lastDetails = '';
    let lastFetchError: string | null = null;
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        openaiRes = await fetch('https://api.openai.com/v1/realtime/sessions', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model,
            voice,
          }),
        });
        lastFetchError = null;
      } catch (e) {
        openaiRes = null;
        lastFetchError = e instanceof Error ? e.message : String(e);
        const isLast = attempt === maxAttempts;
        console.error('Realtime session create fetch failed', {
          attempt,
          maxAttempts,
          model,
          voice,
          error: lastFetchError,
        });
        if (isLast) break;
        const backoffMs = 250 * Math.pow(2, attempt - 1);
        await sleep(backoffMs);
        continue;
      }

      if (openaiRes.ok) break;

      lastDetails = await openaiRes.text().catch(() => '');

      // If the cheaper model isn't available for this account/region, fall back once.
      if (
        openaiRes.status >= 400 &&
        openaiRes.status < 500 &&
        model === cheapDefaultModel &&
        /invalid_model|model_not_found|unsupported_model/i.test(lastDetails)
      ) {
        console.error('Realtime model not available; falling back', {
          fromModel: model,
          toModel: fallbackModel,
          status: openaiRes.status,
          details: lastDetails,
        });
        model = fallbackModel;
        continue;
      }

      const retryable = openaiRes.status === 429 || openaiRes.status >= 500;
      const isLast = attempt === maxAttempts;

      console.error('Realtime session create failed', {
        attempt,
        maxAttempts,
        status: openaiRes.status,
        statusText: openaiRes.statusText,
        model,
        voice,
        details: lastDetails,
        retryable,
      });

      if (!retryable || isLast) break;

      const backoffMs = 250 * Math.pow(2, attempt - 1);
      await sleep(backoffMs);
    }

    if (!openaiRes) {
      return NextResponse.json(
        {
          error: 'Failed to create realtime session',
          details:
            lastFetchError ||
            'Network error reaching api.openai.com (check DNS/proxy/firewall/internet).',
        },
        { status: 500 }
      );
    }

    if (!openaiRes.ok) {
      const details = lastDetails || (await openaiRes.text().catch(() => ''));
      return NextResponse.json(
        {
          error: 'Failed to create realtime session',
          status: openaiRes.status,
          statusText: openaiRes.statusText,
          details,
        },
        { status: openaiRes.status }
      );
    }

    let data: { client_secret?: { value?: string } } | null = null;
    try {
      data = (await openaiRes.json()) as { client_secret?: { value?: string } };
    } catch (e) {
      const raw = await openaiRes.text().catch(() => '');
      console.error('Realtime session create JSON parse failed', {
        model,
        voice,
        raw,
        error: e instanceof Error ? e.message : String(e),
      });
      return NextResponse.json(
        { error: 'Invalid JSON from OpenAI', details: raw },
        { status: 500 }
      );
    }

    const token = data.client_secret?.value;
    if (!token) {
      console.error('Realtime session create missing client_secret', { model, voice, data });
      return NextResponse.json({ error: 'Missing client_secret in response' }, { status: 500 });
    }

    return NextResponse.json({ token, model });
  } catch (e) {
    console.error('Realtime token route unexpected error', e);
    return NextResponse.json(
      { error: 'Unexpected error', details: e instanceof Error ? e.message : String(e) },
      { status: 500 }
    );
  }
}
