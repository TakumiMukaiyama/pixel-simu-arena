import { useEffect, useRef } from 'react';
import './AIThoughtDisplay.css';

interface AIThought {
  timestamp: number;
  decision: 'spawn' | 'wait';
  reason: string;
  unitName?: string;
}

interface AIThoughtDisplayProps {
  thoughts: AIThought[];
  maxDisplay?: number;
}

export const AIThoughtDisplay: React.FC<AIThoughtDisplayProps> = ({
  thoughts,
  maxDisplay = 5,
}) => {
  const thoughtsEndRef = useRef<HTMLDivElement>(null);

  // 新しい思考が追加されたら自動スクロール
  useEffect(() => {
    thoughtsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [thoughts]);

  const formatTime = (timestamp: number) => {
    const seconds = Math.floor(timestamp / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // 最新の思考のみを表示
  const displayThoughts = thoughts.slice(-maxDisplay);

  return (
    <div className="ai-thought-display">
      <div className="ai-thought-header">
        <span className="ai-icon">🤖</span>
        <span>AI の思考</span>
      </div>
      <div className="ai-thought-list">
        {displayThoughts.length === 0 ? (
          <div className="ai-thought-empty">
            AIの判断を待っています...
          </div>
        ) : (
          displayThoughts.map((thought, index) => (
            <div
              key={`${thought.timestamp}-${index}`}
              className={`ai-thought-item ${thought.decision}`}
            >
              <div className="ai-thought-time">
                {formatTime(thought.timestamp)}
              </div>
              <div className="ai-thought-content">
                {thought.decision === 'spawn' && thought.unitName && (
                  <div className="ai-thought-action">
                    📤 {thought.unitName} を召喚
                  </div>
                )}
                {thought.decision === 'wait' && (
                  <div className="ai-thought-action">
                    ⏳ 待機
                  </div>
                )}
                <div className="ai-thought-reason">
                  {thought.reason}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={thoughtsEndRef} />
      </div>
    </div>
  );
};
