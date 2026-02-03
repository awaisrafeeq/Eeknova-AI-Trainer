'use client';
import Image from 'next/image';
import React, { useState, useEffect } from 'react';
import Avatar3D from '@/components/Avatar3D';
import Walktour from '@/components/Walktour';
import AuthGuard from '@/components/AuthGuard';

export default function Page() {
    const [showWalktour, setShowWalktour] = useState(false);
    const [selectedPose, setSelectedPose] = useState('');

    useEffect(() => {
        console.log('Walktour useEffect triggered');

        // Check if it's the first visit for this user
        const token = localStorage.getItem('access_token');
        console.log('Token found:', !!token);

        if (token) {
            try {
                // Get username from token (simple parsing)
                const payload = JSON.parse(atob(token.split('.')[1]));
                const username = payload.sub;
                const walktourKey = `walktour-seen-${username}`;

                console.log('Username:', username);
                console.log('Walktour key:', walktourKey);

                const hasSeenWalktour = localStorage.getItem(walktourKey);
                console.log('Has seen walktour:', hasSeenWalktour);

                if (!hasSeenWalktour) {
                    console.log('Starting walktour in 1.5 seconds...');
                    // Add a small delay to ensure page is fully loaded
                    const timer = setTimeout(() => {
                        console.log('Setting showWalktour to true');
                        setShowWalktour(true);
                    }, 1500); // 1.5 second delay for better UX
                    return () => clearTimeout(timer);
                }
            } catch (error) {
                console.error('Error parsing token:', error);
                // Fallback to generic walktour
                const hasSeenWalktour = localStorage.getItem('walktour-seen');
                console.log('Fallback - Has seen walktour:', hasSeenWalktour);
                if (!hasSeenWalktour) {
                    console.log('Starting fallback walktour in 1.5 seconds...');
                    const timer = setTimeout(() => {
                        console.log('Setting showWalktour to true (fallback)');
                        setShowWalktour(true);
                    }, 1500);
                    return () => clearTimeout(timer);
                }
            }
        } else {
            console.log('No token found, checking generic walktour');
            // For testing - also check generic walktour
            const hasSeenWalktour = localStorage.getItem('walktour-seen');
            if (!hasSeenWalktour) {
                console.log('Starting generic walktour in 1.5 seconds...');
                const timer = setTimeout(() => {
                    console.log('Setting showWalktour to true (generic)');
                    setShowWalktour(true);
                }, 1500);
                return () => clearTimeout(timer);
            }
        }
    }, []);

    const handleWalktourComplete = () => {
        setShowWalktour(false);
        // Mark walktour as seen for this specific user
        const token = localStorage.getItem('access_token');
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split('.')[1]));
                const username = payload.sub;
                const walktourKey = `walktour-seen-${username}`;
                localStorage.setItem(walktourKey, 'true');
            } catch (error) {
                console.error('Error parsing token:', error);
                // Fallback to generic walktour
                localStorage.setItem('walktour-seen', 'true');
            }
        }
    };

    const startWalktour = () => {
        console.log('Manual walktour triggered');
        setShowWalktour(true);
    };

    // For testing - add keyboard shortcut
    useEffect(() => {
        const handleKeyPress = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                console.log('Keyboard shortcut triggered');
                startWalktour();
            }
        };

        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, []);
    const [userProfile, setUserProfile] = useState<{ full_name?: string, username?: string }>({});
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        const fetchProfile = async () => {
            const token = localStorage.getItem('access_token');
            if (!token) return;
            try {
                const response = await fetch('http://localhost:8000/api/auth/me', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    setUserProfile(data);
                }
            } catch (e) { console.error(e); }
        };
        fetchProfile();
    }, []);

    if (!mounted) return null;

    return (
        <AuthGuard>
            <main
                className="min-h-screen w-full overflow-hidden text-[var(--ink-hi)] content-center"
                style={{ background: 'var(--bg-gradient)', fontFamily: 'var(--font-ui)' }}
            >
                <Particles />

                <div className="mx-auto max-w-[1080px] px-6 md:px-8 py-6 md:py-8">
                    <section className="relative grid grid-cols-12 gap-4 md:gap-6">
                        <div className="col-span-12 lg:col-span-5 xl:col-span-5 relative">
                            <div className="avatar-wrap relative h-[72vh] rounded-[var(--radius-lg)] border border-[var(--glass-stroke)]" data-walktour="avatar" style={{ background: 'linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02))', backdropFilter: 'blur(12px)' }}>
                                <Avatar3D selectedPose="Mountain Pose" onlyInAnimation={false} />
                                <div className="pointer-events-none absolute left-1/2 -translate-x-1/2 bottom-[42px] h-[18px] w-[60%]" style={{ filter: 'blur(10px)', background: 'radial-gradient(closest-side, rgba(25,227,255,.35), transparent)' }} />
                            </div>
                        </div>

                        <div className="hidden lg:block col-span-1 relative">
                            <div className="absolute inset-y-6 left-1/2 w-px -translate-x-1/2 bg-gradient-to-b from-[rgba(25,227,255,.0)] via-[rgba(25,227,255,.75)] to-[rgba(25,227,255,.0)] shadow-[0_0_16px_rgba(25,227,255,.65),0_0_48px_rgba(25,227,255,.28)]" />
                        </div>

                        <aside className="col-span-12 lg:col-span-6 xl:col-span-6 content-center">
                            <div className="flex items-center gap-4 mb-6">
                                <div className="h-39 w-39 rounded-full border border-[var(--glass-stroke)] bg-[var(--glass)] grid place-items-center shadow-[var(--glow-neo)]">
                                    <RunnerBadge />
                                </div>
                                <div>
                                    <div className="font-[700] text-[44px] leading-16 text-[var(--brand-neo)]" style={{ fontFamily: 'var(--font-future)' }}>Eeknova<br />AITrainer</div>
                                </div>
                            </div>

                            <h2 className="text-[42px] font-bold leading-tight">
                                Welcome back, {userProfile.full_name || userProfile.username || 'Friend'}!
                            </h2>
                            <p className="mt-1 text-[24px] text-[var(--ink-med)]">Continue your progress</p>

                            <div className="mt-6 space-y-4">
                                <MenuCard label="Yoga" icon={<YogaIcon />} href="/yoga" data-walktour="yoga-module" />
                                <MenuCard label="Zumba" icon={<ZumbaIcon />} href="/zumba" data-walktour="zumba-module" />
                                <MenuCard label="Chess" icon={<ChessIcon />} href="/chess" data-walktour="chess-module" />
                                <MenuCard label="Dashboard" icon={<UserIcon />} href="/dashboard" data-walktour="dashboard-module" />
                                <MenuCard label="Settings" icon={<CogIcon />} href="/settings" data-walktour="settings-module" />
                            </div>

                            {/* Walktour trigger button */}
                            <div className="mt-4">
                                <button
                                    onClick={startWalktour}
                                    className="text-sm text-blue-400 hover:text-blue-300 transition-colors underline"
                                >
                                    🎯 Take a tour of all modules (or press Ctrl+Shift+T)
                                </button>
                            </div>
                        </aside>
                    </section>

                    {/* Bottom action bar (kept for system consistency; can be hidden on this screen) */}
                    {/* <footer className="mt-8 h-[96px] flex gap-4 items-center">
                    <CTA variant="secondary">Pause</CTA>
                    <CTA variant="primary">Next Pose</CTA>
                    <CTA variant="danger">End Session</CTA>
                </footer> */}
                </div>

                {/* Walktour Component */}
                <Walktour
                    isActive={showWalktour}
                    onComplete={handleWalktourComplete}
                />

                {/* Global CSS variables + animations */}
                {/* <style jsx global>{`
        </style> */}
            </main >
        </AuthGuard >
    );
}

