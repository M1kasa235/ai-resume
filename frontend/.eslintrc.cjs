module.exports = {
  ignorePatterns: ['dist', 'node_modules', 'coverage', '*.config.ts', '.storybook'],
  extends: [
    'eslint:recommended',
    'plugin:react-hooks/recommended',
    'plugin:react/recommended',
    'prettier'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ['react-hooks', 'react', 'import'],
  settings: {
    react: {
      version: 'detect',
    },
  },
  env: {
    browser: true,
    node: true,
    es6: true,
  },
  globals: {
    React: 'readonly',
    setTimeout: 'readonly',
    clearTimeout: 'readonly',
    window: 'readonly',
    document: 'readonly',
    console: 'readonly',
    URLSearchParams: 'readonly',
    NodeJS: 'readonly',
    MouseEvent: 'readonly',
    TouchEvent: 'readonly',
    Node: 'readonly',
    MediaQueryListEvent: 'readonly',
    HTMLElement: 'readonly',
    File: 'readonly',
    FormData: 'readonly',
    localStorage: 'readonly',
  },
  rules: {
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
    'react/jsx-uses-react': 'off',
    'react/jsx-uses-vars': 'error',
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-undef': 'error',
    'no-console': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    'eqeqeq': ['error', 'always'],
    'import/order': [
      'error',
      {
        groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
        'newlines-between': 'always',
        alphabetize: { order: 'asc', caseInsensitive: true },
        pathGroups: [
          {
            pattern: 'react',
            group: 'external',
            position: 'before',
          },
          {
            pattern: '@/**',
            group: 'internal',
            position: 'before',
          },
        ],
        pathGroupsExcludedImportTypes: ['react'],
      },
    ],
    'import/no-unresolved': 'off',
    'no-prototype-builtins': 'warn',
  },
};