# Frontend Bug Fixes Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all frontend bugs including Alert component API mismatch, test failures, TypeScript errors, and missing ESLint configuration.

**Architecture:** Redesign Alert component with Context API (AlertProvider + useAlert hook), fix test infrastructure with proper type declarations, add ESLint config, and validate all fixes.

**Tech Stack:** React, TypeScript, Vitest, Tailwind CSS, Ant Design, Zustand

**Design Reference:** `docs/superpowers/specs/2026-03-11-frontend-bug-fixes-design.md`

---

## Chunk 1: Alert Component System Redesign

This chunk implements the complete Alert component system with AlertProvider, useAlert hook, and redesigned Alert component to match test expectations.

### Task 1: Create Alert context file

**Files:**
- Create: `frontend/src/components/ui/Alert.context.tsx`

- [ ] **Step 1: Create AlertContext and AlertProvider**

```typescript
import { createContext, useContext, ReactNode } from 'react';

export type AlertVariant = 'success' | 'error' | 'warning' | 'info' | 'default';

export type AlertPosition = 'top-left' | 'top-center' | 'top-right' |
  'bottom-left' | 'bottom-center' | 'bottom-right';

export interface AlertItem {
  id: string;
  variant: AlertVariant;
  title?: string;
  message: string;
  duration?: number;
}

export interface AlertOptions {
  duration?: number;
}

export interface AlertContextValue {
  alerts: AlertItem[];
  showToast: (message: string, options?: AlertOptions) => string;
  showSuccess: (message: string, options?: AlertOptions) => string;
  showError: (message: string, options?: AlertOptions) => string;
  showWarning: (message: string, options?: AlertOptions) => string;
  showInfo: (message: string, options?: AlertOptions) => string;
  close: (id: string) => void;
  closeAll: () => void;
}

export const AlertContext = createContext<AlertContextValue | undefined>(undefined);

export interface AlertProviderProps {
  defaultDuration?: number;
  position?: AlertPosition;
  maxAlerts?: number;
  children: ReactNode;
}

export function AlertProvider({
  defaultDuration = 5000,
  position = 'top-right',
  maxAlerts = 5,
  children
}: AlertProviderProps) {
  // Implementation will be completed in the next step
  throw new Error('Not implemented yet');
}

export function useAlert(): AlertContextValue {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useAlert must be used within AlertProvider');
  }
  return context;
}
```

- [ ] **Step 2: Run type check to verify file compiles**

Run: `cd frontend && npm run type-check`
Expected: PASS (no errors)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/Alert.context.tsx
git commit -m "feat: add AlertContext and Provider skeleton"
```

---

### Task 2: Implement AlertProvider state management

**Files:**
- Modify: `frontend/src/components/ui/Alert.context.tsx`

- [ ] **Step 1: Implement AlertProvider with useState**

Replace the entire file with:

```typescript
import { createContext, useContext, ReactNode, useState, useCallback } from 'react';

export type AlertVariant = 'success' | 'error' | 'warning' | 'info' | 'default';

export type AlertPosition = 'top-left' | 'top-center' | 'top-right' |
  'bottom-left' | 'bottom-center' | 'bottom-right';

export interface AlertItem {
  id: string;
  variant: AlertVariant;
  title?: string;
  message: string;
  duration?: number;
}

export interface AlertOptions {
  duration?: number;
}

export interface AlertContextValue {
  alerts: AlertItem[];
  position: AlertPosition;
  showToast: (message: string, options?: AlertOptions) => string;
  showSuccess: (message: string, options?: AlertOptions) => string;
  showError: (message: string, options?: AlertOptions) => string;
  showWarning: (message: string, options?: AlertOptions) => string;
  showInfo: (message: string, options?: AlertOptions) => string;
  close: (id: string) => void;
  closeAll: () => void;
}

export const AlertContext = createContext<AlertContextValue | undefined>(undefined);

let alertId = 0;

export interface AlertProviderProps {
  defaultDuration?: number;
  position?: AlertPosition;
  maxAlerts?: number;
  children: ReactNode;
}

