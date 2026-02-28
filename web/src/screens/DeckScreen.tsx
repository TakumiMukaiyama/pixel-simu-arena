import { useState, useEffect } from 'react';
import { galleryList, deckSave } from '../api/mockApi';
import type { UnitSpec } from '../types/game';
import './DeckScreen.css';

export const DeckScreen: React.FC = () => {
  const [allUnits, setAllUnits] = useState<UnitSpec[]>([]);
  const [selectedUnits, setSelectedUnits] = useState<UnitSpec[]>([]);
  const [deckName, setDeckName] = useState('My Deck');
  const [loading, setLoading] = useState(true);
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    const fetchUnits = async () => {
      try {
        const result = await galleryList();
        setAllUnits(result.unit_specs);
      } catch (error) {
        console.error('Failed to fetch units:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUnits();
  }, []);

  const handleSelectUnit = (unit: UnitSpec) => {
    if (selectedUnits.length >= 5) {
      setSaveMessage('デッキは最大5体までです');
      setTimeout(() => setSaveMessage(''), 2000);
      return;
    }

    if (selectedUnits.find((u) => u.id === unit.id)) {
      setSaveMessage('すでに選択されています');
      setTimeout(() => setSaveMessage(''), 2000);
      return;
    }

    setSelectedUnits([...selectedUnits, unit]);
  };

  const handleRemoveUnit = (unitId: string) => {
    setSelectedUnits(selectedUnits.filter((u) => u.id !== unitId));
  };

  const handleSaveDeck = async () => {
    if (selectedUnits.length !== 5) {
      setSaveMessage('デッキは5体必要です');
      setTimeout(() => setSaveMessage(''), 2000);
      return;
    }

    try {
      const result = await deckSave(
        deckName,
        selectedUnits.map((u) => u.id)
      );
      setSaveMessage(`デッキを保存しました: ${result.deck_id}`);
      setTimeout(() => setSaveMessage(''), 3000);
    } catch (error) {
      console.error('Failed to save deck:', error);
      setSaveMessage('保存に失敗しました');
      setTimeout(() => setSaveMessage(''), 2000);
    }
  };

  if (loading) {
    return (
      <div className="deck-screen loading">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  return (
    <div className="deck-screen">
      <div className="deck-header">
        <h1>デッキ編成</h1>
        <p className="deck-subtitle">5体のユニットを選択してデッキを作成</p>
      </div>

      {/* 選択中のデッキ */}
      <div className="selected-deck">
        <div className="selected-deck-header">
          <h2>
            選択中のデッキ ({selectedUnits.length}/5)
          </h2>
          <input
            type="text"
            value={deckName}
            onChange={(e) => setDeckName(e.target.value)}
            placeholder="デッキ名"
            className="deck-name-input"
          />
        </div>

        <div className="deck-slots">
          {Array.from({ length: 5 }).map((_, i) => {
            const unit = selectedUnits[i];
            return (
              <div key={i} className={`deck-slot ${unit ? 'filled' : 'empty'}`}>
                {unit ? (
                  <div className="deck-slot-content" onClick={() => handleRemoveUnit(unit.id)}>
                    <div className="deck-slot-image">
                      <div
                        className="unit-shape-small"
                        style={{
                          backgroundColor: '#00ff00',
                          width: 48,
                          height: 48,
                          borderRadius: '50%',
                          margin: 'auto',
                        }}
                      />
                    </div>
                    <div className="deck-slot-name">{unit.name}</div>
                    <div className="deck-slot-cost">Cost: {unit.cost}</div>
                    <div className="remove-hint">クリックで削除</div>
                  </div>
                ) : (
                  <div className="deck-slot-empty">
                    <span>空き</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="deck-actions">
          <button
            onClick={handleSaveDeck}
            disabled={selectedUnits.length !== 5}
            className="save-button"
          >
            デッキを保存
          </button>
          {saveMessage && <div className="save-message">{saveMessage}</div>}
        </div>
      </div>

      {/* 全ユニット一覧 */}
      <div className="all-units">
        <h2>全ユニット</h2>
        <div className="units-grid">
          {allUnits.map((unit) => {
            const isSelected = selectedUnits.find((u) => u.id === unit.id);
            return (
              <div
                key={unit.id}
                className={`unit-item ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSelectUnit(unit)}
              >
                <div className="unit-item-image">
                  <div
                    className="unit-shape-small"
                    style={{
                      backgroundColor: isSelected ? '#666' : '#00ff00',
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      margin: 'auto',
                    }}
                  />
                </div>
                <div className="unit-item-info">
                  <h3>{unit.name}</h3>
                  <div className="unit-item-stats">
                    <span>Cost: {unit.cost}</span>
                    <span>HP: {unit.max_hp}</span>
                    <span>ATK: {unit.atk}</span>
                  </div>
                </div>
                {isSelected && <div className="selected-badge">✓</div>}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
