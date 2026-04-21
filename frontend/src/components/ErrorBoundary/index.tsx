import { Component, ErrorInfo, ReactNode } from 'react';

import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Sentry 错误追踪（可选）
    // if (import.meta.env.VITE_SENTRY_DSN) {
    //   import('@sentry/react').then((Sentry) => {
    //     Sentry.captureException(error, { extra: errorInfo });
    //   }).catch(() => {
    //     // 如果 @sentry/react 未安装，忽略错误
    //     console.warn('Sentry is not installed, skipping error tracking');
    //   });
    // }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    const { hasError, error } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      if (fallback) {
        return fallback;
      }

      return (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            padding: '24px',
          }}
        >
          <Result
            status="500"
            title="页面出错了"
            subTitle={error?.message || '抱歉，页面遇到了一些问题'}
            extra={[
              <Button type="primary" key="reset" onClick={this.handleReset}>
                重试
              </Button>,
              <Button key="reload" onClick={this.handleReload}>
                刷新页面
              </Button>,
            ]}
          />
        </div>
      );
    }

    return children;
  }
}
