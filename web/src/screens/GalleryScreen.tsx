import { useState, useEffect } from 'react';
import { galleryList, unitsDelete } from '../api';
import { UnitCreator } from '../components/UnitCreator';
import { useError } from '../components/ErrorNotification';
import { mapErrorToUserMessage } from '../api/errors';
import env from '../config/env';
import type { UnitSpec } from '../types/game';
import './GalleryScreen.css';

export const GalleryScreen: React.FC = () => {
  const [units, setUnits] = useState<UnitSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUnit, setSelectedUnit] = useState<UnitSpec | null>(null);
  const [showCreator, setShowCreator] = useState(false);
  const { showError } = useError();

  const fetchUnits = async () => {
    try {
      setLoading(true);
      const result = await galleryList();
      setUnits(result.unit_specs);
    } catch (error) {
      showError(mapErrorToUserMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnits();
  }, []);

  const handleUnitCreated = (unit: UnitSpec) => {
    setUnits((prev) => [unit, ...prev]);
    setShowCreator(false);
  };

  const handleDeleteUnit = async (unitId: string, unitName: string) => {
    if (!window.confirm(`「${unitName}」を削除しますか？この操作は取り消せません。`)) {
      return;
    }

    try {
      await unitsDelete(unitId);
      setUnits((prev) => prev.filter((u) => u.id !== unitId));
      if (selectedUnit?.id === unitId) {
        setSelectedUnit(null);
      }
    } catch (error) {
      showError(mapErrorToUserMessage(error));
    }
  };

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
        <button
          onClick={() => setShowCreator(true)}
          style={{
            padding: '12px 24px',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
            marginTop: '16px',
          }}
        >
          新しいユニットを作成
        </button>
      </div>

      <div className="gallery-grid">
        {units.map((unit) => (
          <div
            key={unit.id}
            className="unit-card"
            style={{ position: 'relative' }}
          >
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteUnit(unit.id, unit.name);
              }}
              style={{
                position: 'absolute',
                top: '8px',
                right: '8px',
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                border: 'none',
                backgroundColor: 'rgba(220, 38, 38, 0.9)',
                color: 'white',
                fontSize: '18px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 10,
              }}
              title="削除"
            >
              ×
            </button>
            <div className="card-image" onClick={() => setSelectedUnit(unit)}>
              <img
                src={`${env.apiBaseUrl}${unit.battle_sprite_url}`}
                alt={unit.name}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  imageRendering: 'pixelated',
                }}
              />
            </div>
            <div className="card-content" onClick={() => setSelectedUnit(unit)}>
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

      {/* ユニット作成モーダル */}
      {showCreator && (
        <UnitCreator
          onCreated={handleUnitCreated}
          onClose={() => setShowCreator(false)}
        />
      )}

      {/* ユニット詳細モーダル */}
      {selectedUnit && (
        <div className="modal-overlay" onClick={() => setSelectedUnit(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedUnit(null)}>
              ×
            </button>
            <h2>{selectedUnit.name}</h2>
            <button
              onClick={() => handleDeleteUnit(selectedUnit.id, selectedUnit.name)}
              style={{
                position: 'absolute',
                top: '60px',
                right: '20px',
                padding: '8px 16px',
                backgroundColor: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
              }}
            >
              削除
            </button>
            <div className="modal-image">
              <img
                src={`${env.apiBaseUrl}${selectedUnit.battle_sprite_url}`}
                alt={selectedUnit.name}
                style={{
                  width: '256px',
                  height: '256px',
                  objectFit: 'contain',
                  imageRendering: 'pixelated',
                  margin: 'auto',
                  display: 'block',
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
