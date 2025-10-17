import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);
const API_BASE_URL = '/api';

// AUTHENTICATION FRONT=END COMPONENT
export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const initializeAuth = async () => {
          const storedToken = sessionStorage.getItem('token');

          if (storedToken) {
            try {
              const response = await fetch(`${API_BASE_URL}/auth/profile`, {
                headers: {
                  'Authorization': `Bearer ${storedToken}`,
                  'Content-Type': 'application/json'
                }
              });

              if (response.ok) {
                const userData = await response.json();
                setToken(storedToken);
                setUser(userData);
              } else {
                sessionStorage.removeItem('token');
              }

            } catch (error) {
              console.error('Token verification failed:', error);
              sessionStorage.removeItem('token');
            }
          }

          setLoading(false);
        };

        initializeAuth();
      }, []);

    // LOGIN

    const login = async (username, password) => {

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (data.success && data.token) {
        sessionStorage.setItem('token', data.token);

        setToken(data.token);
        setUser(data.user);

        return { success: true };
      } else {
            return {
              success: false,
              error: data.message || 'Login failed'
            };
      }
    } catch (error) {
          console.error('Login error:', error);
          return {
            success: false,
            error: 'Network error. Please try again.'
          };
        }
  };

  // REGISTRATION

    const register = async (username, email, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },

        body: JSON.stringify({ username, email, password })
      });

      const data = await response.json();

      if (data.success && data.token) {
        sessionStorage.setItem('token', data.token);

        setToken(data.token);
        setUser(data.user);

        return { success: true };
      } else {
        return {
          success: false,
          error: data.message || 'Registration failed'
        };
      }
    } catch (error) {
        console.error('Registration error:', error);

      return {
        success: false,
        error: 'Network error. Please try again.'
      };
    }
  };

  // LOGOUT

    const logout = () => {
    sessionStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };


  // PROFILE UPDATES

    const updateProfile = async (updates) => {
    if (!token) {
      return { success: false, error: 'Not authenticated' };
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });

      const data = await response.json();

      if (data.success) {
        const profileResponse = await fetch(`${API_BASE_URL}/auth/profile`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (profileResponse.ok) {
          const userData = await profileResponse.json();
          setUser(userData);
        }

        return { success: true };
      } else {
            return {
              success: false,
              error: data.message || 'Update failed'
            };
      }
    } catch (error) {
          console.error('Update profile error:', error);
          return {
            success: false,
            error: 'Network error. Please try again.'
      };
    }
  };


    const isAuthenticated = !!token;

    const value = {
        user,
        token,
        login,
        register,
        logout,
        updateProfile,
        isAuthenticated,
        loading
    };

    return (
        <AuthContext.Provider value = { value }>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
};

export default AuthContext;
