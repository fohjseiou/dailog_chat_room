import { Message } from '../../stores/chatStore';
import { useChatStore } from '../../stores/chatStore';
import { Card, Typography, Tag, Dropdown, Button, Space } from 'antd';
import { MoreOutlined, DeleteOutlined, BookOutlined } from '@ant-design/icons';
import { CaseSearchButton } from './CaseSearchButton';
import { extractKeyQuestion, isLegalConsultation } from '../../utils/queryExtractor';

const { Paragraph } = Typography;

interface MessageBubbleProps {
  message: Message;
  lastUserMessage?: string;
}

export function MessageBubble({ message, lastUserMessage }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const { deleteMessage } = useChatStore();

  // Determine if we should show CaseSearchButton
  const showCaseSearch = !isUser &&
                        !message.streaming &&
                        isLegalConsultation(message.content) &&
                        !!lastUserMessage;

  const handleDelete = async () => {
    await deleteMessage(message.id);
  };

  const items = [
    {
      key: 'delete',
      label: '删除',
      icon: <DeleteOutlined />,
      danger: true,
      onClick: handleDelete,
    },
  ];

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <Card
        className={`max-w-[70%] ${
          isUser
            ? 'bg-blue-600 text-white border-blue-600'
            : 'bg-gray-100 text-gray-800 border-gray-200'
        }`}
        bodyStyle={{ padding: '12px 16px' }}
      >
        {!isUser && (
          <div className="flex justify-end">
            <Dropdown menu={{ items }} trigger={['click']}>
              <Button
                type="text"
                icon={<MoreOutlined />}
                className="text-gray-400 hover:text-gray-600"
                size="small"
              />
            </Dropdown>
          </div>
        )}

        <Paragraph
          className={`!mb-2 whitespace-pre-wrap ${isUser ? 'text-white' : 'text-gray-800'}`}
          ellipsis={false}
        >
          {message.content || (message.streaming && '▊')}
        </Paragraph>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <Space wrap size="small" className="mt-2">
            {message.sources.map((source: { title: string }, idx: number) => (
              <Tag key={idx} icon={<BookOutlined />} color="blue">
                {source.title}
              </Tag>
            ))}
          </Space>
        )}

        {/* Case Search Button */}
        {showCaseSearch && lastUserMessage && (
          <div className="mt-3">
            <CaseSearchButton query={extractKeyQuestion(lastUserMessage)} />
          </div>
        )}

        {/* Timestamp */}
        <div className={`text-xs mt-2 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </Card>
    </div>
  );
}
