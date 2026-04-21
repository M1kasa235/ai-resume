import { createContext, useContext, useCallback, useEffect } from 'react';

import { authApi } from '@services/api';
import { useUserStore } from '@stores/userStore';
import { message } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';

import type { LoginRequest, RegisterRequest, User, Token } from '@/types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (_data: LoginRequest) => Promise<void>;
  register: (_data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, token, isAuthenticated, isLoading, setUser, setToken, logout: logoutStore } = useUserStore();

  const login = useCallback(
    async (data: LoginRequest) => {
      try {
        // http 拦截器已经处理了响应，直接返回 Token 对象
        const tokenData = await authApi.login(data) as unknown as Token;
        setToken(tokenData.access_token, tokenData.refresh_token);
        message.success('登录成功');
        
        const from = (location.state as { from?: Location })?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
      } catch (error) {
        message.error('登录失败，请检查用户名和密码');
        throw error;
      }
    },
    [setToken, navigate, location.state]
  );

  const register = useCallback(
    async (data: RegisterRequest) => {
      try {
        await authApi.register(data);
        message.success('注册成功，请登录');
        navigate('/auth/login');
      } catch (error) {
        message.error('注册失败');
        throw error;
      }
    },
    [navigate]
  );

  const logout = useCallback(() => {
    logoutStore();
    message.success('已退出登录');
    navigate('/auth/login');
  }, [logoutStore, navigate]);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    
    try {
      // http 拦截器已经处理了响应，直接返回 User 对象
      const userData = await authApi.getCurrentUser() as unknown as User;
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  }, [token, setUser]);

  useEffect(() => {
    if (isAuthenticated && !user) {
      refreshUser();
    }
  }, [isAuthenticated, user, refreshUser]);

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
