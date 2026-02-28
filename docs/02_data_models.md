# データモデル定義（1レーンリアルタイムMVP）

このドキュメントでは、Pixel Simulation Arenaで使用する全てのデータモデルをPydanticスキーマで定義します。

## 概要

- **言語**: Python 3.11+
- **フレームワーク**: Pydantic v2
- **型安全性**: 全てのフィールドに型アノテーションを使用
- **バリデーション**: Pydanticの自動検証を活用

## 基本モデル

### UnitSpec（ユニット仕様）

永続化されるユニットの設計図:

```python
from pydantic import BaseModel, Field
from typing import Optional

class UnitSpec(BaseModel):
    """ユニット仕様（永続）"""
    id: str = Field(..., description="ユニットID（UUID）")
    name: str = Field(..., min_length=1, max_length=50, description="ユニット名")

    # ステータス
    cost: int = Field(..., ge=1, le=8, description="召喚コスト")
    max_hp: int = Field(..., ge=5, le=30, description="最大HP")
    atk: int = Field(..., ge=1, le=15, description="攻撃力")
    speed: float = Field(..., ge=0.2, le=2.0, description="移動速度（マス/tick）")
    range: float = Field(..., ge=1.0, le=7.0, description="射程")
    atk_interval: float = Field(..., ge=1.0, le=5.0, description="攻撃間隔（秒）")

    # アセット（画像）
    sprite_url: str = Field(..., description="スプライト画像URL（32x32px、ゲーム内表示用）")
    card_url: str = Field(..., description="カード絵画像URL（256x256px、デッキ・ギャラリー表示用）")

    # 画像生成メタデータ（オプション）
    image_prompt: Optional[str] = Field(None, description="画像生成時のプロンプト")
    original_prompt: Optional[str] = Field(None, description="ユニット生成時のオリジナルプロンプト")

    # メタデータ
    created_at: str = Field(..., description="生成日時（ISO8601形式）")

# 画像URL生成例
# sprite_url: http://localhost:8000/static/sprites/{unit_id}.png
# card_url: http://localhost:8000/static/cards/{unit_id}.png
```

### UnitInstance（ユニットインスタンス）

試合中のユニットの状態:

```python
class UnitInstance(BaseModel):
    """ユニットインスタンス（試合中）"""
    instance_id: str = Field(..., description="インスタンスID")
    spec_id: str = Field(..., description="UnitSpec参照")
    side: Literal["player", "ai"] = Field(..., description="所属陣営")
    hp: int = Field(..., ge=0, description="現在HP")
    pos: float = Field(..., ge=0.0, le=20.0, description="現在位置（0-20）")
    cooldown_remaining: float = Field(default=0.0, ge=0.0, description="攻撃クールダウン（秒）")
```

### GameState（ゲーム状態）

```python
class GameState(BaseModel):
    """ゲーム状態"""
    match_id: str = Field(..., description="対戦ID")
    tick_ms: int = Field(default=200, description="tick間隔（ms）")
    time_ms: int = Field(default=0, description="経過時間（ms）")

    # 拠点HP
    player_base_hp: int = Field(default=100, ge=0, le=100, description="プレイヤー拠点HP")
    ai_base_hp: int = Field(default=100, ge=0, le=100, description="AI拠点HP")

    # コスト
    player_cost: float = Field(default=10.0, ge=0.0, le=20.0, description="プレイヤーコスト")
    ai_cost: float = Field(default=10.0, ge=0.0, le=20.0, description="AIコスト")

    # ユニット
    units: List[UnitInstance] = Field(default_factory=list, description="盤面上のユニット")

    # 勝敗
    winner: Optional[Literal["player", "ai"]] = Field(None, description="勝者")
```

### Event（イベント）

演出用のイベントログ:

```python
class Event(BaseModel):
    """イベント（演出用）"""
    type: Literal["SPAWN", "MOVE", "ATTACK", "HIT", "DEATH", "BASE_DAMAGE"] = Field(
        ..., description="イベント種別"
    )
    timestamp_ms: int = Field(..., description="発生時刻（ms）")
    data: Dict[str, Any] = Field(default_factory=dict, description="イベント固有データ")

# イベント例:
# SPAWN: {"side": "player", "instance_id": "u1", "pos": 0}
# MOVE: {"instance_id": "u1", "from_pos": 5.0, "to_pos": 5.2}
# ATTACK: {"attacker_id": "u1", "target_id": "u2", "damage": 5}
# HIT: {"instance_id": "u2", "damage": 5, "hp_after": 10}
# DEATH: {"instance_id": "u2", "pos": 10.5}
# BASE_DAMAGE: {"side": "ai", "damage": 8, "hp_after": 42}
```

### Deck（デッキ）

```python
class Deck(BaseModel):
    """デッキ"""
    id: str = Field(..., description="デッキID（UUID）")
    name: str = Field(default="My Deck", description="デッキ名")
    unit_spec_ids: List[str] = Field(..., min_items=5, max_items=5, description="UnitSpec IDリスト")
```

## API入出力モデル

### ユニット生成リクエスト

```python
class UnitGenerateRequest(BaseModel):
    """ユニット生成リクエスト"""
    prompt: str = Field(..., min_length=1, max_length=200, description="ユニット生成プロンプト")
```

### ユニット生成レスポンス

