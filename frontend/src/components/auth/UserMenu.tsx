import { Dropdown, Avatar, Space, Typography } from 'antd';
import { LogoutOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../stores/authStore';
import type { MenuProps } from 'antd';

const { Text } = Typography;

export function UserMenu() {
  const { user, logout } = useAuthStore();

  if (!user) {
    return null;
  }

  const getAvatarLetter = () => {
    return user.username.charAt(0).toUpperCase();
  };

  const menuItems: MenuProps['items'] = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
      'data-testid': 'logout-button',
    },
  ];

  return (
    <Dropdown menu={{ items: menuItems }} placement="bottomRight" trigger={['click']}>
      <Space className="cursor-pointer hover:bg-gray-100 px-3 py-2 rounded-lg transition-colors">
        <Avatar
          size="small"
          style={{ backgroundColor: '#1890ff' }}
        >
          {getAvatarLetter()}
        </Avatar>
        <Text strong>{user.username}</Text>
      </Space>
    </Dropdown>
  );
}
