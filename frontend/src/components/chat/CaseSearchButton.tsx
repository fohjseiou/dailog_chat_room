import { chatApi } from '@/api/client';
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
 */
export function CaseSearchButton({
  query,
  disabled = false,
  className = ''
}: CaseSearchButtonProps) {
  const handleClick = async () => {
    try {
      await chatApi.sendMessage({ message: `search_cases:${query}` });
    } catch (error) {
      console.error('Failed to send case search request:', error);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className={`${styles['case-search-button']} ${className}`}
      title="搜索相关法律案例"
    >
      🔍 搜索相关案例
    </button>
  );
}
