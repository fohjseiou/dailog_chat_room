import { Spin } from 'antd';

interface ThinkingIndicatorProps {
  stage: 'idle' | 'processing' | 'done' | 'error';
}

export function ThinkingIndicator({ stage }: ThinkingIndicatorProps) {
  if (stage === 'idle' || stage === 'done') return null;

  return (
    <div className="flex justify-start mb-4">
      <Spin tip="AI 正在处理..." size="small" />
    </div>
  );
}
