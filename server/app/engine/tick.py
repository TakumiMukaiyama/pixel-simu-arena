"""
tick処理

ゲームの中心ロジック。200msごとに呼ばれ、全ユニットの移動・攻撃・死亡判定を行う。
"""
from typing import List

from app.schemas.game import Event, GameState

from .movement import (
    find_nearest_enemy,
    move_unit,
    remove_dead_units,
    try_attack,
    update_cooldown
)
from .victory import (
    check_base_reached,
    determine_winner,
    remove_units_that_reached_base
)


def process_tick(game_state: GameState) -> List[Event]:
    """
    1tickの処理を実行

    処理順序:
    1. クールダウン更新
    2. 移動処理
    3. 拠点到達チェック
    4. 攻撃処理
    5. 死亡ユニット除去
    6. コスト回復
    7. 勝敗判定
    8. 時間更新

    Args:
        game_state: 現在のゲーム状態（インプレースで更新される）

    Returns:
        発生したイベントのリスト
    """
    events: List[Event] = []
    tick_duration_sec = game_state.tick_ms / 1000.0  # ミリ秒を秒に変換

    # 勝敗が決している場合は何もしない
    if game_state.is_finished():
        return events

    # 1. クールダウン更新
    for unit in game_state.units:
        update_cooldown(unit, tick_duration_sec)

    # 2. 移動処理
    for unit in game_state.units:
        move_event = move_unit(unit, tick_duration_sec)
        if move_event:
            move_event.timestamp_ms = game_state.time_ms
            events.append(move_event)

    # 3. 拠点到達チェック
    units_to_remove = []
    for unit in game_state.units:
        reached, base_events = check_base_reached(unit, game_state, game_state.time_ms)
        if reached:
            units_to_remove.append(unit.instance_id)
            events.extend(base_events)

    # 拠点到達ユニットを除去
    game_state.units = [u for u in game_state.units if u.instance_id not in units_to_remove]

    # 4. 攻撃処理
    player_units = game_state.get_player_units()
    ai_units = game_state.get_ai_units()

    # プレイヤーユニットの攻撃
    for unit in player_units:
        target = find_nearest_enemy(unit, ai_units)
        if target:
            attack_events = try_attack(unit, target, game_state.time_ms)
            events.extend(attack_events)

    # AIユニットの攻撃
    for unit in ai_units:
        target = find_nearest_enemy(unit, player_units)
        if target:
            attack_events = try_attack(unit, target, game_state.time_ms)
            events.extend(attack_events)

    # 5. 死亡ユニット除去
    game_state.units = remove_dead_units(game_state.units)

    # 6. コスト回復
    game_state.player_cost += game_state.cost_recovery_per_tick
    game_state.player_cost = min(game_state.player_cost, game_state.max_cost)

    game_state.ai_cost += game_state.cost_recovery_per_tick
    game_state.ai_cost = min(game_state.ai_cost, game_state.max_cost)

    # 7. 勝敗判定
    winner = determine_winner(game_state)
    if winner:
        game_state.winner = winner

    # 8. 時間更新
    game_state.time_ms += game_state.tick_ms

    return events


def spawn_unit_in_game(
    game_state: GameState,
    unit_instance,
    timestamp_ms: int
) -> Event:
    """
    ゲームにユニットを召喚

    Args:
        game_state: ゲーム状態
        unit_instance: 召喚するユニットインスタンス
        timestamp_ms: 召喚時刻

    Returns:
        SPAWNイベント
    """
    game_state.units.append(unit_instance)

    return Event(
        type="SPAWN",
        timestamp_ms=timestamp_ms,
        data={
            "instance_id": str(unit_instance.instance_id),
            "unit_spec_id": str(unit_instance.unit_spec_id),
            "side": unit_instance.side,
            "pos": round(unit_instance.pos, 2),
            "hp": unit_instance.hp,
            "max_hp": unit_instance.max_hp,
            "atk": unit_instance.atk,
            "speed": unit_instance.speed,
            "range": unit_instance.range,
            "atk_interval": unit_instance.atk_interval
        }
    )
