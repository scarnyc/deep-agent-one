/**
 * Jest Configuration for Unit and Integration Testing (Phase 0)
 *
 * This configuration file sets up Jest for testing Next.js components,
 * hooks, and utilities. It includes:
 * - jsdom test environment for React component testing
 * - Path alias resolution (@/ imports)
 * - Coverage collection and thresholds (80% minimum)
 * - Mock setup for Next.js and third-party dependencies
 *
 * Usage:
 * - npm test: Run all tests
 * - npm run test:watch: Run tests in watch mode
 * - npm run test:coverage: Generate coverage report
 *
 * References:
 * - https://nextjs.org/docs/testing/jest
 * - https://jestjs.io/docs/configuration
 *
 * @type {import('jest').Config}
 */

const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  // Add more setup options before each test is run
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Test environment
  testEnvironment: 'jest-environment-jsdom',

  // Module name mapper for path aliases
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },

  // Coverage configuration
  collectCoverageFrom: [
    'app/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    'hooks/**/*.{js,jsx,ts,tsx}',
    'types/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/.next/**',
    '!**/coverage/**',
    '!**/dist/**',
  ],

  // Coverage thresholds - 80% minimum for Phase 0
  coverageThreshold: {
    global: {
      statements: 80,
      branches: 80,
      functions: 80,
      lines: 80,
    },
  },

  // Test match patterns
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)',
  ],

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],

  // Ignore patterns
  testPathIgnorePatterns: ['/node_modules/', '/.next/', '/e2e/'],

  // Transform ESM modules
  transformIgnorePatterns: [
    'node_modules/(?!(react-error-boundary|@copilotkit)/)',
  ],

  // Verbose output
  verbose: true,
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
