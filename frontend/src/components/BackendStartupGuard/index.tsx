import { Button, Spin, Typography } from 'antd';
import { useCallback, useEffect, useState } from 'react';

const MAX_ATTEMPTS = 30;
const RETRY_INTERVAL_MS = 1000;

function resolveHealthUrl(): string {
  // 开发环境始终走 Vite 代理，避免 VITE_API_BASE_URL 直连后端导致 CORS/空白页
  if (import.meta.env.DEV) {
    return '/health';
  }
  const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
  return base ? `${base}/health` : '/health';
}

function fetchWithTimeout(url: string, timeoutMs: number): Promise<Response> {
  if (typeof AbortSignal !== 'undefined' && 'timeout' in AbortSignal) {
    return fetch(url, {
      method: 'GET',
      cache: 'no-store',
      signal: AbortSignal.timeout(timeoutMs),
    });
  }
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  return fetch(url, {
    method: 'GET',
    cache: 'no-store',
    signal: controller.signal,
  }).finally(() => window.clearTimeout(timer));
}

async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetchWithTimeout(resolveHealthUrl(), 2500);
    return response.ok;
  } catch {
    return false;
  }
}

function StartupScreen({ attempt }: { attempt: number }) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        background: '#f5f5f5',
      }}
    >
      <Spin size="large" />
      <Typography.Title level={4} style={{ marginTop: 24, marginBottom: 8 }}>
        服务启动中…
      </Typography.Title>
      <Typography.Text type="secondary">
        正在等待后端就绪{attempt > 0 ? `（${attempt}s）` : ''}
      </Typography.Text>
    </div>
  );
}

function StartupFailedScreen({ onRetry }: { onRetry: () => void }) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        textAlign: 'center',
        background: '#f5f5f5',
      }}
    >
      <Typography.Title level={4} style={{ marginBottom: 8 }}>
        后端服务未就绪
      </Typography.Title>
      <Typography.Text type="secondary" style={{ marginBottom: 24, maxWidth: 420 }}>
        已等待 {MAX_ATTEMPTS} 秒仍无法连接后端。请确认后端已启动（如运行 run.py），然后重试。
      </Typography.Text>
      <Button type="primary" onClick={onRetry}>
        重新检测
      </Button>
    </div>
  );
}

export function BackendStartupGuard({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [runId, setRunId] = useState(0);

  const waitForBackend = useCallback(async (cancelled: () => boolean) => {
    setFailed(false);
    setReady(false);
    setAttempt(0);

    for (let i = 1; i <= MAX_ATTEMPTS; i += 1) {
      if (cancelled()) return;
      setAttempt(i);
      if (await checkBackendHealth()) {
        if (!cancelled()) setReady(true);
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, RETRY_INTERVAL_MS));
    }

    if (!cancelled()) setFailed(true);
  }, []);

  useEffect(() => {
    let cancelled = false;
    waitForBackend(() => cancelled);
    return () => {
      cancelled = true;
    };
  }, [runId, waitForBackend]);

  const handleRetry = useCallback(() => {
    setRunId((id) => id + 1);
  }, []);

  if (failed) {
    return <StartupFailedScreen onRetry={handleRetry} />;
  }

  if (!ready) {
    return <StartupScreen attempt={attempt} />;
  }

  return <>{children}</>;
}
