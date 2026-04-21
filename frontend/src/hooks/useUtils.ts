import { useCallback, useRef, useState } from 'react';

type Timer = ReturnType<typeof setTimeout>;

export function useDebounce<T extends (..._args: Parameters<T>) => ReturnType<T>>(
  callback: T,
  delay: number
): (..._args: Parameters<T>) => void {
  const timerRef = useRef<Timer | null>(null);

  return useCallback(
    (...args: Parameters<T>) => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      timerRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    },
    [callback, delay]
  );
}

export function useThrottle<T extends (..._args: Parameters<T>) => ReturnType<T>>(
  callback: T,
  delay: number
): (..._args: Parameters<T>) => void {
  const lastRunRef = useRef<number>(0);
  const timerRef = useRef<Timer | null>(null);

  return useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now();
      const remaining = delay - (now - lastRunRef.current);

      if (remaining <= 0) {
        if (timerRef.current) {
          clearTimeout(timerRef.current);
        }
        callback(...args);
        lastRunRef.current = now;
      } else if (!timerRef.current) {
        timerRef.current = setTimeout(() => {
          callback(...args);
          lastRunRef.current = Date.now();
          timerRef.current = null;
        }, remaining);
      }
    },
    [callback, delay]
  );
}

export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (_value: T | ((_val: T) => T)) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((_val: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      } catch (error) {
        console.error('Error saving to localStorage:', error);
      }
    },
    [key, storedValue]
  );

  return [storedValue, setValue];
}

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useState(() => {
    if (typeof window === 'undefined') return;
    
    const mediaQuery = window.matchMedia(query);
    const handler = (event: MediaQueryListEvent) => setMatches(event.matches);

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  });

  return matches;
}

export function useClickOutside(
  ref: React.RefObject<HTMLElement>,
  handler: () => void
): void {
  useState(() => {
    const listener = (event: MouseEvent | TouchEvent) => {
      if (!ref.current || ref.current.contains(event.target as Node)) {
        return;
      }
      handler();
    };

    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);

    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  });
}
