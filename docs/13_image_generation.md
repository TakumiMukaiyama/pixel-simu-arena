# 画像生成システム設計

## 概要

Pixel Simulation Arenaでは、ユニット生成時にMistral Image API（Pixtral Large）を使って自動的に画像を生成します。

## 画像の種類

### 1. スプライト画像（32×32px）
- **用途**: ゲーム内のユニット表示
- **形式**: PNG
- **スタイル**: ピクセルアート、横向き（side view）
- **保存先**: `server/static/sprites/{unit_id}.png`
- **URL**: `http://localhost:8000/static/sprites/{unit_id}.png`

### 2. カード絵（256×256px）
- **用途**: デッキ・ギャラリー表示
- **形式**: PNG
- **スタイル**: 詳細なピクセルアート、正面向き（front view）
- **保存先**: `server/static/cards/{unit_id}.png`
- **URL**: `http://localhost:8000/static/cards/{unit_id}.png`

## 画像生成フロー

### 全体フロー
```
1. ユーザーがプロンプト入力（例: "A fast ninja with low HP"）
   ↓
2. Mistral LLMでユニット名・ステータス生成
   ↓
3. 画像プロンプト自動生成
   ↓
4. Mistral Image API（Pixtral Large）で画像生成
   - 32×32スプライト
   - 256×256カード絵
   ↓
5. 画像をローカルストレージに保存
   ↓
6. UnitSpecをDBに保存（画像URL含む）
   ↓
7. レスポンス返却
```

### 詳細フロー

#### ステップ1: ユニット情報生成
```python
# 入力
prompt = "A fast ninja with low HP"

# Mistral LLMで生成
unit_data = {
    "name": "Ninja",
    "max_hp": 8,
    "atk": 5,
    "speed": 1.5,
    "range": 1.5,
    "atk_interval": 1.2,
    "description": "A swift assassin with low health but high speed"
}
```

#### ステップ2: 画像プロンプト自動生成
```python
def generate_image_prompt(unit_data: dict, size: str) -> str:
    """
    ユニット情報から画像生成プロンプトを作成

    Args:
        unit_data: ユニット情報
        size: "sprite" (32x32) or "card" (256x256)

    Returns:
        画像生成プロンプト
    """
    base_style = "pixel art" if size == "sprite" else "detailed pixel art"
    view = "side view" if size == "sprite" else "front view"

    # ユニット特徴を抽出
    features = []
    if unit_data.get("speed", 0) > 1.0:
        features.append("fast movement")
    if unit_data.get("atk", 0) > 10:
        features.append("strong weapon")
    if unit_data.get("max_hp", 0) < 10:
        features.append("light armor")

    # プロンプト生成
    prompt = f"{base_style}, {view}, {unit_data['name'].lower()} character"
    if features:
        prompt += f", {', '.join(features)}"

    # サイズ指定
    if size == "sprite":
        prompt += ", 32x32 pixel art, simple design"
    else:
        prompt += ", 256x256 pixel art, detailed character portrait"

    return prompt

# 例
sprite_prompt = generate_image_prompt(unit_data, "sprite")
# "pixel art, side view, ninja character, fast movement, light armor, 32x32 pixel art, simple design"

card_prompt = generate_image_prompt(unit_data, "card")
# "detailed pixel art, front view, ninja character, fast movement, light armor, 256x256 pixel art, detailed character portrait"
```

#### ステップ3: Mistral Image API呼び出し
```python
from mistralai import Mistral

async def generate_unit_images(
    unit_id: str,
    sprite_prompt: str,
    card_prompt: str
) -> tuple[str, str]:
    """
    ユニット画像を生成

    Args:
        unit_id: ユニットID
        sprite_prompt: スプライト用プロンプト
        card_prompt: カード絵用プロンプト

    Returns:
        (sprite_url, card_url)
    """
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

    # スプライト生成（32×32）
    sprite_response = await client.images.generate_async(
        model="pixtral-large-latest",
        prompt=sprite_prompt,
        size="32x32"  # または最小サイズから縮小
    )
    sprite_image = sprite_response.data[0].b64_json

    # カード絵生成（256×256）
    card_response = await client.images.generate_async(
        model="pixtral-large-latest",
        prompt=card_prompt,
        size="256x256"
    )
    card_image = card_response.data[0].b64_json

    # 画像を保存
    sprite_path = f"server/static/sprites/{unit_id}.png"
    card_path = f"server/static/cards/{unit_id}.png"

    save_base64_image(sprite_image, sprite_path)
    save_base64_image(card_image, card_path)

    # URL生成
    sprite_url = f"http://localhost:8000/static/sprites/{unit_id}.png"
    card_url = f"http://localhost:8000/static/cards/{unit_id}.png"

    return sprite_url, card_url
```

