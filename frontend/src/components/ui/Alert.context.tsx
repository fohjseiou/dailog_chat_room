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
