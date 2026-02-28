"""
ゲーム状態データモデル

GameState: 対戦の全状態（tick処理で更新）
Event: tick処理中に発生したイベント（演出用）
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .unit import UnitInstance


class Event(BaseModel):
    """
    ゲーム内イベント（演出用）

    tick処理中に発生したイベントをクライアントに通知する。
    SPAWN: ユニット召喚
    MOVE: ユニット移動
    ATTACK: 攻撃開始
    HIT: ダメージ発生
    DEATH: ユニット死亡
    BASE_DAMAGE: 拠点ダメージ
    """
    type: Literal["SPAWN", "MOVE", "ATTACK", "HIT", "DEATH", "BASE_DAMAGE"] = Field(
        ..., description="イベントタイプ"
    )
    timestamp_ms: int = Field(..., description="発生時刻（ゲーム内時間、ミリ秒）")
    data: Dict[str, Any] = Field(default_factory=dict, description="イベント固有データ")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "type": "SPAWN",
                    "timestamp_ms": 1000,
                    "data": {
                        "instance_id": "123e4567-e89b-12d3-a456-426614174000",
                        "side": "player",
                        "pos": 0.0
                    }
                },
                {
                    "type": "ATTACK",
                    "timestamp_ms": 2000,
                    "data": {
                        "attacker_id": "123e4567-e89b-12d3-a456-426614174000",
                        "target_id": "987fcdeb-51a2-43d7-89ab-fedcba098765",
                        "damage": 5
                    }
                },
                {
                    "type": "BASE_DAMAGE",
                    "timestamp_ms": 3000,
                    "data": {
                        "side": "ai",
                        "damage": 5,
                        "remaining_hp": 95
                    }
                }
            ]
        }


class GameState(BaseModel):
    """
    対戦の全状態

    インメモリで管理され、tick処理で更新される。
    サーバー再起動で失われるが、短期対戦なので許容範囲。
    """
    match_id: UUID = Field(..., description="マッチID")

    # 時間管理
    tick_ms: int = Field(default=200, description="1tickの時間（ミリ秒）")
    time_ms: int = Field(default=0, description="経過時間（ミリ秒）")

    # 拠点HP
    player_base_hp: int = Field(default=100, ge=0, description="プレイヤー拠点HP")
    ai_base_hp: int = Field(default=100, ge=0, description="AI拠点HP")

    # コスト管理
    player_cost: float = Field(default=10.0, ge=0.0, le=20.0, description="プレイヤーコスト")
    ai_cost: float = Field(default=10.0, ge=0.0, le=20.0, description="AIコスト")
    max_cost: float = Field(default=20.0, description="最大コスト")
    cost_recovery_per_tick: float = Field(default=0.6, description="tick毎のコスト回復量")

    # ユニット状態
    units: List[UnitInstance] = Field(default_factory=list, description="盤面上のユニット")

    # 勝敗
    winner: Optional[Literal["player", "ai"]] = Field(None, description="勝者（未決定の場合None）")

    # デッキ情報（参照用）
    player_deck_id: Optional[UUID] = Field(None, description="プレイヤーデッキID")
    ai_deck_id: Optional[UUID] = Field(None, description="AIデッキID")

    # 作成日時
    created_at: datetime = Field(default_factory=datetime.utcnow, description="マッチ作成日時")

    def is_finished(self) -> bool:
        """対戦が終了しているか"""
        return self.winner is not None

    def get_player_units(self) -> List[UnitInstance]:
        """プレイヤー側のユニット一覧"""
        return [u for u in self.units if u.side == "player"]

    def get_ai_units(self) -> List[UnitInstance]:
        """AI側のユニット一覧"""
        return [u for u in self.units if u.side == "ai"]

    class Config:
        json_schema_extra = {
            "example": {
                "match_id": "550e8400-e29b-41d4-a716-446655440000",
                "tick_ms": 200,
                "time_ms": 5000,
                "player_base_hp": 100,
                "ai_base_hp": 95,
                "player_cost": 8.5,
                "ai_cost": 12.0,
                "max_cost": 20.0,
                "cost_recovery_per_tick": 0.6,
                "units": [
                    {
                        "instance_id": "123e4567-e89b-12d3-a456-426614174000",
                        "unit_spec_id": "550e8400-e29b-41d4-a716-446655440000",
                        "side": "player",
                        "pos": 5.0,
                        "hp": 8,
                        "cooldown": 1.5,
                        "max_hp": 10,
                        "atk": 5,
                        "speed": 1.5,
                        "range": 2.0,
                        "atk_interval": 2.0
                    }
                ],
                "winner": None,
                "player_deck_id": "abc12345-1234-1234-1234-123456789abc",
                "ai_deck_id": "def67890-5678-5678-5678-567890abcdef"
            }
        }
