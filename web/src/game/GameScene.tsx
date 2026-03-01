import { useCallback, useMemo, useState, useEffect } from 'react';
import { Stage, Container, Graphics, Sprite, TilingSprite } from '@pixi/react';
import { Assets } from 'pixi.js';
import type { GameState, UnitInstance } from '../types/game';

interface GameSceneProps {
  gameState: GameState;
}

const LANE_WIDTH = 800;
const LANE_HEIGHT = 200;
const GRID_SIZE = 40; // 800px / 20マス = 40px/マス
const BASE_WIDTH = 30;
const BASE_HEIGHT = 100;

type LoadingState = 'idle' | 'loading' | 'loaded' | 'error';

export const GameScene: React.FC<GameSceneProps> = ({ gameState }) => {
  // 読み込み状態の管理
  const [assetsLoadingState, setAssetsLoadingState] = useState<LoadingState>('idle');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadedUnitIds, setLoadedUnitIds] = useState<string>(''); // 読み込み済みのユニット構成

  // 背景画像のURL
  const backgroundUrl = useMemo(() => {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    return `${apiBaseUrl}/static/backgrounds/battle_field.png`;
  }, []);

  // 事前読み込みする画像URLのリスト
  // ユニットのIDリストをキーにして、ユニットの追加/削除時のみ再計算
  const unitIds = useMemo(() =>
    gameState.units.map(u => u.instance_id).sort().join(','),
    [gameState.units]
  );

  const imagesToPreload = useMemo(() => {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const urls = new Set<string>();

    // 背景画像
    urls.add(`${apiBaseUrl}/static/backgrounds/battle_field.png`);

    // ユニットスプライト (placeholderを除外)
    gameState.units.forEach(unit => {
      if (unit.battle_sprite_url && !unit.battle_sprite_url.includes('placeholder')) {
        urls.add(`${apiBaseUrl}${unit.battle_sprite_url}`);
      }
    });

    return Array.from(urls);
  }, [unitIds, gameState.units]);

  // 画像の事前読み込み（ユニット構成が変わった時のみ実行）
  useEffect(() => {
    // 既に同じユニット構成で読み込み済みの場合はスキップ
    if (loadedUnitIds === unitIds && assetsLoadingState === 'loaded') {
      console.log(`Skipping preload: already loaded for unitIds ${unitIds}`);
      return;
    }

    // 読み込み中の場合はスキップ
    if (assetsLoadingState === 'loading') {
      console.log('Skipping preload: already loading');
      return;
    }

    // 読み込む画像がない場合は即座にloaded状態にする
    if (imagesToPreload.length === 0) {
      console.log('No images to preload, setting state to loaded');
      setAssetsLoadingState('loaded');
      setLoadedUnitIds(unitIds);
      return;
    }

    const preloadAssets = async () => {
      console.log(`Starting to preload ${imagesToPreload.length} images for units: ${unitIds}`);
      setAssetsLoadingState('loading');
      setLoadingProgress(0);

      try {
        let loaded = 0;
        const total = imagesToPreload.length;

        // 並行読み込み
        const loadPromises = imagesToPreload.map(async (url) => {
          try {
            await Assets.load(url);
            loaded++;
            const progress = Math.round((loaded / total) * 100);
            setLoadingProgress(progress);
          } catch (err) {
            console.warn(`Failed to load image: ${url}`, err);
          }
        });

        await Promise.all(loadPromises);
        console.log('All images loaded successfully');
        setAssetsLoadingState('loaded');
        setLoadedUnitIds(unitIds); // 読み込み完了したユニット構成を記録
      } catch (error) {
        console.error('Asset preloading error:', error);
        setAssetsLoadingState('error');
      }
    };

    preloadAssets();
  }, [unitIds]); // ユニット構成が変わった時のみ再実行

  // グリッド線を描画
  const drawGridLines = useCallback((g: any) => {
    g.clear();

    // グリッド線（縦）- 控えめに
    g.lineStyle(1, 0xffffff, 0.1);
    for (let i = 0; i <= 20; i++) {
      g.moveTo(i * GRID_SIZE, 0);
      g.lineTo(i * GRID_SIZE, LANE_HEIGHT);
    }

    // 中央線を強調 (戦場の境界)
    g.lineStyle(2, 0xfbbf24, 0.4);
    g.moveTo(LANE_WIDTH / 2, 0);
    g.lineTo(LANE_WIDTH / 2, LANE_HEIGHT);
  }, []);

  // プレイヤー拠点を描画
  const drawPlayerBase = useCallback(
    (g: any) => {
      g.clear();

      // 拠点本体
      g.beginFill(0x4444ff);
      g.drawRect(0, (LANE_HEIGHT - BASE_HEIGHT) / 2, BASE_WIDTH, BASE_HEIGHT);
      g.endFill();

      // 枠線
      g.lineStyle(2, 0x6666ff);
      g.drawRect(0, (LANE_HEIGHT - BASE_HEIGHT) / 2, BASE_WIDTH, BASE_HEIGHT);

      // HPバー背景
      const barWidth = BASE_WIDTH;
      const barHeight = 8;
      const barY = (LANE_HEIGHT - BASE_HEIGHT) / 2 - 15;
      g.beginFill(0x333333);
      g.drawRect(0, barY, barWidth, barHeight);
      g.endFill();

      // HPバー（緑）
      const hpPercent = gameState.player_base_hp / 100;
      g.beginFill(0x00ff00);
      g.drawRect(0, barY, barWidth * hpPercent, barHeight);
      g.endFill();
    },
    [gameState.player_base_hp]
  );

  // AI拠点を描画
  const drawAIBase = useCallback(
    (g: any) => {
      g.clear();

      // 拠点本体
      g.beginFill(0xff4444);
      g.drawRect(0, (LANE_HEIGHT - BASE_HEIGHT) / 2, BASE_WIDTH, BASE_HEIGHT);
      g.endFill();

      // 枠線
      g.lineStyle(2, 0xff6666);
      g.drawRect(0, (LANE_HEIGHT - BASE_HEIGHT) / 2, BASE_WIDTH, BASE_HEIGHT);

      // HPバー背景
      const barWidth = BASE_WIDTH;
      const barHeight = 8;
      const barY = (LANE_HEIGHT - BASE_HEIGHT) / 2 - 15;
      g.beginFill(0x333333);
      g.drawRect(0, barY, barWidth, barHeight);
      g.endFill();

      // HPバー（緑）
      const hpPercent = gameState.ai_base_hp / 100;
      g.beginFill(0x00ff00);
      g.drawRect(0, barY, barWidth * hpPercent, barHeight);
      g.endFill();
    },
    [gameState.ai_base_hp]
  );

  // HPバーを描画
  const drawUnitHPBar = useCallback(
    (unit: UnitInstance) => (g: any) => {
      g.clear();

      // HPバー (バトルスプライト 64x64表示に合わせる)
      const barWidth = 64;
      const barHeight = 6;
      const barY = -40; // スプライトの上部

      // HPバー背景
      g.beginFill(0x333333);
      g.drawRect(-barWidth / 2, barY, barWidth, barHeight);
      g.endFill();

      // HPバー（緑→黄→赤）
      const hpPercent = unit.hp / unit.max_hp;
      let barColor = 0x00ff00; // 緑
      if (hpPercent < 0.5) barColor = 0xffff00; // 黄
      if (hpPercent < 0.25) barColor = 0xff0000; // 赤

      g.beginFill(barColor);
      g.drawRect(-barWidth / 2, barY, barWidth * hpPercent, barHeight);
      g.endFill();
    },
    []
  );

  // 再試行ハンドラー
  const retryPreload = useCallback(() => {
    setAssetsLoadingState('idle');
  }, []);

  // ユニット描画のメモ化（フックの順序を保つため、条件分岐前に定義）
  const unitsContent = useMemo(() => {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    return gameState.units.map((unit) => {
      const x = unit.pos * GRID_SIZE;
      const y = LANE_HEIGHT / 2;
      const battleSpriteUrl = `${apiBaseUrl}${unit.battle_sprite_url}`;

      // デバッグ情報をログ出力
      const hasValidSprite = unit.battle_sprite_url &&
                            !unit.battle_sprite_url.includes('placeholder');

      if (!hasValidSprite) {
        console.warn(
          `Unit ${unit.instance_id} (${unit.name}) has invalid sprite URL: ${unit.battle_sprite_url}`
        );
      }

      return (
        <Container key={unit.instance_id} x={x} y={y}>
          {/* 画像がある場合はスプライト表示 */}
          {hasValidSprite && (
            <Sprite
              image={battleSpriteUrl}
              anchor={0.5}
              scale={0.5}
            />
          )}

          {/* フォールバック: 色付き円を表示 */}
          {!hasValidSprite && (
            <Graphics
              draw={(g) => {
                g.clear();
                g.beginFill(unit.side === 'player' ? 0x4444ff : 0xff4444, 0.8);
                g.drawCircle(0, 0, 25);
                g.endFill();
                g.lineStyle(2, unit.side === 'player' ? 0x6666ff : 0xff6666);
                g.drawCircle(0, 0, 25);
              }}
            />
          )}

          {/* HPバー */}
          <Graphics draw={drawUnitHPBar(unit)} />
        </Container>
      );
    });
  }, [gameState.units, drawUnitHPBar]);

  // デバッグ: 現在の状態をログ出力
  console.log('[GameScene] Current state:', {
    assetsLoadingState,
    loadedUnitIds,
    unitIds,
    imagesToPreloadCount: imagesToPreload.length,
    unitsCount: gameState.units.length
  });

  return (
    <div style={{ position: 'relative', width: LANE_WIDTH, height: LANE_HEIGHT }}>
      {/* PixiJS Stage（常に表示） */}
      <Stage width={LANE_WIDTH} height={LANE_HEIGHT} options={{ background: 0x000000 }}>
        {/* 背景画像 (タイル状に繰り返し) */}
        <TilingSprite
          image={backgroundUrl}
          width={LANE_WIDTH}
          height={LANE_HEIGHT}
          tilePosition={{ x: 0, y: 0 }}
        />

        {/* グリッド線 */}
        <Graphics draw={drawGridLines} />

        {/* プレイヤー拠点（左端 pos 0）*/}
        <Graphics x={0} y={0} draw={drawPlayerBase} />

        {/* AI拠点（右端 pos 20）*/}
        <Graphics x={LANE_WIDTH - BASE_WIDTH} y={0} draw={drawAIBase} />

        {/* ユニット描画（loaded状態の場合のみ） */}
        {assetsLoadingState === 'loaded' && unitsContent}
      </Stage>

      {/* ローディング中のオーバーレイ */}
      {(assetsLoadingState === 'idle' || assetsLoadingState === 'loading') && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: LANE_WIDTH,
          height: LANE_HEIGHT,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
        }}>
          <div style={{ fontSize: '18px', marginBottom: '16px' }}>
            {assetsLoadingState === 'idle' ? '初期化中...' : '画像を読み込み中...'}
          </div>
          {assetsLoadingState === 'loading' && (
            <>
              <div style={{
                width: '200px',
                height: '20px',
                backgroundColor: '#333',
                borderRadius: '10px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${loadingProgress}%`,
                  height: '100%',
                  backgroundColor: '#3b82f6',
                  transition: 'width 0.3s ease',
                }} />
              </div>
              <div style={{ fontSize: '14px', marginTop: '8px', color: '#888' }}>
                {loadingProgress}%
              </div>
            </>
          )}
          {assetsLoadingState === 'idle' && (
            <>
              <div style={{ fontSize: '14px', color: '#888', marginTop: '8px' }}>
                ユニット数: {gameState.units.length}
              </div>
              <div style={{ fontSize: '14px', color: '#888' }}>
                読み込む画像数: {imagesToPreload.length}
              </div>
            </>
          )}
        </div>
      )}

      {/* エラー時のオーバーレイ */}
      {assetsLoadingState === 'error' && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: LANE_WIDTH,
          height: LANE_HEIGHT,
          backgroundColor: 'rgba(0, 0, 0, 0.9)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
        }}>
          <div style={{ fontSize: '18px', marginBottom: '16px', color: '#ef4444' }}>
            画像の読み込みに失敗しました
          </div>
          <button
            onClick={retryPreload}
            style={{
              padding: '8px 16px',
              fontSize: '14px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
            }}
          >
            再試行
          </button>
        </div>
      )}
    </div>
  );
};
