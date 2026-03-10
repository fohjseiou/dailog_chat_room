import { useState } from 'react';
import { Form, Input, Button, Card, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuthStore } from '../../stores/authStore';

interface LoginFormProps {
  onSuccess?: () => void;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [form] = Form.useForm();
  const { login, register, isLoading, error, clearError } = useAuthStore();

  const handleSubmit = async (values: { username: string; password: string }) => {
    clearError();
    try {
      if (isLogin) {
        await login(values.username, values.password);
      } else {
        await register(values.username, values.password);
      }
      onSuccess?.();
    } catch (err) {
      // Error is handled by the store
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    clearError();
    form.resetFields();
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <Card className="w-full max-w-md shadow-lg">
        <Space direction="vertical" size="large" className="w-full">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-800">
              {isLogin ? '登录' : '注册'}
            </h1>
            <p className="text-gray-500 mt-2">
              {isLogin ? '欢迎回来' : '创建新账户'}
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <Alert
              message={error}
              type="error"
              closable
              onClose={clearError}
              showIcon
            />
          )}

          {/* Form */}
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            autoComplete="off"
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                size="large"
                disabled={isLoading}
              />
            </Form.Item>

            <Form.Item
              label="密码"
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                size="large"
                disabled={isLoading}
              />
            </Form.Item>

            <Form.Item className="!mb-0">
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                loading={isLoading}
                block
                data-testid="submit-button"
              >
                {isLogin ? '登录' : '注册'}
              </Button>
            </Form.Item>
          </Form>

          {/* Toggle Login/Register */}
          <div className="text-center">
            <span className="text-gray-500">
              {isLogin ? '还没有账户？' : '已有账户？'}
            </span>
            <Button
              type="link"
              onClick={toggleMode}
              disabled={isLoading}
              className="!p-0 !ml-1"
              data-testid="toggle-mode-button"
            >
              {isLogin ? '立即注册' : '立即登录'}
            </Button>
          </div>
        </Space>
      </Card>
    </div>
  );
}
