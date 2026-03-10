import { useState } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import { useChatStore } from '../../stores/chatStore';

export function MessageInput() {
  const [message, setMessage] = useState('');
  const { sendMessageStream, isLoading, thinking } = useChatStore();

  const isDisabled = isLoading || thinking.stage === 'processing';

  const handleSubmit = async () => {
    if (!message.trim() || isDisabled) return;

    const currentMessage = message;
    setMessage('');
    await sendMessageStream(currentMessage);
  };

  return (
    <div className="flex gap-2 p-4 border-t border-gray-200 bg-white">
      <Input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onPressEnter={(e) => {
          if (!e.shiftKey) {
            e.preventDefault();
            handleSubmit();
          }
        }}
        placeholder={isDisabled ? 'AI 正在处理中...' : '输入您的法律问题...'}
        disabled={isDisabled}
        size="large"
        className="flex-1"
      />
      <Button
        type="primary"
        icon={<SendOutlined />}
        onClick={handleSubmit}
        disabled={!message.trim() || isDisabled}
        size="large"
      >
        发送
      </Button>
    </div>
  );
}
