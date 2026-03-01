/**
 * 実API実装 - バックエンドと通信
 */

import { get, post, put, del } from './client';
import type { GameState, Event, UnitSpec, Deck, AIDecideResponse } from '../types/game';

/**
 * 対戦開始
 */
export const matchStart = async (
  playerDeckId: string,
  aiDeckId?: string
): Promise<{ match_id: string; game_state: GameState }> => {
  return post('/match/start', {
    player_deck_id: playerDeckId,
    ai_deck_id: aiDeckId,
  });
};

/**
 * tick実行
 */
export const matchTick = async (
  matchId: string
): Promise<{ game_state: GameState; events: Event[] }> => {
  return post(`/match/tick`, { match_id: matchId });
};

/**
 * ユニット召喚
 */
export const matchSpawn = async (
  matchId: string,
  side: 'player' | 'ai',
  unitSpecId: string
): Promise<{ game_state: GameState; events: Event[] }> => {
  return post('/match/spawn', {
    match_id: matchId,
    side,
    unit_spec_id: unitSpecId,
  });
};

/**
 * AI判断実行
 */
export const matchAiDecide = async (
  matchId: string
): Promise<AIDecideResponse> => {
  return post('/match/ai_decide', { match_id: matchId });
};

/**
 * マッチ終了
 */
export const matchEnd = async (
  matchId: string
): Promise<{ message: string; match_id: string }> => {
  return post('/match/end', { match_id: matchId });
};

/**
 * ユニット作成
 */
export const unitsCreate = async (
  prompt: string
): Promise<{ unit_spec: UnitSpec }> => {
  return post('/units/create', { prompt });
};

/**
 * ユニット削除
 */
export const unitsDelete = async (
  unitId: string
): Promise<{ message: string; unit_id: string }> => {
  return del(`/units/${unitId}`);
};

/**
 * ギャラリー一覧
 */
export const galleryList = async (
  limit: number = 100,
  offset: number = 0
): Promise<{ unit_specs: UnitSpec[]; total: number }> => {
  return get(`/gallery/list?limit=${limit}&offset=${offset}`);
};

/**
 * デッキ保存
 */
export const deckSave = async (
  name: string,
  unitSpecIds: string[]
): Promise<{ deck_id: string }> => {
  return post('/deck/save', {
    name,
    unit_spec_ids: unitSpecIds,
  });
};

/**
 * デッキ一覧取得
 */
export const deckList = async (): Promise<{ decks: Deck[] }> => {
  return get('/deck/list');
};

/**
 * デッキ取得
 */
export const deckGet = async (deckId: string): Promise<{ deck: Deck; units: UnitSpec[] }> => {
  return get(`/deck/${deckId}`);
};

/**
 * デッキ更新
 */
export const deckUpdate = async (
  deckId: string,
  name: string,
  unitSpecIds: string[]
): Promise<{ message: string; deck_id: string }> => {
  return put(`/deck/${deckId}`, {
    name,
    unit_spec_ids: unitSpecIds,
  });
};

/**
 * デッキ削除
 */
export const deckDelete = async (
  deckId: string
): Promise<{ message: string; deck_id: string }> => {
  return del(`/deck/${deckId}`);
};
