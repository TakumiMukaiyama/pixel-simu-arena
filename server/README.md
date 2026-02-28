# Pixel Simulation Arena - Server

リアルタイム1レーン対戦ゲームのバックエンドサーバー。Mistral APIを使用したAI生成ユニットと戦略的AI対戦を実装。

## 技術スタック

- **言語**: Python 3.11+
- **フレームワーク**: FastAPI
- **データベース**: PostgreSQL (asyncpg)
- **AI**: Mistral API (mistral-large-latest + mistral-medium-2505)
- **パッケージ管理**: uv

## セットアップ

### 1. 依存関係のインストール

```bash
cd server
uv sync
```

### 2. PostgreSQL起動（Docker使用）

```bash
docker compose up -d
```

### 3. 環境変数設定

`.env`ファイルを作成：

```bash
cp .env.example .env
```

以下の環境変数を設定：

```env
# Mistral API
MISTRAL_API_KEY=your_actual_api_key

# Database
DATABASE_URL=postgresql://pixel_user:pixel_pass@localhost:5432/pixel_simu_arena

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Game Settings
TICK_MS=200
INITIAL_COST=10.0
MAX_COST=20.0
COST_RECOVERY_PER_TICK=0.6
INITIAL_BASE_HP=100
```

### 4. データベースマイグレーション

```bash
uv run alembic upgrade head
```

### 5. サーバー起動

```bash
uv run uvicorn app.main:app --reload
```

サーバーは http://localhost:8000 で起動します。

## API仕様

### Swagger UI

起動後、以下のURLでインタラクティブなAPI仕様を確認できます：

- http://localhost:8000/docs

### 主要エンドポイント

#### ユニット生成

```bash
POST /units/create
Content-Type: application/json

{
  "prompt": "fast ninja with high speed"
}
```

**レスポンス:**
- ステータス: 200 OK
- Mistral LLMがプロンプトからユニットを生成
- バランス調整済みのステータス（cost, hp, atk, speed, range, atk_interval）
- 画像URL（Rate limit時はプレースホルダー）

#### デッキ作成

```bash
POST /deck/save
Content-Type: application/json

{
  "name": "My Deck",
  "unit_spec_ids": [
    "uuid-1",
    "uuid-2",
    "uuid-3",
    "uuid-4",
    "uuid-5"
  ]
}
```

#### マッチ開始

```bash
POST /match/start
Content-Type: application/json

{
  "player_deck_id": "deck-uuid",
  "ai_deck_id": "deck-uuid"  # Optional
}
```

#### tick処理（200msごと）

```bash
POST /match/tick
Content-Type: application/json

{
  "match_id": "match-uuid"
}
```

#### ユニット召喚

```bash
POST /match/spawn
Content-Type: application/json

{
  "match_id": "match-uuid",
  "side": "player",
  "unit_spec_id": "unit-uuid"
}
```

#### AI決定

```bash
POST /match/ai_decide
Content-Type: application/json

{
  "match_id": "match-uuid"
}
```

**レスポンス:**
- Mistral LLMが盤面を分析して召喚判断
- `spawn_unit_spec_id`: 召喚するユニットID（null=召喚しない）
- `reason`: 判断理由（デバッグ用）

## テスト

### ユニットテスト

```bash
uv run pytest tests/ -v
```

### エンドツーエンドテスト

サーバーを起動してから：

```bash
uv run python test_e2e.py
```

このテストは以下を実行します：
1. 5体のユニット生成（Mistral API使用）
2. プレイヤーとAIのデッキ作成
3. マッチ開始
4. 60秒間のAI対戦シミュレーション

## プロジェクト構造