```python
class UnitGenerateResponse(BaseModel):
    """ユニット生成レスポンス"""
    unit_spec: UnitSpec = Field(..., description="生成されたUnitSpec")
```

### 対戦開始リクエスト

```python
class MatchStartRequest(BaseModel):
    """対戦開始リクエスト"""
    player_deck_id: Optional[str] = Field(None, description="プレイヤーデッキID")
    ai_deck_id: Optional[str] = Field(None, description="AIデッキID（省略時は自動生成）")
```

### 対戦開始レスポンス

```python
class MatchStartResponse(BaseModel):
    """対戦開始レスポンス"""
    match_id: str = Field(..., description="対戦ID")
    game_state: GameState = Field(..., description="初期ゲーム状態")
```

### ユニット召喚リクエスト

```python
class SpawnRequest(BaseModel):
    """ユニット召喚リクエスト"""
    match_id: str = Field(..., description="対戦ID")
    side: Literal["player", "ai"] = Field(..., description="召喚側")
    unit_spec_id: str = Field(..., description="召喚するUnitSpec ID")
```

### ユニット召喚レスポンス

```python
class SpawnResponse(BaseModel):
    """ユニット召喚レスポンス"""
    game_state: GameState = Field(..., description="更新後のゲーム状態")
    events: List[Event] = Field(default_factory=list, description="発生したイベント")
```

### tick実行リクエスト

```python
class TickRequest(BaseModel):
    """tick実行リクエスト"""
    match_id: str = Field(..., description="対戦ID")
```

### tick実行レスポンス

```python
class TickResponse(BaseModel):
    """tick実行レスポンス"""
    game_state: GameState = Field(..., description="更新後のゲーム状態")
    events: List[Event] = Field(default_factory=list, description="発生したイベント")
```

### AI決定リクエスト

```python
class AIDecideRequest(BaseModel):
    """AI決定リクエスト"""
    match_id: str = Field(..., description="対戦ID")
```

### AI決定レスポンス

```python
class AIDecideResponse(BaseModel):
    """AI決定レスポンス"""
    spawn_unit_spec_id: Optional[str] = Field(None, description="召喚するUnitSpec ID")
    wait_ms: int = Field(default=600, description="次の判断までの待機時間")
    reason: str = Field(default="", description="判断理由")
```

### ギャラリー一覧レスポンス

```python
class GalleryListResponse(BaseModel):
    """ギャラリー一覧レスポンス"""
    unit_specs: List[UnitSpec] = Field(..., description="保存済みUnitSpecリスト")
    total: int = Field(..., description="総数")
```

### デッキ保存リクエスト

```python
class DeckSaveRequest(BaseModel):
    """デッキ保存リクエスト"""
    name: str = Field(..., description="デッキ名")
    unit_spec_ids: List[str] = Field(..., min_items=5, max_items=5, description="UnitSpec IDリスト")
```

### デッキ保存レスポンス

```python
class DeckSaveResponse(BaseModel):
    """デッキ保存レスポンス"""
    deck_id: str = Field(..., description="デッキID")
```

## データベーススキーマ（SQLite）

### units テーブル

```sql
CREATE TABLE units (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cost INTEGER NOT NULL,
    max_hp INTEGER NOT NULL,
    atk INTEGER NOT NULL,
    speed REAL NOT NULL,
    range REAL NOT NULL,
    atk_interval REAL NOT NULL,
    sprite_url TEXT NOT NULL,
    card_url TEXT NOT NULL,
    image_prompt TEXT,           -- 画像生成時のプロンプト
    original_prompt TEXT,         -- ユニット生成時のオリジナルプロンプト
    created_at TEXT NOT NULL
);
```

### decks テーブル

```sql
CREATE TABLE decks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    unit_spec_ids TEXT NOT NULL  -- JSON array
);
```

### matches テーブル（オプション）

```sql
CREATE TABLE matches (
    match_id TEXT PRIMARY KEY,
    player_deck_id TEXT,
    ai_deck_id TEXT,
    winner TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT
);
```

## パワースコア計算

```python
def calculate_power_score(unit_spec: UnitSpec) -> float:
    """パワースコアを計算"""
    return (
        unit_spec.max_hp * 0.4 +
        unit_spec.atk * 1.4 +
        (unit_spec.range ** 1.5) * 8 +
        unit_spec.speed * 6 +
        (1 / unit_spec.atk_interval) * 10
    )

def calculate_cost(power: float) -> int:
    """コストを計算"""
    import math
    return max(1, min(8, math.ceil(power / 20)))
```

## バリデーション例

```python
from pydantic import validator

class UnitSpec(BaseModel):
    # ... fields ...

    @validator("cost")
    def validate_cost(cls, v):
        """コストは1-8の範囲"""
        if not (1 <= v <= 8):
            raise ValueError("cost must be between 1 and 8")
        return v

    @validator("max_hp")
    def validate_max_hp(cls, v):
        """HPは5-30の範囲"""
        if not (5 <= v <= 30):
            raise ValueError("max_hp must be between 5 and 30")
        return v
```

## 次のステップ

1. `server/app/schemas/`にPydanticモデルを実装
2. SQLiteデータベースとテーブルを作成
3. APIエンドポイントで入出力モデルを使用
4. パワースコア計算とコスト調整のロジックを実装
