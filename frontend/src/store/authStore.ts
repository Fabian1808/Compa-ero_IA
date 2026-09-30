import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  /** Role held in the active tenant, as resolved by the API. */
  role: string | null;
  tenantId: string | null;
  /**
   * Whether the caller may administer the active tenant.
   *
   * This comes from `GET /auth/me` and must not be recomputed from `role` here:
   * the API is what enforces the rule, and duplicating it on the client is how
   * the admin menu ended up visible to everyone.
   */
  isAdmin: boolean;
  setUser: (user: User | null) => void;
  setSession: (session: Session) => void;
  setAuthenticated: (authenticated: boolean) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

/** Response shape of `GET /auth/me`. */
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
  persist(
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
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        role: state.role,
        tenantId: state.tenantId,
        isAdmin: state.isAdmin,
      }),
    }
  )
);