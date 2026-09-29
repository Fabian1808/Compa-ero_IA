import { useCallback, useEffect } from 'react';
import { api } from '@/services/api';
import { useAuthStore } from '@/store/authStore';

export function useAuth() {
  const { user, isAuthenticated, isLoading, setUser, setAuthenticated, setLoading, logout } = useAuthStore();

  const checkAuth = useCallback(async () => {
    setLoading(true);
    try {
      // In a real app, this would validate the token with the backend
      const token = localStorage.getItem('access_token');
      if (token) {
        setAuthenticated(true);
      } else {
        setAuthenticated(false);
      }
    } catch {
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, [setAuthenticated, setLoading]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async () => {
    const response = await api.initiateLogin();
    return response;
  };

  const completeLogin = async (deviceCode: string) => {
    const response = await api.completeLogin(deviceCode);
    if (response.access_token) {
      // In a real app, fetch user info
      setAuthenticated(true);
    }
    return response;
  };

  const logoutUser = () => {
    api.logout();
    logout();
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    login,
    completeLogin,
    logout: logoutUser,
    checkAuth,
  };
}