'use client';
import React, { useCallback, useEffect, useState } from 'react';
import Avatar3D from '@/components/Avatar3D';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import AuthGuard from '@/components/AuthGuard';
import { useAuthenticatedFetch } from '@/hooks/useAuth';

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

export default function Page() {
    const router = useRouter();
    const authenticatedFetch = useAuthenticatedFetch();
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loadingStats, setLoadingStats] = useState(false);

    const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8000';

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

            <div className="mx-auto max-w-[1080px] px-6 md:px-8 py-6 md:py-8">
                <section className="relative grid grid-cols-12 gap-4 md:gap-6">
                    {/* Avatar Section */}
                    <div className="col-span-12 lg:col-span-5 xl:col-span-5 relative">
                        <div
                            className="avatar-wrap relative h-[72vh] rounded-[var(--radius-lg)] border border-[var(--glass-stroke)]"
                            style={{
                                background:
                                    'linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02))',
                                backdropFilter: 'blur(12px)',
                            }}
                        >
                            <Avatar3D selectedPose="" onlyInAnimation={false} staticModelPath="/smile & greet_compressed.glb" />
                            <div
                                className="pointer-events-none absolute left-1/2 -translate-x-1/2 bottom-[42px] h-[18px] w-[60%]"
                                style={{
                                    filter: 'blur(10px)',
                                    background:
                                        'radial-gradient(closest-side, rgba(25,227,255,.35), transparent)',
                                }}
                            />
                        </div>
                    </div>

                    {/* Divider */}
                    <div className="hidden lg:block col-span-1 relative">
                        <div className="absolute inset-y-6 left-1/2 w-px -translate-x-1/2 bg-gradient-to-b from-[rgba(25,227,255,.0)] via-[rgba(25,227,255,.75)] to-[rgba(25,227,255,.0)] shadow-[0_0_16px_rgba(25,227,255,.65),0_0_48px_rgba(25,227,255,.28)]" />
                    </div>

                    {/* Dashboard Cards */}
                    <aside className="col-span-12 lg:col-span-6 xl:col-span-6 content-center">
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
                            onClick={() => router.back()}
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
