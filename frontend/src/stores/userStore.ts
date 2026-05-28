import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

import type { User } from '@/types';

interface UserState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface UserActions {
  setUser: (_user: User | null) => void;
  setToken: (_token: string, _refreshToken: string) => void;
  logout: () => void;
  initialize: () => void;
  setLoading: (_loading: boolean) => void;
}

type UserStore = UserState & UserActions;

const initialState: UserState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
};

export const useUserStore = create<UserStore>()(
  persist(
    immer((set, get) => ({
      ...initialState,

      setUser: (user) =>
        set((state) => {
          state.user = user;
          state.isAuthenticated = !!user;
        }),

      setToken: (token, refreshToken) =>
        set((state) => {
          state.token = token;
          state.refreshToken = refreshToken;
          state.isAuthenticated = true;
          state.isLoading = false;
        }),

      logout: () =>
        set((state) => {
          state.user = null;
          state.token = null;
          state.refreshToken = null;
          state.isAuthenticated = false;
          state.isLoading = false;
        }),

      initialize: () => {
        const { token, refreshToken } = get();
        if (token && refreshToken) {
          set((state) => {
            state.isAuthenticated = true;
            state.isLoading = false;
          });
        } else {
          set((state) => {
            state.isLoading = false;
          });
        }
      },

      setLoading: (loading) =>
        set((state) => {
          state.isLoading = loading;
        }),
    })),
    {
      name: 'user-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);