/* ===================== UI Primitives ===================== */
function IconButton({ children, label, active }: { children: React.ReactNode; label: string; active?: boolean }) {
    return (
        <button aria-label={label} title={label} className={`w-[44px] h-[44px] rounded-[12px] border flex items-center justify-center transition-all active:translate-y-px ${active ? 'btn-glow' : ''}`} style={{ borderColor: 'var(--glass-stroke)', background: 'var(--glass)' }}>
            <span className="sr-only">{label}</span>
            <span className="[&>svg]:h-[22px] [&>svg]:w-[22px] [&>svg]:stroke-[#BFEFFF]">{children}</span>
        </button>
    );
}

function MenuCard({ label, icon, href, ...props }: { label: string; icon: React.ReactNode; href?: string;[key: string]: any }) {
    return (
        <a href={href || '#'} className="group block rounded-[var(--radius-lg)] border btn-glass transition-all hover:shadow-[var(--glow-neo)] active:translate-y-px" style={{ borderColor: 'var(--glass-stroke)' }} {...props}>
            <div className="flex items-center justify-between px-4 py-6">
                <div className="flex items-center gap-6">
                    <div className="h-16 w-16 grid place-items-center rounded-lg border" style={{ borderColor: 'var(--glass-stroke)', background: 'rgba(255,255,255,.04)' }}>
                        <span className="[&>svg]:h-12 [&>svg]:w-12 [&>svg]:stroke-[var(--brand-neo)]">{icon}</span>
                    </div>
                    <span className="text-[36px] font-semibold">{label}</span>
                </div>
                <ChevronRight />
            </div>
        </a>
    );
}

