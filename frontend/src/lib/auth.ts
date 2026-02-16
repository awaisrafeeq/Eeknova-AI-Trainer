// Authentication utilities and constants

export const AUTH_TOKEN_KEY = 'auth_token';
export const USER_DATA_KEY = 'user_data';
export const SESSION_DURATION = 60 * 60 * 1000; // 60 minutes in milliseconds

// Token management utilities
export const tokenManager = {
  // Set authentication token
  setToken: (token: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(AUTH_TOKEN_KEY, token);
      // Set cookie for server-side access
      document.cookie = `${AUTH_TOKEN_KEY}=${token}; path=/; max-age=${SESSION_DURATION / 1000}; secure; samesite=strict`;
    }
  },

  // Get authentication token
  getToken: () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(AUTH_TOKEN_KEY);
    }
    return null;
  },

  // Remove authentication token
  removeToken: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      // Remove cookie
      document.cookie = `${AUTH_TOKEN_KEY}=; path=/; max-age=0; secure; samesite=strict`;
    }
  },

  // Check if token is expired
  isTokenExpired: () => {
    const token = tokenManager.getToken();
    if (!token) return true;

    try {
      // Parse JWT payload (basic implementation)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp < currentTime;
    } catch {
      return true; // If token is invalid, consider it expired
    }
  },

  // Store user data
  setUserData: (userData: any) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(USER_DATA_KEY, JSON.stringify(userData));
    }
  },

  // Get user data
  getUserData: () => {
    if (typeof window !== 'undefined') {
      const data = localStorage.getItem(USER_DATA_KEY);
      return data ? JSON.parse(data) : null;
    }
    return null;
  },

  // Remove user data
  removeUserData: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(USER_DATA_KEY);
    }
  },

  // Clear all auth data
  clearAuth: () => {
    tokenManager.removeToken();
    tokenManager.removeUserData();
  },
};

// Session management utilities
export const sessionManager = {
  // Check if user is logged in
  isLoggedIn: () => {
    const token = tokenManager.getToken();
    return token && !tokenManager.isTokenExpired();
  },

  // Get session expiry time
  getSessionExpiry: () => {
    const token = tokenManager.getToken();
    if (!token) return null;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.exp * 1000; // Convert to milliseconds
    } catch {
      return null;
    }
  },

  // Check if session is about to expire (within 5 minutes)
  isSessionExpiringSoon: () => {
    const expiry = sessionManager.getSessionExpiry();
    if (!expiry) return false;
    
    const fiveMinutesFromNow = Date.now() + (5 * 60 * 1000);
    return expiry < fiveMinutesFromNow;
  },
};

// API utilities for authenticated requests
export const authApi = {
  // Get default headers for authenticated requests
  getAuthHeaders: () => {
    const token = tokenManager.getToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  },

  // Make authenticated API request
  async request(url: string, options: RequestInit = {}) {
    const response = await fetch(url, {
      ...options,
      headers: {
        ...authApi.getAuthHeaders(),
        ...options.headers,
      },
      credentials: 'include',
    });

    if (response.status === 401 || response.status === 404) {
      // Token expired or API not found - clear auth and redirect
      tokenManager.clearAuth();
      if (typeof window !== 'undefined') {
        window.location.href = '/auth';
      }
      throw new Error('Session expired');
    }

    return response;
  },

  // GET request
  get: (url: string) => authApi.request(url, { method: 'GET' }),

  // POST request
  post: (url: string, data: any) => authApi.request(url, {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // PUT request
  put: (url: string, data: any) => authApi.request(url, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),

  // DELETE request
  delete: (url: string) => authApi.request(url, { method: 'DELETE' }),
};

// Redirect utilities
export const authRedirect = {
  // Redirect to login with return URL
  toLogin: (returnUrl?: string) => {
    if (typeof window !== 'undefined') {
      const loginUrl = new URL('/auth', window.location.origin);
      if (returnUrl) {
        loginUrl.searchParams.set('redirect', returnUrl);
      } else {
        loginUrl.searchParams.set('redirect', window.location.pathname);
      }
      window.location.href = loginUrl.toString();
    }
  },

  // Redirect after successful login
  afterLogin: (defaultUrl = '/dashboard') => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const returnUrl = urlParams.get('redirect');
      window.location.href = returnUrl || defaultUrl;
    }
  },
};
