# Pixel Simulation Arena

> テキストプロンプトから生成したオリジナルユニットで、AIと戦略バトルを繰り広げるリアルタイムストラテジーゲーム

🎮 **[Live Demo](#)** | 📹 **[デモ動画 (2分)](#)** | 🐙 **[GitHub](https://github.com/TakumiMukaiyama/pixel-simu-arena)**

---

## 🎬 Demo

### Unit Creation Demo
> テキストプロンプト → ユニット生成 → 自動ピクセルアート生成

![Unit Creation Demo](docs/images/demo_unit_creation.gif)
*プレースホルダー: 「忍者」と入力してユニットが生成される様子*

### Battle Demo
> リアルタイムバトル - ユニットが自律的に移動・攻撃

![Battle Demo](docs/images/demo_battle.gif)
*プレースホルダー: 実際のバトルシーン*

### AI Decision Making Demo
> AIが戦場状態を分析して戦略的判断

![AI Decision Demo](docs/images/demo_ai_decision.gif)
*プレースホルダー: AIが戦場状態（ユニット位置・HP・コスト）を分析してユニット召喚を決定*

---

## 💡 Why This Project?

### Problem
従来のゲームでは、運営が用意したキャラクターでしか遊べない

### Solution
ユーザーが**自分の好きなキャラクター/ユニットをテキストで自由に作成**し、それを使ってバトルできるゲーム

### Innovation

**1. AI-Powered Unit Creation Pipeline**
- **mistral-large-latest**: プロンプトから自動的にバランスの取れたステータス（HP、攻撃力、速度など）をJSON形式で生成
- **pixtral-large-latest (fallback: PixelLab)**: ユニット特性に基づいた128×128ピクセルアートを自動生成
- パワースコア計算とコスト調整でゲームバランスを自動維持

**2. Strategic AI Opponent**
- 単なるランダム行動ではない
- **mistral-large-latest**: ゲーム状態（ユニット位置・HP・残コスト）を構造化データとして分析
- 敵の編成に対抗する戦略的なユニット召喚を決定
- JSON出力モードで確実な意思決定

**3. Real-Time Autonomous Gameplay**
- 200msティックベースのゲームエンジン
- ユニットが自律的に移動・攻撃
- 動的で予測不可能なバトル

---

## 🏆 Hackathon Highlights

**Track:** Mistral AI - Building with Mistral API

**このプロジェクトが際立つ理由:**

1. **高度なAIエージェントシステム** - 単純なプロンプトではなく、AIがゲーム状態を構造化データとして分析し、リアルタイムで戦略的判断を実行

2. **複数のMistral APIの統合** - テキスト生成（mistral-large-latest）と画像生成（Pixtral Large）を組み合わせた自動ユニット作成

3. **プロダクション品質のアーキテクチャ** - FastAPIバックエンド、Reactフロントエンド、ゲームエンジンとAI統合の適切な分離

---

## 🎯 Core Features

- **🎨 Prompt-Driven Unit Creation**: 自然言語でユニットを記述 - 「素早い忍者」「重装甲の戦車」などと入力すると、バランスの取れたステータスで具現化
- **🖼️ Automatic Pixel Art Generation**: 各ユニットに128×128のユニークなピクセルアートを自動生成（pixtral-large-latest + PixelLab API fallback）
- **⚔️ Real-Time 1-Lane Battle**: ユニットが0-20のレーン上で自動的に移動・戦闘
- **🤖 Intelligent AI Opponent**: Mistral AIが戦場状態を分析し、戦略的にユニット召喚を決定
- **📚 Visual Gallery**: 生成したユニットを閲覧し、カスタムデッキに整理

---

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
│  Visual Assets  │         │   SQLite DB      │
│  (Sprites)      │         │   (Game State)   │
└─────────────────┘         └──────────────────┘
```

### Tech Stack

**Backend (Python)**
- FastAPI - High-performance async API
- Pydantic v2 - Type-safe data validation
- Mistral API - `mistral-large-latest` for reasoning, `Pixtral Large` for images
- SQLite - Persistent storage

**Frontend (TypeScript)**
- React 18 - Component architecture
- PixiJS 8 - Hardware-accelerated 2D rendering
- Vite - Fast development builds

**AI Integration**
- **Text Generation**: Unit stats balancing, AI strategic decisions (mistral-large-latest with JSON mode)
- **Image Generation**: Automatic 128×128 pixel art creation (pixtral-large-latest + PixelLab fallback)
- **Strategic Reasoning**: Battlefield state analysis and counter-unit selection (mistral-large-latest)

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
Battlefield State → Text Analysis → Strategic Reasoning → Unit Selection
  {units, hp...}   (structured data)  (mistral-large)      "Spawn Tank!"
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
│   │   │   ├── unit_gen.py          # Unit generation from prompts
│   │   │   ├── image_gen.py         # 128×128 pixel art creation
│   │   │   └── ai_decide.py         # AI decision-making agent
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

### 1. AI-Powered Unit Creation Pipeline

単にユーザー入力をLLMに投げるのではなく、洗練されたパイプラインを使用:

```python
# Stage 1: mistral-large-latest でユニットステータスを生成（JSON mode）
response = client.chat.complete(
    model="mistral-large-latest",
    messages=[
        {"role": "system", "content": UNIT_GENERATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ],
    response_format={"type": "json_object"}  # 確実なJSON出力
)

# Stage 2: パワースコア計算 → ゲームバランス調整
power = calculate_power_score(unit_data)
cost = calculate_cost(power)
unit_data = adjust_stats_to_cost(unit_data, target_cost)

# Stage 3: ユニット特性に基づいた画像プロンプト生成
image_prompt = f"pixel art, 128x128, {unit_name}, {modifiers}, game token"

# Stage 4: Pixtral Large で画像生成（失敗時はPixelLabにフォールバック）
response = client.images.generate(
    model="pixtral-large-latest",
    prompt=image_prompt,
    size="128x128"
)
```

これにより一貫した品質とゲームバランスを確保。

### 2. Strategic AI Opponent

AI対戦相手はMistral LLMを使ってゲーム状態を分析:

```python
# ゲーム状態を構造化テキストで要約
summary = f"""Current game state:
- AI cost: {game_state.ai_cost} / {game_state.max_cost}
- AI base HP: {game_state.ai_base_hp} / 100
- Player base HP: {game_state.player_base_hp} / 100

AI units on field: [pos, hp, atk, range...]
Enemy units on field: [pos, hp, atk, range...]
Available units to spawn: [id, cost, stats...]
"""

# LLMに戦略的決定を依頼
response = client.chat.complete(
    model="mistral-large-latest",
    messages=[
        {"role": "system", "content": "You are an AI player..."},
        {"role": "user", "content": summary}
    ],
    response_format={"type": "json_object"}
)
```

**これは単なるランダムなスポーンではありません:**
- 現在のユニット配置と残りHPを分析
- 利用可能なコストと召喚可能なユニットを考慮
- 脅威と機会を評価
- プレイヤーの編成に対抗する戦略的決定

### 3. Efficient Real-Time Rendering

PixiJSが60 FPSレンダリングを処理し、ゲームエンジンは5 TPS（ティック/秒）で実行:
- ゲーム状態間のスムーズな補間
- ハードウェアアクセラレーションによるスプライトレンダリング
- React.memoとuseMemoを使った最小限の再レンダリング

---

## 📊 Mistral API Usage

This project showcases advanced Mistral API integration:

| Feature | Model/API | Use Case |
|---------|-----------|----------|
| Unit Generation | `mistral-large-latest` | Parse user prompts, generate balanced stats (HP, ATK, speed, range) in JSON format |
| Image Generation | `pixtral-large-latest` (fallback: `PixelLab API`) | Generate 128×128 pixel art game tokens based on unit characteristics |
| AI Strategic Decision-Making | `mistral-large-latest` | Analyze game state (unit positions, HP, cost), strategically select counter units in JSON format |

**Estimated Costs** (with typical usage):
- Unit creation: ~$0.01-0.02 per unit
- Single match (50 turns): ~$0.50-1.00
- 100 units + 10 matches: ~$7-8

See [Mistral Pricing](https://mistral.ai/pricing/) for details.

---

## 🎉 Future Enhancements

- Unit evolution system（バトル中のユニット成長）
- Tournament mode（トーナメント戦）
- Voice-to-unit（音声でユニット作成）
- Community gallery（ユニットのシェア機能）
- Multiplayer battles（プレイヤー同士の対戦）

---

**Built for the Mistral AI Hackathon**

*テキスト生成、画像生成、戦略的AI推論を組み合わせたリアルタイムインタラクティブ体験*

---

## 📖 Additional Resources

- **Full API Documentation**: http://localhost:8000/docs
- **Design Documents**: [docs/](docs/) フォルダ内に詳細な技術ドキュメント
- **Troubleshooting**: 問題が発生した場合は、`.env`ファイルのMISTRAL_API_KEYを確認してください
