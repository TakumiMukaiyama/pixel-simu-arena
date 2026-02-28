# API設計（1レーンリアルタイムMVP）

## 概要

このドキュメントでは、Pixel Simulation ArenaのREST API仕様を定義します。

- **ベースURL**: `http://localhost:8000`
- **フォーマット**: JSON
- **認証**: なし（MVP）
- **CORS**: 有効

## エンドポイント一覧

### Match（対戦）

#### POST /match/start
対戦を開始する。

**リクエスト**:
```json
{
  "player_deck_id": "deck-123",  // optional
  "ai_deck_id": "deck-456"       // optional
}
```

**レスポンス**:
```json
{
  "match_id": "match-789",
  "game_state": {
    "match_id": "match-789",
    "tick_ms": 200,
    "time_ms": 0,
    "player_base_hp": 100,
    "ai_base_hp": 100,
    "player_cost": 10.0,
    "ai_cost": 10.0,
    "units": [],
    "winner": null
  }
}
```

#### POST /match/tick
ゲームを1tick進める（200ms分）。

**リクエスト**:
```json
{
  "match_id": "match-789"
}
```

**レスポンス**:
```json
{
  "game_state": {
    "match_id": "match-789",
    "tick_ms": 200,
    "time_ms": 200,
    "player_base_hp": 100,
    "ai_base_hp": 95,
    "player_cost": 10.6,
    "ai_cost": 10.6,
    "units": [
      {
        "instance_id": "u1",
        "spec_id": "spec-1",
        "side": "player",
        "hp": 10,
        "pos": 0.2,
        "cooldown_remaining": 1.8
      }
    ],
    "winner": null
  },
  "events": [
    {
      "type": "MOVE",
      "timestamp_ms": 200,
      "data": {
        "instance_id": "u1",
        "from_pos": 0.0,
        "to_pos": 0.2
      }
    }
  ]
}
```

#### POST /match/spawn
ユニットを召喚する。

**リクエスト**:
```json
{
  "match_id": "match-789",
  "side": "player",
  "unit_spec_id": "spec-1"
}
```

**レスポンス**:
```json
{
  "game_state": {
    // ... (更新後のGameState)
  },
  "events": [
    {
      "type": "SPAWN",
      "timestamp_ms": 400,
      "data": {
        "side": "player",
        "instance_id": "u2",
        "pos": 0.0
      }
    }
  ]
}
```

#### POST /match/ai_decide
AIが次に召喚するユニットを決定する（1秒に1回呼ぶ）。

**リクエスト**:
```json
{
  "match_id": "match-789"
}
```

**レスポンス**:
```json
{
  "spawn_unit_spec_id": "spec-3",
  "wait_ms": 600,
  "reason": "Need a tank unit to absorb damage"
}
```

### Units（ユニット）

#### POST /units/create
プロンプトからユニットを生成する（画像生成含む）。

**処理フロー**:
1. Mistralでユニット名・ステータスをJSON生成
2. パワースコア計算→コスト調整
3. 画像プロンプト自動生成（ユニット特徴に基づく）
4. Mistral Image API（Pixtral Large）で画像生成
   - 32×32スプライト
   - 256×256カード絵
5. 画像をローカルストレージに保存
6. UnitSpecをDBに保存
7. レスポンス返却

**リクエスト**:
```json
{
  "prompt": "A fast ninja with low HP"
}
```

**レスポンス**:
```json
{
  "unit_spec": {
    "id": "spec-1",
    "name": "Ninja",
    "cost": 3,
    "max_hp": 8,
    "atk": 5,
    "speed": 1.5,
    "range": 1.5,
    "atk_interval": 1.2,
    "sprite_url": "http://localhost:8000/static/sprites/spec-1.png",
    "card_url": "http://localhost:8000/static/cards/spec-1.png",
    "created_at": "2026-02-28T12:00:00Z"
  }
}
```

**エラー**:
- 画像生成失敗時はプレースホルダー画像URLを返す
- ステータス生成失敗時はルールベースフォールバック

### Gallery（ギャラリー）

#### GET /gallery/list
保存済みユニット一覧を取得する。

**クエリパラメータ**:
- `limit`: 取得件数（デフォルト: 50）
- `offset`: オフセット（デフォルト: 0）

**レスポンス**:
```json
{
  "unit_specs": [
    {
      "id": "spec-1",
      "name": "Ninja",
      "cost": 3,
      // ... (UnitSpec)
    },
    {
      "id": "spec-2",
      "name": "Knight",
      "cost": 5,
      // ... (UnitSpec)
    }
  ],
  "total": 42
}
```

### Deck（デッキ）

#### POST /deck/save
デッキを保存する。

**リクエスト**:
```json
{
  "name": "My Deck",
  "unit_spec_ids": [
    "spec-1",
    "spec-2",
    "spec-3",
    "spec-4",
    "spec-5"
  ]
}
```

**レスポンス**:
```json
{
  "deck_id": "deck-123"
}
```

#### GET /deck/{deck_id}
デッキを取得する。

**レスポンス**:
```json
{
  "id": "deck-123",
  "name": "My Deck",
  "unit_spec_ids": [
    "spec-1",
    "spec-2",
    "spec-3",
    "spec-4",
    "spec-5"
  ]
}
```

## エラーレスポンス

### 400 Bad Request
```json
{
  "detail": "Invalid request: cost must be between 1 and 8"
}
```

### 404 Not Found
```json
{
  "detail": "Match not found: match-789"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## 呼び出しフロー例

### ゲーム開始から終了まで

1. **ユニット生成**（事前準備）
```
POST /units/create
→ UnitSpec (spec-1)

POST /units/create
→ UnitSpec (spec-2)

...（5体生成）
```

2. **デッキ保存**
```
POST /deck/save
→ deck_id: "deck-123"
```

3. **対戦開始**
```
POST /match/start
→ match_id: "match-789"
```

4. **ゲームループ**（200msごと）
```
クライアント:
  - 200msごとに POST /match/tick を呼ぶ
  - GameState + Events を受け取る
  - PixiJSで描画更新
  - ユーザーがユニット召喚 → POST /match/spawn

AI:
  - 1秒に1回 POST /match/ai_decide を呼ぶ
  - spawn_unit_spec_id を受け取る
  - nullでなければ POST /match/spawn を呼ぶ
```

5. **勝敗確定**
```
POST /match/tick
→ game_state.winner = "player"
```

## 実装の推奨順序

1. **POST /units/create** - ユニット生成の基本動作確認
2. **POST /match/start** - 対戦の初期化
3. **POST /match/tick** - tick処理（移動・攻撃・死亡・拠点ダメージ）
4. **POST /match/spawn** - ユニット召喚
5. **POST /match/ai_decide** - AI召喚決定
6. **GET /gallery/list** - ギャラリー
7. **POST /deck/save, GET /deck/{deck_id}** - デッキ管理

## 次のステップ

1. FastAPIでエンドポイントを実装（`server/app/api/`）
2. ゲームエンジンの実装（`server/app/engine/`）
3. Mistral連携の実装（`server/app/llm/`）
4. Reactクライアントからの呼び出し
