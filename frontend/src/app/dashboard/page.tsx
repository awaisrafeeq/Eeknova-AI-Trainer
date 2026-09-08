'use client';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import Avatar3D from '@/components/Avatar3D';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import AuthGuard from '@/components/AuthGuard';
import { useAuthenticatedFetch } from '@/hooks/useAuth';
import { TTSFeedback } from '@/lib/yogaApi';

type CardStats = {
    progress: number;
    accuracy: number;
    calories: number;
    history: string;
};

type DashboardStats = {
    yoga: CardStats;
    zumba: CardStats;
    chess: CardStats;
};

const DASHBOARD_GREETING = 'Welcome to Eeknova. I am your AI trainer. Let us get started.';

export default function Page() {
    const router = useRouter();
    const authenticatedFetch = useAuthenticatedFetch();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loadingStats, setLoadingStats] = useState(false);
    const [isTTSSpeaking, setIsTTSSpeaking] = useState(false);
    const [ttsText, setTtsText] = useState('');
    const greetingTtsRef = useRef<TTSFeedback | null>(null);
    const greetingStartedRef = useRef(false);

    // Create this before the avatar's loader effect can fire, so the gesture
    // start callback can never miss its speech trigger.
    if (!greetingTtsRef.current) {
        greetingTtsRef.current = new TTSFeedback(setIsTTSSpeaking, setTtsText);
    }

    const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8002';

    const loadStats = useCallback(async () => {
        try {
            setLoadingStats(true);
            const meRes = await authenticatedFetch('/api/auth/me');
            if (!meRes.ok) return;
            const me = await meRes.json();
            const username = me?.username;
            if (!username) return;

            const statsRes = await authenticatedFetch(
                `${apiBaseUrl}/api/dashboard/${encodeURIComponent(username)}`
            );
            if (!statsRes.ok) return;
            const payload = await statsRes.json();
            if (payload?.success && payload?.data) {
                setStats(payload.data as DashboardStats);
            }
        } catch {
            // ignore
        } finally {
            setLoadingStats(false);
        }
    }, [authenticatedFetch]);

    useEffect(() => {
        void loadStats();
    }, [loadStats]);

    useEffect(() => {
        const tts = greetingTtsRef.current;
        if (!tts) return;
        void tts.prepare(DASHBOARD_GREETING);
        return () => tts.stop();
    }, []);

    useEffect(() => {
        const onFocus = () => void loadStats();
        const onVisibility = () => {
            if (document.visibilityState === 'visible') void loadStats();
        };
        window.addEventListener('focus', onFocus);
        document.addEventListener('visibilitychange', onVisibility);
        return () => {
            window.removeEventListener('focus', onFocus);
            document.removeEventListener('visibilitychange', onVisibility);
        };
    }, [loadStats]);

    const yoga = stats?.yoga ?? { progress: 0, accuracy: 0, calories: 0, history: loadingStats ? 'Loading…' : '—' };
    const zumba = stats?.zumba ?? { progress: 0, accuracy: 0, calories: 0, history: loadingStats ? 'Loading…' : '—' };
    const chess = stats?.chess ?? { progress: 0, accuracy: 0, calories: 0, history: loadingStats ? 'Loading…' : '—' };

    return (
        <AuthGuard>
            <main
                className="min-h-screen w-full overflow-hidden text-[var(--ink-hi)] content-center"
                style={{
                    background: 'var(--bg-gradient)',
                    fontFamily: 'var(--font-ui)',
                }}
            >
            <Particles />

            <div className="mx-auto max-w-[1280px]">
                <section className="relative grid grid-cols-12">
                    {/* Avatar Section */}
                    <div className="col-span-12 lg:col-span-7 xl:col-span-7 relative flex items-center justify-start">
                        <div
                            className="avatar-wrap relative h-[78vh] w-full overflow-visible"
                            style={{ background: 'transparent' }}
                        >
                            <Avatar3D
                                selectedPose=""
                                onlyInAnimation={false}
                                staticModelPath="/smile_greet_compressed.glb"
                                cameraManualDistanceFactor={1.29}
                                cameraManualTargetYOffsetFactor={0.08}
                                cameraManualTargetXOffsetFactor={-0.08}
                                lockCamera={true}
                                showGroundShadow={true}
                                isTTSSpeaking={isTTSSpeaking}
                                ttsText={ttsText}
                                useTextVisemes={true}
                                onAnimationStart={() => {
                                    if (greetingStartedRef.current) return;
                                    greetingStartedRef.current = true;
                                    greetingTtsRef.current?.speak(DASHBOARD_GREETING, true);
                                }}
                            />
                            {/* Fake shadow removed to stop float illusion */}
                        </div>
                    </div>

                    {/* Divider */}
                    <div className="hidden lg:block col-span-1 relative">
                        <div className="absolute inset-y-6 left-1/2 w-px -translate-x-1/2 bg-gradient-to-b from-[rgba(25,227,255,.0)] via-[rgba(25,227,255,.75)] to-[rgba(25,227,255,.0)] shadow-[0_0_16px_rgba(25,227,255,.65),0_0_48px_rgba(25,227,255,.28)]" />
                    </div>

                    {/* Dashboard Cards */}
                    <aside className="col-span-12 lg:col-span-4 xl:col-span-4 content-center lg:-ml-8 xl:-ml-10 lg:max-w-[390px]">
                        <div className="mb-6 relative">
                            <div className="flex items-center gap-4 mb-2">
                                <div className="h-39 w-39 rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] grid place-items-center shadow-[var(--glow-neo)]">
                                    <Image
                                        src="/logo.png"
                                        alt="Logo"
                                        width={64}
                                        height={64}
                                        className="h-29 w-29"
                                    />
                                </div>
                                <h1
                                    className="text-[44px] font-[700] leading-16 text-[var(--brand-neo)]"
                                    style={{ fontFamily: 'var(--font-future)' }}
                                >
                                    Eeknova
                                    <br />
                                    AITrainer
                                </h1>
                            </div>

                            <h2 className="text-[38px] font-bold leading-tight text-[var(--brand-neo)] mt-20">
                                Dashboard
                            </h2>
                        </div>

                        <div className="space-y-5">
                            <DashboardCard
                                title="Yoga"
                                progress={yoga.progress}
                                accuracy={yoga.accuracy}
                                calories={yoga.calories}
                                history={yoga.history}
                                href="/yoga"
                            />
                            <DashboardCard
                                title="Zumba"
                                progress={zumba.progress}
                                accuracy={zumba.accuracy}
                                calories={zumba.calories}
                                history={zumba.history}
                                href='/zumba'
                            />
                            <DashboardCard
                                title="Chess"
                                progress={chess.progress}
                                accuracy={chess.accuracy}
                                calories={chess.calories}
                                history={chess.history}
                                href='/chess'
                            />

                        </div>
                        {/* === Back Button === */}
                        <button
                            onClick={() => router.push('/module-selection')}
                            className="absolute top-0 left-0 px-4 py-2 rounded-[var(--radius-md)] border border-[var(--glass-stroke)] bg-[rgba(255,255,255,.06)] text-[var(--brand-neo)] font-semibold text-[16px] tracking-wide transition-all hover:shadow-[0_0_12px_rgba(25,227,255,.65)] hover:scale-105 active:scale-95"
                        >
                            ← Back
                        </button>
                    </aside>
                </section>
            </div>
        </main>
        </AuthGuard>
    );
}

