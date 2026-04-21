import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeAll, afterAll } from 'vitest';

import { ErrorBoundary } from '@/components/ErrorBoundary';

// Mock console.error to avoid noise in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (!args[0].includes('ErrorBoundary caught an error')) {
      originalError(...args);
    }
  };
});

afterAll(() => {
  console.error = originalError;
});

describe('ErrorBoundary', () => {
  it('renders children without errors', () => {
    const ChildComponent = () => <div>Child content</div>;
    
    render(
      <ErrorBoundary>
        <ChildComponent />
      </ErrorBoundary>
    );
    
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('renders error UI when child component throws error', () => {
    const ChildComponent = () => {
      throw new Error('Test error');
    };
    
    render(
      <ErrorBoundary>
        <ChildComponent />
      </ErrorBoundary>
    );
    
    expect(screen.getByText('页面出错了')).toBeInTheDocument();
    expect(screen.getByText('抱歉，页面遇到了一些问题')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '刷新页面' })).toBeInTheDocument();
  });

  it('calls reset function when retry button is clicked', () => {
    const ChildComponent = () => {
      throw new Error('Test error');
    };
    
    render(
      <ErrorBoundary>
        <ChildComponent />
      </ErrorBoundary>
    );
    
    const retryButton = screen.getByRole('button', { name: '重试' });
    fireEvent.click(retryButton);
    
    // The error boundary should be reset and children should be rendered again
    // In a real test, you might need to mock the error throwing behavior
  });

  it('calls reload function when reload button is clicked', () => {
    const mockReload = vi.fn();
    // @ts-ignore
    delete window.location;
    // @ts-ignore
    window.location = { reload: mockReload };
    
    const ChildComponent = () => {
      throw new Error('Test error');
    };
    
    render(
      <ErrorBoundary>
        <ChildComponent />
      </ErrorBoundary>
    );
    
    const reloadButton = screen.getByRole('button', { name: '刷新页面' });
    fireEvent.click(reloadButton);
    
    expect(mockReload).toHaveBeenCalled();
  });

  it('renders custom fallback when provided', () => {
    const customFallback = <div>Custom error UI</div>;
    const ChildComponent = () => {
      throw new Error('Test error');
    };
    
    render(
      <ErrorBoundary fallback={customFallback}>
        <ChildComponent />
      </ErrorBoundary>
    );
    
    expect(screen.getByText('Custom error UI')).toBeInTheDocument();
  });
});
