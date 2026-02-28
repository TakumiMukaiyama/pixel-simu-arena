"""
バランス計算のテスト

パワースコア計算とコスト計算が正しく動作することを確認する。
"""
import pytest
from app.engine.balance import (
    calculate_power_score,
    calculate_cost,
    adjust_stats_to_cost,
    validate_unit_balance
)


def test_calculate_power_score_basic():
    """基本的なパワースコア計算"""
    stats = {
        "max_hp": 10,
        "atk": 5,
        "range": 2.0,
        "speed": 1.0,
        "atk_interval": 2.0
    }
    power = calculate_power_score(stats)

    # HP×0.4 + ATK×1.4 + (RANGE^1.5)×8 + SPEED×6 + (1/ATK_INTERVAL)×10
    # = 10×0.4 + 5×1.4 + (2^1.5)×8 + 1×6 + 0.5×10
    # = 4 + 7 + 22.627 + 6 + 5
    # = 44.627
    assert 44 <= power <= 45


def test_calculate_power_score_high_range():
    """射程が長い場合のパワースコア"""
    stats = {
        "max_hp": 10,
        "atk": 5,
        "range": 5.0,  # 長射程
        "speed": 1.0,
        "atk_interval": 2.0
    }
    power = calculate_power_score(stats)

    # 射程5.0の場合: (5^1.5)×8 = 89.44
    # 合計は約100以上
    assert power >= 100


def test_calculate_cost_from_power():
    """パワースコアからコスト計算"""
    # コスト1: power 1-20
    assert calculate_cost(10) == 1
    assert calculate_cost(20) == 1

    # コスト2: power 21-40
    assert calculate_cost(21) == 2
    assert calculate_cost(40) == 2

    # コスト3: power 41-60
    assert calculate_cost(45) == 3

    # コスト8: power 141-160
    assert calculate_cost(150) == 8

    # 上限クランプ
    assert calculate_cost(200) == 8


def test_adjust_stats_to_cost_upscale():
    """弱いユニットを目標コストに上げる"""
    weak_stats = {
        "max_hp": 5,
        "atk": 2,
        "range": 1.0,
        "speed": 0.5,
        "atk_interval": 3.0
    }
    # 元のパワー: 約10（コスト1相当）
    # 目標: コスト4（power 80）

    adjusted = adjust_stats_to_cost(weak_stats, target_cost=4)

    # 全ステータスがスケーリング
    assert adjusted["max_hp"] > weak_stats["max_hp"]
    assert adjusted["atk"] > weak_stats["atk"]
    assert adjusted["range"] > weak_stats["range"]
    assert adjusted["speed"] > weak_stats["speed"]
    assert adjusted["atk_interval"] < weak_stats["atk_interval"]  # 攻撃速度は逆数

    # 調整後のコストが目標に近い
    adjusted_power = calculate_power_score(adjusted)
    adjusted_cost = calculate_cost(adjusted_power)
    assert adjusted_cost == 4


def test_adjust_stats_to_cost_downscale():
    """強すぎるユニットを目標コストに下げる"""
    strong_stats = {
        "max_hp": 30,
        "atk": 15,
        "range": 7.0,
        "speed": 2.0,
        "atk_interval": 1.0
    }
    # 元のパワー: 約180（コスト8相当）
    # 目標: コスト2（power 40）

    adjusted = adjust_stats_to_cost(strong_stats, target_cost=2)

    # 全ステータスがスケーリングダウン
    assert adjusted["max_hp"] < strong_stats["max_hp"]
    assert adjusted["atk"] < strong_stats["atk"]

    # 調整後のコストが目標に近い
    adjusted_power = calculate_power_score(adjusted)
    adjusted_cost = calculate_cost(adjusted_power)
    assert 1 <= adjusted_cost <= 3  # 完全一致は難しいので許容範囲


def test_validate_unit_balance_valid():
    """バランス範囲内のユニット"""
    valid_stats = {
        "max_hp": 15,
        "atk": 7,
        "range": 3.0,
        "speed": 1.2,
        "atk_interval": 2.5
    }
    assert validate_unit_balance(valid_stats) is True


def test_validate_unit_balance_invalid_hp():
    """HP範囲外"""
    invalid_stats = {
        "max_hp": 50,  # 上限30を超える
        "atk": 7,
        "range": 3.0,
        "speed": 1.2,
        "atk_interval": 2.5
    }
    assert validate_unit_balance(invalid_stats) is False


def test_validate_unit_balance_invalid_speed():
    """速度範囲外"""
    invalid_stats = {
        "max_hp": 15,
        "atk": 7,
        "range": 3.0,
        "speed": 5.0,  # 上限2.0を超える
        "atk_interval": 2.5
    }
    assert validate_unit_balance(invalid_stats) is False


def test_validate_unit_balance_edge_case():
    """最小値でもバランス範囲内であることを確認"""
    min_stats = {
        "max_hp": 5,
        "atk": 1,
        "range": 1.0,
        "speed": 0.2,
        "atk_interval": 5.0
    }
    power = calculate_power_score(min_stats)
    # 最小値でもpower約14.6なので範囲内
    assert power >= 10
    assert validate_unit_balance(min_stats) is True
