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
