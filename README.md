# Pixel Simulation Arena

> テキストプロンプトから生成したオリジナルユニットで、AIと戦略バトルを繰り広げるリアルタイムストラテジーゲーム

🎮 **[Live Demo](#)** | 📹 **[デモ動画 (2分)](#)** | 🐙 **[GitHub](https://github.com/TakumiMukaiyama/pixel-simu-arena)**

---

## 🎬 Demo
### Battle Demo
> リアルタイムバトル - ユニットが自律的に移動・攻撃

![Battle Demo](docs/images/1.png)
*プレースホルダー: 実際のバトルシーン*

---

## 💡 Why This Project?

### Problem
従来のゲームでは、運営が用意したキャラクターでしか遊べない

### Solution
ユーザーが**自分の好きなキャラクター/ユニットをテキストで自由に作成**し、それを使ってバトルできるゲーム

### Innovation

**1. Multi-Modal AI Pipeline**
- テキスト → バランスの取れたステータス生成
- ステータス → ピクセルアートの自動生成（Mistral Pixtral Large）
- リアルタイムAI対戦相手との戦略バトル

**2. Strategic AI Opponent**
- 単なるランダム行動ではない
- **Mistral LLMがゲーム状態（ユニット位置・HP・コスト）を分析**
- 敵の編成に対抗する戦略的なユニット召喚を決定

**3. Real-Time Autonomous Gameplay**
- 200msティックベースのゲームエンジン
- ユニットが自律的に移動・攻撃
- 動的で予測不可能なバトル

## 🏆 Hackathon Highlights

**Track:** Mistral AI - Building with Mistral API

## 🎯 Core Features

- **Prompt-Driven Unit Creation**: 自然言語でユニットを記述 - 「素早い忍者」「重装甲の戦車」などと入力すると、バランスの取れたステータスで具現化
- **Automatic Pixel Art Generation**: 各ユニットに128×128のユニークなピクセルアートを自動生成（Mistral Pixtral Large + PixelLab API fallback）
- **Real-Time 1-Lane Battle**: ユニットが0-20のレーン上で自動的に移動・戦闘
- **Intelligent AI Opponent**: Mistral AIが戦場状態を分析し、戦略的にユニット召喚を決定
- **Visual Gallery**: 生成したユニットを閲覧し、カスタムデッキに整理


## 🏗️ Technical Architecture

### System Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  React Client   │────────▶│  FastAPI Server  │────────▶│   Mistral API   │
│  (PixiJS UI)    │◀────────│  (Game Engine)   │◀────────│  (AI + Images)  │
└─────────────────┘         └──────────────────┘         └─────────────────┘
       │                            │
       │                            │
       ▼                            ▼
┌─────────────────┐         ┌──────────────────┐
│  Visual Assets  │         │   Postgres DB      │
│  (Sprites)      │         │   (Game State)   │
└─────────────────┘         └──────────────────┘
```

### Tech Stack

**Backend (Python)**
- FastAPI - High-performance async API
- Pydantic v2 - Type-safe data validation
- Mistral API - `mistral-large-latest` for reasoning, `Pixtral Large` for images
- PostgreSQL - Persistent storage

**Frontend (TypeScript)**
- React 18 - Component architecture
- PixiJS 8 - Hardware-accelerated 2D rendering
- Vite - Fast development builds

**AI Integration**
- **Text Generation**: Unit stats balancing, AI strategic decisions (mistral-large-latest)
- **Image Generation**: Automatic 128×128 pixel art creation (Pixtral Large + PixelLab fallback)
- **Vision Model**: Battlefield state analysis for AI decision-making (Pixtral Large)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Mistral API key ([Get one here](https://console.mistral.ai/))

### 1. Server Setup

```bash
cd server

# Install dependencies (using uv for faster installation)
uv venv
uv sync

# Configure environment
cp .env.example .env
# Edit .env and add your MISTRAL_API_KEY

# Create image directories
mkdir -p static/battle_sprites static/backgrounds

# Test Mistral API connection
uv run python test_mistral.py

# Start server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Client Setup

```bash
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

Open http://localhost:5173 in your browser and start creating units!

---

## 🎮 How It Works

### Unit Creation Flow

```
User Prompt → Mistral LLM → Balanced Stats → Image Generation → Ready to Battle
   "ninja"      (reasoning)    {hp, atk...}  (Pixtral/PixelLab)  [128x128 sprite]
```

**Example:**
```javascript
Input: "素早いが脆いアサシン"
Output: {
  name: "Shadow Assassin",
  hp: 30,
  attack: 15,
  speed: 8,
  range: 1,
  cost: 4,
  battle_sprite: "static/battle_sprites/[自動生成された128x128ピクセルアート]"
}
```

### AI Decision-Making Flow

```
Battlefield State → Vision Analysis → Strategic Reasoning → Unit Selection
  {units, hp...}   (Pixtral sees)    (mistral-large)      "Spawn Tank!"
```

### Real-Time Battle System

- **200ms tick cycle**: 全ゲームロジックが離散的な時間ステップで実行
- **Autonomous units**: 敵の基地に向かって移動、射程内で攻撃
- **Dynamic spawning**: プレイヤーとAIがバトル中にユニット召喚
- **Win condition**: 敵の基地を破壊（100 HP）

---

## 📐 Project Structure

```
pixel-simu-arena/
├── server/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/           # REST API endpoints
│   │   ├── engine/        # Game engine (tick processing, combat logic)
│   │   ├── llm/           # Mistral + PixelLab integration
│   │   │   ├── unit_creator.py      # Unit generation from prompts
│   │   │   ├── image_gen.py         # 128×128 pixel art creation
│   │   │   └── ai_player.py         # AI decision-making agent
│   │   ├── storage/       # Database and file storage
│   │   └── schemas/       # Pydantic models
│   └── static/
│       ├── battle_sprites/  # 128×128 battle sprites
│       └── backgrounds/     # Battle backgrounds
│
├── web/                   # React + PixiJS Frontend
│   └── src/
│       ├── api/          # API client
│       ├── game/         # PixiJS game rendering
│       ├── screens/      # React pages
│       └── components/   # UI components
│
└── docs/                 # Design documents
    ├── 00_overview.md
    ├── 01_game_rules.md
    ├── 02_data_models.md
    └── 03_api_design.md
```

---

## 🔧 Key Technical Innovations

### 1. Multi-Stage AI Pipeline

単にユーザー入力をLLMに投げるのではなく、洗練されたパイプラインを使用:

```python
# Stage 1: ユーザー意図の解析とキーキャラクタリスティックの抽出
# Stage 2: ゲームバランスルールを使った統計値の生成
# Stage 3: ユニットのテーマに合致する画像プロンプトの作成
# Stage 4: Mistral Pixtral Large（またはPixelLab fallback）で128x128ピクセルアートを生成
```

これにより一貫した品質とゲームバランスを確保。

### 2. Vision-Powered AI Opponent

AI対戦相手はMistralの視覚機能を使って戦場を「見る」:

```python
# ゲーム状態を視覚表現に変換
battlefield_image = render_battlefield_state(game_state)

# AIに分析・決定させる
response = mistral_vision_api(
    image=battlefield_image,
    prompt="あなたは戦略ゲームをプレイしています。戦場を分析し、次の行動を決定してください。"
)
```

**これは単なるランダムなスポーンではありません:**
- 現在の戦場レイアウトを分析
- 利用可能なマナとユニットコストを考慮
- 脅威と機会を評価
- プレイヤーの編成に対抗する戦略的決定

### 3. Efficient Real-Time Rendering

PixiJSが60 FPSレンダリングを処理し、ゲームエンジンは5 TPS（ティック/秒）で実行:
- ゲーム状態間のスムーズな補間
- ハードウェアアクセラレーションによるスプライトレンダリング
- React.memoとuseMemoを使った最小限の再レンダリング

---

## 📊 API Usage

This project showcases advanced Mistral API integration:

| Feature | Model/API | Use Case |
|---------|-----------|----------|
| Unit Generation | `mistral-large-latest` | Parse prompts, generate balanced stats |
| Image Generation | `Mistral Agent Image Generation Tool` （or `PixelLab API`） | Generate 128×128 pixel art (Mistral primary, PixelLab fallback) |
| AI Decision-Making | `mistral-large-latest` | Analyze battlefield, select counter units |
