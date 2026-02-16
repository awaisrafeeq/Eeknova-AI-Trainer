'use client';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

interface AuthData {
  username: string;
  password: string;
  email?: string;
}

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [authData, setAuthData] = useState<AuthData>({ username: '', password: '', email: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [mounted, setMounted] = useState(false);
  const router = useRouter();

  const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8000';

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAuthData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const body = isLogin
        ? { username: authData.username, password: authData.password }
        : authData;

      const response = await fetch(`${apiBaseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        
        // Also set cookie for server-side access
        document.cookie = `access_token=${data.access_token}; path=/; max-age=3600; secure; samesite=strict`;
        
        console.log('✅ Token saved to localStorage and cookies');
        console.log('🍪 Cookies after login:', document.cookie);
        
        setMessage(isLogin ? 'Login successful!' : 'Registration successful!');
        setTimeout(() => {
          router.push('/');
        }, 1000);
      } else {
        setMessage(data.detail || 'Authentication failed');
      }
    } catch (error) {
      console.error('Auth error:', error);
      setMessage('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setMessage('');
    setAuthData({ username: '', password: '', email: '' });
  };

  if (!mounted) return null;

  return (
    <main
      className="min-h-screen w-full overflow-hidden text-[var(--ink-hi)] flex items-center justify-center"
      style={{ background: 'var(--bg-gradient)', fontFamily: 'var(--font-ui)' }}
    >
      <div className="w-full max-w-md px-6">
        <div className="rounded-[var(--radius-lg)] border border-[var(--glass-stroke)] p-8" style={{ background: 'rgba(255,255,255,.02)', backdropFilter: 'blur(12px)' }}>
          <h1 className="text-[36px] font-bold text-center mb-8">
            {isLogin ? 'Login' : 'Sign Up'}
          </h1>

          {/* Message */}
          {message && (
            <div className={`mb-6 p-4 rounded-lg border ${message.includes('successful')
              ? 'bg-green-500/20 border-green-500 text-green-300'
              : 'bg-red-500/20 border-red-500 text-red-300'
              }`}>
              {message}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username */}
            <div>
              <label className="block text-[18px] mb-2">Username</label>
              <input
                type="text"
                name="username"
                value={authData.username}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white placeholder-gray-400"
                placeholder="Enter your username"
              />
            </div>

            {/* Email (only for registration) */}
            {!isLogin && (
              <div>
                <label className="block text-[18px] mb-2">Email</label>
                <input
                  type="email"
                  name="email"
                  value={authData.email}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white placeholder-gray-400"
                  placeholder="Enter your email"
                />
              </div>
            )}

            {/* Password */}
            <div>
              <label className="block text-[18px] mb-2">Password (max 72 characters)</label>
              <input
                type="password"
                name="password"
                value={authData.password}
                onChange={handleInputChange}
                required
                maxLength={72}
                className="w-full px-4 py-3 rounded-lg border border-[var(--glass-stroke)] bg-[var(--glass)] text-white placeholder-gray-400"
                placeholder="Enter your password"
              />
              {authData.password.length > 60 && (
                <p className="text-yellow-400 text-sm mt-1">
                  {authData.password.length}/72 characters
                </p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Processing...' : (isLogin ? 'Login' : 'Sign Up')}
            </button>
          </form>

          {/* Toggle Mode */}
          <div className="mt-6 text-center">
            <p className="text-[16px] text-[var(--ink-med)]">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              <button
                onClick={toggleMode}
                className="ml-2 text-blue-400 hover:text-blue-300 transition-colors"
              >
                {isLogin ? 'Sign Up' : 'Login'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