#### ステップ4: 画像保存
```python
import base64
from pathlib import Path

def save_base64_image(b64_data: str, file_path: str) -> None:
    """
    Base64画像をファイルに保存

    Args:
        b64_data: Base64エンコードされた画像データ
        file_path: 保存先パス
    """
    # ディレクトリ作成
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    # Base64デコード
    image_data = base64.b64decode(b64_data)

    # ファイル保存
    with open(file_path, "wb") as f:
        f.write(image_data)
```

## エラーハンドリング

### 画像生成失敗時の対応
```python
async def generate_unit_images_with_fallback(
    unit_id: str,
    sprite_prompt: str,
    card_prompt: str,
    max_retries: int = 3
) -> tuple[str, str]:
    """
    画像生成（リトライ＋フォールバック付き）
    """
    for attempt in range(max_retries):
        try:
            return await generate_unit_images(unit_id, sprite_prompt, card_prompt)
        except Exception as e:
            if attempt == max_retries - 1:
                # 最終試行失敗時はプレースホルダー
                return (
                    "http://localhost:8000/static/sprites/placeholder.png",
                    "http://localhost:8000/static/cards/placeholder.png"
                )
            await asyncio.sleep(2 ** attempt)  # 指数バックオフ
```

### プレースホルダー画像
- `server/static/sprites/placeholder.png`: 32×32の汎用スプライト
- `server/static/cards/placeholder.png`: 256×256の汎用カード絵

## パフォーマンス最適化

### 1. 非同期処理
```python
# 2つの画像を並行生成
sprite_task = generate_image(sprite_prompt, "32x32")
card_task = generate_image(card_prompt, "256x256")

sprite_url, card_url = await asyncio.gather(sprite_task, card_task)
```

### 2. キャッシュ
```python
# 同じプロンプトで画像を再生成しない
def get_or_generate_image(prompt: str, size: str) -> str:
    cache_key = hashlib.md5(f"{prompt}:{size}".encode()).hexdigest()
    cache_path = f"server/cache/{cache_key}.png"

    if os.path.exists(cache_path):
        return cache_path

    # 生成
    image_url = generate_image(prompt, size)
    return image_url
```

### 3. バッチ生成（MVP後）
複数ユニットの画像を一度に生成する場合、バッチAPIを使用。

## 画像表示（フロントエンド）

### React + PixiJS
```typescript
// スプライト表示（ゲーム内）
const sprite = PIXI.Sprite.from(unit.sprite_url);
sprite.width = 32;
sprite.height = 32;
sprite.position.set(x, y);
app.stage.addChild(sprite);

// カード絵表示（デッキ・ギャラリー）
<img
  src={unit.card_url}
  alt={unit.name}
  width="256"
  height="256"
/>
```

## テスト戦略

### 1. 単体テスト
```python
def test_generate_image_prompt():
    unit_data = {
        "name": "Ninja",
        "speed": 1.5,
        "max_hp": 8
    }

    prompt = generate_image_prompt(unit_data, "sprite")

    assert "ninja" in prompt.lower()
    assert "fast movement" in prompt
    assert "32x32" in prompt
```

### 2. 統合テスト
```python
@pytest.mark.asyncio
async def test_generate_unit_images():
    unit_id = "test-001"
    sprite_prompt = "pixel art, ninja, 32x32"
    card_prompt = "detailed pixel art, ninja, 256x256"

    sprite_url, card_url = await generate_unit_images(
        unit_id, sprite_prompt, card_prompt
    )

    assert os.path.exists(f"server/static/sprites/{unit_id}.png")
    assert os.path.exists(f"server/static/cards/{unit_id}.png")
```

### 3. モック（開発時）
```python
# Mistral APIをモック
@pytest.fixture
def mock_mistral_image_api(monkeypatch):
    async def mock_generate(*args, **kwargs):
        return MockImageResponse(b64_json="<base64データ>")

    monkeypatch.setattr("mistralai.Mistral.images.generate_async", mock_generate)
```

## セキュリティ

### 1. 入力検証
- プロンプトの長さ制限（200文字）
- 不適切な単語のフィルタリング

### 2. レート制限
- ユーザーごとに1時間あたり10回まで
- IPアドレスベースの制限

### 3. ファイルストレージ
- ユニットIDはUUIDを使用（予測不可能）
- ディレクトリトラバーサル対策

## 次のステップ

1. `server/app/llm/image_gen.py`の実装
2. プレースホルダー画像の作成
3. 画像保存ディレクトリの作成（`server/static/sprites/`, `server/static/cards/`）
4. Mistral Image APIのテスト
5. React UIでの画像表示テスト
