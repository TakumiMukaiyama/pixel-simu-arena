/**
 * ゲーム関連の型定義
 */

export interface UnitSpec {
  id: string;
  name: string;
  cost: number;
  max_hp: number;
  atk: number;
  speed: number;
  range: number;
  atk_interval: number;
  sprite_url: string;
  card_url: string;
  image_prompt?: string;
  original_prompt?: string;
  created_at: string;
}

export interface UnitInstance {
  instance_id: string;
  spec_id: string;
  side: 'player' | 'ai';
  hp: number;
  pos: number;
  cooldown_remaining: number;
}

export interface GameState {
  match_id: string;
  tick_ms: number;
  time_ms: number;
  player_base_hp: number;
  ai_base_hp: number;
  player_cost: number;
  ai_cost: number;
  units: UnitInstance[];
  winner: 'player' | 'ai' | null;
}

export type EventType = 'SPAWN' | 'MOVE' | 'ATTACK' | 'HIT' | 'DEATH' | 'BASE_DAMAGE';

export interface Event {
  type: EventType;
  timestamp_ms: number;
  data: Record<string, unknown>;
}

export interface Deck {
  id: string;
  name: string;
  unit_spec_ids: string[];
}
