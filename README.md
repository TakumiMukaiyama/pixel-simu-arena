# Pixel Simulation Arena

生成AIを活用したリアルタイム対戦ゲーム。プレイヤーは自由なプロンプトを入力してオリジナルのユニットを生成し、AI（Mistral）が操作する敵と対戦します。

## コアコンセプト

- **プロンプト駆動のユニット生成**: テキストからバランスの取れたユニットが自動生成される
- **自動画像生成**: Mistral Image APIで32×32スプライト + 256×256カード絵を自動生成
- **リアルタイム1レーンバトル**: 0-20の1次元レーンで、ユニットが自動的に移動・攻撃
- **AI対戦相手**: Mistral APIが盤面を見て、次に召喚するユニットを決定
- **ビジュアルギャラリー**: 生成したユニットをカード形式で閲覧・デッキ編成

## 技術スタック

### サーバーサイド
- Python 3.11+
- FastAPI
- Pydantic v2
- Mistral API（mistral-large-latest + Pixtral Large）
- SQLite

### クライアントサイド
- React 18+
- TypeScript
- Vite
- PixiJS 8.x
- @pixi/react

## プロジェクト構造（monorepo）

```
pixel-simu-arena/
├── server/         # FastAPIバックエンド
│   ├── app/
│   │   ├── api/         # APIエンドポイント
│   │   ├── engine/      # ゲームエンジン（tick処理）
│   │   ├── llm/         # Mistral連携（ユニット生成・画像生成・AI決定）
│   │   ├── storage/     # DB・画像保存
│   │   └── schemas/     # Pydanticモデル
│   └── static/
│       ├── sprites/     # 32×32スプライト画像
│       └── cards/       # 256×256カード絵
├── web/            # React + PixiJSフロントエンド
│   └── src/
│       ├── api/         # APIクライアント
│       ├── game/        # PixiJS統合
│       ├── screens/     # React画面
│       └── components/  # UIコンポーネント
└── docs/           # 設計ドキュメント
    ├── 00_overview.md
    ├── 01_game_rules.md
    ├── 02_data_models.md
    ├── 03_api_design.md
    ├── 12_implementation_roadmap.md
    └── 13_image_generation.md
```

## クイックスタート

### 1. Mistral API キーの取得

1. [Mistral Console](https://console.mistral.ai/) でアカウント作成
2. API Keysセクションで新しいキーを作成
3. APIキーをコピー

### 2. サーバー環境のセットアップ

```bash
cd server

# 依存関係のインストール
uv venv
uv sync

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してMISTRAL_API_KEYを設定

# 画像保存用ディレクトリの作成
mkdir -p static/sprites static/cards

# Mistral API接続テスト
uv run python test_mistral.py

# サーバー起動
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

詳細は [server/SETUP_MISTRAL.md](server/SETUP_MISTRAL.md) を参照。

### 3. クライアント環境のセットアップ（React + PixiJS）

```bash
cd web

# 依存関係のインストール
npm install

# 開発サーバー起動
npm run dev
```

ブラウザで http://localhost:5173 を開く。

## API ドキュメント

サーバー起動後、以下のURLでAPI仕様を確認できます:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要エンドポイント

#### Match（対戦）
- `POST /match/start` - 対戦開始
- `POST /match/tick` - tick実行（200ms分）
- `POST /match/spawn` - ユニット召喚
- `POST /match/ai_decide` - AI召喚決定

#### Units（ユニット）
- `POST /units/create` - ユニット生成（画像生成含む）

#### Gallery（ギャラリー）
- `GET /gallery/list` - 保存済みユニット一覧

#### Deck（デッキ）
- `POST /deck/save` - デッキ保存
- `GET /deck/{deck_id}` - デッキ取得

## 設計ドキュメント

詳細な設計ドキュメントは `docs/` ディレクトリを参照:

- [00_overview.md](docs/00_overview.md) - プロジェクト概要
- [01_game_rules.md](docs/01_game_rules.md) - ゲームルール（1レーン・リアルタイム）
- [02_data_models.md](docs/02_data_models.md) - データモデル定義
- [03_api_design.md](docs/03_api_design.md) - API設計
- [12_implementation_roadmap.md](docs/12_implementation_roadmap.md) - 実装ロードマップ
- [13_image_generation.md](docs/13_image_generation.md) - 画像生成システム設計

## 特徴的な機能

### 画像生成
- プロンプトからユニットを生成すると、自動的に以下の画像が生成されます:
  - **32×32スプライト**: ゲーム内のユニット表示用
  - **256×256カード絵**: デッキ・ギャラリー表示用
- Mistral Image API（Pixtral Large）を使用
- 画像プロンプトはユニット特徴から自動生成
- ギャラリーで生成したユニットを一覧表示・デッキ編成可能

### リアルタイムバトル
- 200ms単位のtick処理
- ユニットは自動的に移動・攻撃
- プレイヤーは召喚タイミングとユニット選択で戦略を練る
- AIは1秒に1回、盤面を見て次の召喚を決定

- [00_overview.md](docs/00_overview.md) - プロジェクト概要
- [01_game_rules.md](docs/01_game_rules.md) - ゲームルール
- [02_data_models.md](docs/02_data_models.md) - データモデル定義
- [03_api_design.md](docs/03_api_design.md) - API設計
- [04_battle_system.md](docs/04_battle_system.md) - 戦闘システム
- [05_ai_integration.md](docs/05_ai_integration.md) - AI連携
- [06_balance_design.md](docs/06_balance_design.md) - バランス調整

## 開発ガイド

開発環境のセットアップ詳細は [DEVELOPMENT.md](DEVELOPMENT.md) を参照してください。

### サーバー開発

```bash
cd server

# 開発サーバー起動（自動リロード）
uv run uvicorn main:app --reload

# テスト実行
uv run pytest

# Mistral API テスト
uv run python test_mistral.py
```

### Unity開発

1. Unity Editorで `client/` プロジェクトを開く
2. `Scenes/MainGame.unity` を開く
3. Play Modeでテスト
4. ビルド: `File > Build Settings > Build`

## トラブルシューティング

### Mistral API エラー

- **401 Unauthorized**: APIキーが無効
  - `.env` ファイルのMISTRAL_API_KEYを確認
  - Mistral Consoleでキーが有効か確認

- **429 Too Many Requests**: レート制限
  - しばらく待ってから再試行
  - Mistral Consoleでプランを確認

詳細は [server/SETUP_MISTRAL.md](server/SETUP_MISTRAL.md) を参照。

### サーバーが起動しない

```bash
# ポート8000が既に使用されている場合
uv run uvicorn main:app --reload --port 8001

# 依存関係の再インストール
uv sync --force
```

### Unity ビルドエラー

- `Library/` フォルダを削除してUnityを再起動
- `Edit > Preferences > External Tools` でC#エディタを確認

## コスト管理

Mistral APIは従量課金:
- mistral-large-latest: 約 $0.002/1K tokens (入力) + $0.006/1K tokens (出力)
- 1ユニット生成: 約 $0.01-0.02
- 1ゲーム（50ターン）: 約 $0.50-1.00

詳細は [Mistral Pricing](https://mistral.ai/pricing/) を参照。

## ライセンス

MIT License
