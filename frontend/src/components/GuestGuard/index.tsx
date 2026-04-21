import { useUserStore } from '@stores/userStore';
import { Spin } from 'antd';
import { Navigate, useLocation } from 'react-router-dom';

interface GuestGuardProps {
  children: React.ReactNode;
}

export function GuestGuard({ children }: GuestGuardProps) {
  const location = useLocation();
  const { isAuthenticated, isLoading } = useUserStore();
  const from = (location.state as { from?: Location })?.from?.pathname || '/dashboard';

  if (isLoading) {
    return (
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
  }

  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
}