function CTA({ children, variant }: { children: React.ReactNode; variant: 'primary' | 'secondary' | 'danger' }) {
    const base = 'flex-1 h-16 rounded-[16px] font-bold tracking-[.2px] border btn-glass transition-all active:translate-y-px';
    const styles = {
        primary: base + ' btn-glow',
        secondary: base,
        danger: base + ' border-[#FF5C7A66]'
    } as const;
    return <button className={styles[variant]} style={{ borderColor: 'var(--glass-stroke)' }}>{children}</button>;
}

/* ===================== Icons (inline SVG, no deps) ===================== */
function UserIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21a8 8 0 0 0-16 0" /><circle cx="12" cy="7" r="4" /></svg>
    )
}
function CogIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06c.46-.46.6-1.14.33-1.82a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09c.68 0 1.28-.39 1.51-1 .27-.68.13-1.36-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06c.46.46 1.14.6 1.82.33.61-.23 1-.83 1-1.51V3a2 2 0 1 1 4 0v.09c0 .68.39 1.28 1 1.51.68.27 1.36.13 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06c-.46.46-.6 1.14-.33 1.82.23.61.83 1 1.51 1H21a2 2 0 1 1 0 4h-.09c-.68 0-1.28.39-1.51 1Z" /></svg>
    )
}
function PowerIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v10" /><path d="M5.5 6.5a7 7 0 1 0 13 0" /></svg>
    )
}
function ChevronRight() {
    return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5 opacity-80 group-hover:translate-x-0.5 transition-transform"><path d="M9 18l6-6-6-6" /></svg>
    )
}
function YogaIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z" /><path d="M5 21l3-6 2-2" /><path d="M19 21l-3-6-2-2" /><path d="M12 7v4" /><path d="M6 12h12" /></svg>
    )
}
function ZumbaIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="4" r="2" /><path d="M12 6v4l3 3" /><path d="M9 12l-4 2" /><path d="M12 13l0 7" /></svg>
    )
}
function ChessIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 20h12" /><path d="M8 17h8l-1-5 2-2-3-1-2-3-2 3-3 1 2 2-1 5Z" /></svg>
    )
}
function RunnerBadge() {
    return (
        <Image src="/logo.png" alt="Runner Badge" width={64} height={64} className="h-29 w-29" />
    )
}

/* =============== Decorative Particles Layer =============== */
function Particles() {
    return (
        <div aria-hidden className="particles pointer-events-none fixed inset-0 -z-10">
            {/* two slow-drifting blobs */}
            <div className="absolute left-[10%] top-[10%] h-[420px] w-[420px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(25,227,255,.5), transparent 60%)', animation: 'drift 48s ease-in-out infinite' }} />
            <div className="absolute right-[5%] top-[30%] h-[520px] w-[520px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(106,93,255,.4), transparent 60%)', animation: 'drift 56s ease-in-out infinite' }} />
        </div>
    );
}
