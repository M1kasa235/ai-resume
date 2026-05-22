import { Suspense, useEffect } from 'react';

import { useCallback } from 'react';

import { ErrorBoundary } from '@components/ErrorBoundary';
import { AuthProvider } from '@hooks/useAuth';
import { routes, flattenRoutes } from '@router/index';
import { useUserStore } from '@stores/userStore';
import { Skeleton } from 'antd';
import { Routes, Route, useLocation } from 'react-router-dom';

const LoadingFallback = () => (
  <div style={{ display: 'flex', height: '100vh', padding: 24 }}>
    <Skeleton active paragraph={{ rows: 8 }} />
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

  const getTitle = useCallback(() => {
    const flat = flattenRoutes(routes);
    const matched = flat.find((r) => r.path === location.pathname);
    return matched?.meta?.title || 'Offer Pilot';
  }, [location.pathname]);

  useEffect(() => {
    document.title = `${getTitle()} | Offer Pilot`;
  }, [getTitle]);

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
