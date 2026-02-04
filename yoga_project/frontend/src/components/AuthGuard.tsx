'use client';
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface AuthGuardProps {
  children: React.ReactNode;
}

export default function AuthGuard({ children }: AuthGuardProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  const isTokenExpired = (token: string): boolean => {
    try {
      // Decode JWT token to check expiration
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp < currentTime;
    } catch (error) {
      // If token is invalid, consider it expired
      return true;
    }
  };

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        // No token found
        setIsAuthenticated(false);
        localStorage.removeItem('access_token'); // Clean up any invalid data
        router.push('/auth');
        setIsLoading(false);
        return;
      }

      // Check if token is expired
      if (isTokenExpired(token)) {
        console.log('Token expired, redirecting to login...');
        setIsAuthenticated(false);
        localStorage.removeItem('access_token'); // Remove expired token
        router.push('/auth');
        setIsLoading(false);
        return;
      }

      // Token is valid
      setIsAuthenticated(true);
      setIsLoading(false);
    };

    checkAuth();

    // Set up periodic token validation (every 5 minutes)
    const interval = setInterval(checkAuth, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-gradient)' }}>
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  return <>{children}</>;
}
