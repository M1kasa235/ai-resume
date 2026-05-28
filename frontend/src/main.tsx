import React from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import App from './App';
import { BackendStartupGuard } from '@components/BackendStartupGuard';
import './styles/index.scss';

// 开发环境清理旧 PWA Service Worker，避免 lazy chunk 被缓存导致路由切换失败
if (import.meta.env.DEV && 'serviceWorker' in navigator) {
  void navigator.serviceWorker.getRegistrations().then((registrations) => {
    registrations.forEach((registration) => {
      void registration.unregister();
    });
  });
  if ('caches' in window) {
    void caches.keys().then((keys) => {
      keys.forEach((key) => {
        void caches.delete(key);
      });
    });
  }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhCN}
        theme={{
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
          },
        }}
      >
        <BrowserRouter>
          <BackendStartupGuard>
            <App />
          </BackendStartupGuard>
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
