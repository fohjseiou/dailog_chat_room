import { Link, useLocation } from 'react-router-dom';
import { Menu, Typography } from 'antd';
import { MessageOutlined, BookOutlined, SafetyCertificateOutlined } from '@ant-design/icons';

const { Title } = Typography;

export function Navigation() {
  const location = useLocation();

  const getCurrentKey = () => {
    if (location.pathname === '/' || location.pathname.startsWith('/chat')) {
      return 'chat';
    }
    if (location.pathname === '/knowledge') {
      return 'knowledge';
    }
    return 'chat';
  };

  const menuItems = [
    {
      key: 'chat',
      icon: <MessageOutlined />,
      label: <Link to="/">对话咨询</Link>,
    },
    {
      key: 'knowledge',
      icon: <BookOutlined />,
      label: <Link to="/knowledge">知识库管理</Link>,
    },
  ];

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <SafetyCertificateOutlined className="text-white text-lg" />
              </div>
              <Title level={5} className="!mb-0 text-gray-900">法律咨询助手</Title>
            </Link>
          </div>

          {/* Navigation Links */}
          <Menu
            mode="horizontal"
            selectedKeys={[getCurrentKey()]}
            items={menuItems}
            className="border-0 [&_.anticon]:mr-2"
          />
        </div>
      </div>
    </nav>
  );
}
