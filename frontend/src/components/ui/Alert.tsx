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
