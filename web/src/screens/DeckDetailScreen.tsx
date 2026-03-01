import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { deckGet, deckUpdate } from '../api';
import { useError } from '../components/ErrorNotification';
import { mapErrorToUserMessage } from '../api/errors';
import env from '../config/env';
import type { Deck, UnitSpec } from '../types/game';
import './DeckDetailScreen.css';

export const DeckDetailScreen: React.FC = () => {
  const { deckId } = useParams<{ deckId: string }>();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [units, setUnits] = useState<UnitSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState('');
  const [isSavingName, setIsSavingName] = useState(false);
  const { showError } = useError();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDeck = async () => {
      if (!deckId) {
        showError('デッキIDが指定されていません');
        navigate('/deck-list');
        return;
      }

      try {
        setLoading(true);
        const result = await deckGet(deckId);
        setDeck(result.deck);
        setUnits(result.units);
      } catch (error) {
        showError(mapErrorToUserMessage(error));
        navigate('/deck-list');
      } finally {
        setLoading(false);
      }
    };

    fetchDeck();
  }, [deckId]);

  const handleStartEditName = () => {
    if (deck) {
      setEditedName(deck.name);
      setIsEditingName(true);
    }
  };

  const handleCancelEditName = () => {
    setIsEditingName(false);
    setEditedName('');
  };

  const handleSaveName = async () => {
    if (!deckId || !deck || !editedName.trim()) {
      showError('デッキ名を入力してください');
      return;
    }

    setIsSavingName(true);
    try {
      await deckUpdate(
        deckId,
        editedName.trim(),
        deck.unit_spec_ids
      );
      setDeck({ ...deck, name: editedName.trim() });
      setIsEditingName(false);
    } catch (error) {
      showError(mapErrorToUserMessage(error));
    } finally {
      setIsSavingName(false);
    }
  };

  if (loading) {
    return (
      <div className="deck-detail-screen loading">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  if (!deck) {
    return null;
  }

  return (
    <div className="deck-detail-screen">
      <div className="deck-detail-header">
        <button
          onClick={() => navigate('/deck-list')}
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
          ← 一覧に戻る
        </button>

        {isEditingName ? (
          <div className="deck-name-edit">
            <input
              type="text"
              value={editedName}
              onChange={(e) => setEditedName(e.target.value)}
              placeholder="デッキ名"
              autoFocus
              style={{
                padding: '8px 12px',
                fontSize: '1.5rem',
                fontWeight: 'bold',
                border: '2px solid #3b82f6',
                borderRadius: '8px',
                textAlign: 'center',
                width: '400px',
                maxWidth: '100%',
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSaveName();
                } else if (e.key === 'Escape') {
                  handleCancelEditName();
                }
              }}
            />
            <div style={{ display: 'flex', gap: '8px', marginTop: '8px', justifyContent: 'center' }}>
              <button
                onClick={handleSaveName}
                disabled={isSavingName || !editedName.trim()}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: 'bold',
                }}
              >
                {isSavingName ? '保存中...' : '保存'}
              </button>
              <button
                onClick={handleCancelEditName}
                disabled={isSavingName}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#64748b',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                }}
              >
                キャンセル
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
            <h1>{deck.name}</h1>
            <button
              onClick={handleStartEditName}
              style={{
                padding: '8px',
                backgroundColor: 'transparent',
                border: 'none',
                cursor: 'pointer',
                fontSize: '20px',
                color: '#64748b',
                display: 'flex',
                alignItems: 'center',
              }}
              title="デッキ名を編集"
            >
              ✏️
            </button>
          </div>
        )}

        <p className="deck-detail-subtitle">
          作成日: {deck.created_at
            ? new Date(deck.created_at).toLocaleDateString('ja-JP', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })
            : '不明'
          }
        </p>
        <button
          onClick={() => navigate(`/deck-edit/${deck.id}`)}
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
          ユニット編成を編集
        </button>
      </div>

      <div className="deck-units">
        <h2>デッキ構成 ({units.length}/5)</h2>
        <div className="units-grid">
          {units.map((unit) => (
            <div key={unit.id} className="unit-card">
              <div className="card-image">
                <img
                  src={`${env.apiBaseUrl}${unit.battle_sprite_url}`}
                  alt={unit.name}
                  style={{
                    width: '128px',
                    height: '128px',
                    objectFit: 'contain',
                    imageRendering: 'pixelated',
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
      </div>
    </div>
  );
};
