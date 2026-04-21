import '@testing-library/jest-dom';
import { vi, beforeEach, beforeAll } from 'vitest';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock IntersectionObserver
class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin: string = '0px';
  readonly thresholds: ReadonlyArray<number> = [];
  
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
  takeRecords() { return []; }
}
global.IntersectionObserver = MockIntersectionObserver;

// Mock ResizeObserver
class MockResizeObserver implements ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}
global.ResizeObserver = MockResizeObserver;

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
} as unknown as Storage;
Object.defineProperty(global, 'localStorage', { value: localStorageMock });

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
} as unknown as Storage;
Object.defineProperty(global, 'sessionStorage', { value: sessionStorageMock });

// Mock fetch
global.fetch = vi.fn();

// Mock Ant Design components
vi.mock('antd', () => ({
  ...vi.importActual('antd'),
  message: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
    loading: vi.fn(),
  },
  notification: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
    open: vi.fn(),
  },
}));

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn(),
  },
}));

// Mock react-router-dom
vi.mock('react-router-dom', () => ({
  ...vi.importActual('react-router-dom'),
  useNavigate: vi.fn(() => vi.fn()),
  useLocation: vi.fn(() => ({
    pathname: '/',
    search: '',
    hash: '',
    state: null,
  })),
  useParams: vi.fn(() => ({})),
  useSearchParams: vi.fn(() => [new URLSearchParams(), vi.fn()]),
}));

// Mock react-query
vi.mock('@tanstack/react-query', () => ({
  ...vi.importActual('@tanstack/react-query'),
  useQuery: vi.fn(() => ({
    data: null,
    isLoading: false,
    isError: false,
    error: null,
  })),
  useMutation: vi.fn(() => ({
    mutate: vi.fn(),
    isLoading: false,
    isError: false,
    error: null,
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
    setQueryData: vi.fn(),
  })),
}));

// Mock zustand
vi.mock('zustand', () => ({
  create: vi.fn(() => vi.fn()),
}));

// Mock dayjs
vi.mock('dayjs', () => ({
  default: vi.fn(() => ({
    format: vi.fn(() => '2024-01-01'),
    fromNow: vi.fn(() => '2 days ago'),
    diff: vi.fn(() => 2),
    add: vi.fn(() => vi.fn()),
    subtract: vi.fn(() => vi.fn()),
    startOf: vi.fn(() => vi.fn()),
    endOf: vi.fn(() => vi.fn()),
    isSame: vi.fn(() => false),
    isAfter: vi.fn(() => false),
    isBefore: vi.fn(() => false),
    isValid: vi.fn(() => true),
  })),
}));

// 清理所有 mocks
beforeEach(() => {
  vi.clearAllMocks();
});

// 模拟 console.error 以避免测试中的噪音
beforeAll(() => {
  const originalError = console.error;
  console.error = (...args) => {
    if (!args[0].includes('Warning: ReactDOM.render is deprecated')) {
      originalError(...args);
    }
  };
});