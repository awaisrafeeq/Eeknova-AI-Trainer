import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Get token from cookies or headers
    const token = request.cookies.get('access_token')?.value || 
                  request.headers.get('authorization')?.replace('Bearer ', '');

    console.log('🔍 API Auth Check - Token:', token ? 'Present' : 'Missing');
    console.log('🍪 API Cookies:', request.cookies.getAll());

    if (!token) {
      console.log('❌ No token found');
      return NextResponse.json(
        { error: 'No authentication token provided' },
        { status: 401 }
      );
    }

    // Forward request to backend
    const apiBaseUrl = process.env.NEXT_PUBLIC_YOGA_API_URL || 'http://localhost:8000';
    const backendUrl = `${apiBaseUrl}/api/auth/me`;
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    console.log('📡 Backend response status:', response.status);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.log('❌ Backend error:', errorData);
      return NextResponse.json(
        { error: errorData.error || 'Authentication failed' },
        { status: response.status }
      );
    }

    const userData = await response.json();
    console.log('✅ Backend auth success:', userData);

    return NextResponse.json(userData);

  } catch (error) {
    console.error('❌ Auth API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
