'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  email: string;
  name?: string;
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

  // Check authentication status
  const checkAuth = useCallback(async () => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));

      // Debug: Log current auth state
      console.log('🔍 Checking auth status...');
      console.log('🍪 Cookies:', document.cookie);

      const response = await fetch('/api/auth/me', {
        method: 'GET',
        credentials: 'include', // Include cookies
      });

      console.log('📡 Auth response status:', response.status);
      console.log('📡 Auth response headers:', response.headers);

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
      console.log('✅ Auth success - user data:', userData);
      
      setAuthState({
        user: userData.user,
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

  // Check auth on mount and when dependencies change
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Auto-check auth every 5 minutes to catch expired sessions
  useEffect(() => {
    if (authState.isAuthenticated) {
      const interval = setInterval(checkAuth, 5 * 60 * 1000); // 5 minutes
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

      const response = await fetch(url, {
        ...options,
        credentials: 'include', // Include auth cookies
        headers: {
          'Content-Type': 'application/json',
          ...(token && !(options.headers as any)?.Authorization && !(options.headers as any)?.authorization
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
