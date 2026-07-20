'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id?: string;
  username?: string;
  email: string;
  name?: string;
  full_name?: string;
  age?: number | null;
  height?: number | null;
  /** kg — used for the post-session calories estimate. */
  weight?: number | null;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
  });

  const router = useRouter();

  // Check authentication status.
  //
  // `silent` mode is used by the periodic background refresh: it re-validates
  // the session WITHOUT flipping `isLoading` back to `true`. Without this, the
  // 5-minute refresh made every page briefly render its loading state, which
  // unmounted and rebuilt heavy children (e.g. the Zumba avatar's WebGL canvas)
  // on every tick. Initial mount still uses the non-silent path so the first
  // load shows a spinner.
  const checkAuth = useCallback(async (silent = false) => {
    try {
      if (!silent) {
        setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      }

      const response = await fetch('/api/auth/me', {
        method: 'GET',
        credentials: 'include', // Include cookies
      });

      if (response.status === 401 || response.status === 404) {
        // Token expired or API not found - redirect to login
        console.log('❌ Auth failed - redirecting to login');
        setAuthState({
          user: null,
          isLoading: false,
          isAuthenticated: false,
          error: null, // Don't show error, just redirect
        });
        
        // Redirect to login without showing error
        router.push('/auth');
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to check authentication status');
      }

      const userData = await response.json();
      const resolvedUser = userData.user || userData;

      setAuthState({
        user: resolvedUser,
        isLoading: false,
        isAuthenticated: true,
        error: null,
      });
    } catch (error) {
      console.error('❌ Auth check failed:', error);
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null, // Don't show error to user
      });
      
      // Redirect to login on error
      router.push('/auth');
    }
  }, [router]);

  // Logout function
  const logout = useCallback(async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear auth state and redirect
      setAuthState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
      });
      router.push('/auth');
    }
  }, [router]);

  // Check auth on initial mount (shows the loading state).
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Auto-check auth every 5 minutes to catch expired sessions. Silent so the
  // background refresh never flips the page back into its loading state.
  useEffect(() => {
    if (authState.isAuthenticated) {
      const interval = setInterval(() => checkAuth(true), 5 * 60 * 1000); // 5 minutes
      return () => clearInterval(interval);
    }
  }, [authState.isAuthenticated, checkAuth]);

  return {
    ...authState,
    checkAuth,
    logout,
    refreshToken: checkAuth, // Alias for consistency
  };
}

// API fetch wrapper that handles auth errors
export function useAuthenticatedFetch() {
  const { checkAuth } = useAuth();

  return useCallback(async (url: string, options: RequestInit = {}) => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const optionHeaders = options.headers as Record<string, string> | undefined;

      const response = await fetch(url, {
        ...options,
        credentials: 'include', // Include auth cookies
        headers: {
          'Content-Type': 'application/json',
          ...(token && !optionHeaders?.Authorization && !optionHeaders?.authorization
            ? { Authorization: `Bearer ${token}` }
            : {}),
          ...options.headers,
        },
      });

      if (response.status === 401 || response.status === 404) {
        // Token expired or API not found - trigger auth check which will redirect
        await checkAuth();
        throw new Error('Session expired');
      }

      return response;
    } catch (error) {
      // If it's already a session expired error, don't check again
      if (error instanceof Error && error.message === 'Session expired') {
        throw error;
      }
      
      console.error('Authenticated fetch error:', error);
      // For other errors, also check auth and redirect
      await checkAuth();
      throw error;
    }
  }, [checkAuth]);
}
