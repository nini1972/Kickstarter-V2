// Simple Auth Context for Kickstarter Investment Tracker
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // With httpOnly cookies, we can't directly access tokens from JavaScript
    // Instead, we check if the user is authenticated by trying to fetch user profile
    const checkAuthentication = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/me`, {
          method: 'GET',
          credentials: 'include', // Include cookies in request
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
          setToken('cookie-based-auth'); // Placeholder since we can't access the actual token
        } else {
          // User is not authenticated
          setUser(null);
          setToken(null);
        }
      } catch (error) {
        console.log('Auth check failed:', error);
        setUser(null);
        setToken(null);
      }
      setIsLoading(false);
    };

    checkAuthentication();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        credentials: 'include', // Include cookies for secure authentication
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        // With httpOnly cookies, tokens are automatically stored securely by the browser
        // We only need to store user data and set authentication state
        setUser(data.user);
        setToken('cookie-based-auth'); // Placeholder since actual token is in httpOnly cookie
        
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Login failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const register = async (email, username, password) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/register`, {
        method: 'POST',
        credentials: 'include', // Include cookies for consistency
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        return { success: true, message: 'Registration successful. Please login.' };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail || 'Registration failed' };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint to clear httpOnly cookies on server side
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include', // Include cookies for logout
        headers: {
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.log('Logout API call failed:', error);
      // Continue with client-side cleanup even if server call fails
    }
    
    // Clear client-side state
    setToken(null);
    setUser(null);
  };

  // Secure demo login using server-side token generation
  const loginAsDemo = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/demo-login`, {
        method: 'POST',
        credentials: 'include', // Include cookies for secure authentication
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        // With httpOnly cookies, tokens are automatically stored securely by the browser
        // We only need to store user data and set authentication state
        setUser(data.user);
        setToken('secure-demo-auth'); // Placeholder since actual token is in httpOnly cookie
        
        return { success: true };
      } else {
        const error = await response.json();
        // Fallback to client-side demo if server-side fails
        console.log('Server-side demo login failed, using fallback');
        const fallbackDemoUser = {
          id: 'demo-user-fallback',
          email: 'demo@example.com',
          username: 'demo_user',
          role: 'user'
        };
        setToken('fallback-demo-auth');
        setUser(fallbackDemoUser);
        return { success: true };
      }
    } catch (error) {
      console.log('Demo login failed, using fallback:', error);
      // Fallback to client-side demo if network fails
      const fallbackDemoUser = {
        id: 'demo-user-fallback',
        email: 'demo@example.com',
        username: 'demo_user',
        role: 'user'
      };
      setToken('fallback-demo-auth');
      setUser(fallbackDemoUser);
      return { success: true };
    }
  };

  const value = {
    token,
    user,
    isLoading,
    login,
    register,
    logout,
    loginAsDemo,
    isAuthenticated: !!token
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};