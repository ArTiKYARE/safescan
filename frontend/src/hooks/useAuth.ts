import { create } from 'zustand';
import { authApi } from '@/lib/api';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName?: string, lastName?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: typeof window !== 'undefined' ? localStorage.getItem('access_token') : null,
  refreshToken: typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.login({ email, password });
      const { access_token, refresh_token } = response.data;

      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      set({
        accessToken: access_token,
        refreshToken: refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      // Load user profile
      try {
        const userResp = await authApi.getMe();
        set({ user: userResp.data });
      } catch {
        // User will be loaded on next navigation
      }
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Ошибка входа';
      set({ error: message, isLoading: false, isAuthenticated: false });
      throw err;
    }
  },

  register: async (email: string, password: string, firstName?: string, lastName?: string) => {
    set({ isLoading: true, error: null });
    try {
      await authApi.register({ email, password, first_name: firstName, last_name: lastName });
      set({ isLoading: false, error: null });
      // After registration, user needs to login
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Ошибка регистрации';
      set({ error: message, isLoading: false });
      throw err;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      error: null,
    });
  },

  loadUser: async () => {
    if (!localStorage.getItem('access_token')) {
      set({ isAuthenticated: false, user: null });
      return;
    }
    try {
      const response = await authApi.getMe();
      set({ user: response.data, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false, accessToken: null, refreshToken: null });
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  clearError: () => set({ error: null }),
}));

// ── Helpers ──
export function useIsAdmin(): boolean {
  const user = useAuthStore((s) => s.user);
  return user?.role === 'admin' || user?.role === 'security_auditor';
}
