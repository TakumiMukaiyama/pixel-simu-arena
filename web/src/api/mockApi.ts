import type { GameState, Event, UnitSpec, UnitInstance } from '../types/game';
import { mockUnits, mockDecks } from './mockData';

/**
 * モックAPI - シンプルなダミーデータを返す
 */

let currentMatchState: GameState | null = null;
let unitInstanceCounter = 0;

/**
 * 対戦開始
 */
export const matchStart = async (): Promise<{ match_id: string; game_state: GameState }> => {
  const matchId = `match-${Date.now()}`;
  currentMatchState = {
    match_id: matchId,
    tick_ms: 200,
    time_ms: 0,
    player_base_hp: 100,
    ai_base_hp: 100,
    player_cost: 10.0,
    ai_cost: 10.0,
    units: [],
    winner: null,
  };

  return {
    match_id: matchId,
    game_state: { ...currentMatchState },
  };
};

/**
 * tick実行 - ゲーム状態を更新
 */
export const matchTick = async (
  matchId: string
): Promise<{ game_state: GameState; events: Event[] }> => {
  if (!currentMatchState || currentMatchState.match_id !== matchId) {
    throw new Error('Invalid match_id');
  }

  const events: Event[] = [];
  const state = currentMatchState;

  // 経過時間を更新
  state.time_ms += state.tick_ms;

  // コストを増加 (200ms = 0.2秒で +0.6 cost)
  state.player_cost = Math.min(20.0, state.player_cost + 0.6);
  state.ai_cost = Math.min(20.0, state.ai_cost + 0.6);

  // ユニット移動とクールダウン更新
  state.units.forEach((unit) => {
    const spec = mockUnits.find((u) => u.id === unit.spec_id);
    if (!spec) return;

    // 移動速度に応じて位置を更新
    const moveAmount = spec.speed * 0.2; // 0.2秒分の移動
    if (unit.side === 'player') {
      unit.pos = Math.min(20.0, unit.pos + moveAmount);
    } else {
      unit.pos = Math.max(0.0, unit.pos - moveAmount);
    }

    // クールダウンを減少
    if (unit.cooldown_remaining > 0) {
      unit.cooldown_remaining = Math.max(0, unit.cooldown_remaining - 0.2);
    }

    events.push({
      type: 'MOVE',
      timestamp_ms: state.time_ms,
      data: {
        instance_id: unit.instance_id,
        from_pos: unit.pos - moveAmount,
        to_pos: unit.pos,
      },
    });
  });

  // 簡易的な戦闘判定
  state.units.forEach((attacker) => {
    if (attacker.cooldown_remaining > 0) return;

    const attackerSpec = mockUnits.find((u) => u.id === attacker.spec_id);
    if (!attackerSpec) return;

    // 敵ユニットを探す
    const enemies = state.units.filter((u) => u.side !== attacker.side);
    for (const target of enemies) {
      const distance = Math.abs(attacker.pos - target.pos);
      if (distance <= attackerSpec.range) {
        // 攻撃
        target.hp = Math.max(0, target.hp - attackerSpec.atk);
        attacker.cooldown_remaining = attackerSpec.atk_interval;

        events.push({
          type: 'ATTACK',
          timestamp_ms: state.time_ms,
          data: {
            attacker_id: attacker.instance_id,
            target_id: target.instance_id,
            damage: attackerSpec.atk,
          },
        });

        events.push({
          type: 'HIT',
          timestamp_ms: state.time_ms,
          data: {
            instance_id: target.instance_id,
            damage: attackerSpec.atk,
            hp_after: target.hp,
          },
        });

        if (target.hp <= 0) {
          events.push({
            type: 'DEATH',
            timestamp_ms: state.time_ms,
            data: {
              instance_id: target.instance_id,
              pos: target.pos,
            },
          });
        }

        break;
      }
    }

    // 拠点への攻撃判定
    if (attacker.side === 'player' && attacker.pos >= 19.5) {
      state.ai_base_hp = Math.max(0, state.ai_base_hp - attackerSpec.atk);
      attacker.cooldown_remaining = attackerSpec.atk_interval;
      events.push({
        type: 'BASE_DAMAGE',
        timestamp_ms: state.time_ms,
        data: {
          side: 'ai',
          damage: attackerSpec.atk,
          hp_after: state.ai_base_hp,
        },
      });
    } else if (attacker.side === 'ai' && attacker.pos <= 0.5) {
      state.player_base_hp = Math.max(0, state.player_base_hp - attackerSpec.atk);
      attacker.cooldown_remaining = attackerSpec.atk_interval;
      events.push({
        type: 'BASE_DAMAGE',
        timestamp_ms: state.time_ms,
        data: {
          side: 'player',
          damage: attackerSpec.atk,
          hp_after: state.player_base_hp,
        },
      });
    }
  });

  // HP0のユニットを削除
  state.units = state.units.filter((u) => u.hp > 0);

  // 勝敗判定
  if (state.player_base_hp <= 0) {
    state.winner = 'ai';
  } else if (state.ai_base_hp <= 0) {
    state.winner = 'player';
  }

  return {
    game_state: { ...state },
    events,
  };
};

/**
 * ユニット召喚
 */
export const matchSpawn = async (
  matchId: string,
  side: 'player' | 'ai',
  unitSpecId: string
): Promise<{ game_state: GameState; events: Event[] }> => {
  if (!currentMatchState || currentMatchState.match_id !== matchId) {
    throw new Error('Invalid match_id');
  }

  const state = currentMatchState;
  const spec = mockUnits.find((u) => u.id === unitSpecId);
  if (!spec) {
    throw new Error('Invalid unit_spec_id');
  }

  // コストチェック
  const currentCost = side === 'player' ? state.player_cost : state.ai_cost;
  if (currentCost < spec.cost) {
    throw new Error('Not enough cost');
  }

  // コストを減算
  if (side === 'player') {
    state.player_cost -= spec.cost;
  } else {
    state.ai_cost -= spec.cost;
  }

  // ユニットを生成
  const instanceId = `instance-${++unitInstanceCounter}`;
  const newUnit: UnitInstance = {
    instance_id: instanceId,
    spec_id: unitSpecId,
    side,
    hp: spec.max_hp,
    pos: side === 'player' ? 0.0 : 20.0,
    cooldown_remaining: 0.0,
  };

  state.units.push(newUnit);

  const events: Event[] = [
    {
      type: 'SPAWN',
      timestamp_ms: state.time_ms,
      data: {
        side,
        instance_id: instanceId,
        pos: newUnit.pos,
      },
    },
  ];

  return {
    game_state: { ...state },
    events,
  };
};

/**
 * ギャラリー一覧
 */
export const galleryList = async (): Promise<{ unit_specs: UnitSpec[]; total: number }> => {
  return {
    unit_specs: mockUnits,
    total: mockUnits.length,
  };
};

/**
 * デッキ保存
 */
export const deckSave = async (name: string, unitSpecIds: string[]): Promise<{ deck_id: string }> => {
  if (unitSpecIds.length !== 5) {
    throw new Error('Deck must have exactly 5 units');
  }

  const deckId = `deck-${Date.now()}`;
  mockDecks.push({
    id: deckId,
    name,
    unit_spec_ids: unitSpecIds,
  });

  return { deck_id: deckId };
};

/**
 * デッキ一覧取得
 */
export const deckList = async (): Promise<{ decks: typeof mockDecks }> => {
  return { decks: mockDecks };
};
