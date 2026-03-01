"""
移動・攻撃ロジック

ユニットの移動、攻撃範囲判定、最近接敵の選定を行う。
"""
from typing import List, Optional

from app.schemas.game import Event
from app.schemas.unit import UnitInstance


def calculate_distance(pos1: float, pos2: float) -> float:
    """1次元距離を計算"""
    return abs(pos2 - pos1)


def is_in_range(attacker: UnitInstance, target: UnitInstance) -> bool:
    """攻撃範囲内にいるか判定"""
    distance = calculate_distance(attacker.pos, target.pos)
    return distance <= attacker.range


def find_nearest_enemy(
    unit: UnitInstance,
    enemies: List[UnitInstance]
) -> Optional[UnitInstance]:
    """
    最も近い敵を見つける

    Args:
        unit: 攻撃者ユニット
        enemies: 敵ユニットリスト

    Returns:
        最近接敵（範囲内にいない場合はNone）
    """
    if not enemies:
        return None

    # 射程内の敵をフィルタリング
    enemies_in_range = [e for e in enemies if is_in_range(unit, e)]

    if not enemies_in_range:
        return None

    # 最も近い敵を選択
    nearest = min(enemies_in_range, key=lambda e: calculate_distance(unit.pos, e.pos))
    return nearest


def move_unit(
    unit: UnitInstance,
    enemies: List[UnitInstance],
    tick_duration_sec: float
) -> Optional[Event]:
    """
    ユニットを移動させる（射程内に敵がいる場合は停止）

    Args:
        unit: 移動するユニット
        enemies: 敵ユニットリスト
        tick_duration_sec: tick期間（秒）

    Returns:
        移動イベント（移動した場合）
    """
    # 射程内に敵がいる場合は移動しない
    if find_nearest_enemy(unit, enemies) is not None:
        return None

    old_pos = unit.pos

    # プレイヤーユニットは右へ（pos増加）、AIユニットは左へ（pos減少）
    if unit.side == "player":
        unit.pos += unit.speed * tick_duration_sec
    else:  # ai
        unit.pos -= unit.speed * tick_duration_sec

    # 位置をクランプ（0-20の範囲内）
    unit.pos = max(0.0, min(20.0, unit.pos))

    # 移動した場合のみイベント生成
    if abs(unit.pos - old_pos) > 0.001:
        return Event(
            type="MOVE",
            timestamp_ms=0,  # tickで設定される
            data={
                "instance_id": str(unit.instance_id),
                "from_pos": round(old_pos, 2),
                "to_pos": round(unit.pos, 2),
                "side": unit.side
            }
        )
    return None


def update_cooldown(unit: UnitInstance, tick_duration_sec: float) -> None:
    """
    攻撃クールダウンを更新

    Args:
        unit: ユニット
        tick_duration_sec: tick期間（秒）
    """
    if unit.cooldown > 0:
        unit.cooldown = max(0.0, unit.cooldown - tick_duration_sec)


def try_attack(
    unit: UnitInstance,
    target: UnitInstance,
    timestamp_ms: int
) -> List[Event]:
    """
    攻撃を試みる

    Args:
        unit: 攻撃者
        target: 攻撃対象
        timestamp_ms: 現在時刻（ミリ秒）

    Returns:
        発生したイベントリスト（ATTACK, HIT, 場合によってはDEATH）
    """
    events = []

    # クールダウン中は攻撃できない
    if unit.cooldown > 0:
        return events

    # 攻撃イベント
    events.append(Event(
        type="ATTACK",
        timestamp_ms=timestamp_ms,
        data={
            "attacker_id": str(unit.instance_id),
            "attacker_side": unit.side,
            "target_id": str(target.instance_id),
            "target_side": target.side,
            "damage": unit.atk
        }
    ))

    # ダメージ適用
    old_hp = target.hp
    target.hp -= unit.atk
    target.hp = max(0, target.hp)

    # ヒットイベント
    events.append(Event(
        type="HIT",
        timestamp_ms=timestamp_ms,
        data={
            "target_id": str(target.instance_id),
            "target_side": target.side,
            "damage": unit.atk,
            "remaining_hp": target.hp,
            "old_hp": old_hp
        }
    ))

    # 死亡判定
    if target.hp <= 0:
        events.append(Event(
            type="DEATH",
            timestamp_ms=timestamp_ms,
            data={
                "instance_id": str(target.instance_id),
                "unit_spec_id": str(target.unit_spec_id),
                "side": target.side,
                "pos": round(target.pos, 2)
            }
        ))

    # クールダウン設定
    unit.cooldown = unit.atk_interval

    return events


def remove_dead_units(units: List[UnitInstance]) -> List[UnitInstance]:
    """
    死亡ユニットを除去

    Args:
        units: ユニットリスト

    Returns:
        生存ユニットリスト
    """
    return [u for u in units if u.hp > 0]
