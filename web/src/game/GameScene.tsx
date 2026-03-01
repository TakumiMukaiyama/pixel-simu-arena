import { useCallback, useMemo } from 'react';
import { Stage, Container, Graphics, Sprite, TilingSprite } from '@pixi/react';
import type { GameState, UnitInstance } from '../types/game';

interface GameSceneProps {
  gameState: GameState;
}

const LANE_WIDTH = 800;
const LANE_HEIGHT = 200;
const GRID_SIZE = 40; // 800px / 20マス = 40px/マス
const BASE_WIDTH = 30;
const BASE_HEIGHT = 100;

export const GameScene: React.FC<GameSceneProps> = ({ gameState }) => {
  // 背景画像のURL
  const backgroundUrl = useMemo(() => {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    return `${apiBaseUrl}/static/backgrounds/battle_field.png`;
  }, []);

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

  return (
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

      {/* ユニット描画 */}
      {useMemo(() => {
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
      }, [gameState.units, drawUnitHPBar])}

    </Stage>
  );
};
