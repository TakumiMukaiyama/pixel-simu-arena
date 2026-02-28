# Pixel Simulation Arena - プロジェクト概要

## プロジェクトの目的とビジョン

Pixel Simulation Arenaは、生成AIを活用したリアルタイム対戦ゲームです。プレイヤーは自由なプロンプトを入力してオリジナルのユニットを生成し、AI（Mistral）が操作する敵と対戦します。

### コアコンセプト
- **プロンプト駆動のユニット生成**: 「素早い忍者」「強力な騎士」などのテキストから、バランスの取れたユニットが自動生成される
- **リアルタイム1レーンバトル**: 0-20の21マスの1次元レーンで、ユニットが自動的に移動・攻撃
- **AI対戦相手**: Mistral APIが盤面を見て、次に召喚するユニットを決定
- **シンプルな戦術**: コスト管理とユニット配置のタイミングが勝敗を分ける

### ターゲット
- ハッカソン向けMVP（短期間での実装）
- カジュアルゲーム好きなプレイヤー
- 生成AIの創造性を体験したいユーザー

## システムアーキテクチャ

```
┌─────────────────────────────────────────┐
│       React + PixiJS Client              │
│  ┌─────────────────────────────────┐    │
│  │  Game Scene (PixiJS)             │    │
│  │  - 1D Lane (21 positions)        │    │
│  │  - Unit Sprites                  │    │
│  │  - Attack Animations             │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │  React UI                        │    │
│  │  - Cost Display                  │    │
│  │  - Deck Cards                    │    │
│  │  - Base HP                       │    │
│  └─────────────────────────────────┘    │
│             ↕ HTTP/REST API              │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│         FastAPI Server                   │
│  ┌─────────────────────────────────┐    │
│  │  Game Engine                     │    │
│  │  - Tick (200ms)                  │    │
│  │  - Movement & Attack             │    │
│  │  - Cost Recovery                 │    │
│  │  - Victory Check                 │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │  API Endpoints                   │    │
│  │  - POST /match/start             │    │
│  │  - POST /match/tick              │    │
│  │  - POST /match/spawn             │    │
│  │  - POST /match/ai_decide         │    │
│  │  - POST /units/create            │    │
│  │  - GET  /gallery/list            │    │
│  │  - POST /deck/save               │    │
│  └─────────────────────────────────┘    │
│             ↕ External APIs              │
└─────────────────────────────────────────┘
          ↕
┌──────────────────┐
│  Mistral API     │
│  - Unit Gen      │
│  - AI Decision   │
│  - Image Gen     │
└──────────────────┘
```

### コンポーネント概要

#### 1. React + PixiJS Client（クライアント）
- **役割**: ゲーム画面の描画、ユーザー入力の受付、APIとの通信
- **技術**: React + Vite + PixiJS + @pixi/react
- **主要機能**:
  - 1レーン（21マス）の表示
  - ユニットスプライトのアニメーション
  - プロンプト入力UI
  - デッキ表示（カード形式）
  - コスト・拠点HP表示
  - リアルタイム更新（tickごとに状態取得）

#### 2. FastAPI Server（サーバー）
- **役割**: ゲームエンジンの実行、AI連携、状態管理
- **技術**: FastAPI + uvicorn + Python 3.11+
- **主要機能**:
  - RESTful API提供
  - リアルタイムtick処理（200ms単位）
  - 移動・攻撃・死亡判定
  - コスト回復（+0.6/tick）
  - セッション管理（インメモリ）

#### 3. Mistral API（生成AI）
- **役割**: ユニット生成、AI行動決定、画像生成
- **モデル**:
  - mistral-large-latest（テキスト生成・AI決定）
  - Pixtral Large（画像生成）
- **主要機能**:
  - プロンプトベースのユニット生成（JSON形式）
  - 盤面状態に基づく召喚決定（1秒に1回）
  - **32×32ピクセルスプライト生成（ゲーム内表示用）**
  - **256×256ピクセルカード絵生成（デッキ・ギャラリー表示用）**
  - 画像プロンプト自動生成
  - 画像保存（server/static/sprites/, server/static/cards/）

## 技術スタック詳細

### サーバーサイド
- **言語**: Python 3.11+
- **Webフレームワーク**: FastAPI 0.100+
- **非同期**: uvicorn + asyncio
- **データ検証**: Pydantic v2
- **環境管理**: uv（推奨）
- **データベース**: SQLite（ユニット・デッキ保存用）
- **テスト**: pytest

### クライアントサイド
- **ライブラリ**: React 18+
- **ビルドツール**: Vite
- **描画エンジン**: PixiJS 8.x
- **React統合**: @pixi/react
- **言語**: TypeScript
- **HTTP通信**: fetch API
- **状態管理**: React hooks

### 外部サービス
- **AI**: Mistral API（mistral-large-latest）
- **画像生成**: Mistral Image API
- **画像保存**: ローカルストレージ（server/static/sprites/）

### 開発ツール
- **バージョン管理**: Git + GitHub
- **ローカルサーバー**: uvicorn --reload（サーバー）、vite（クライアント）
- **ドキュメント**: Markdown + FastAPI自動生成ドキュメント

## 開発環境セットアップ概要

