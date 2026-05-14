import React, { createContext, useState, useEffect } from 'react';
import { authAPI, recommendationAPI } from '../services/api';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  const refreshUserProfile = async () => {
    try {
      const response = await recommendationAPI.getUserProfile();
      if (response.data) {
        setUser(response.data);
      }
    } catch (error) {
      localStorage.removeItem('access_token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      refreshUserProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const register = async (username, email, password) => {
    const response = await authAPI.register({ username, email, password });
    return response.data;
  };

  const login = async (username, password) => {
    const response = await authAPI.login({ username, password });
    if (response.data.access) {
      localStorage.setItem('access_token', response.data.access);
      setToken(response.data.access);
      await refreshUserProfile();
    }
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  const isAuthenticated = !!token && !!user;

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    register,
    login,
    logout,
    refreshUserProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
