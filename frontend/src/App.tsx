import { Suspense, useEffect } from 'react';

import { ErrorBoundary } from '@components/ErrorBoundary';
import { AuthProvider } from '@hooks/useAuth';
import { routes } from '@router/index';
import { useUserStore } from '@stores/userStore';
import { Spin } from 'antd';
import { Routes, Route, useLocation } from 'react-router-dom';

const LoadingFallback = () => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
    }}
  >
    <Spin size="large" tip="加载中..." />
  </div>
);

function App() {
  const location = useLocation();
  const { initialize } = useUserStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  return (
    <ErrorBoundary>
      <AuthProvider>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            {routes.map((route) => (
              <Route
                key={route.path}
                path={route.path}
                element={route.element}
              >
                {route.children?.map((child) => (
                  <Route
                    key={child.path}
                    path={child.path}
                    element={child.element}
                  />
                ))}
              </Route>
            ))}
          </Routes>
        </Suspense>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
