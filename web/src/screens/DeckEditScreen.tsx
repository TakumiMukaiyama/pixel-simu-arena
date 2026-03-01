import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { galleryList, deckGet, deckUpdate } from '../api';
import { useError } from '../components/ErrorNotification';
import { mapErrorToUserMessage } from '../api/errors';
import env from '../config/env';
import type { UnitSpec, Deck } from '../types/game';
import './DeckEditScreen.css';

export const DeckEditScreen: React.FC = () => {
  const { deckId } = useParams<{ deckId: string }>();
  const [allUnits, setAllUnits] = useState<UnitSpec[]>([]);
  const [selectedUnits, setSelectedUnits] = useState<UnitSpec[]>([]);
  const [deckName, setDeckName] = useState('');
  const [loading, setLoading] = useState(true);
  const [saveMessage, setSaveMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const { showError } = useError();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      if (!deckId) {
        showError('デッキIDが指定されていません');
        navigate('/deck-list');
        return;
      }

      try {
        setLoading(true);

        // デッキ情報と全ユニットを並行取得
        const [deckResult, galleryResult] = await Promise.all([
          deckGet(deckId),
          galleryList(),
        ]);

        setDeckName(deckResult.deck.name);
        setAllUnits(galleryResult.unit_specs);

        // 既存のデッキのユニットを選択状態にする
        setSelectedUnits(deckResult.units);
      } catch (error) {
        showError(mapErrorToUserMessage(error));
        navigate('/deck-list');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [deckId]);

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

  const handleUpdateDeck = async () => {
    if (!deckId) {
      showError('デッキIDが指定されていません');
      return;
    }

    if (selectedUnits.length !== 5) {
      showError('デッキは5体必要です');
      return;
    }

    if (!deckName.trim()) {
      showError('デッキ名を入力してください');
      return;
    }

    setIsSaving(true);
    try {
      await deckUpdate(
        deckId,
        deckName,
        selectedUnits.map((u) => u.id)
      );
      setSaveMessage('デッキを更新しました');
      setTimeout(() => {
        navigate(`/deck-detail/${deckId}`);
      }, 1000);
    } catch (error) {
      showError(mapErrorToUserMessage(error));
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="deck-edit-screen loading">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  return (
    <div className="deck-edit-screen">
      <div className="deck-edit-header">
        <button
          onClick={() => navigate(`/deck-detail/${deckId}`)}
          style={{
            padding: '8px 16px',
            backgroundColor: '#64748b',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px',
            marginBottom: '16px',
          }}
        >
          ← キャンセル
        </button>
        <h1>デッキを編集</h1>
        <p className="deck-edit-subtitle">5体のユニットを選択してデッキを更新</p>
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
                      <img
                        src={`${env.apiBaseUrl}${unit.battle_sprite_url}`}
                        alt={unit.name}
                        style={{
                          width: '64px',
                          height: '64px',
                          imageRendering: 'pixelated',
                          objectFit: 'contain',
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
            onClick={handleUpdateDeck}
            disabled={selectedUnits.length !== 5 || isSaving}
            className="save-button"
          >
            {isSaving ? '更新中...' : 'デッキを更新'}
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
                  <img
                    src={`${env.apiBaseUrl}${unit.battle_sprite_url}`}
                    alt={unit.name}
                    style={{
                      width: '64px',
                      height: '64px',
                      imageRendering: 'pixelated',
                      objectFit: 'contain',
                      opacity: isSelected ? 0.5 : 1,
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
