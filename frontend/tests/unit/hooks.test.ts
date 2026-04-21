import { describe, it, expect, vi, beforeEach } from 'vitest';

import { useDebounce, useThrottle, useLocalStorage } from '@/hooks/useUtils';

describe('useUtils Hooks', () => {
  describe('useDebounce', () => {
    it('should debounce function calls', () => {
      const mockFn = vi.fn();
      const debouncedFn = useDebounce(mockFn, 100);
      
      debouncedFn('test');
      debouncedFn('test2');
      debouncedFn('test3');
      
      expect(mockFn).not.toHaveBeenCalled();
      
      // Wait for debounce timeout
      setTimeout(() => {
        expect(mockFn).toHaveBeenCalledTimes(1);
        expect(mockFn).toHaveBeenCalledWith('test3');
      }, 150);
    });
  });

  describe('useThrottle', () => {
    it('should throttle function calls', () => {
      const mockFn = vi.fn();
      const throttledFn = useThrottle(mockFn, 100);
      
      throttledFn('test1');
      throttledFn('test2');
      throttledFn('test3');
      
      expect(mockFn).toHaveBeenCalledTimes(1);
      expect(mockFn).toHaveBeenCalledWith('test1');
      
      // Wait for throttle timeout
      setTimeout(() => {
        throttledFn('test4');
        expect(mockFn).toHaveBeenCalledTimes(2);
        expect(mockFn).toHaveBeenCalledWith('test4');
      }, 150);
    });
  });

  describe('useLocalStorage', () => {
    beforeEach(() => {
      // Clear localStorage before each test
      localStorage.clear();
    });

    it('should store and retrieve values from localStorage', () => {
      const [value, setValue] = useLocalStorage('test-key', 'default');
      
      expect(value).toBe('default');
      
      setValue('new-value');
      expect(value).toBe('new-value');
    });

    it('should handle complex objects', () => {
      const [value, setValue] = useLocalStorage('complex-key', { name: 'test', count: 0 });
      
      expect(value).toEqual({ name: 'test', count: 0 });
      
      setValue({ name: 'updated', count: 1 });
      expect(value).toEqual({ name: 'updated', count: 1 });
    });
  });
});