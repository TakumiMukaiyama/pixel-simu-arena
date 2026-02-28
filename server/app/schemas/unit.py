"""
ユニットデータモデル

UnitSpec: データベースに保存されるユニットの設計図
UnitInstance: ゲーム内で実際に召喚されたユニットの状態
"""
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class UnitSpec(BaseModel):
    """
    ユニットの設計図（永続化されるデータ）

    プロンプトから生成されたユニットの基本情報とステータス。
    データベースに保存され、デッキやギャラリーで参照される。
    """
    id: UUID = Field(default_factory=uuid4, description="ユニットID")
    name: str = Field(..., min_length=1, max_length=50, description="ユニット名")

    # ステータス（バランス調整済み）
    cost: int = Field(..., ge=1, le=8, description="召喚コスト")
    max_hp: int = Field(..., ge=5, le=30, description="最大HP")
    atk: int = Field(..., ge=1, le=15, description="攻撃力")
    speed: float = Field(..., ge=0.2, le=2.0, description="移動速度（マス/tick）")
    range: float = Field(..., ge=1.0, le=7.0, description="攻撃射程（マス）")
    atk_interval: float = Field(..., ge=1.0, le=5.0, description="攻撃間隔（秒）")

    # 画像URL
    sprite_url: str = Field(..., description="32x32スプライトのURL")
    card_url: str = Field(..., description="256x256カード絵のURL")

    # メタデータ
    image_prompt: Optional[str] = Field(None, description="画像生成に使用したプロンプト")
    original_prompt: Optional[str] = Field(None, description="ユーザーの元プロンプト")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="作成日時")

    @field_validator('speed', 'range', 'atk_interval')
    @classmethod
    def round_to_two_decimals(cls, v: float) -> float:
        """小数点第2位まで丸める"""
        return round(v, 2)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Fast Ninja",
                "cost": 3,
                "max_hp": 10,
                "atk": 5,
                "speed": 1.5,
                "range": 2.0,
                "atk_interval": 2.0,
                "sprite_url": "/static/sprites/550e8400-e29b-41d4-a716-446655440000.png",
                "card_url": "/static/cards/550e8400-e29b-41d4-a716-446655440000.png",
                "image_prompt": "pixel art, side view, ninja, 32x32, simple design",
                "original_prompt": "fast ninja"
            }
        }


class UnitInstance(BaseModel):
    """
    ゲーム内で召喚されたユニットの状態

    GameStateの一部として、対戦中のユニットの現在の状態を表す。
    tick処理で位置、HP、クールダウンが更新される。
    """
    instance_id: UUID = Field(default_factory=uuid4, description="インスタンスID")
    unit_spec_id: UUID = Field(..., description="元となるUnitSpecのID")
    side: Literal["player", "ai"] = Field(..., description="所属（player or ai）")

    # 現在の状態
    pos: float = Field(..., description="現在位置（0-20のレーン上）")
    hp: int = Field(..., ge=0, description="現在HP")
    cooldown: float = Field(default=0.0, ge=0, description="攻撃クールダウン（秒）")

    # 元のスペック（計算用にコピー）
    max_hp: int = Field(..., ge=5, le=30)
    atk: int = Field(..., ge=1, le=15)
    speed: float = Field(..., ge=0.2, le=2.0)
    range: float = Field(..., ge=1.0, le=7.0)
    atk_interval: float = Field(..., ge=1.0, le=5.0)

    @field_validator('pos')
    @classmethod
    def validate_position(cls, v: float) -> float:
        """位置を0-20の範囲にクランプ"""
        return max(0.0, min(20.0, v))

    @classmethod
    def from_spec(
        cls,
        spec: UnitSpec,
        side: Literal["player", "ai"],
        initial_pos: float
    ) -> "UnitInstance":
        """UnitSpecから初期化されたインスタンスを作成"""
        return cls(
            unit_spec_id=spec.id,
            side=side,
            pos=initial_pos,
            hp=spec.max_hp,
            cooldown=0.0,
            max_hp=spec.max_hp,
            atk=spec.atk,
            speed=spec.speed,
            range=spec.range,
            atk_interval=spec.atk_interval
        )

    class Config:
        json_schema_extra = {
            "example": {
                "instance_id": "123e4567-e89b-12d3-a456-426614174000",
                "unit_spec_id": "550e8400-e29b-41d4-a716-446655440000",
                "side": "player",
                "pos": 0.0,
                "hp": 10,
                "cooldown": 0.0,
                "max_hp": 10,
                "atk": 5,
                "speed": 1.5,
                "range": 2.0,
                "atk_interval": 2.0
            }
        }
