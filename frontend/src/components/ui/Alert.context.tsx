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
