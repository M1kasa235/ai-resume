import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';
import compression from 'vite-plugin-compression';
import { visualizer } from 'rollup-plugin-visualizer';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const isProd = mode === 'production';

  return {
    plugins: [
      react(),
      // 开发环境禁用：PWA/压缩会干扰 Vite 原生 ESM + HMR，导致 lazy route 404
      ...(isProd
        ? [
            compression({
              algorithm: 'gzip',
              ext: '.gz',
            }),
            compression({
              algorithm: 'brotliCompress',
              ext: '.br',
            }),
            visualizer({
              open: false,
              gzipSize: true,
              brotliSize: true,
            }),
            VitePWA({
              registerType: 'autoUpdate',
              includeAssets: ['favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
              manifest: {
                name: 'Offer Pilot',
                short_name: 'Offer Pilot',
                description: '智能求职助手 — AI 驱动的求职、面试与简历优化平台',
                theme_color: '#1677ff',
                background_color: '#ffffff',
                display: 'standalone',
                icons: [
                  {
                    src: 'pwa-192x192.png',
                    sizes: '192x192',
                    type: 'image/png',
                  },
                  {
                    src: 'pwa-512x512.png',
                    sizes: '512x512',
                    type: 'image/png',
                  },
                ],
              },
              workbox: {
                globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
                runtimeCaching: [
                  {
                    urlPattern: /^https:\/\/api\./i,
                    handler: 'NetworkFirst',
                    options: {
                      cacheName: 'api-cache',
                      expiration: {
                        maxEntries: 100,
                        maxAgeSeconds: 60 * 60 * 24,
                      },
                    },
                  },
                ],
              },
            }),
          ]
        : []),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@components': path.resolve(__dirname, './src/components'),
        '@features': path.resolve(__dirname, './src/features'),
        '@hooks': path.resolve(__dirname, './src/hooks'),
        '@utils': path.resolve(__dirname, './src/utils'),
        '@services': path.resolve(__dirname, './src/services'),
        '@stores': path.resolve(__dirname, './src/stores'),
        '@styles': path.resolve(__dirname, './src/styles'),
        '@assets': path.resolve(__dirname, './src/assets'),
        '@types': path.resolve(__dirname, './src/types'),
        '@constants': path.resolve(__dirname, './src/constants'),
        '@router': path.resolve(__dirname, './src/router'),
        '@locales': path.resolve(__dirname, './src/locales'),
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: `@import "@/styles/variables.scss";`,
        },
      },
      modules: {
        localsConvention: 'camelCaseOnly',
      },
    },
    build: {
      target: 'esnext',
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: isProd,
          drop_debugger: isProd,
        },
      },
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'antd-vendor': ['antd', '@ant-design/icons', '@ant-design/pro-components'],
            'state-vendor': ['zustand', 'immer', '@tanstack/react-query'],
            'i18n-vendor': ['react-i18next', 'i18next'],
            'utils-vendor': ['axios', 'dayjs', 'lodash-es'],
            'charts-vendor': ['recharts'],
          },
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
        },
      },
      chunkSizeWarningLimit: 500,
      sourcemap: !isProd,
    },
    server: {
      host: true,
      port: 5173,
      strictPort: true,
      open: true,
      proxy: {
        '/health': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8080',
          changeOrigin: true,
        },
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8080',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '/api'),
        },
        '/uploads': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8080',
          changeOrigin: true,
        },
      },
    },
    preview: {
      port: 4173,
    },
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        'antd',
        '@ant-design/icons',
        'zustand',
        'axios',
        'dayjs',
        'recharts',
      ],
    },
  };
});
