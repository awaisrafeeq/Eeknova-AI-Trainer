'use client';

// Post-session Zumba result screen (AITrainer Zumba Post-Session Stats Guide,
// section 7). Simple and encouraging: top summary cards, body-part bars, a
// move-wise table, and exactly one clear improvement tip.

import React from 'react';
import type { ZumbaSessionSummary, ZumbaScores } from '@/lib/zumbaApi';

type ZumbaSummaryProps = {
  summary: ZumbaSessionSummary;
  songTitle?: string;
  mode?: string;
  userName?: string;
};

function formatDuration(totalSeconds: number): string {
  const s = Math.max(0, Math.round(totalSeconds));
  const minutes = Math.floor(s / 60);
  const seconds = s % 60;
  return `${minutes}:${String(seconds).padStart(2, '0')}`;
}

function formatCalories(calories: ZumbaScores['calories']): string {
  if (calories?.value != null) return `~${calories.value} kcal`;
  if (calories?.range) return `${calories.range[0]}-${calories.range[1]} kcal`;
  return '--';
}

function scoreTone(value: number | null | undefined): string {
  if (value == null) return 'text-[var(--ink-med)]';
  if (value >= 80) return 'text-green-400';
  if (value >= 60) return 'text-[var(--brand-neo)]';
  if (value >= 40) return 'text-yellow-400';
  return 'text-red-300';
}

