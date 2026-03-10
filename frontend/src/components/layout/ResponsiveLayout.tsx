import { useState } from 'react';
import { Layout, Drawer, Button, Typography } from 'antd';
import { CloseOutlined, MenuOutlined, SafetyCertificateOutlined } from '@ant-design/icons';

const { Header } = Layout;
const { Title } = Typography;

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  sidebarContent: React.ReactNode;
}

export function ResponsiveLayout({ children, sidebarContent }: ResponsiveLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <Layout className="h-screen bg-gray-50">
      {/* Desktop Sidebar */}
      <Layout.Sider
        width={256}
        className="hidden md:block !bg-gray-50 border-r border-gray-200"
      >
        {sidebarContent}
      </Layout.Sider>

      {/* Mobile Sidebar Drawer */}
      <Drawer
        title={null}
        placement="left"
        onClose={() => setSidebarOpen(false)}
        open={sidebarOpen}
        width={256}
        className="md:hidden"
        styles={{
          body: { padding: 0 },
          header: { borderBottom: '1px solid #e5e7eb' },
        }}
        headerStyle={{ borderBottom: '1px solid #e5e7eb' }}
      >
        <div className="flex items-center justify-between p-4 border-b">
          <Title level={5} className="!mb-0">会话列表</Title>
        </div>
        {sidebarContent}
      </Drawer>

      {/* Main Content */}
      <Layout className="flex flex-col overflow-hidden">
        {/* Mobile Header */}
        <Header className="md:hidden flex items-center justify-between px-4 bg-white border-b border-gray-200 h-16">
          <Button
            type="text"
            icon={<MenuOutlined />}
            onClick={() => setSidebarOpen(true)}
          />
          <div className="flex items-center gap-2">
            <SafetyCertificateOutlined className="text-blue-600" />
            <Title level={5} className="!mb-0">法律咨询助手</Title>
          </div>
          <div style={{ width: 36 }} />
        </Header>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </Layout>
    </Layout>
  );
}