### サーバー環境
```bash
# uvを使用（推奨）
cd server
uv venv
uv pip install fastapi uvicorn pydantic mistralai pytest

# サーバー起動
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### クライアント環境
```bash
# npmまたはyarn
cd web
npm install
npm run dev
```

### 環境変数
```bash
# server/.env
MISTRAL_API_KEY=your_mistral_api_key
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## MVP範囲（ハッカソンで実装する範囲）

### 必須機能
- ✅ 1レーン（0-20の21マス）の実装
- ✅ リアルタイムtick（200ms）
- ✅ ユニット生成（Mistral）
  - プロンプト入力（例: "A fast ninja with low HP"）
  - 基本ステータス生成（HP, ATK, Speed, Range, Atk_interval）
  - パワースコア計算→コスト調整
  - **画像生成（自動・同期処理）**
    - 32×32スプライト: ゲーム内ユニット表示用
    - 256×256カード絵: デッキ・ギャラリー表示用
    - ユニット特徴に基づく画像プロンプト自動生成
    - ローカルストレージに保存
- ✅ デッキシステム（5体のユニット）
- ✅ コスト管理（初期10、上限20、回復+0.6/tick）
- ✅ 自動移動・攻撃
  - ユニットは自動的に前進
  - 射程内の敵を自動攻撃
  - 攻撃インターバル管理
- ✅ AI対戦相手（Mistral）
  - 盤面状態に基づく召喚決定（1秒に1回）
  - JSON固定出力
- ✅ 拠点HP
  - プレイヤー・AI両方
  - 敵拠点HP=0で勝利
- ✅ **画像保存＆ギャラリー**
  - 生成したユニットをカード形式で一覧表示
  - 各ユニットの画像・ステータス表示
  - ギャラリーからデッキ編成可能
- ✅ 基本的なAPI実装
  - POST /match/start
  - POST /match/tick
  - POST /match/spawn
  - POST /match/ai_decide
  - POST /units/create（画像生成含む）
  - GET /gallery/list

### MVP後の拡張機能（優先度順）
1. **サーバー側自動tick** - バックグラウンドでtick処理
2. **複雑なスキル** - 範囲攻撃、バフ/デバフ
3. **カード絵ギャラリー強化** - フィルタ・検索
4. **リプレイ機能** - 戦闘の再生
5. **マルチプレイヤー対応** - 人間vs人間

## プロジェクト構成（monorepo）

```
pixel-simu-arena/
├── server/               # FastAPIサーバー
│   ├── app/
│   │   ├── api/         # APIエンドポイント
│   │   ├── engine/      # ゲームエンジン
│   │   │   ├── tick.py      # tick処理
│   │   │   ├── movement.py  # 移動・攻撃
│   │   │   └── victory.py   # 勝敗判定
│   │   ├── llm/         # Mistral連携
│   │   │   ├── unit_gen.py    # ユニット生成
│   │   │   ├── ai_decide.py   # AI召喚決定
│   │   │   └── image_gen.py   # 画像生成
│   │   ├── storage/     # DB・画像保存
│   │   └── schemas/     # Pydanticモデル
│   ├── pyproject.toml
│   └── README.md
├── web/                  # React + PixiJS
│   ├── src/
│   │   ├── api/         # APIクライアント
│   │   ├── game/        # PixiJS統合
│   │   ├── screens/     # React画面
│   │   └── components/  # UIコンポーネント
│   ├── package.json
│   └── vite.config.ts
├── docs/                # 設計ドキュメント
│   ├── 00_overview.md
│   ├── 01_game_rules.md
│   ├── 02_data_models.md
│   ├── 03_api_design.md
│   ├── 04_battle_system.md（旧仕様・参考）
│   ├── 12_implementation_roadmap.md
│   └── 13_image_generation.md
└── README.md
```

## 開発スケジュール（目安）

### Phase 1: サーバーエンジン実装（最優先）
- tick処理（移動・攻撃・死亡判定）
- API実装（/match/start, /match/tick, /match/spawn）
- データモデル（UnitSpec, UnitInstance, GameState）

### Phase 2: React + PixiJS統合
- レーン表示（背景・拠点）
- ユニットスプライト描画
- 状態更新（tickごとにAPI呼び出し）
- イベントアニメーション

### Phase 3: Mistral統合
- AI召喚決定（ai_decide）
- ユニット生成＆画像生成
- ギャラリー

### Phase 4: 最終調整
- バランス調整
- バグ修正
- 演出強化

## 推奨実装順序

1. サーバーのengine: tickで移動＆攻撃＆死亡＆拠点ダメージ
2. /match/start /match/tick /match/spawn を通す
3. React + Pixi でレーンと丸（仮ユニット）で動かす
4. Mistralの ai_decide を繋ぐ（召喚だけ）
5. ユニット生成＆画像生成＆ギャラリーは後段（MVP+）

## 次のステップ

1. `docs/13_image_generation.md` - 画像生成システムの詳細確認
2. `server/app/schemas/`にデータモデルを実装
3. `server/app/engine/`にtick処理を実装
4. `server/app/llm/image_gen.py`に画像生成機能を実装
5. `server/static/sprites/`と`server/static/cards/`ディレクトリを作成
6. プレースホルダー画像を用意
7. React + PixiJSのセットアップ

## 参考リンク

- Mistral API: https://docs.mistral.ai/
- FastAPI: https://fastapi.tiangolo.com/
- PixiJS: https://pixijs.com/
- @pixi/react: https://github.com/inlet/react-pixi
