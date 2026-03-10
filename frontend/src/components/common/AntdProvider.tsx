import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';

/**
 * Ant Design Provider Component
 *
 * Wraps the application with Ant Design's ConfigProvider to enable:
 * - Chinese locale
 * - Consistent theme configuration
 * - Global Ant Design component settings
 */
export function AntdProvider({ children }: { children: React.ReactNode }) {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          // Use the existing color scheme from the project
          colorPrimary: '#2563eb',
          colorSuccess: '#10b981',
          colorWarning: '#f59e0b',
          colorError: '#ef4444',
          borderRadius: 8,
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
}
