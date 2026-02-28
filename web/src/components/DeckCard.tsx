import type { UnitSpec } from '../types/game';
import './DeckCard.css';

interface DeckCardProps {
  unit: UnitSpec;
  currentCost: number;
  onSpawn: () => void;
}

export const DeckCard: React.FC<DeckCardProps> = ({ unit, currentCost, onSpawn }) => {
  const canSpawn = currentCost >= unit.cost;

  return (
    <div
      className={`deck-card ${canSpawn ? 'can-spawn' : 'cannot-spawn'}`}
      onClick={canSpawn ? onSpawn : undefined}
      title={canSpawn ? `クリックして ${unit.name} を召喚` : 'コストが不足しています'}
    >
      <div className="card-image">
        {/* 幾何学形でユニットを表現 */}
        <div
          className="unit-shape"
          style={{
            backgroundColor: '#00ff00',
            opacity: canSpawn ? 1 : 0.4,
          }}
        />
      </div>
      <div className="card-info">
        <div className="card-name">{unit.name}</div>
        <div className="card-stats">
          <div className="stat">
            <span className="stat-label">Cost:</span>
            <span className="stat-value">{unit.cost}</span>
          </div>
          <div className="stat">
            <span className="stat-label">HP:</span>
            <span className="stat-value">{unit.max_hp}</span>
          </div>
          <div className="stat">
            <span className="stat-label">ATK:</span>
            <span className="stat-value">{unit.atk}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