export default function ZumbaSummary({ summary, songTitle, mode, userName }: ZumbaSummaryProps) {
  const scores = summary.scores ?? null;
  const song = summary.song_title || songTitle || '';
  const sessionMode = summary.mode || mode || '';

  // Legacy fallback: sessions without the analytics payload keep the old card.
  if (!scores) {
    return (
      <SummaryShell title="Session Summary">
        <ul className="space-y-1 text-[14px] text-[var(--ink-med)]">
          <li>
            Song<span className="float-right font-semibold text-white">{song || '--'}</span>
          </li>
          <li>
            Frames Processed
            <span className="float-right font-semibold">{summary.frames_processed}</span>
          </li>
          <li>
            Avg Accuracy
            <span className="float-right font-semibold text-[var(--brand-neo)]">
              {summary.average_accuracy.toFixed(1)}%
            </span>
          </li>
          <li>
            Feedback Count
            <span className="float-right font-semibold">{summary.feedback_count}</span>
          </li>
        </ul>
      </SummaryShell>
    );
  }

  const bodyParts: Array<{ label: string; value: number | null }> = [
    { label: 'Arms', value: scores.body_parts.arms },
    { label: 'Legs', value: scores.body_parts.legs },
    { label: 'Core', value: scores.body_parts.core },
    { label: 'Balance', value: scores.body_parts.balance },
    { label: 'Rhythm', value: scores.body_parts.rhythm },
  ];

  return (
    <SummaryShell title={`Great job${userName ? `, ${userName}` : ''}!`}>
      {/* Overall score hero */}
      <div className="mb-5 text-center">
        <div className="text-[52px] font-black leading-none text-[var(--brand-neo)]" style={{ fontFamily: 'var(--font-future)' }}>
          {scores.overall}
          <span className="text-[24px] font-bold text-[var(--ink-med)]"> / 100</span>
        </div>
        <div className="mt-1 text-[14px] text-[var(--ink-med)]">
          {song}{sessionMode ? ` - ${sessionMode}` : ''} · {formatDuration(summary.duration_seconds)}
        </div>
      </div>

      {/* Top summary cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Pose Accuracy" value={`${scores.pose_accuracy}%`} tone={scoreTone(scores.pose_accuracy)} />
        <StatCard label="Beat Sync" value={`${scores.beat_sync}%`} tone={scoreTone(scores.beat_sync)} />
        <StatCard label="Calories" value={formatCalories(scores.calories)} tone="text-[var(--brand-neo)]" />
        <StatCard label="Active Time" value={formatDuration(scores.active_time_seconds)} tone="text-white" />
        <StatCard label="Completion" value={`${scores.completion}%`} tone={scoreTone(scores.completion)} />
        <StatCard label="Energy" value={`${scores.energy}%`} tone={scoreTone(scores.energy)} />
        <StatCard label="Consistency" value={`${scores.consistency}%`} tone={scoreTone(scores.consistency)} />
        <StatCard
          label="Beats Matched"
          value={`${scores.beat_sync_detail.matched} / ${scores.beat_sync_detail.total}`}
          tone="text-white"
        />
      </div>

      {/* Best / Needs practice */}
      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-green-400/25 bg-green-400/5 px-4 py-3">
          <div className="text-[12px] uppercase tracking-wide text-green-400">Best Move</div>
          <div className="mt-1 text-[16px] font-semibold text-white">
            {scores.best_move ? `${scores.best_move.name} - ${scores.best_move.accuracy}%` : 'Not enough data'}
          </div>
        </div>
        <div className="rounded-lg border border-yellow-300/25 bg-yellow-300/5 px-4 py-3">
          <div className="text-[12px] uppercase tracking-wide text-yellow-300">Needs Practice</div>
          <div className="mt-1 text-[16px] font-semibold text-white">
            {scores.needs_practice
              ? `${scores.needs_practice.name} - ${scores.needs_practice.accuracy}%`
              : 'Nothing flagged - nice work!'}
          </div>
        </div>
      </div>

      {/* Body part bars */}
      <div className="mt-5">
        <h4 className="mb-2 text-[15px] font-semibold text-[var(--brand-neo)]">Body Focus</h4>
        <div className="space-y-2">
          {bodyParts.map(({ label, value }) => (
            <div key={label} className="flex items-center gap-3">
              <div className="w-[72px] shrink-0 text-[13px] text-[var(--ink-med)]">{label}</div>
              <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-[var(--brand-neo)] transition-all duration-500"
                  style={{ width: `${Math.max(0, Math.min(100, value ?? 0))}%` }}
                />
              </div>
              <div className={`w-[44px] shrink-0 text-right text-[13px] font-semibold ${scoreTone(value)}`}>
                {value != null ? `${value}%` : '--'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Move-wise breakdown */}
      {scores.moves.length > 0 && (
        <div className="mt-5">
          <h4 className="mb-2 text-[15px] font-semibold text-[var(--brand-neo)]">Move Breakdown</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-[13px]">
              <thead>
                <tr className="text-[var(--ink-med)]">
                  <th className="py-1.5 pr-3 font-medium">Move</th>
                  <th className="py-1.5 pr-3 font-medium">Accuracy</th>
                  <th className="py-1.5 pr-3 font-medium">Rhythm</th>
                  <th className="py-1.5 font-medium">Completion</th>
                </tr>
              </thead>
              <tbody>
                {scores.moves.map((move) => (
                  <tr key={move.key} className="border-t border-white/10">
                    <td className="py-1.5 pr-3 font-semibold text-white">{move.name}</td>
                    <td className={`py-1.5 pr-3 font-semibold ${scoreTone(move.accuracy)}`}>
                      {move.accuracy != null ? `${move.accuracy}%` : '--'}
                    </td>
                    <td className={`py-1.5 pr-3 ${scoreTone(move.rhythm)}`}>
                      {move.rhythm != null ? `${move.rhythm}%` : '--'}
                    </td>
                    <td className="py-1.5">{move.completion}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* One clear improvement tip */}
      <div className="mt-5 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] px-4 py-3">
        <div className="text-[12px] uppercase tracking-wide text-[var(--brand-neo)]">Tip</div>
        <div className="mt-1 text-[14px] leading-relaxed text-white">{scores.tip}</div>
      </div>
    </SummaryShell>
  );
}

function SummaryShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-5 btn-glass"
      style={{
        background: 'linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02))',
      }}
    >
      <h3 className="mb-3 text-[22px] font-semibold text-[var(--brand-neo)]">{title}</h3>
      {children}
    </div>
  );
}

function StatCard({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] px-3 py-2.5">
      <div className="text-[11px] uppercase tracking-wide text-[var(--ink-med)]">{label}</div>
      <div className={`mt-0.5 text-[18px] font-bold ${tone}`}>{value}</div>
    </div>
  );
}