export function AlertProvider({
  defaultDuration = 5000,
  position = 'top-right',
  maxAlerts = 5,
  children
}: AlertProviderProps) {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  const removeAlert = useCallback((id: string) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== id));
  }, []);

  const addAlert = useCallback((
    message: string,
    variant: AlertVariant,
    options?: AlertOptions
  ): string => {
    const id = `alert-${alertId++}`;
    const alert: AlertItem = {
      id,
      variant,
      message,
      duration: options?.duration ?? defaultDuration,
    };

    setAlerts((prev) => {
      const newAlerts = [...prev, alert];
      // Enforce maxAlerts limit by removing oldest if exceeded
      if (newAlerts.length > maxAlerts!) {
        return newAlerts.slice(-maxAlerts!);
      }
      return newAlerts;
    });

    if (alert.duration && alert.duration > 0) {
      setTimeout(() => {
        removeAlert(id);
      }, alert.duration);
    }

    return id;
  }, [defaultDuration, maxAlerts, removeAlert]);

  const showToast = useCallback((message: string, options?: AlertOptions) => {
    return addAlert(message, 'default', options);
  }, [addAlert]);

  const showSuccess = useCallback((message: string, options?: AlertOptions) => {
    return addAlert(message, 'success', options);
  }, [addAlert]);

  const showError = useCallback((message: string, options?: AlertOptions) => {
    return addAlert(message, 'error', options);
  }, [addAlert]);

  const showWarning = useCallback((message: string, options?: AlertOptions) => {
    return addAlert(message, 'warning', options);
  }, [addAlert]);

  const showInfo = useCallback((message: string, options?: AlertOptions) => {
    return addAlert(message, 'info', options);
  }, [addAlert]);

  const close = useCallback((id: string) => {
    removeAlert(id);
  }, [removeAlert]);

  const closeAll = useCallback(() => {
    setAlerts([]);
  }, []);

  const value: AlertContextValue = {
    alerts,
    position,
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    close,
    closeAll,
  };

  return (
    <AlertContext.Provider value={value}>
      {children}
    </AlertContext.Provider>
  );
}

export function useAlert(): AlertContextValue {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useAlert must be used within AlertProvider');
  }
  return context;
}
```

- [ ] **Step 2: Run type check to verify implementation**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/Alert.context.tsx
git commit -m "feat: implement AlertProvider state management"
```

---

### Task 3: Rewrite Alert component with new API

**Files:**
- Modify: `frontend/src/components/ui/Alert.tsx`

- [ ] **Step 1: Write new Alert component with variant prop**

Replace entire file with:

```typescript
import { ReactNode } from 'react';
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react';
import type { AlertVariant } from './Alert.context';

export type { AlertVariant } from './Alert.context';

export interface AlertProps {
  variant?: AlertVariant;
  title?: string;
  showIcon?: boolean;
  closable?: boolean;
  onClose?: () => void;
  className?: string;
  children: ReactNode;
}

const ALERT_CONFIG = {
  success: {
    icon: CheckCircle,
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
    iconColor: 'text-green-500',
  },
  error: {
    icon: AlertCircle,
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800',
    iconColor: 'text-red-500',
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-800',
    iconColor: 'text-yellow-500',
  },
  info: {
    icon: Info,
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    textColor: 'text-blue-800',
    iconColor: 'text-blue-500',
  },
  default: {
    icon: Info,
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-200',
    textColor: 'text-gray-800',
    iconColor: 'text-gray-500',
  },
};

export function Alert({
  variant = 'default',
  title,
  showIcon = true,
  closable = false,
  onClose,
  className = '',
  children,
}: AlertProps) {
  const config = ALERT_CONFIG[variant];
  const Icon = config.icon;

  return (
    <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        {showIcon && (
          <Icon className={`h-5 w-5 ${config.iconColor} mr-3 mt-0.5 flex-shrink-0`} />
        )}
        <div className={`flex-1 ${config.textColor} text-sm`}>
          {title && <div className="font-semibold mb-1">{title}</div>}
          <div>{children}</div>
        </div>
        {closable && (
          <button
            onClick={onClose}
            className={`ml-3 ${config.textColor} hover:opacity-75 transition-opacity`}
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}

export { AlertProvider, useAlert, type AlertItem, type AlertContextValue, type AlertPosition } from './Alert.context';
```

- [ ] **Step 2: Run type check to verify new Alert API**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/Alert.tsx
git commit -m "feat: rewrite Alert component with variant prop API"
```

---

### Task 4: Create ToastContainer component

**Files:**
- Create: `frontend/src/components/ui/Alert.toast.tsx`

- [ ] **Step 1: Create ToastContainer component with position support**

```typescript
import { useAlert, type AlertItem, type AlertPosition } from './Alert.context';
import { Alert } from './Alert';

