import { useState } from 'react';
import { Modal, Input } from 'antd';
import { useChatStore } from '../../stores/chatStore';
import styles from './CaseSearchButton.module.css';

export interface CaseSearchButtonProps {
  /** The search query extracted from conversation context */
  query: string;
  /** Whether the button should be disabled */
  disabled?: boolean;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Button component for triggering legal case search.
 *
 * This button appears after legal consultation responses,
 * allowing users to search for relevant court cases.
 *
 * When clicked, opens a modal dialog for the user to input
 * their search keywords.
 */
export function CaseSearchButton({
  query,
  disabled = false,
  className = ''
}: CaseSearchButtonProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState(query);
  const { sendMessage } = useChatStore();

  const handleClick = () => {
    setIsModalOpen(true);
    setSearchQuery(query);
  };

  const handleConfirm = () => {
    const trimmedQuery = searchQuery.trim();
    if (trimmedQuery) {
      sendMessage(`search_cases:${trimmedQuery}`);
      setIsModalOpen(false);
    }
  };

  const handleCancel = () => {
    setIsModalOpen(false);
    setSearchQuery(query);
  };

  return (
    <>
      <button
        onClick={handleClick}
        disabled={disabled}
        className={`${styles['case-search-button']} ${className}`}
        title="搜索相关法律案例"
      >
        🔍 搜索相关案例
      </button>

      <Modal
        title="搜索法律案例"
        open={isModalOpen}
        onOk={handleConfirm}
        onCancel={handleCancel}
        okText="搜索"
        cancelText="取消"
        destroyOnClose
      >
        <div className="flex flex-col gap-2">
          <p className="text-gray-600 text-sm">
            请输入搜索关键词，例如：
          </p>
          <ul className="text-gray-600 text-sm list-disc list-inside">
            <li>劳动合同纠纷</li>
            <li>合同违约责任</li>
            <li>交通事故赔偿</li>
            <li>房产纠纷</li>
          </ul>
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="请输入搜索关键词"
            onPressEnter={handleConfirm}
            autoFocus
            size="large"
          />
        </div>
      </Modal>
    </>
  );
}
