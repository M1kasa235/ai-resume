export const APP_CONFIG = {
  name: 'AI Job Assistant',
  version: '1.0.0',
  description: 'AI-powered job search assistant',
  author: 'AI Team',
  repository: 'https://github.com/your-org/ai-job-assistant',
  homepage: 'https://ai-job-assistant.com',
  keywords: ['ai', 'job', 'assistant', 'career', 'recruitment'],
} as const;

export const API_CONFIG = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  retryCount: 3,
  retryDelay: 1000,
} as const;

export const ROUTES = {
  home: '/',
  dashboard: '/dashboard',
  jobs: '/jobs',
  jobsDetail: '/jobs/:id',
  questions: '/questions',
  workbench: '/workbench',
  profile: '/profile',
  settings: '/settings',
  auth: {
    login: '/auth/login',
    register: '/auth/register',
    forgotPassword: '/auth/forgot-password',
  },
  error: {
    notFound: '/404',
    forbidden: '/403',
  },
} as const;

export const PAGINATION = {
  defaultPageSize: 20,
  pageSizeOptions: [10, 20, 50, 100],
  maxPageSize: 100,
} as const;

export const STORAGE_KEYS = {
  user: 'user-storage',
  theme: 'theme-storage',
  language: 'language-storage',
  preferences: 'preferences-storage',
} as const;

export const THEMES = {
  light: 'light',
  dark: 'dark',
} as const;

export const LANGUAGES = {
  zhCN: 'zh-CN',
  zhTW: 'zh-TW',
  en: 'en',
} as const;

export const DATE_FORMATS = {
  full: 'YYYY-MM-DD HH:mm:ss',
  date: 'YYYY-MM-DD',
  time: 'HH:mm:ss',
  relative: 'relative',
} as const;

export const COLORS = {
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  error: '#ff4d4f',
  info: '#1890ff',
} as const;

export const BREAKPOINTS = {
  xs: 480,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600,
} as const;

export const ANIMATION_DURATION = {
  fast: 150,
  normal: 300,
  slow: 500,
} as const;