import { useState, useEffect } from 'react';
import { galleryList } from '../api/mockApi';
import type { UnitSpec } from '../types/game';
import './GalleryScreen.css';

export const GalleryScreen: React.FC = () => {
  const [units, setUnits] = useState<UnitSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUnit, setSelectedUnit] = useState<UnitSpec | null>(null);

  useEffect(() => {
    const fetchUnits = async () => {
      try {
        const result = await galleryList();
        setUnits(result.unit_specs);
      } catch (error) {
        console.error('Failed to fetch units:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUnits();
  }, []);

  if (loading) {
    return (
      <div className="gallery-screen loading">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  return (
    <div className="gallery-screen">
      <div className="gallery-header">
        <h1>ユニットギャラリー</h1>
        <p className="gallery-subtitle">全 {units.length} 体のユニット</p>
      </div>

      <div className="gallery-grid">
        {units.map((unit) => (
          <div
            key={unit.id}
            className="unit-card"
            onClick={() => setSelectedUnit(unit)}
          >
            <div className="card-image">
              {/* 幾何学形でユニットを表現 */}
              <div
                className="unit-shape"
                style={{
                  backgroundColor: '#00ff00',
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  margin: 'auto',
                }}
              />
            </div>
            <div className="card-content">
              <h3 className="unit-name">{unit.name}</h3>
              <div className="unit-stats">
                <div className="stat-row">
                  <span className="stat-label">コスト</span>
                  <span className="stat-value cost">{unit.cost}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">HP</span>
                  <span className="stat-value">{unit.max_hp}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">攻撃力</span>
                  <span className="stat-value">{unit.atk}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">速度</span>
                  <span className="stat-value">{unit.speed.toFixed(1)}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">射程</span>
                  <span className="stat-value">{unit.range.toFixed(1)}</span>
                </div>
                <div className="stat-row">
                  <span className="stat-label">攻撃間隔</span>
                  <span className="stat-value">{unit.atk_interval.toFixed(1)}s</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ユニット詳細モーダル */}
      {selectedUnit && (
        <div className="modal-overlay" onClick={() => setSelectedUnit(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedUnit(null)}>
              ×
            </button>
            <h2>{selectedUnit.name}</h2>
            <div className="modal-image">
              <div
                className="unit-shape-large"
                style={{
                  backgroundColor: '#00ff00',
                  width: 128,
                  height: 128,
                  borderRadius: '50%',
                  margin: 'auto',
                }}
              />
            </div>
            <div className="modal-stats">
              <div className="modal-stat-row">
                <span>コスト</span>
                <span className="highlight">{selectedUnit.cost}</span>
              </div>
              <div className="modal-stat-row">
                <span>最大HP</span>
                <span>{selectedUnit.max_hp}</span>
              </div>
              <div className="modal-stat-row">
                <span>攻撃力</span>
                <span>{selectedUnit.atk}</span>
              </div>
              <div className="modal-stat-row">
                <span>移動速度</span>
                <span>{selectedUnit.speed.toFixed(2)} マス/tick</span>
              </div>
              <div className="modal-stat-row">
                <span>射程</span>
                <span>{selectedUnit.range.toFixed(1)} マス</span>
              </div>
              <div className="modal-stat-row">
                <span>攻撃間隔</span>
                <span>{selectedUnit.atk_interval.toFixed(1)} 秒</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
