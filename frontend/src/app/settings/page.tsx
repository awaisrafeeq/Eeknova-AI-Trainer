'use client';
import React, { useState, useEffect } from 'react';
import { CogIcon } from '@/components/Icons';
import AuthGuard from '@/components/AuthGuard';

interface UserProfile {
  username: string;
  email: string;
  full_name?: string;
  age?: number;
  height?: number;
  weight?: number;
  fitness_level?: string;
  preferences?: Record<string, any>;
}

export default function SettingsPage() {
  const [profile, setProfile] = useState<UserProfile>({
    username: '',
    email: '',
    full_name: '',
    age: undefined,
    height: undefined,
    weight: undefined,
    fitness_level: 'beginner',
    preferences: {}
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setMessage('Please login to view your profile');
        setIsLoading(false);
        return;
      }

      const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProfile(data);
      } else {
        setMessage('Failed to load profile');
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
      setMessage('Error loading profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage('');

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setMessage('Please login to update your profile');
        setIsSaving(false);
        return;
      }

      const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/api/auth/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profile)
      });

      if (response.ok) {
        setMessage('Profile updated successfully!');
      } else {
        setMessage('Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      setMessage('Error updating profile');
    } finally {
      setIsSaving(false);
    }
  };

  const resetWalktour = () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const username = payload.sub;
        const walktourKey = `walktour-seen-${username}`;
        localStorage.removeItem(walktourKey);
        setMessage('Walktour reset! You will see it on your next visit to the main page.');
      } catch (error) {
        console.error('Error parsing token:', error);
        localStorage.removeItem('walktour-seen');
        setMessage('Walktour reset! You will see it on your next visit to the main page.');
      }
    }
  };

  const handleInputChange = (field: keyof UserProfile, value: any) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-white">Loading profile...</div>
      </div>
    );
  }

  if (!mounted) return null;

  return (
    <AuthGuard>
      <main
        className="min-h-screen w-full overflow-hidden text-[var(--ink-hi)]"
        style={{ background: 'var(--bg-gradient)', fontFamily: 'var(--font-ui)' }}
      >
        <div className="mx-auto max-w-[1080px] px-6 md:px-8 py-6 md:py-8">
          {/* ... (rest of header) ... */}
          {/* Profile Form */}
          <div className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-8" style={{ background: 'rgba(255,255,255,.02)', backdropFilter: 'blur(12px)' }}>
            <form onSubmit={handleSaveProfile} className="space-y-8">
              {/* Basic Information */}
              <section>
                <h2 className="text-[28px] font-semibold mb-6 flex items-center gap-2">
                  <span className="w-1.5 h-6 bg-blue-500 rounded-full inline-block"></span>
                  Basic Information
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-[14px] uppercase tracking-wider text-[var(--ink-med)] mb-2">Username</label>
                    <input
                      type="text"
                      value={profile.username}
                      disabled
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label className="block text-[14px] uppercase tracking-wider text-[var(--ink-med)] mb-2">Email</label>
                    <input
                      type="email"
                      value={profile.email}
                      disabled
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label className="block text-[14px] uppercase tracking-wider text-[var(--ink-med)] mb-2">Full Name</label>
                    <input
                      type="text"
                      value={profile.full_name || ''}
                      onChange={(e) => handleInputChange('full_name', e.target.value)}
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white focus:border-blue-500 transition-colors"
                      placeholder="E.g. John Doe"
                    />
                  </div>
                  <div>
                    <label className="block text-[14px] uppercase tracking-wider text-[var(--ink-med)] mb-2">Age</label>
                    <input
                      type="number"
                      value={profile.age || ''}
                      onChange={(e) => handleInputChange('age', e.target.value ? parseInt(e.target.value) : undefined)}
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white focus:border-blue-500 transition-colors"
                    />
                  </div>
                </div>
              </section>

              {/* AI Analysis Settings */}
              <section className="pt-6 border-t border-[var(--glass-stroke)]">
                <h2 className="text-[28px] font-semibold mb-6 flex items-center gap-2">
                  <span className="w-1.5 h-6 bg-purple-500 rounded-full inline-block"></span>
                  AI Analysis Settings
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-[14px] uppercase tracking-wider text-[var(--ink-med)] mb-2">
                      Angle Tolerance ({profile.preferences?.angle_tolerance || 10}°)
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="30"
                      step="1"
                      value={profile.preferences?.angle_tolerance || 10}
                      onChange={(e) => {
                        const prefs = { ...profile.preferences, angle_tolerance: parseInt(e.target.value) };
                        handleInputChange('preferences', prefs);
                      }}
                      className="w-full h-2 bg-[var(--glass)] rounded-lg appearance-none cursor-pointer accent-purple-500"
                    />
                    <p className="text-[12px] text-[var(--ink-med)] mt-2">Higher = More lenient pose analysis</p>
                  </div>
                  <div>
                    <label className="block text-[14px] uppercase tracking-wider text-[var(--ink-med)] mb-2">
                      Confidence ({Math.round((profile.preferences?.confidence_threshold || 0.5) * 100)}%)
                    </label>
                    <input
                      type="range"
                      min="0.1"
                      max="0.9"
                      step="0.05"
                      value={profile.preferences?.confidence_threshold || 0.5}
                      onChange={(e) => {
                        const prefs = { ...profile.preferences, confidence_threshold: parseFloat(e.target.value) };
                        handleInputChange('preferences', prefs);
                      }}
                      className="w-full h-2 bg-[var(--glass)] rounded-lg appearance-none cursor-pointer accent-purple-500"
                    />
                    <p className="text-[12px] text-[var(--ink-med)] mt-2">Required clarity for pose detection</p>
                  </div>
                  <div className="flex flex-col justify-center">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={profile.preferences?.mirror_mode !== false}
                          onChange={(e) => {
                            const prefs = { ...profile.preferences, mirror_mode: e.target.checked };
                            handleInputChange('preferences', prefs);
                          }}
                          className="sr-only"
                        />
                        <div className={`w-12 h-6 rounded-full transition-colors ${profile.preferences?.mirror_mode !== false ? 'bg-purple-500' : 'bg-gray-600'}`}></div>
                        <div className={`absolute left-1 top-1 w-4 h-4 rounded-full bg-white transition-transform ${profile.preferences?.mirror_mode !== false ? 'translate-x-6' : 'translate-x-0'}`}></div>
                      </div>
                      <span className="text-[16px]">Mirror Camera Mode</span>
                    </label>
                    <p className="text-[12px] text-[var(--ink-med)] mt-2 ml-15">Flip camera horizontally</p>
                  </div>
                </div>
              </section>

              {/* Physical Information */}
              <section className="pt-6 border-t border-[var(--glass-stroke)]">
                <h2 className="text-[28px] font-semibold mb-6 flex items-center gap-2">
                  <span className="w-1.5 h-6 bg-green-500 rounded-full inline-block"></span>
                  Physical Information
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-[14px] uppercase tracking-wider text-[var(--ink-med)] mb-2">Height (cm)</label>
                    <input
                      type="number"
                      value={profile.height || ''}
                      onChange={(e) => handleInputChange('height', e.target.value ? parseFloat(e.target.value) : undefined)}
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white focus:border-green-500 transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-[14px] uppercase tracking-wider text-[var(--ink-med)] mb-2">Weight (kg)</label>
                    <input
                      type="number"
                      value={profile.weight || ''}
                      onChange={(e) => handleInputChange('weight', e.target.value ? parseFloat(e.target.value) : undefined)}
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white focus:border-green-500 transition-colors"
                    />
                  </div>
                  <div>
                    <label className="block text-[14px] uppercase tracking-wider text-[var(--ink-med)] mb-2">Fitness Level</label>
                    <select
                      value={profile.fitness_level || 'beginner'}
                      onChange={(e) => handleInputChange('fitness_level', e.target.value)}
                      className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white focus:border-green-500 transition-colors"
                    >
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                      <option value="expert">Expert</option>
                    </select>
                  </div>
                </div>
              </section>

              {/* Save Button */}
              <div className="flex justify-end pt-8">
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-8 py-3 bg-blue-500 text-white rounded-lg hover:shadow-[0_0_20px_rgba(59,130,246,0.5)] transition-all disabled:opacity-50 disabled:cursor-not-allowed font-bold"
                >
                  {isSaving ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Saving Changes...
                    </span>
                  ) : 'Save All Changes'}
                </button>
              </div>
            </form>
          </div>

          {/* Account Actions */}
          <div className="mt-8 rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-8" style={{ background: 'rgba(255,255,255,.02)', backdropFilter: 'blur(12px)' }}>
            <h2 className="text-[28px] font-semibold mb-4">Account Actions</h2>
            <div className="space-y-4">
              <button
                onClick={resetWalktour}
                className="px-6 py-3 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
              >
                🎯 Reset Walktour
              </button>
              <button
                onClick={() => {
                  localStorage.removeItem('access_token');
                  window.location.href = '/';
                }}
                className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </main>
    </AuthGuard>
  );
}
