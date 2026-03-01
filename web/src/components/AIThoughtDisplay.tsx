import { useEffect, useRef, useState } from 'react';
import './AIThoughtDisplay.css';
import { AIAnalysis } from '../types/game';

interface AIThought {
  timestamp: number;
  decision: 'spawn' | 'wait';
  reason: string;
  unitName?: string;
  analysis?: AIAnalysis;
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
  const [expandedThought, setExpandedThought] = useState<number | null>(null);

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

  const getThreatLevelColor = (level: 'high' | 'medium' | 'low') => {
    switch (level) {
      case 'high': return '#ff6b6b';
      case 'medium': return '#ffd93d';
      case 'low': return '#6bcf7f';
    }
  };

  const getStrategyColor = (strategy: string) => {
    switch (strategy) {
      case 'defensive': return '#4dabf7';
      case 'offensive': return '#ff6b6b';
      case 'economic': return '#ffd93d';
      case 'balanced': return '#9775fa';
      default: return '#868e96';
    }
  };

  const toggleExpand = (index: number) => {
    setExpandedThought(expandedThought === index ? null : index);
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
          displayThoughts.map((thought, index) => {
            const isExpanded = expandedThought === index;
            const hasAnalysis = !!thought.analysis;

            return (
              <div
                key={`${thought.timestamp}-${index}`}
                className={`ai-thought-item ${thought.decision}`}
              >
                <div className="ai-thought-summary">
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
                  {hasAnalysis && (
                    <button
                      className="ai-thought-expand"
                      onClick={() => toggleExpand(index)}
                    >
                      {isExpanded ? '▲' : '▼'}
                    </button>
                  )}
                </div>

                {hasAnalysis && isExpanded && thought.analysis && (
                  <div className="ai-thought-detail">
                    {/* 戦場評価 */}
                    <div className="analysis-section">
                      <h4>戦場評価</h4>
                      <div className="battlefield-assessment">
                        <div className="threat-level">
                          <span>脅威レベル: </span>
                          <span
                            className={`threat-badge ${thought.analysis.battlefield_assessment.enemy_threat_level}`}
                            style={{
                              backgroundColor: getThreatLevelColor(
                                thought.analysis.battlefield_assessment.enemy_threat_level
                              ),
                            }}
                          >
                            {thought.analysis.battlefield_assessment.enemy_threat_level}
                          </span>
                        </div>
                        <p><strong>敵構成:</strong> {thought.analysis.battlefield_assessment.enemy_composition}</p>
                        <p><strong>味方状況:</strong> {thought.analysis.battlefield_assessment.ally_status}</p>
                        <p><strong>戦略的状況:</strong> {thought.analysis.battlefield_assessment.strategic_situation}</p>
                      </div>
                    </div>

                    {/* 候補ユニット評価 */}
                    <div className="analysis-section">
                      <h4>候補ユニット評価</h4>
                      <div className="candidate-list">
                        {thought.analysis.candidate_evaluation.map((candidate) => (
                          <div key={candidate.unit_id} className="candidate-card">
                            <div className="candidate-header">
                              <span className="candidate-name">{candidate.unit_name}</span>
                              <span className="candidate-score">{candidate.score}/100</span>
                            </div>
                            <div className="candidate-efficiency">
                              コスト効率: {candidate.cost_efficiency}
                            </div>
                            <div className="candidate-pros">
                              <strong>長所:</strong>
                              <ul>
                                {candidate.pros.map((pro, i) => (
                                  <li key={i}>{pro}</li>
                                ))}
                              </ul>
                            </div>
                            <div className="candidate-cons">
                              <strong>短所:</strong>
                              <ul>
                                {candidate.cons.map((con, i) => (
                                  <li key={i}>{con}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 推論ステップ */}
                    <div className="analysis-section">
                      <h4>推論ステップ</h4>
                      <ol className="reasoning-steps">
                        {thought.analysis.decision_reasoning.map((step, i) => (
                          <li key={i}>{step}</li>
                        ))}
                      </ol>
                    </div>

                    {/* 戦略と信頼度 */}
                    <div className="analysis-section">
                      <div className="strategy-confidence">
                        <div className="strategy">
                          <span>戦略: </span>
                          <span
                            className="strategy-badge"
                            style={{
                              backgroundColor: getStrategyColor(thought.analysis.selected_strategy),
                            }}
                          >
                            {thought.analysis.selected_strategy}
                          </span>
                        </div>
                        <div className="confidence">
                          <span>信頼度: </span>
                          <div className="confidence-bar-container">
                            <div
                              className="confidence-bar"
                              style={{ width: `${thought.analysis.confidence * 100}%` }}
                            />
                          </div>
                          <span className="confidence-value">
                            {(thought.analysis.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={thoughtsEndRef} />
      </div>
    </div>
  );
};
