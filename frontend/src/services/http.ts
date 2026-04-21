import { useUserStore } from '@stores/userStore';
import { message } from 'antd';
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface ApiResponse<T = unknown> {
  error_code?: string;
  detail?: string;
  data?: T;
}

export interface PaginatedResponse<T> {
  total: number;
  items: T[];
  page: number;
  page_size: number;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

const instance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let refreshSubscribers: ((_: string) => void)[] = [];

const subscribeTokenRefresh = (cb: (_: string) => void) => {
  refreshSubscribers.push(cb);
};

const onTokenRefreshed = (token: string) => {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
};

// 请求拦截器
instance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { token } = useUserStore.getState();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
instance.interceptors.response.use(
  <T = unknown>(response: { data: T }) => {
    // 处理后端统一响应格式
    const { data } = response;
    
    // 如果是分页响应，直接返回
    if ((data as any).total !== undefined && (data as any).items !== undefined) {
      return data as T;
    }
    
    // 如果是成功响应，返回data字段
    if ((data as any).data !== undefined) {
      return (data as any).data as T;
    }
    
    // 如果没有data字段，直接返回原始数据
    return data as T;
  },
  async (error: AxiosError<ApiResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // 处理401错误 - Token过期
    if (error.response?.status === 401 && !originalRequest?._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            resolve(instance(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const { refreshToken, setToken, logout } = useUserStore.getState();

      if (!refreshToken) {
        logout();
        window.location.href = '/auth/login';
        return Promise.reject(error);
      }

      try {
        const response = await instance.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token: new_refresh_token } = response.data || response;
        setToken(access_token, new_refresh_token);
        onTokenRefreshed(access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }

        return instance(originalRequest);
      } catch (refreshError) {
        logout();
        window.location.href = '/auth/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // 处理其他错误
    const errorMessage = error.response?.data?.detail || error.message || '请求失败';
    
    // 根据错误类型显示不同的错误信息
    if (error.response?.status === 403) {
      message.error('权限不足');
    } else if (error.response?.status === 404) {
      message.error('请求的资源不存在');
    } else if (error.response?.status === 422) {
      message.error('请求数据格式错误');
    } else if (error.response?.status === 500) {
      message.error('服务器内部错误');
    } else {
      message.error(errorMessage);
    }

    return Promise.reject(error);
  }
);

export default instance;