import { useState, useEffect, useRef } from 'react';
import { GameScene } from '../game/GameScene';
import { DeckCard } from '../components/DeckCard';
import { StatsDisplay } from '../components/StatsDisplay';
import { matchStart, matchTick, matchSpawn, deckList } from '../api/mockApi';
import { mockUnits } from '../api/mockData';
import type { GameState, UnitSpec } from '../types/game';
import './GameScreen.css';

export const GameScreen: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [matchId, setMatchId] = useState<string | null>(null);
  const [deckUnits, setDeckUnits] = useState<UnitSpec[]>([]);
  const intervalRef = useRef<number | null>(null);

  // ゲーム開始
  useEffect(() => {
    const startGame = async () => {
      try {
        const result = await matchStart();
        setMatchId(result.match_id);
        setGameState(result.game_state);

        // デッキを取得（最初のデッキを使用）
        const decksResult = await deckList();
        if (decksResult.decks.length > 0) {
          const deck = decksResult.decks[0];
          const units = deck.unit_spec_ids
            .map((id) => mockUnits.find((u) => u.id === id))
            .filter((u): u is UnitSpec => u !== undefined);
          setDeckUnits(units);
        }
      } catch (error) {
        console.error('Failed to start game:', error);
      }
    };

    startGame();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // 200msごとにtick
  useEffect(() => {
    if (!matchId || !gameState || gameState.winner) return;

    intervalRef.current = window.setInterval(async () => {
      try {
        const result = await matchTick(matchId);
        setGameState(result.game_state);

        // 勝敗が決まったらtickを停止
        if (result.game_state.winner) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
          }
        }
      } catch (error) {
        console.error('Failed to tick:', error);
      }
    }, 200);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [matchId, gameState?.winner]);

  // ユニット召喚
  const handleSpawn = async (unitSpecId: string) => {
    if (!matchId || !gameState || gameState.winner) return;

    try {
      const result = await matchSpawn(matchId, 'player', unitSpecId);
      setGameState(result.game_state);
    } catch (error) {
      console.error('Failed to spawn unit:', error);
    }
  };

  if (!gameState) {
    return (
      <div className="game-screen loading">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  return (
    <div className="game-screen">
      <div className="game-header">
        <h1>Pixel Simulation Arena</h1>
      </div>

      {/* ステータス表示 */}
      <StatsDisplay
        playerHp={gameState.player_base_hp}
        aiHp={gameState.ai_base_hp}
        playerCost={gameState.player_cost}
        timeMs={gameState.time_ms}
      />

      {/* ゲーム画面 */}
      <div className="game-canvas">
        <GameScene gameState={gameState} />
      </div>

      {/* デッキカード（5枚）*/}
      <div className="deck-cards">
        <div className="deck-cards-label">デッキカード</div>
        <div className="deck-cards-list">
          {deckUnits.map((unit) => (
            <DeckCard
              key={unit.id}
              unit={unit}
              currentCost={gameState.player_cost}
              onSpawn={() => handleSpawn(unit.id)}
            />
          ))}
        </div>
      </div>

      {/* 勝敗表示 */}
      {gameState.winner && (
        <div className="victory-overlay">
          <div className="victory-message">
            {gameState.winner === 'player' ? (
              <div className="win">
                <h2>勝利!</h2>
                <p>おめでとうございます</p>
              </div>
            ) : (
              <div className="lose">
                <h2>敗北...</h2>
                <p>もう一度挑戦しましょう</p>
              </div>
            )}
            <button onClick={() => window.location.reload()}>もう一度プレイ</button>
          </div>
        </div>
      )}
    </div>
  );
};
