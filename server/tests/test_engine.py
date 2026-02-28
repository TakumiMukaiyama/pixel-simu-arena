"""
ゲームエンジンのテスト

movement, victory, tickの各モジュールが正しく動作することを確認する。
"""
from uuid import uuid4

import pytest

from app.engine.movement import (
    calculate_distance,
    find_nearest_enemy,
    is_in_range,
    move_unit,
    try_attack,
    update_cooldown
)
from app.engine.tick import process_tick, spawn_unit_in_game
from app.engine.victory import check_base_reached, determine_winner
from app.schemas.game import GameState
from app.schemas.unit import UnitInstance


def create_test_unit(side="player", pos=0.0, hp=10, atk=5, speed=1.0, range_val=2.0):
    """テスト用ユニットを作成"""
    return UnitInstance(
        unit_spec_id=uuid4(),
        side=side,
        pos=pos,
        hp=hp,
        cooldown=0.0,
        max_hp=hp,
        atk=atk,
        speed=speed,
        range=range_val,
        atk_interval=2.0
    )


def test_calculate_distance():
    """距離計算"""
    assert calculate_distance(0.0, 5.0) == 5.0
    assert calculate_distance(5.0, 0.0) == 5.0
    assert calculate_distance(10.0, 10.0) == 0.0


def test_is_in_range():
    """射程範囲判定"""
    attacker = create_test_unit(pos=0.0, range_val=3.0)
    target1 = create_test_unit(side="ai", pos=2.0)
    target2 = create_test_unit(side="ai", pos=5.0)

    assert is_in_range(attacker, target1) is True
    assert is_in_range(attacker, target2) is False


def test_find_nearest_enemy():
    """最近接敵の選定"""
    attacker = create_test_unit(pos=0.0, range_val=5.0)
    enemy1 = create_test_unit(side="ai", pos=3.0)
    enemy2 = create_test_unit(side="ai", pos=1.0)  # より近い
    enemy3 = create_test_unit(side="ai", pos=10.0)  # 射程外

    enemies = [enemy1, enemy2, enemy3]
    nearest = find_nearest_enemy(attacker, enemies)

    assert nearest == enemy2


def test_move_unit_player():
    """プレイヤーユニットの移動（右へ）"""
    unit = create_test_unit(side="player", pos=5.0, speed=1.0)
    event = move_unit(unit, 0.2)  # 200msで0.2秒

    assert unit.pos == 5.2
    assert event is not None
    assert event.type == "MOVE"


def test_move_unit_ai():
    """AIユニットの移動（左へ）"""
    unit = create_test_unit(side="ai", pos=15.0, speed=1.0)
    event = move_unit(unit, 0.2)

    assert unit.pos == 14.8
    assert event is not None


def test_move_unit_clamp():
    """位置クランプ（0-20の範囲）"""
    unit1 = create_test_unit(side="player", pos=19.9, speed=1.0)
    move_unit(unit1, 0.2)
    assert unit1.pos == 20.0  # 上限

    unit2 = create_test_unit(side="ai", pos=0.1, speed=1.0)
    move_unit(unit2, 0.2)
    assert unit2.pos == 0.0  # 下限


def test_update_cooldown():
    """クールダウン更新"""
    unit = create_test_unit()
    unit.cooldown = 2.0

    update_cooldown(unit, 0.2)
    assert unit.cooldown == 1.8

    update_cooldown(unit, 2.0)
    assert unit.cooldown == 0.0  # 負にならない


def test_try_attack():
    """攻撃処理"""
    attacker = create_test_unit(atk=5)
    target = create_test_unit(side="ai", hp=10)

    events = try_attack(attacker, target, 1000)

    # ATTACK, HITイベントが発生
    assert len(events) >= 2
    assert events[0].type == "ATTACK"
    assert events[1].type == "HIT"

    # ダメージ適用
    assert target.hp == 5

    # クールダウン設定
    assert attacker.cooldown == 2.0


def test_try_attack_death():
    """攻撃で敵を倒す"""
    attacker = create_test_unit(atk=10)
    target = create_test_unit(side="ai", hp=5)

    events = try_attack(attacker, target, 1000)

    # ATTACK, HIT, DEATHイベントが発生
    assert len(events) == 3
    assert events[2].type == "DEATH"
    assert target.hp == 0


def test_check_base_reached_player():
    """プレイヤーユニットが拠点到達"""
    game_state = GameState(
        match_id=uuid4(),
        ai_base_hp=100
    )
    unit = create_test_unit(side="player", pos=20.0)

    reached, events = check_base_reached(unit, game_state, 1000)

    assert reached is True
    assert game_state.ai_base_hp == 95  # atk=5のダメージ
    assert len(events) == 2
    assert events[0].type == "BASE_DAMAGE"
    assert events[1].type == "DEATH"


def test_check_base_reached_ai():
    """AIユニットが拠点到達"""
    game_state = GameState(
        match_id=uuid4(),
        player_base_hp=100
    )
    unit = create_test_unit(side="ai", pos=0.0)

    reached, events = check_base_reached(unit, game_state, 1000)

    assert reached is True
    assert game_state.player_base_hp == 95


def test_determine_winner():
    """勝者判定"""
    game_state1 = GameState(match_id=uuid4(), player_base_hp=0, ai_base_hp=50)
    assert determine_winner(game_state1) == "ai"

    game_state2 = GameState(match_id=uuid4(), player_base_hp=50, ai_base_hp=0)
    assert determine_winner(game_state2) == "player"

    game_state3 = GameState(match_id=uuid4(), player_base_hp=50, ai_base_hp=50)
    assert determine_winner(game_state3) is None


def test_process_tick_basic():
    """基本的なtick処理"""
    game_state = GameState(
        match_id=uuid4(),
        tick_ms=200,
        time_ms=0,
        player_cost=5.0,
        ai_cost=5.0,
        cost_recovery_per_tick=0.6
    )

    # ユニットを配置
    player_unit = create_test_unit(side="player", pos=5.0, speed=1.0)
    ai_unit = create_test_unit(side="ai", pos=15.0, speed=1.0)
    game_state.units = [player_unit, ai_unit]

    events = process_tick(game_state)

    # 時間が進む
    assert game_state.time_ms == 200

    # コストが回復
    assert game_state.player_cost == 5.6
    assert game_state.ai_cost == 5.6

    # ユニットが移動
    assert player_unit.pos == 5.2
    assert ai_unit.pos == 14.8

    # MOVEイベントが発生
    move_events = [e for e in events if e.type == "MOVE"]
    assert len(move_events) == 2


def test_spawn_unit_in_game():
    """ユニット召喚"""
    game_state = GameState(match_id=uuid4())
    unit = create_test_unit(side="player", pos=0.0)

    event = spawn_unit_in_game(game_state, unit, 1000)

    assert len(game_state.units) == 1
    assert event.type == "SPAWN"
    assert event.timestamp_ms == 1000
