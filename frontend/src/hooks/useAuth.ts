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
      // Check auth status via httpOnly cookie
      const response = await api.get<{ authenticated: boolean; user: Session['user'] | null }>('/auth/status');
      if (response.data.authenticated && response.data.user) {
        // Fetch full session with tenant/role info
        const sessionResponse = await api.get<Session>('/auth/me');
        setSession(sessionResponse.data);
      } else {
        setAuthenticated(false);
      }
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
    // The callback endpoint now sets httpOnly cookies and creates session
    const response = await api.completeLogin(deviceCode);
    if (response.access_token) {
      // Fetch session to get user/role/tenant info
      await checkAuth();
    }
    return response;
  };

  const logoutUser = async () => {
    await api.logout();
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