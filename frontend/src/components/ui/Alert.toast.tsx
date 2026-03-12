import { useAlert, type AlertPosition } from './Alert.context';
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
