import './StatsDisplay.css';

interface StatsDisplayProps {
  playerHp: number;
  aiHp: number;
  playerCost: number;
  aiCost: number;
  timeMs: number;
}

export const StatsDisplay: React.FC<StatsDisplayProps> = ({
  playerHp,
  aiHp,
  playerCost,
  aiCost,
  timeMs,
}) => {
  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="stats-display">
      <div className="stat-item">
        <label>プレイヤー拠点</label>
        <div className="hp-bar">
          <div className="hp-fill player" style={{ width: `${playerHp}%` }} />
        </div>
        <span className="stat-text">
          {playerHp} / 100
        </span>
      </div>

      <div className="stat-item center">
        <label>経過時間</label>
        <span className="stat-text large">{formatTime(timeMs)}</span>
      </div>

      <div className="stat-item">
        <label>AI拠点</label>
        <div className="hp-bar">
          <div className="hp-fill ai" style={{ width: `${aiHp}%` }} />
        </div>
        <span className="stat-text">
          {aiHp} / 100
        </span>
      </div>

      <div className="stat-item">
        <label>プレイヤー コスト</label>
        <div className="cost-bar">
          <div className="cost-fill player" style={{ width: `${(playerCost / 20) * 100}%` }} />
        </div>
        <span className="stat-text">
          {playerCost.toFixed(1)} / 20.0
        </span>
      </div>

      <div className="stat-item">
        <label>AI コスト</label>
        <div className="cost-bar">
          <div className="cost-fill ai" style={{ width: `${(aiCost / 20) * 100}%` }} />
        </div>
        <span className="stat-text">
          {aiCost.toFixed(1)} / 20.0
        </span>
      </div>
    </div>
  );
};
