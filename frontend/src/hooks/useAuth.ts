import { useCallback, useEffect } from 'react';
import { api } from '@/services/api';
import { useAuthStore, type Session } from '@/store/authStore';

export function useAuth() {
  const {
    user,
    isAuthenticated,
    isLoading,
    role,
    tenantId,
    isAdmin,
    setUser,
    setSession,
    setAuthenticated,
    setLoading,
    logout,
  } = useAuthStore();

  const checkAuth = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setAuthenticated(false);
        return;
      }

      // Ask the API who the caller is and what role they hold. A token alone
      // says nothing about admin rights: those live on the tenant membership.
      const response = await api.get<Session>('/auth/me');
      setSession(response.data);
    } catch {
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, [setAuthenticated, setLoading, setSession]);

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
    role,
    tenantId,
    isAdmin,
    login,
    completeLogin,
    logout: logoutUser,
    checkAuth,
  };
}