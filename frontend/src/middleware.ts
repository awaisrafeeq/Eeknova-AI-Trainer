import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Public routes that don't require authentication
const publicRoutes = ['/auth', '/login', '/register', '/'];

// API routes that require authentication
const protectedApiRoutes = ['/api/auth/me', '/api/yoga', '/api/chess', '/api/user', '/api/zumba'];

// Page routes that require authentication
const protectedPageRoutes = ['/yoga', '/chess', '/dashboard', '/settings', '/module-selection', '/zumba'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Check if it's a public route
  if (publicRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next();
  }
  
  // Check if it's a protected route
  const isProtectedApi = protectedApiRoutes.some(route => pathname.startsWith(route));
  const isProtectedPage = protectedPageRoutes.some(route => pathname.startsWith(route));
  
  if (isProtectedApi || isProtectedPage) {
    // Get token from cookies
    const token = request.cookies.get('auth_token')?.value;
    
    if (!token) {
      // For API routes, return 401
      if (isProtectedApi) {
        return NextResponse.json(
          { error: 'Unauthorized - Please login first' },
          { status: 401 }
        );
      }
      
      // For page routes, redirect to login
      const loginUrl = new URL('/auth', request.url);
      loginUrl.searchParams.set('redirect', pathname);
      return NextResponse.redirect(loginUrl);
    }
    
    // For API routes, we could add token validation here
    // For now, we'll let the individual API routes handle token validation
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public).*)',
  ],
};
