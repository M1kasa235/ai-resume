/// <reference types="vite/client" />

declare module '*.scss' {
  const content: Record<string, string>;
  export default content;
}

declare module '*.css' {
  const content: Record<string, string>;
  export default content;
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_SENTRY_DSN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
  readonly url: string;
}

// Example usage:
// const isDevelopment = import.meta.env.MODE === 'development';
// const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Type declaration for import.meta
declare const importMeta: ImportMeta;
