interface ThinkingIndicatorProps {
  stage: 'idle' | 'routing' | 'retrieving' | 'generating' | 'done' | 'error';
  intent?: string;
  retrievedDocs?: Array<{ title: string; score: number }>;
}

const STAGE_CONFIG = {
  idle: { icon: '💭', text: '准备中...' },
  routing: { icon: '🔍', text: '理解问题...' },
  retrieving: { icon: '📚', text: '检索知识库...' },
  generating: { icon: '✍️', text: '生成回复...' },
  done: { icon: '✅', text: '完成' },
  error: { icon: '❌', text: '出错了' },
};

const INTENT_LABELS: Record<string, string> = {
  greeting: '问候',
  legal_consultation: '法律咨询',
  general_chat: '一般对话',
};

export function ThinkingIndicator({ stage, intent, retrievedDocs }: ThinkingIndicatorProps) {
  if (stage === 'idle' || stage === 'done') return null;

  const config = STAGE_CONFIG[stage];

  return (
    <div className="flex justify-start mb-4">
      <div className="bg-gray-100 rounded-lg px-4 py-2 max-w-md">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span className="text-lg">{config.icon}</span>
          <span>{config.text}</span>

          {intent && stage === 'retrieving' && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
              {INTENT_LABELS[intent] || intent}
            </span>
          )}
        </div>

        {stage === 'retrieving' && retrievedDocs && retrievedDocs.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-1">找到相关文档：</p>
            <div className="space-y-1">
              {retrievedDocs.slice(0, 3).map((doc, idx) => (
                <div key={idx} className="flex items-center gap-2 text-xs">
                  <span className="text-green-500">📄</span>
                  <span className="text-gray-700 truncate">{doc.title}</span>
                  <span className="text-gray-400">
                    {(doc.score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {stage === 'generating' && (
          <div className="flex gap-1 mt-2">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
          </div>
        )}
      </div>
    </div>
  );
}
