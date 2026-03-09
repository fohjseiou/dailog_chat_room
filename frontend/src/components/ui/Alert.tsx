import { useEffect, useState } from 'react';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

export type AlertType = 'success' | 'error' | 'warning' | 'info';

interface AlertProps {
  type: AlertType;
  message: string;
  onClose?: () => void;
  duration?: number;
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
};

export function Alert({ type, message, onClose, duration }: AlertProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (duration && duration > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration]);

  const handleClose = () => {
    setVisible(false);
    onClose?.();
  };

  const config = ALERT_CONFIG[type];
  const Icon = config.icon;

  if (!visible) return null;

  return (
    <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4 mb-4`}>
      <div className="flex items-start">
        <Icon className={`h-5 w-5 ${config.iconColor} mr-3 mt-0.5 flex-shrink-0`} />
        <div className={`flex-1 ${config.textColor} text-sm`}>
          {message}
        </div>
        {onClose && (
          <button
            onClick={handleClose}
            className={`ml-3 ${config.textColor} hover:opacity-75 transition-opacity`}
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}

// Toast Container for global alerts
interface Toast {
  id: string;
  type: AlertType;
  message: string;
}

let toastId = 0;
let toastListeners: ((toasts: Toast[]) => void)[] = [];

export const toast = {
  show: (message: string, type: AlertType = 'info', duration = 5000) => {
    const id = `toast-${toastId++}`;
    const newToast: Toast = { id, type, message };

    // Add toast to all listeners
    toastListeners.forEach(listener => {
      const listenerToasts = (listener as any)._toasts || [];
      listener([...listenerToasts, newToast]);
    });

    // Auto remove after duration
    if (duration > 0) {
      setTimeout(() => {
        toast.remove(id);
      }, duration);
    }

    return id;
  },

  success: (message: string, duration?: number) => toast.show(message, 'success', duration),
  error: (message: string, duration?: number) => toast.show(message, 'error', duration),
  warning: (message: string, duration?: number) => toast.show(message, 'warning', duration),
  info: (message: string, duration?: number) => toast.show(message, 'info', duration),

  remove: (id: string) => {
    toastListeners.forEach(listener => {
      const listenerToasts = (listener as any)._toasts || [];
      (listener as any)._toasts = listenerToasts.filter(t => t.id !== id);
    });
  },
};

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    (setToasts as any)._toasts = toasts;
    toastListeners.push(setToasts);

    return () => {
      toastListeners = toastListeners.filter(l => l !== setToasts);
    };
  }, [toasts]);

  const removeToast = (id: string) => {
    setToasts(toasts.filter(t => t.id !== id));
  };

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
      {toasts.map((toast) => (
        <Alert
          key={toast.id}
          type={toast.type}
          message={toast.message}
          onClose={() => removeToast(toast.id)}
          duration={0}
        />
      ))}
    </div>
  );
}
