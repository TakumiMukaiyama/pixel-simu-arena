import { useCallback } from 'react';
import { Stage, Container, Graphics } from '@pixi/react';
import type { GameState, UnitInstance } from '../types/game';
import { mockUnits } from '../api/mockData';

interface GameSceneProps {
  gameState: GameState;
}

const LANE_WIDTH = 800;
const LANE_HEIGHT = 200;
const GRID_SIZE = 40; // 800px / 20マス = 40px/マス
const BASE_WIDTH = 30;
const BASE_HEIGHT = 100;
const UNIT_RADIUS = 15;

export const GameScene: React.FC<GameSceneProps> = ({ gameState }) => {
  // レーン背景とグリッド線を描画
  const drawLane = useCallback((g: any) => {
    g.clear();

    // 背景
    g.beginFill(0x2a2a2a);
    g.drawRect(0, 0, LANE_WIDTH, LANE_HEIGHT);
    g.endFill();

    // グリッド線（縦）
    g.lineStyle(1, 0x444444, 0.5);
    for (let i = 0; i <= 20; i++) {
      g.moveTo(i * GRID_SIZE, 0);
      g.lineTo(i * GRID_SIZE, LANE_HEIGHT);
    }

    // 中央線を強調
    g.lineStyle(2, 0x666666, 0.8);
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

  // ユニットを描画
  const drawUnit = useCallback(
    (unit: UnitInstance) => (g: any) => {
      g.clear();

      const spec = mockUnits.find((u) => u.id === unit.spec_id);
      if (!spec) return;

      // ユニット本体（円）
      const color = unit.side === 'player' ? 0x00ff00 : 0xff0000;
      g.beginFill(color);
      g.drawCircle(0, 0, UNIT_RADIUS);
      g.endFill();

      // 枠線
      g.lineStyle(2, 0xffffff, 0.8);
      g.drawCircle(0, 0, UNIT_RADIUS);

      // HPバー
      const barWidth = UNIT_RADIUS * 2;
      const barHeight = 4;
      const barY = -UNIT_RADIUS - 8;

      // HPバー背景
      g.beginFill(0x333333);
      g.drawRect(-UNIT_RADIUS, barY, barWidth, barHeight);
      g.endFill();

      // HPバー（緑→黄→赤）
      const hpPercent = unit.hp / spec.max_hp;
      let barColor = 0x00ff00; // 緑
      if (hpPercent < 0.5) barColor = 0xffff00; // 黄
      if (hpPercent < 0.25) barColor = 0xff0000; // 赤

      g.beginFill(barColor);
      g.drawRect(-UNIT_RADIUS, barY, barWidth * hpPercent, barHeight);
      g.endFill();
    },
    []
  );

  return (
    <Stage width={LANE_WIDTH} height={LANE_HEIGHT} options={{ background: 0x000000 }}>
      {/* レーン背景 */}
      <Graphics draw={drawLane} />

      {/* プレイヤー拠点（左端 pos 0）*/}
      <Graphics x={0} y={0} draw={drawPlayerBase} />

      {/* AI拠点（右端 pos 20）*/}
      <Graphics x={LANE_WIDTH - BASE_WIDTH} y={0} draw={drawAIBase} />

      {/* ユニット描画 */}
      {gameState.units.map((unit) => {
        const x = unit.pos * GRID_SIZE;
        const y = LANE_HEIGHT / 2;
        return (
          <Container key={unit.instance_id} x={x} y={y}>
            <Graphics draw={drawUnit(unit)} />
          </Container>
        );
      })}

    </Stage>
  );
};
