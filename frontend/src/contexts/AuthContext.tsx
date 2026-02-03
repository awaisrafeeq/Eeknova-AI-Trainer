'use client';
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  username: string;
  email: string;
  full_name?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  const isTokenExpired = (token: string): boolean => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp < currentTime;
    } catch (error) {
      return true;
    }
  };

  const fetchUserProfile = async (authToken: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const profile = await response.json();
        setUser({
          username: profile.username,
          email: profile.email,
          full_name: profile.full_name
        });
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      return false;
    }
  };

  const login = (authToken: string) => {
    setToken(authToken);
    // Store token in localStorage as fallback (can be removed later)
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', authToken);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
    router.push('/auth');
  };

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        let authToken = token;

        // Try to get token from localStorage as fallback
        if (!authToken && typeof window !== 'undefined') {
          authToken = localStorage.getItem('access_token');
        }

        if (!authToken) {
          setIsLoading(false);
          return;
        }

        if (isTokenExpired(authToken)) {
          console.log('Token expired, logging out...');
          logout();
          setIsLoading(false);
          return;
        }

        setToken(authToken);
        const profileFetched = await fetchUserProfile(authToken);
        
        if (!profileFetched) {
          logout();
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        logout();
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
