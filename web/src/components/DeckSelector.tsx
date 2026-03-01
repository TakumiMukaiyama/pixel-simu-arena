/**
 * デッキ選択コンポーネント
 */

import React, { useEffect, useState } from 'react';
import { deckList } from '../api';
import type { Deck } from '../types/game';

interface DeckSelectorProps {
  onSelectDeck: (deckId: string) => void;
  onClose: () => void;
}

export const DeckSelector: React.FC<DeckSelectorProps> = ({ onSelectDeck, onClose }) => {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDeckId, setSelectedDeckId] = useState<string | null>(null);

  useEffect(() => {
    const loadDecks = async () => {
      try {
        setLoading(true);
        const result = await deckList();
        setDecks(result.decks);
        setError(null);
      } catch (err) {
        setError('デッキの読み込みに失敗しました');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadDecks();
  }, []);

  const handleStart = () => {
    if (selectedDeckId) {
      onSelectDeck(selectedDeckId);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#1a1a1a',
          padding: '32px',
          borderRadius: '12px',
          maxWidth: '600px',
          width: '90%',
          maxHeight: '80vh',
          overflow: 'auto',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ marginBottom: '24px', color: 'white' }}>デッキを選択</h2>

        {loading && <div style={{ color: 'white' }}>読み込み中...</div>}

        {error && <div style={{ color: '#ef4444', marginBottom: '16px' }}>{error}</div>}

        {!loading && decks.length === 0 && (
          <div style={{ color: '#9ca3af' }}>
            デッキが見つかりません。先にデッキを作成してください。
          </div>
        )}

        {!loading && decks.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {decks.map((deck) => (
              <div
                key={deck.id}
                style={{
                  padding: '16px',
                  backgroundColor: selectedDeckId === deck.id ? '#3b82f6' : '#2a2a2a',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                  border: selectedDeckId === deck.id ? '2px solid #60a5fa' : '2px solid transparent',
                }}
                onClick={() => setSelectedDeckId(deck.id)}
              >
                <div style={{ color: 'white', fontWeight: 'bold', marginBottom: '8px' }}>
                  {deck.name}
                </div>
                <div style={{ color: '#9ca3af', fontSize: '14px' }}>
                  {deck.unit_spec_ids.length}枚のユニット
                </div>
              </div>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
          <button
            onClick={handleStart}
            disabled={!selectedDeckId || loading}
            style={{
              flex: 1,
              padding: '12px 24px',
              backgroundColor: selectedDeckId && !loading ? '#3b82f6' : '#4b5563',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: selectedDeckId && !loading ? 'pointer' : 'not-allowed',
              fontSize: '16px',
              fontWeight: 'bold',
            }}
          >
            ゲーム開始
          </button>
          <button
            onClick={onClose}
            style={{
              padding: '12px 24px',
              backgroundColor: '#374151',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px',
            }}
          >
            キャンセル
          </button>
        </div>
      </div>
    </div>
  );
};
