"""
AI召喚決定

Mistral LLMを使用して盤面を分析し、次に召喚するユニットを決定する。
"""
import json
from typing import Optional
from uuid import UUID

from mistralai import Mistral

from app.config import get_settings
from app.schemas.deck import Deck
from app.schemas.game import GameState
from app.schemas.unit import UnitSpec

settings = get_settings()


AI_DECISION_SYSTEM_PROMPT = """You are an AI player in a 1-lane realtime battle game.

Goal: Destroy the enemy base (at position 0). Your base is at position 20.

Game mechanics:
- Lane: 0 (player base) ←→ 20 (AI base)
- Player units move right (→), AI units move left (←)
- Units attack enemies in range automatically
- Cost regenerates over time (max 20.0)

Strategy considerations:
1. Balance offense and defense
2. Counter enemy composition (e.g., spawn tanks vs high damage enemies)
3. Manage cost efficiently
4. Consider timing (e.g., save cost for critical moments)

Output ONLY valid JSON:
{
  "spawn_unit_spec_id": "unit-id" or null,
  "reason": "Brief tactical reason (max 100 chars)"
}

If you decide not to spawn, set spawn_unit_spec_id to null."""


async def ai_decide_spawn(game_state: GameState, ai_deck: Deck) -> dict:
    """
    AIの召喚決定

    1. ゲーム状態サマリー作成
    2. Mistral LLMで決定
    3. レスポンス返却

    Args:
        game_state: 現在のゲーム状態
        ai_deck: AIのデッキ

    Returns:
        {
            "spawn_unit_spec_id": UUID or None,
            "wait_ms": int,
            "reason": str
        }
    """
    from app.storage.db import get_units_by_ids

    # デッキのユニット情報取得
    deck_units = await get_units_by_ids(ai_deck.unit_spec_ids)

    # コスト範囲内のユニットのみ
    available_units = [u for u in deck_units if u.cost <= game_state.ai_cost]

    if not available_units:
        return {
            "spawn_unit_spec_id": None,
            "wait_ms": 600,
            "reason": "No units available in cost range"
        }

    # 1. ゲーム状態サマリー作成
    summary = _create_game_summary(game_state, available_units)

    # 2. Mistral LLMで決定（同期呼び出し）
    try:
        decision = _call_mistral_for_decision(summary, available_units)

        # spawn_unit_spec_idをUUIDに変換
        spawn_id = None
        if decision.get("spawn_unit_spec_id"):
            try:
                spawn_id = UUID(decision["spawn_unit_spec_id"])
                # 有効なユニットIDか確認
                if not any(u.id == spawn_id for u in available_units):
                    spawn_id = None
                    decision["reason"] = "Invalid unit ID, not spawning"
            except (ValueError, TypeError):
                spawn_id = None
                decision["reason"] = "Invalid unit ID format"

        return {
            "spawn_unit_spec_id": spawn_id,
            "wait_ms": 600,
            "reason": decision.get("reason", "")
        }

    except Exception as e:
        print(f"AI decision error: {e}")
        # フォールバック: 貪欲戦略
        return _fallback_decision(game_state, available_units)


def _create_game_summary(game_state: GameState, available_units: list[UnitSpec]) -> str:
    """ゲーム状態サマリーを作成"""
    player_units = game_state.get_player_units()
    ai_units = game_state.get_ai_units()

    summary = f"""Current game state:
- Time: {game_state.time_ms / 1000:.1f}s
- AI cost: {game_state.ai_cost:.1f} / {game_state.max_cost}
- AI base HP: {game_state.ai_base_hp} / 100
- Player base HP: {game_state.player_base_hp} / 100

AI units on field ({len(ai_units)}):
"""
    for unit in ai_units:
        summary += f"  - pos={unit.pos:.1f}, hp={unit.hp}/{unit.max_hp}, atk={unit.atk}, range={unit.range}\n"

    summary += f"\nEnemy units on field ({len(player_units)}):\n"
    for unit in player_units:
        summary += f"  - pos={unit.pos:.1f}, hp={unit.hp}/{unit.max_hp}, atk={unit.atk}, range={unit.range}\n"

    summary += "\nAvailable units to spawn:\n"
    for unit in available_units:
        summary += f"  - {unit.id}: {unit.name} (cost={unit.cost}, hp={unit.max_hp}, atk={unit.atk}, speed={unit.speed}, range={unit.range})\n"

    return summary


def _call_mistral_for_decision(summary: str, available_units: list[UnitSpec], max_retries: int = 2) -> dict:
    """
    Mistral LLMを呼び出して決定を取得

    Args:
        summary: ゲーム状態サマリー
        available_units: 召喚可能なユニット
        max_retries: 最大リトライ回数

    Returns:
        決定辞書

    Raises:
        Exception: 生成失敗時
    """
    client = Mistral(api_key=settings.mistral_api_key)

    for attempt in range(max_retries):
        try:
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": AI_DECISION_SYSTEM_PROMPT},
                    {"role": "user", "content": summary}
                ],
                temperature=0.8,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content.strip()

            # JSONパース
            decision = json.loads(content)

            # 必須フィールド検証
            if "spawn_unit_spec_id" not in decision:
                decision["spawn_unit_spec_id"] = None
            if "reason" not in decision:
                decision["reason"] = "No reason provided"

            return decision

        except json.JSONDecodeError as e:
            print(f"JSON parse error in AI decision (attempt {attempt + 1}/{max_retries}): {e}")
            print(f"Response content: {content}")
            if attempt == max_retries - 1:
                raise

        except Exception as e:
            print(f"Mistral API error in AI decision (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise

    raise Exception("Failed to get AI decision from Mistral")


def _fallback_decision(game_state: GameState, available_units: list[UnitSpec]) -> dict:
    """
    フォールバック決定（LLM失敗時）

    貪欲戦略: 最も高コストのユニットを召喚
    """
    if not available_units:
        return {
            "spawn_unit_spec_id": None,
            "wait_ms": 600,
            "reason": "No available units (fallback)"
        }

    # 最も高コストのユニットを選択
    selected = max(available_units, key=lambda u: u.cost)

    return {
        "spawn_unit_spec_id": selected.id,
        "wait_ms": 600,
        "reason": f"Fallback: Spawning highest cost unit ({selected.name})"
    }
