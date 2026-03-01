import { useState, useEffect, useRef } from 'react';
import { GameScene } from '../game/GameScene';
import { DeckCard } from '../components/DeckCard';
import { StatsDisplay } from '../components/StatsDisplay';
import { DeckSelector } from '../components/DeckSelector';
import { AIThoughtDisplay } from '../components/AIThoughtDisplay';
import { useError } from '../components/ErrorNotification';
import { matchStart, matchTick, matchSpawn, matchAiDecide, matchEnd, galleryList, deckGet } from '../api';
import { mapErrorToUserMessage } from '../api/errors';
import type { GameState, UnitSpec } from '../types/game';
import './GameScreen.css';

interface AIThought {
  timestamp: number;
  decision: 'spawn' | 'wait';
  reason: string;
  unitName?: string;
}

export const GameScreen: React.FC = () => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [matchId, setMatchId] = useState<string | null>(null);
  const [deckUnits, setDeckUnits] = useState<UnitSpec[]>([]);
  const [showDeckSelector, setShowDeckSelector] = useState(true);
  const [isSpawning, setIsSpawning] = useState(false);
  const [aiThoughts, setAiThoughts] = useState<AIThought[]>([]);
  const intervalRef = useRef<number | null>(null);
  const aiDecisionTimerRef = useRef<number>(0);
  const matchIdRef = useRef<string | null>(null);
  const { showError } = useError();

  // デバッグツールをwindowに追加
  useEffect(() => {
    if (gameState) {
      (window as any).debugGame = {
        getState: () => gameState,
        getUnits: () => gameState.units.map(u => ({
          id: u.instance_id,
          name: u.name,
          side: u.side,
          spriteUrl: u.battle_sprite_url,
          hasValidSprite: u.battle_sprite_url &&
                         !u.battle_sprite_url.includes('placeholder')
        }))
      };
    }
  }, [gameState]);

  // ゲーム開始
  const handleDeckSelect = async (deckId: string) => {
    try {
      setShowDeckSelector(false);
      const result = await matchStart(deckId);
      setMatchId(result.match_id);
      setGameState(result.game_state);

      // デッキ情報を取得してユニット一覧を設定
      if (deckGet) {
        const deckResult = await deckGet(deckId);
        setDeckUnits(deckResult.units);
      } else {
        // deckGetが利用できない場合のフォールバック
        const galleryResult = await galleryList();
        setDeckUnits(galleryResult.unit_specs.slice(0, 5));
      }
    } catch (error) {
      showError(mapErrorToUserMessage(error));
      setShowDeckSelector(true);
    }
  };

  // 適応型ティックループ（AI自律動作含む）
  useEffect(() => {
    if (!matchId || !gameState || gameState.winner) return;

    const runGameLoop = async () => {
      try {
        const startTime = Date.now();

        // Tick実行
        const result = await matchTick(matchId);
        setGameState(result.game_state);

        if (result.game_state.winner) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
          }
          return;
        }

        // AI判断（1200msごと = 約6tick）
        aiDecisionTimerRef.current += 200;
        if (aiDecisionTimerRef.current >= 1200) {
          aiDecisionTimerRef.current = 0;

          try {
            const aiDecision = await matchAiDecide(matchId);

            // AIがユニット召喚を決定した場合、自動的に実行
            if (aiDecision.spawn_unit_spec_id) {
              const updatedState = await matchSpawn(matchId, 'ai', aiDecision.spawn_unit_spec_id);

              // 召喚したユニットの名前を取得
              // 最後に追加されたAIユニットを探す
              const aiUnits = updatedState.game_state.units.filter(u => u.side === 'ai');
              const latestAiUnit = aiUnits[aiUnits.length - 1];

              // AI思考を記録
              setAiThoughts(prev => [...prev, {
                timestamp: result.game_state.time_ms,
                decision: 'spawn',
                reason: aiDecision.reason,
                unitName: latestAiUnit?.name || 'Unknown Unit',
                analysis: aiDecision.analysis
              }]);
            } else {
              // 待機判断を記録
              setAiThoughts(prev => [...prev, {
                timestamp: result.game_state.time_ms,
                decision: 'wait',
                reason: aiDecision.reason,
                analysis: aiDecision.analysis
              }]);
            }
          } catch (aiError) {
            // AI判断エラーはログのみ（ゲームは継続）
            console.error('AI decision error:', aiError);
          }
        }

        const elapsed = Date.now() - startTime;
        const waitTime = Math.max(0, 250 - elapsed);

        intervalRef.current = window.setTimeout(runGameLoop, waitTime);
      } catch (error) {
        showError(mapErrorToUserMessage(error));
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      }
    };

    runGameLoop();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [matchId, gameState?.winner]);

  // matchIdをrefに保存（最新の値を保持）
  useEffect(() => {
    matchIdRef.current = matchId;
  }, [matchId]);

  // コンポーネントのアンマウント時にマッチを終了（別のuseEffect）
  useEffect(() => {
    return () => {
      // コンポーネントがアンマウントされる時のみ実行
      // refから最新のmatchIdを取得
      if (matchIdRef.current) {
        matchEnd(matchIdRef.current).catch(err => {
          console.warn('Failed to end match on unmount:', err);
        });
      }
    };
  }, []); // 空の依存配列 = マウント時に1回だけ設定、アンマウント時にクリーンアップ

  // ユニット召喚（デバウンス付き）
  const handleSpawn = async (unitSpecId: string) => {
    if (!matchId || !gameState || gameState.winner || isSpawning) return;

    setIsSpawning(true);
    try {
      const result = await matchSpawn(matchId, 'player', unitSpecId);
      setGameState(result.game_state);
    } catch (error) {
      showError(mapErrorToUserMessage(error));
    } finally {
      setTimeout(() => setIsSpawning(false), 500);
    }
  };

  if (showDeckSelector) {
    return (
      <div className="game-screen loading">
        <DeckSelector
          onSelectDeck={handleDeckSelect}
          onClose={() => window.history.back()}
        />
      </div>
    );
  }

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
        aiCost={gameState.ai_cost}
        timeMs={gameState.time_ms}
      />

      {/* メインゲームエリア */}
      <div className="game-main">
        {/* ゲーム画面 */}
        <div className="game-canvas">
          <GameScene gameState={gameState} />
        </div>

        {/* AI思考パネル */}
        <div className="ai-panel">
          <AIThoughtDisplay thoughts={aiThoughts} maxDisplay={8} />
        </div>
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