```
server/
├── app/
│   ├── main.py              # FastAPI初期化
│   ├── config.py            # 設定管理
│   ├── schemas/             # Pydanticモデル
│   │   ├── unit.py         # UnitSpec, UnitInstance
│   │   ├── game.py         # GameState, Event
│   │   ├── deck.py         # Deck
│   │   └── api.py          # API入出力モデル
│   ├── engine/              # ゲームエンジン
│   │   ├── tick.py         # メインtick処理
│   │   ├── movement.py     # 移動・攻撃ロジック
│   │   ├── victory.py      # 勝敗判定
│   │   └── balance.py      # パワースコア計算
│   ├── api/                 # APIエンドポイント
│   │   ├── match.py        # 対戦関連
│   │   ├── units.py        # ユニット生成
│   │   ├── gallery.py      # ギャラリー
│   │   ├── deck.py         # デッキ管理
│   │   └── exceptions.py   # カスタム例外
│   ├── llm/                 # Mistral連携
│   │   ├── unit_gen.py     # ユニット生成
│   │   ├── ai_decide.py    # AI決定
│   │   └── image_gen.py    # 画像生成
│   └── storage/             # データ永続化
│       ├── db.py           # PostgreSQL操作
│       └── session.py      # インメモリセッション
├── alembic/                 # DBマイグレーション
├── static/                  # 静的ファイル
│   ├── sprites/            # 32x32 スプライト
│   └── cards/              # 256x256 カード絵
├── tests/                   # テスト
├── docker-compose.yml       # PostgreSQL
├── pyproject.toml          # 依存関係
└── test_e2e.py             # E2Eテスト
```

## ゲームルール

### 1レーンリアルタイムバトル

- **レーン**: 0 (プレイヤー拠点) ←→ 20 (AI拠点)
- **tick**: 200msごとに状態更新
- **ユニット移動**: プレイヤーユニットは右へ、AIユニットは左へ自動移動
- **攻撃**: 射程内の最近接敵を自動攻撃
- **勝利条件**: 敵拠点のHPを0にする

### コストシステム

- **初期コスト**: 10.0
- **最大コスト**: 20.0
- **回復**: tick毎に+0.6 (1秒で+3.0)
- **ユニットコスト**: 1-8（パワースコアから自動計算）

### パワースコア計算式

```
power = HP×0.4 + ATK×1.4 + (RANGE^1.5)×8 + SPEED×6 + (1/ATK_INTERVAL)×10
cost = clamp(ceil(power / 20), 1, 8)
```

射程が戦略的に重要（指数的重み付け）。

## Mistral API使用

### ユニット生成

- **モデル**: mistral-large-latest
- **機能**: JSON mode（`response_format={"type": "json_object"}`）
- **プロンプト**: ユニット名とステータスを生成
- **バランス調整**: パワースコア計算後にコスト決定

### AI決定

- **モデル**: mistral-large-latest
- **機能**: JSON mode
- **入力**: 盤面状態サマリー（両陣営のユニット、HP、コスト）
- **出力**: 召喚判断とその理由

### 画像生成

- **モデル**: mistral-medium-2505
- **機能**: エージェントツール（image_generation）
- **出力**: 32x32スプライト + 256x256カード絵
- **Rate limit対策**: 失敗時はプレースホルダー使用

## エラーハンドリング

### カスタム例外

- `MatchNotFoundException`: マッチが見つからない
- `DeckNotFoundException`: デッキが見つからない
- `UnitNotFoundException`: ユニットが見つからない
- `InsufficientCostException`: コスト不足
- `MatchAlreadyFinishedException`: マッチ既に終了

### Mistral APIエラー

- **Rate limit**: 自動的にプレースホルダーにフォールバック
- **リトライ**: 最大3回（ユニット生成）、2回（AI決定、画像生成）
- **タイムアウト**: 設定可能

## パフォーマンス

- **tick処理**: <50ms（目標）
- **ユニット生成**: 2-5秒（Mistral API呼び出し）
- **画像生成**: 5-10秒（Rate limit時はスキップ）
- **同時接続**: インメモリセッション管理（スケールアウト時はRedis推奨）

## デプロイ

### 本番環境推奨設定

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@prod-host:5432/dbname
```

### スケーリング考慮事項

1. **セッション管理**: Redis使用を推奨
2. **データベース**: コネクションプール調整
3. **Mistral API**: レート制限に注意
4. **静的ファイル**: CDN使用推奨

## トラブルシューティング

### PostgreSQLに接続できない

```bash
# Dockerコンテナの状態確認
docker compose ps

# 再起動
docker compose restart
```

### Mistral APIエラー

- **401**: APIキーを確認
- **429**: Rate limit到達（時間を置いて再試行）
- **500**: Mistral側の問題（リトライまたはフォールバック）

### マイグレーションエラー

```bash
# 現在のリビジョン確認
uv run alembic current

# 強制的に最新に
uv run alembic upgrade head
```

## ライセンス

MIT License

## 開発者

Pixel Simulation Arena チーム