/* ================= Dashboard Card Component ================= */
function DashboardCard({
    title,
    progress,
    accuracy,
    calories,
    history,
    href
}: {
    title: string;
    progress: number;
    accuracy: number;
    calories: number;
    history: string;
    href: string;
}) {
    const showCalories = title !== 'Chess';
    return (
        <Link href={href}>
        <div
            className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-5 btn-glass transition-all hover:shadow-[var(--glow-neo)]"
            style={{
                background:
                    'linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))',
            }}
        >
            <div className="flex items-center justify-between">
                <h3 className="text-[28px] font-semibold text-[var(--brand-neo)]">
                    {title}
                </h3>
                <span className="text-[22px] font-bold">{progress}%</span>
            </div>

            <div className="mt-2 w-full h-[6px] rounded-full bg-[rgba(255,255,255,.08)] overflow-hidden">
                <div
                    className="h-full rounded-full bg-[var(--brand-neo)] transition-all duration-500"
                    style={{ width: `${progress}%` }}
                />
            </div>

            <ul className="mt-3 space-y-1 text-[18px] text-[var(--ink-med)]">
                <li>
                    Accuracy <span className="float-right font-semibold">{accuracy}%</span>
                </li>
                {showCalories && (
                    <li>
                        Calories burned{' '}
                        <span className="float-right font-semibold">{calories} cl</span>
                    </li>
                )}
                <li>
                    Session history{' '}
                    <span className="float-right font-semibold">{history}</span>
                </li>
            </ul>
        </div>
        </Link>
    );
}

/* ================= Decorative Particles ================= */
function Particles() {
    return (
        <div
            aria-hidden
            className="particles pointer-events-none fixed inset-0 -z-10"
        >
            <div
                className="absolute left-[10%] top-[10%] h-[420px] w-[420px] rounded-full"
                style={{
                    background:
                        'radial-gradient(circle, rgba(25,227,255,.5), transparent 60%)',
                    animation: 'drift 48s ease-in-out infinite',
                }}
            />
            <div
                className="absolute right-[5%] top-[30%] h-[520px] w-[520px] rounded-full"
                style={{
                    background:
                        'radial-gradient(circle, rgba(106,93,255,.4), transparent 60%)',
                    animation: 'drift 56s ease-in-out infinite',
                }}
            />
        </div>
    );
}
