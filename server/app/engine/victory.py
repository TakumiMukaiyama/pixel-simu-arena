"""
勝敗判定ロジック

拠点到達判定、拠点ダメージ、勝者決定を行う。
"""
from typing import List, Literal, Optional

from app.schemas.game import Event, GameState
from app.schemas.unit import UnitInstance


def check_base_reached(
    unit: UnitInstance,
    game_state: GameState,
    timestamp_ms: int
) -> tuple[bool, List[Event]]:
    """
    ユニットが拠点に到達したか確認

    Args:
        unit: チェックするユニット
        game_state: ゲーム状態
        timestamp_ms: 現在時刻（ミリ秒）

    Returns:
        (到達したか, 発生したイベント)
    """
    events = []

    # プレイヤーユニットが右端（pos>=20）に到達
    if unit.side == "player" and unit.pos >= 20.0:
        # AI拠点にダメージ
        damage = unit.atk
        game_state.ai_base_hp -= damage
        game_state.ai_base_hp = max(0, game_state.ai_base_hp)

        events.append(Event(
            type="BASE_DAMAGE",
            timestamp_ms=timestamp_ms,
            data={
                "side": "ai",
                "damage": damage,
                "remaining_hp": game_state.ai_base_hp,
                "attacker_id": str(unit.instance_id),
                "attacker_side": unit.side
            }
        ))

        # ユニットを除去（死亡イベント）
        events.append(Event(
            type="DEATH",
            timestamp_ms=timestamp_ms,
            data={
                "instance_id": str(unit.instance_id),
                "unit_spec_id": str(unit.unit_spec_id),
                "side": unit.side,
                "pos": round(unit.pos, 2),
                "reason": "reached_base"
            }
        ))

        return True, events

    # AIユニットが左端（pos<=0）に到達
    if unit.side == "ai" and unit.pos <= 0.0:
        # プレイヤー拠点にダメージ
        damage = unit.atk
        game_state.player_base_hp -= damage
        game_state.player_base_hp = max(0, game_state.player_base_hp)

        events.append(Event(
            type="BASE_DAMAGE",
            timestamp_ms=timestamp_ms,
            data={
                "side": "player",
                "damage": damage,
                "remaining_hp": game_state.player_base_hp,
                "attacker_id": str(unit.instance_id),
                "attacker_side": unit.side
            }
        ))

        # ユニットを除去（死亡イベント）
        events.append(Event(
            type="DEATH",
            timestamp_ms=timestamp_ms,
            data={
                "instance_id": str(unit.instance_id),
                "unit_spec_id": str(unit.unit_spec_id),
                "side": unit.side,
                "pos": round(unit.pos, 2),
                "reason": "reached_base"
            }
        ))

        return True, events

    return False, events


def determine_winner(game_state: GameState) -> Optional[Literal["player", "ai"]]:
    """
    勝者を判定

    Args:
        game_state: ゲーム状態

    Returns:
        勝者（"player" or "ai"）、未決定の場合None
    """
    if game_state.player_base_hp <= 0 and game_state.ai_base_hp <= 0:
        # 同時破壊の場合は先に0になった方が負け（実装上は同時なのでAIの勝ち）
        return "ai"
    elif game_state.player_base_hp <= 0:
        return "ai"
    elif game_state.ai_base_hp <= 0:
        return "player"
    return None


def remove_units_that_reached_base(units: List[UnitInstance]) -> List[UnitInstance]:
    """
    拠点に到達したユニットを除去

    Args:
        units: ユニットリスト

    Returns:
        拠点に到達していないユニットリスト
    """
    result = []
    for unit in units:
        # プレイヤーユニットがpos>=20 or AIユニットがpos<=0なら除去
        if unit.side == "player" and unit.pos >= 20.0:
            continue
        if unit.side == "ai" and unit.pos <= 0.0:
            continue
        result.append(unit)
    return result
