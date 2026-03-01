import env from '../config/env';
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
        <img
          src={`${env.apiBaseUrl}${unit.battle_sprite_url}`}
          alt={unit.name}
          style={{
            width: '64px',
            height: '64px',
            imageRendering: 'pixelated',
            objectFit: 'contain',
            opacity: canSpawn ? 1 : 0.4,
          }}
        />
      </div>
      <div className="card-info">
        <div className="card-name">{unit.name}</div>
        <div className="card-stats">
          <div className="stat">
            <span className="stat-label">Cost:</span>
            <span className="stat-value" style={{ color: '#fbbf24' }}>{unit.cost}</span>
          </div>
          <div className="stat">
            <span className="stat-label">HP:</span>
            <span className="stat-value" style={{ color: '#22c55e' }}>{unit.max_hp}</span>
          </div>
          <div className="stat">
            <span className="stat-label">ATK:</span>
            <span className="stat-value" style={{ color: '#ef4444' }}>{unit.atk}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
