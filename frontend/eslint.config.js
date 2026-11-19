import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', '.vite', 'node_modules']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaVersion: 'latest',
        ecmaFeatures: { jsx: true },
        sourceType: 'module',
      },
    },
    rules: {
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
    },
  },
  // Archivos de configuración (Node)
  {
    files: ['*.config.js'],
    languageOptions: { globals: globals.node },
  },
  // Pruebas E2E (Cypress): globals de Mocha/Chai/Cypress
  {
    files: ['cypress/**/*.{js,jsx}', 'cypress.config.js'],
    languageOptions: {
      globals: {
        ...globals.node,
        cy: 'readonly',
        Cypress: 'readonly',
        describe: 'readonly',
        context: 'readonly',
        it: 'readonly',
        before: 'readonly',
        after: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        expect: 'readonly',
        assert: 'readonly',
      },
    },
  },
  // Pruebas unitarias (Vitest)
  {
    files: ['src/**/*.test.{js,jsx}', 'src/**/__tests__/**/*.{js,jsx}', 'src/test/**/*.{js,jsx}'],
    languageOptions: {
      globals: {
        ...globals.node,
        describe: 'readonly',
        it: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        vi: 'readonly',
        beforeAll: 'readonly',
        afterAll: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
      },
    },
  },
])
