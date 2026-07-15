import React, { createContext, useState, useEffect } from 'react';
import { authAPI, recommendationAPI } from '../services/api';

export const AuthContext = createContext();

const normalizeProvinceList = (value) => {
  if (Array.isArray(value)) {
    return value.map((province) => String(province).trim()).filter(Boolean);
  }

  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) return [];

    try {
      const parsed = JSON.parse(trimmed);
      if (Array.isArray(parsed)) {
        return parsed.map((province) => String(province).trim()).filter(Boolean);
      }
    } catch {
      return trimmed
        .split(',')
        .map((province) => String(province).trim())
        .filter(Boolean);
    }
  }

  return [];
};

const getStoredProvinceList = () => normalizeProvinceList(localStorage.getItem('preferred_provinces'));

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [hasRecommendationHistory, setHasRecommendationHistory] = useState(false);

  const refreshUserProfile = async () => {
    try {
      const [profileResponse, historyResponse] = await Promise.all([
        recommendationAPI.getUserProfile(),
        recommendationAPI.getUserSearchHistory().catch(() => ({ data: [] })),
      ]);

      if (profileResponse.data) {
        const preferredProvinces = normalizeProvinceList(profileResponse.data.preferred_provinces);
        setUser({
          ...profileResponse.data,
          preferred_provinces: preferredProvinces.length > 0 ? preferredProvinces : getStoredProvinceList(),
        });
      }

      const history = Array.isArray(historyResponse?.data) ? historyResponse.data : [];
      setHasRecommendationHistory(history.length > 0);
    } catch (error) {
      localStorage.removeItem('access_token');
      setToken(null);
      setUser(null);
      setHasRecommendationHistory(false);
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
    setHasRecommendationHistory(false);
  };

  const isAuthenticated = !!token && !!user;

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    hasRecommendationHistory,
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