const POSITION_CLASSES: Record<AlertPosition, string> = {
  'top-left': 'fixed top-4 left-4 z-50',
  'top-center': 'fixed top-4 left-1/2 -translate-x-1/2 z-50',
  'top-right': 'fixed top-4 right-4 z-50',
  'bottom-left': 'fixed bottom-4 left-4 z-50',
  'bottom-center': 'fixed bottom-4 left-1/2 -translate-x-1/2 z-50',
  'bottom-right': 'fixed bottom-4 right-4 z-50',
};

export function ToastContainer() {
  const { alerts, close, position } = useAlert();

  return (
    <div className={`${POSITION_CLASSES[position]} flex flex-col gap-2 max-w-sm w-full`}>
      {alerts.map((alert) => (
        <Alert
          key={alert.id}
          variant={alert.variant}
          title={alert.title}
          showIcon
          closable
          onClose={() => close(alert.id)}
        >
          {alert.message}
        </Alert>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/Alert.toast.tsx
git commit -m "feat: add ToastContainer component with position support"
```

---

### Task 5: Create UI components index file

**Files:**
- Create: `frontend/src/components/ui/index.ts`

- [ ] **Step 1: Export all Alert components**

```typescript
export { Alert, ToastContainer } from './Alert';
export { AlertProvider, useAlert } from './Alert.context';
export type { AlertProps, AlertVariant } from './Alert';
export type { AlertItem, AlertContextValue, AlertProviderProps, AlertPosition, AlertOptions } from './Alert.context';
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ui/index.ts
git commit -m "feat: add UI components index file"
```

---

### Task 6: Update App.tsx to use new Alert imports

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update Alert imports**

Replace line 6:
```typescript
// Before:
import { ToastContainer } from './components/ui/Alert';

// After:
import { ToastContainer, AlertProvider } from './components/ui';
```

- [ ] **Step 2: Wrap AntdProvider content with AlertProvider**

Update the function body to wrap with AlertProvider (after AntdProvider opening, before the closing tag):

```typescript
// Before:
function App() {
  return (
    <AntdProvider>
      <div className="App">
        <Routes>
          {/* Login page without navigation */}
          <Route path="/login" element={<LoginPage />} />

          {/* Main app with navigation */}
          <Route
            path="/*"
            element={
              <>
                <Navigation />
                <Routes>
                  <Route path="/" element={<ChatView />} />
                  <Route path="/chat" element={<ChatView />} />
                  <Route path="/chat/:sessionId" element={<SessionDetailPage />} />
                  <Route path="/knowledge" element={<KnowledgePage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
                <ToastContainer />
              </>
            }
          />
        </Routes>
      </div>
    </AntdProvider>
  );
}

// After:
function App() {
  return (
    <AntdProvider>
      <AlertProvider>
        <div className="App">
          <Routes>
            {/* Login page without navigation */}
            <Route path="/login" element={<LoginPage />} />

            {/* Main app with navigation */}
            <Route
              path="/*"
              element={
                <>
                  <Navigation />
                  <Routes>
                    <Route path="/" element={<ChatView />} />
                    <Route path="/chat" element={<ChatView />} />
                    <Route path="/chat/:sessionId" element={<SessionDetailPage />} />
                    <Route path="/knowledge" element={<KnowledgePage />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                  <ToastContainer />
                </>
              }
            />
          </Routes>
        </div>
      </AlertProvider>
    </AntdProvider>
  );
}
```

- [ ] **Step 3: Run type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "fix: use new Alert exports and wrap with AlertProvider"
```

---

### Task 7: Fix ChatView.tsx Alert usage

**Files:**
- Modify: `frontend/src/components/chat/ChatView.tsx`

- [ ] **Step 1: Update Alert import and usage**

Replace line 8:
```typescript
// Before:
import { Empty, Alert, Space, Typography } from 'antd';

// After:
import { Empty, Space, Typography } from 'antd';
import { Alert } from '../../components/ui';
```

- [ ] **Step 2: Update Alert component props**

Replace lines 112-119:
```typescript
// Before:
{error && (
  <Alert
    message={error}
    type="error"
    closable
    onClose={clearError}
    showIcon
    className="mb-4"
  />
)}

// After:
{error && (
  <Alert
    variant="error"
    title="错误"
    showIcon
    closable
    onClose={clearError}
    className="mb-4"
  >
    {error}
  </Alert>
)}
```

- [ ] **Step 3: Run type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 4: Run tests to verify Alert tests pass**

Run: `cd frontend && npm test -- src/components/ui/Alert.test.tsx --run`
Expected: All 17 Alert tests pass

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/chat/ChatView.tsx
git commit -m "fix: use custom Alert component in ChatView"
```

---

## Chunk 2: Test Infrastructure Fix

This chunk fixes the TypeScript type errors for jest-dom matchers and simplifies the test configuration.

### Task 8: Create vitest.d.ts type declaration file

**Files:**
- Create: `frontend/src/test/vitest.d.ts`

- [ ] **Step 1: Create type declaration file**

```typescript
/// <reference types="vitest/globals" />
import '@testing-library/jest-dom/vitest';

declare module 'vitest' {
  interface Assertion<T = any> {
    toBeInTheDocument(): T;
    toHaveClass(...classNames: string[]): T;
    toHaveValue(value: string | number): T;
    toBeDisabled(): T;
    toHaveStyle(css: string | Record<string, string>): T;
    toHaveTextContent(text: string | RegExp): T;
    toBeVisible(): T;
    toBeEmpty(): T;
    toHaveAttribute(name: string, value?: any): T;
  }
}
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/test/vitest.d.ts
git commit -m "test: add vitest type declarations for jest-dom matchers"
```

---

### Task 9: Update setup.ts with type imports

**Files:**
- Modify: `frontend/src/test/setup.ts`

- [ ] **Step 1: Add type import statement**

Add this line after the existing imports:

```typescript
import { expect, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';
import type {} from './vitest';  // ← Add this line

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npm run type-check`
Expected: PASS (no more toBeInTheDocument errors)

- [ ] **Step 3: Run all tests to verify they pass**

Run: `cd frontend && npm test -- --run`
Expected: All tests pass (Alert tests + others)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/test/setup.ts
git commit -m "test: add type import for vitest declarations"
```

---

### Task 10: Remove test config from vite.config.ts

**Files:**
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: Remove test configuration block**

Delete lines 21-37 (the entire `test` block):

```typescript
// Before:
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {      // ← DELETE all of this
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    css: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      exclude: [
        "node_modules/",
        "src/test/",
        "**/*.d.ts",
        "**/*.config.*",
        "**/dist/**",
      ],
    },
  },
});

// After:
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

- [ ] **Step 2: Run tests to ensure they still use vitest.config.ts**

Run: `cd frontend && npm test -- --run`
Expected: All tests pass

- [ ] **Step 3: Run build to verify vite still works**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/vite.config.ts
git commit -m "config: remove test config from vite.config.ts (use vitest.config.ts)"
```

---

## Chunk 3: TypeScript Configuration Fix

This chunk updates TypeScript configuration to recognize vitest and jest-dom types.

### Task 11: Update tsconfig.json with type references

**Files:**
- Modify: `frontend/tsconfig.json`

- [ ] **Step 1: Add types to compilerOptions**

Add `types` array to `compilerOptions`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": "./src",
    "paths": {
      "@/*": ["*"]
    },
    "types": ["vitest/globals", "@testing-library/jest-dom"]
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npm run type-check`
Expected: PASS (0 errors)

- [ ] **Step 3: Commit**

```bash
git add frontend/tsconfig.json
git commit -m "config: add vitest and jest-dom types to tsconfig"
```

---

## Chunk 4: ESLint Configuration

This chunk creates the missing ESLint configuration file.

### Task 12: Create eslint.config.js

**Files:**
- Create: `frontend/eslint.config.js`

- [ ] **Step 1: Create ESLint flat config file**

```javascript
import js from '@eslint/js'
import globals from 'globals'
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import react from 'eslint-plugin-react'

export default [
  { ignores: ['dist', '.eslintrc.cjs'] },
  { globals: globals.browser },
  js.configs.recommended,
  react.configs.flat.recommended,
  reactHooks.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: {
      'react-refresh': reactRefresh,
    },
    rules: {
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      'react/prop-types': 'off',
      'react/react-in-jsx-scope': 'off',
    },
  },
]
```

- [ ] **Step 2: Install missing ESLint dependencies**

Run: `cd frontend && npm install --save-dev @eslint/js globals eslint-plugin-react`
Expected: Dependencies installed successfully

- [ ] **Step 3: Run ESLint**

Run: `cd frontend && npm run lint`
Expected: Runs without configuration error (may have warnings)

- [ ] **Step 4: Commit**

```bash
git add frontend/eslint.config.js frontend/package.json frontend/package-lock.json
git commit -m "config: add ESLint flat configuration"
```

---

## Chunk 5: Minor Issues Cleanup

This chunk fixes minor code quality issues like unused imports.

### Task 13: Remove unused import from UserMenu.tsx

**Files:**
- Modify: `frontend/src/components/auth/UserMenu.tsx`

- [ ] **Step 1: Remove UserOutlined from imports**

```typescript
// Before:
import { UserOutlined, LogoutOutlined } from '@ant-design/icons';

// After:
import { LogoutOutlined } from '@ant-design/icons';
```

- [ ] **Step 2: Run type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/auth/UserMenu.tsx
git commit -m "refactor: remove unused UserOutlined import"
```

---

## Chunk 6: Comprehensive Validation

This chunk runs all validation commands to verify all fixes work correctly.

### Task 14: Run full test suite

**Files:** (None - validation only)

- [ ] **Step 1: Run all tests**

Run: `cd frontend && npm test -- --run`
Expected: All tests pass (0 failures)

- [ ] **Step 2: Run tests with coverage**

Run: `cd frontend && npm run test:coverage`
Expected: Coverage report generated, all tests pass

- [ ] **Step 3: Document test results**

Expected output should show:
- ✓ All Alert component tests pass
- ✓ All existing tests still pass
- ✓ No test failures

---

### Task 15: Run type check verification

**Files:** (None - validation only)

- [ ] **Step 1: Run TypeScript type check**

Run: `cd frontend && npm run type-check`
Expected: 0 errors

- [ ] **Step 2: Verify type errors are fixed**

Expected output should NOT contain:
- ✗ Property 'toBeInTheDocument' does not exist
- ✗ Property 'toHaveClass' does not exist
- ✗ Any other jest-dom matcher errors

---

### Task 16: Run ESLint verification

**Files:** (None - validation only)

- [ ] **Step 1: Run ESLint**

Run: `cd frontend && npm run lint`
Expected: Runs successfully, no "no configuration file" error

- [ ] **Step 2: Fix any auto-fixable ESLint issues**

Run: `cd frontend && npm run lint -- --fix`
Expected: Some issues auto-fixed

---

### Task 17: Run build verification

**Files:** (None - validation only)

- [ ] **Step 1: Run production build**

Run: `cd frontend && npm run build`
Expected: Build completes successfully with no errors

- [ ] **Step 2: Verify dist folder exists**

Run: `ls -la frontend/dist`
Expected: dist folder contains built files

---

### Task 18: Manual functional verification

**Files:** (None - validation only)

- [ ] **Step 1: Start dev server**

Run: `cd frontend && npm run dev`
Expected: Dev server starts on port 5173

- [ ] **Step 2: Test login/logout flow**

Manual verification:
1. Navigate to http://localhost:5173
2. Click "登录" button
3. Enter credentials and submit
4. Verify user menu appears
5. Click "退出登录"
6. Verify redirect to login page

- [ ] **Step 3: Test chat functionality**

Manual verification:
1. Login as admin user
2. Send a test message
3. Verify streaming response works
4. Verify alerts display correctly
5. Verify error handling works

- [ ] **Step 4: Test Alert component**

Manual verification:
1. Trigger a success message
2. Verify success alert displays with icon
3. Click close button
4. Verify alert closes
5. Test error, warning, info variants

- [ ] **Step 5: Document results**

Record all manual test results in a comment

---

## Success Criteria Verification

After completing all tasks, verify:

- [ ] All 17 Alert tests pass
- [ ] All other tests pass (no regressions)
- [ ] 0 TypeScript errors
- [ ] 0 ESLint configuration errors
- [ ] Build succeeds
- [ ] All manual tests pass
- [ ] No regressions introduced

## Implementation Notes

1. **Alert Component Redesign**: The Alert component now uses `variant` instead of `type` to match test expectations and includes `showIcon`, `closable`, `title`, and `className` props.

2. **AlertProvider**: Uses React Context API for global alert state management. The `useAlert` hook provides convenient methods like `success()`, `error()`, `warning()`, `info()`, and `toast()`.

3. **Type Declarations**: The `vitest.d.ts` file extends Vitest's Assertion type with jest-dom matchers, fixing all TypeScript errors related to test assertions.

4. **Configuration Separation**: Test configuration is now exclusively in `vitest.config.ts`, while `vite.config.ts` only handles build configuration.

5. **ESLint Setup**: Uses the new flat config format with React, TypeScript, and React Hooks rules enabled.

## Rollback Plan

If any task causes issues, use git to revert:

```bash
git revert <commit-hash>
# Or reset to specific commit
git reset --hard <commit-hash>
```

Each task commits frequently, allowing granular rollback if needed.
