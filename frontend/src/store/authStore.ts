import { create } from 'zustand';
import { User } from '@/types/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  role: string | null;
  tenantId: string | null;
  isAdmin: boolean;
  setUser: (user: User | null) => void;
  setSession: (session: Session) => void;
  setAuthenticated: (authenticated: boolean) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export interface Session {
  user: User;
  tenant_id: string | null;
  tenant_name: string | null;
  role: string | null;
  is_admin: boolean;
}

const EMPTY = {
  role: null,
  tenantId: null,
  isAdmin: false,
};

export const useAuthStore = create<AuthState>()(
  (set) => ({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    role: null,
    tenantId: null,
    isAdmin: false,
    setUser: (user) => set({ user, isAuthenticated: !!user }),
    setSession: (session) =>
      set({
        user: session.user,
        isAuthenticated: true,
        role: session.role,
        tenantId: session.tenant_id,
        isAdmin: session.is_admin,
      }),
    setAuthenticated: (isAuthenticated) => set({ isAuthenticated }),
    setLoading: (isLoading) => set({ isLoading }),
    logout: () =>
      set({
        user: null,
        isAuthenticated: false,
        ...EMPTY,
      }),
  })
);