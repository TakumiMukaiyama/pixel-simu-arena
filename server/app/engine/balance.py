"""
バランス計算

パワースコアとコスト計算を行う。
ユニット生成時にステータスからコストを自動算出する。
"""
import math
from typing import Dict


def calculate_power_score(stats: Dict[str, float]) -> float:
    """
    ユニットのパワースコアを計算

    パワースコア = HP×0.4 + ATK×1.4 + (RANGE^1.5)×8 + SPEED×6 + (1/ATK_INTERVAL)×10

    Args:
        stats: ユニットステータス辞書
            - max_hp: 最大HP
            - atk: 攻撃力
            - range: 射程
            - speed: 移動速度
            - atk_interval: 攻撃間隔

    Returns:
        パワースコア（浮動小数点数）
    """
    hp = stats.get("max_hp", 10)
    atk = stats.get("atk", 5)
    range_val = stats.get("range", 2.0)
    speed = stats.get("speed", 1.0)
    atk_interval = stats.get("atk_interval", 2.0)

    # 各ステータスの重み付け
    hp_score = hp * 0.4
    atk_score = atk * 1.4
    range_score = (range_val ** 1.5) * 8  # 射程は指数的に重要
    speed_score = speed * 6
    atk_speed_score = (1.0 / atk_interval) * 10  # 攻撃速度は逆数

    power = hp_score + atk_score + range_score + speed_score + atk_speed_score
    return round(power, 2)


def calculate_cost(power_score: float) -> int:
    """
    パワースコアからコストを計算

    コスト = clamp(ceil(power / 20), 1, 8)

    Args:
        power_score: パワースコア

    Returns:
        コスト（1-8の整数）
    """
    cost = math.ceil(power_score / 20)
    return max(1, min(8, cost))


def adjust_stats_to_cost(stats: Dict[str, float], target_cost: int) -> Dict[str, float]:
    """
    ステータスを調整して目標コストに合わせる

    パワースコアが目標コストに近づくように、全ステータスを比例的にスケーリングする。
    LLMが生成したステータスが極端に強い/弱い場合の補正用。

    Args:
        stats: 元のステータス辞書
        target_cost: 目標コスト（1-8）

    Returns:
        調整後のステータス辞書
    """
    current_power = calculate_power_score(stats)
    target_power = target_cost * 20  # コストに対応する目標パワー

    # スケーリング比率を計算
    if current_power == 0:
        scale = 1.0
    else:
        scale = target_power / current_power

    # 全ステータスをスケーリング
    adjusted = {
        "max_hp": max(5, min(30, round(stats["max_hp"] * scale))),
        "atk": max(1, min(15, round(stats["atk"] * scale))),
        "range": max(1.0, min(7.0, round(stats["range"] * (scale ** 0.667), 2))),  # 射程は緩やかに調整
        "speed": max(0.2, min(2.0, round(stats["speed"] * scale, 2))),
        "atk_interval": max(1.0, min(5.0, round(stats["atk_interval"] / scale, 2)))  # 攻撃速度は逆数
    }

    return adjusted


def validate_unit_balance(stats: Dict[str, float]) -> bool:
    """
    ユニットステータスがバランス範囲内か検証

    Args:
        stats: ステータス辞書

    Returns:
        バランス範囲内ならTrue
    """
    # 各ステータスの範囲チェック
    if not (5 <= stats.get("max_hp", 0) <= 30):
        return False
    if not (1 <= stats.get("atk", 0) <= 15):
        return False
    if not (1.0 <= stats.get("range", 0) <= 7.0):
        return False
    if not (0.2 <= stats.get("speed", 0) <= 2.0):
        return False
    if not (1.0 <= stats.get("atk_interval", 0) <= 5.0):
        return False

    # パワースコアの範囲チェック（コスト1-8に対応）
    power = calculate_power_score(stats)
    if not (10 <= power <= 180):  # コスト1-8の許容範囲
        return False

    return True
