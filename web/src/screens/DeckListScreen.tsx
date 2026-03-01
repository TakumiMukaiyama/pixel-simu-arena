import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { deckList, deckDelete } from '../api';
import { useError } from '../components/ErrorNotification';
import { mapErrorToUserMessage } from '../api/errors';
import type { Deck } from '../types/game';
import './DeckListScreen.css';

export const DeckListScreen: React.FC = () => {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(true);
  const { showError } = useError();
  const navigate = useNavigate();

  const fetchDecks = async () => {
    try {
      setLoading(true);
      const result = await deckList();
      setDecks(result.decks);
    } catch (error) {
      showError(mapErrorToUserMessage(error));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDecks();
  }, []);

  const handleDeleteDeck = async (deckId: string, deckName: string) => {
    if (!window.confirm(`「${deckName}」を削除しますか？この操作は取り消せません。`)) {
      return;
    }

    try {
      await deckDelete(deckId);
      setDecks((prev) => prev.filter((d) => d.id !== deckId));
    } catch (error) {
      showError(mapErrorToUserMessage(error));
    }
  };

  if (loading) {
    return (
      <div className="deck-list-screen loading">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  return (
    <div className="deck-list-screen">
      <div className="deck-list-header">
        <h1>デッキ一覧</h1>
        <p className="deck-list-subtitle">全 {decks.length} 個のデッキ</p>
        <button
          onClick={() => navigate('/deck')}
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
          新しいデッキを作成
        </button>
      </div>

      <div className="deck-list-grid">
        {decks.map((deck) => (
          <div
            key={deck.id}
            className="deck-list-item"
            style={{ position: 'relative' }}
          >
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteDeck(deck.id, deck.name);
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
            <div
              className="deck-list-item-content"
              onClick={() => navigate(`/deck-detail/${deck.id}`)}
            >
              <h3 className="deck-name">{deck.name}</h3>
              <div className="deck-info">
                <div className="deck-stat">
                  <span className="stat-label">ユニット数</span>
                  <span className="stat-value">{deck.unit_spec_ids.length}</span>
                </div>
                <div className="deck-stat">
                  <span className="stat-label">作成日</span>
                  <span className="stat-value">
                    {new Date(deck.created_at).toLocaleDateString('ja-JP')}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {decks.length === 0 && (
        <div className="empty-state">
          <p>まだデッキがありません</p>
          <button
            onClick={() => navigate('/deck')}
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
            最初のデッキを作成
          </button>
        </div>
      )}
    </div>
  );
};
