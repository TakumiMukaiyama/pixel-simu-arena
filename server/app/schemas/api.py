"""
API入出力モデル

各エンドポイントのリクエスト・レスポンスモデル
"""
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .game import Event, GameState
from .unit import UnitSpec


# ========== AI Analysis Models ==========

class BattlefieldAssessment(BaseModel):
    """戦場状況の分析"""
    enemy_threat_level: Literal["high", "medium", "low"] = Field(..., description="敵の脅威レベル")
    enemy_composition: str = Field(..., description="敵の構成説明（2-3文）")
    ally_status: str = Field(..., description="味方の状況説明（2-3文）")
    strategic_situation: str = Field(..., description="戦略的状況の全体評価")


class CandidateEvaluation(BaseModel):
    """候補ユニットの評価"""
    unit_id: UUID = Field(..., description="ユニットID")
    unit_name: str = Field(..., description="ユニット名")
    score: int = Field(..., ge=0, le=100, description="評価スコア（0-100）")
    pros: List[str] = Field(..., description="長所リスト")
    cons: List[str] = Field(..., description="短所リスト")
    cost_efficiency: Literal["high", "medium", "low"] = Field(..., description="コスト効率")


class AIAnalysis(BaseModel):
    """AI思考分析の詳細"""
    battlefield_assessment: BattlefieldAssessment = Field(..., description="戦場評価")
    candidate_evaluation: List[CandidateEvaluation] = Field(..., description="候補ユニット評価")
    decision_reasoning: List[str] = Field(..., description="推論ステップ（3-5ステップ）")
    selected_strategy: Literal["defensive", "offensive", "economic", "balanced"] = Field(..., description="選択した戦略")
    confidence: float = Field(..., ge=0.0, le=1.0, description="判断の信頼度")


# ========== Match API ==========

class MatchStartRequest(BaseModel):
    """対戦開始リクエスト"""
    player_deck_id: UUID = Field(..., description="プレイヤーデッキID")
    ai_deck_id: Optional[UUID] = Field(None, description="AIデッキID（指定しない場合はランダム生成）")

    class Config:
        json_schema_extra = {
            "example": {
                "player_deck_id": "abc12345-1234-1234-1234-123456789abc",
                "ai_deck_id": "def67890-5678-5678-5678-567890abcdef"
            }
        }


class MatchStartResponse(BaseModel):
    """対戦開始レスポンス"""
    match_id: UUID = Field(..., description="マッチID")
    game_state: GameState = Field(..., description="初期ゲーム状態")


class MatchTickRequest(BaseModel):
    """tick実行リクエスト"""
    match_id: UUID = Field(..., description="マッチID")


class MatchTickResponse(BaseModel):
    """tick実行レスポンス"""
    game_state: GameState = Field(..., description="更新後のゲーム状態")
    events: List[Event] = Field(default_factory=list, description="発生したイベント")


class MatchSpawnRequest(BaseModel):
    """ユニット召喚リクエスト"""
    match_id: UUID = Field(..., description="マッチID")
    side: str = Field(..., description="召喚側（player or ai）")
    unit_spec_id: UUID = Field(..., description="召喚するユニットのID")

    class Config:
        json_schema_extra = {
            "example": {
                "match_id": "550e8400-e29b-41d4-a716-446655440000",
                "side": "player",
                "unit_spec_id": "660e9511-f30c-52e5-b827-557766551111"
            }
        }


class MatchSpawnResponse(BaseModel):
    """ユニット召喚レスポンス"""
    game_state: GameState = Field(..., description="更新後のゲーム状態")
    events: List[Event] = Field(default_factory=list, description="発生したイベント")


class AIDecideRequest(BaseModel):
    """AI召喚決定リクエスト"""
    match_id: UUID = Field(..., description="マッチID")


class AIDecideResponse(BaseModel):
    """AI召喚決定レスポンス"""
    spawn_unit_spec_id: Optional[UUID] = Field(None, description="召喚するユニットID（召喚しない場合None）")
    wait_ms: int = Field(default=600, description="次回判断までの待機時間（ミリ秒）")
    reason: str = Field(default="", description="簡潔な判断理由（表示用）")
    analysis: Optional[AIAnalysis] = Field(None, description="詳細な思考分析（オプション）")

    class Config:
        json_schema_extra = {
            "example": {
                "spawn_unit_spec_id": "550e8400-e29b-41d4-a716-446655440000",
                "wait_ms": 600,
                "reason": "Enemy has strong units, spawning tank for defense"
            }
        }


# ========== Units API ==========

class UnitCreateRequest(BaseModel):
    """ユニット生成リクエスト"""
    prompt: str = Field(..., min_length=1, max_length=500, description="ユニット生成プロンプト")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "fast ninja with high speed and low defense"
            }
        }


class UnitCreateResponse(BaseModel):
    """ユニット生成レスポンス"""
    unit_spec: UnitSpec = Field(..., description="生成されたユニット")


# ========== Gallery API ==========

class GalleryListRequest(BaseModel):
    """ギャラリー一覧リクエスト（クエリパラメータ）"""
    limit: int = Field(default=20, ge=1, le=100, description="取得件数")
    offset: int = Field(default=0, ge=0, description="オフセット")


class GalleryListResponse(BaseModel):
    """ギャラリー一覧レスポンス"""
    unit_specs: List[UnitSpec] = Field(..., description="ユニット一覧")
    total: int = Field(..., description="総件数")


# ========== Deck API ==========

class DeckSaveRequest(BaseModel):
    """デッキ保存リクエスト"""
    name: str = Field(..., min_length=1, max_length=100, description="デッキ名")
    unit_spec_ids: List[UUID] = Field(..., min_length=5, max_length=5, description="ユニットID配列（5枚）")

    class Config:
        json_schema_extra = {
            "example": {
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


class DeckSaveResponse(BaseModel):
    """デッキ保存レスポンス"""
    deck_id: UUID = Field(..., description="保存されたデッキID")


class DeckUpdateRequest(BaseModel):
    """デッキ更新リクエスト"""
    name: str = Field(..., min_length=1, max_length=100, description="デッキ名")
    unit_spec_ids: List[UUID] = Field(..., min_length=5, max_length=5, description="ユニットID配列（5枚）")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Deck",
                "unit_spec_ids": [
                    "550e8400-e29b-41d4-a716-446655440000",
                    "660e9511-f30c-52e5-b827-557766551111",
                    "770ea622-0401-63f6-c938-668877662222",
                    "880eb733-1512-74g7-d049-779988773333",
                    "990ec844-2623-85h8-e15a-880099884444"
                ]
            }
        }


class DeckGetResponse(BaseModel):
    """デッキ取得レスポンス"""
    deck: "Deck" = Field(..., description="デッキ情報")
    units: List[UnitSpec] = Field(..., description="デッキに含まれるユニット一覧")


# 循環参照対策
from .deck import Deck  # noqa: E402
DeckGetResponse.model_rebuild()
