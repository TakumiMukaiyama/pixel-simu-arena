"""
デッキデータモデル

Deck: 5枚のユニットで構成されるデッキ
"""
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Deck(BaseModel):
    """
    デッキ（5枚のユニット）

    プレイヤーまたはAIが使用するユニットの組み合わせ。
    データベースに保存され、マッチ開始時に読み込まれる。
    """
    id: UUID = Field(default_factory=uuid4, description="デッキID")
    name: str = Field(..., min_length=1, max_length=100, description="デッキ名")
    unit_spec_ids: List[UUID] = Field(..., min_length=5, max_length=5, description="ユニットID配列（5枚）")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="作成日時")

    @field_validator('unit_spec_ids')
    @classmethod
    def validate_unit_count(cls, v: List[UUID]) -> List[UUID]:
        """デッキは必ず5枚"""
        if len(v) != 5:
            raise ValueError("Deck must contain exactly 5 units")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc12345-1234-1234-1234-123456789abc",
                "name": "Balanced Deck",
                "unit_spec_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "660e9511-f30c-52e5-b827-557766551111",
                    "770ea622-0401-63f6-c938-668877662222",
                    "880eb733-1512-74g7-d049-779988773333",
                    "990ec844-2623-85h8-e15a-880099884444"
                ]
            }
        }
