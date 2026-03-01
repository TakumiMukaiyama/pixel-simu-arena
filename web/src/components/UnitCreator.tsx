/**
 * ユニット作成コンポーネント
 */

import React, { useState } from 'react';
import { unitsCreate } from '../api';
import type { UnitSpec } from '../types/game';

interface UnitCreatorProps {
  onCreated: (unit: UnitSpec) => void;
  onClose: () => void;
}

export const UnitCreator: React.FC<UnitCreatorProps> = ({ onCreated, onClose }) => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdUnit, setCreatedUnit] = useState<UnitSpec | null>(null);

  const handleCreate = async () => {
    if (!prompt.trim()) {
      setError('プロンプトを入力してください');
      return;
    }

    if (!unitsCreate) {
      setError('ユニット作成機能は実APIでのみ利用可能です');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await unitsCreate(prompt);
      setCreatedUnit(result.unit_spec);
      onCreated(result.unit_spec);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'ユニットの生成に失敗しました');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setPrompt('');
    setCreatedUnit(null);
    setError(null);
    onClose();
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
      onClick={handleClose}
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
        <h2 style={{ marginBottom: '24px', color: 'white' }}>新しいユニットを作成</h2>

        {!createdUnit ? (
          <>
            <div style={{ marginBottom: '16px' }}>
              <label
                htmlFor="prompt"
                style={{ display: 'block', marginBottom: '8px', color: 'white' }}
              >
                ユニットの説明を入力してください
              </label>
              <textarea
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="例: fast ninja with high speed and low health"
                disabled={loading}
                style={{
                  width: '100%',
                  minHeight: '100px',
                  padding: '12px',
                  backgroundColor: '#2a2a2a',
                  color: 'white',
                  border: '1px solid #4b5563',
                  borderRadius: '8px',
                  fontSize: '14px',
                  resize: 'vertical',
                }}
              />
            </div>

            {error && (
              <div
                style={{
                  padding: '12px',
                  backgroundColor: '#7f1d1d',
                  color: '#fecaca',
                  borderRadius: '8px',
                  marginBottom: '16px',
                }}
              >
                {error}
              </div>
            )}

            {loading && (
              <div
                style={{
                  padding: '16px',
                  backgroundColor: '#1e3a8a',
                  color: '#93c5fd',
                  borderRadius: '8px',
                  marginBottom: '16px',
                  textAlign: 'center',
                }}
              >
                ユニットを生成中...
                <br />
                <small>画像とステータスを生成しています</small>
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={handleCreate}
                disabled={loading || !prompt.trim()}
                style={{
                  flex: 1,
                  padding: '12px 24px',
                  backgroundColor: loading || !prompt.trim() ? '#4b5563' : '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: loading || !prompt.trim() ? 'not-allowed' : 'pointer',
                  fontSize: '16px',
                  fontWeight: 'bold',
                }}
              >
                {loading ? '生成中...' : 'ユニットを生成'}
              </button>
              <button
                onClick={handleClose}
                disabled={loading}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#374151',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '16px',
                }}
              >
                キャンセル
              </button>
            </div>
          </>
        ) : (
          <>
            <div
              style={{
                padding: '16px',
                backgroundColor: '#065f46',
                color: '#6ee7b7',
                borderRadius: '8px',
                marginBottom: '16px',
                textAlign: 'center',
              }}
            >
              ユニットが作成されました
            </div>

            <div
              style={{
                padding: '16px',
                backgroundColor: '#2a2a2a',
                borderRadius: '8px',
                marginBottom: '16px',
              }}
            >
              <div style={{ color: 'white', fontWeight: 'bold', marginBottom: '8px' }}>
                {createdUnit.name}
              </div>
              <div style={{ color: '#9ca3af', fontSize: '14px' }}>
                コスト: {createdUnit.cost} | HP: {createdUnit.max_hp} | 攻撃: {createdUnit.atk}
              </div>
              {createdUnit.card_url && (
                <img
                  src={createdUnit.card_url}
                  alt={createdUnit.name}
                  style={{
                    width: '100%',
                    marginTop: '12px',
                    borderRadius: '8px',
                  }}
                />
              )}
            </div>

            <button
              onClick={handleClose}
              style={{
                width: '100%',
                padding: '12px 24px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: 'bold',
              }}
            >
              閉じる
            </button>
          </>
        )}
      </div>
    </div>
  );
};
