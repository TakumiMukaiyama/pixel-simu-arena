"""
ユニット生成

Mistral LLMを使用してプロンプトからユニットを生成する。
"""
import json
from typing import Dict
from uuid import UUID, uuid4

from mistralai import Mistral

from app.config import get_settings
from app.engine.balance import adjust_stats_to_cost, calculate_cost, calculate_power_score
from app.schemas.unit import UnitSpec
from app.storage.db import save_unit_spec, update_unit_images

settings = get_settings()


UNIT_GENERATION_SYSTEM_PROMPT = """You are a unit generator for a 1-lane realtime battle game.

Generate a unit based on the user's prompt. Output ONLY valid JSON with the following structure:
{
  "name": "Unit Name",
  "max_hp": 10,
  "atk": 5,
  "speed": 1.0,
  "range": 2.0,
  "atk_interval": 2.0
}

Constraints:
- max_hp: 5-30 (integer)
- atk: 1-15 (integer)
- speed: 0.2-2.0 (float, squares/tick, 0.2=very slow, 2.0=very fast)
- range: 1.0-7.0 (float, attack range in squares, 1.0=melee, 7.0=sniper)
- atk_interval: 1.0-5.0 (float, seconds between attacks, 1.0=fast, 5.0=slow)

Design philosophy:
- Fast units should have lower HP/ATK
- High range units should have lower HP/speed
- Balance the unit to be interesting but fair
- Create variety: melee tanks, ranged snipers, fast assassins, etc.

Output ONLY the JSON, no explanation."""


async def generate_unit_from_prompt(prompt: str) -> UnitSpec:
    """
    プロンプトからユニットを生成

    1. Mistral LLMでJSON生成
    2. パワースコア計算 → コスト調整
    3. 画像URL設定（プレースホルダー、Phase 5で実装）
    4. UnitSpecをDBに保存

    Args:
        prompt: ユーザーのプロンプト

    Returns:
        生成されたUnitSpec
    """
    # 1. Mistral LLMでJSON生成（同期呼び出し）
    unit_data = _call_mistral_for_unit(prompt)

    # 2. パワースコア計算 → コスト調整
    power = calculate_power_score(unit_data)
    cost = calculate_cost(power)

    # コストが極端な場合は調整
    if cost < 1 or cost > 8:
        # 目標コストを中央値（4-5）に設定
        target_cost = 4 if cost < 4 else 5
        unit_data = adjust_stats_to_cost(unit_data, target_cost)
        cost = target_cost

    # プロンプトの長さに応じたコストペナルティ
    prompt_penalty = _calculate_prompt_penalty(prompt)
    cost = min(8, cost + prompt_penalty)  # 最大コスト8

    unit_data["cost"] = cost

    # 3. 画像URLはプレースホルダーで初期化（バックグラウンドで生成）
    unit_id = uuid4()
    sprite_url = "/static/sprites/placeholder.png"
    battle_sprite_url = "/static/battle_sprites/placeholder.png"
    card_url = "/static/cards/placeholder.png"
    image_prompt = None

    # 4. UnitSpec作成
    unit_spec = UnitSpec(
        id=unit_id,
        name=unit_data["name"],
        cost=unit_data["cost"],
        max_hp=unit_data["max_hp"],
        atk=unit_data["atk"],
        speed=unit_data["speed"],
        range=unit_data["range"],
        atk_interval=unit_data["atk_interval"],
        sprite_url=sprite_url,
        battle_sprite_url=battle_sprite_url,
        card_url=card_url,
        image_prompt=image_prompt,
        original_prompt=prompt
    )

    # 5. DB保存
    await save_unit_spec(unit_spec)

    return unit_spec


def _call_mistral_for_unit(prompt: str, max_retries: int = 3) -> Dict:
    """
    Mistral LLMを呼び出してユニットJSONを生成

    Args:
        prompt: ユーザーのプロンプト
        max_retries: 最大リトライ回数

    Returns:
        ユニットデータ辞書

    Raises:
        Exception: 生成失敗時
    """
    client = Mistral(api_key=settings.mistral_api_key)

    for attempt in range(max_retries):
        try:
            # Mistral API呼び出し（JSON mode使用）
            response = client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {"role": "system", "content": UNIT_GENERATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            # レスポンスからJSON抽出
            content = response.choices[0].message.content.strip()

            # マークダウンコードブロックを除去
            if content.startswith("```json"):
                content = content[7:]  # ```json を除去
            if content.startswith("```"):
                content = content[3:]  # ``` を除去
            if content.endswith("```"):
                content = content[:-3]  # 末尾の ``` を除去
            content = content.strip()

            # JSONパース
            unit_data = json.loads(content)

            # 必須フィールド検証
            required_fields = ["name", "max_hp", "atk", "speed", "range", "atk_interval"]
            if not all(field in unit_data for field in required_fields):
                raise ValueError(f"Missing required fields. Got: {unit_data.keys()}")

            # 型変換
            unit_data["max_hp"] = int(unit_data["max_hp"])
            unit_data["atk"] = int(unit_data["atk"])
            unit_data["speed"] = float(unit_data["speed"])
            unit_data["range"] = float(unit_data["range"])
            unit_data["atk_interval"] = float(unit_data["atk_interval"])

            # 範囲検証
            if not (5 <= unit_data["max_hp"] <= 30):
                unit_data["max_hp"] = max(5, min(30, unit_data["max_hp"]))
            if not (1 <= unit_data["atk"] <= 15):
                unit_data["atk"] = max(1, min(15, unit_data["atk"]))
            if not (0.2 <= unit_data["speed"] <= 2.0):
                unit_data["speed"] = max(0.2, min(2.0, unit_data["speed"]))
            if not (1.0 <= unit_data["range"] <= 7.0):
                unit_data["range"] = max(1.0, min(7.0, unit_data["range"]))
            if not (1.0 <= unit_data["atk_interval"] <= 5.0):
                unit_data["atk_interval"] = max(1.0, min(5.0, unit_data["atk_interval"]))

            return unit_data

        except json.JSONDecodeError as e:
            print(f"JSON parse error (attempt {attempt + 1}/{max_retries}): {e}")
            print(f"Response content: {content}")
            if attempt == max_retries - 1:
                # 最終リトライ失敗時はフォールバック
                return _fallback_unit(prompt)

        except Exception as e:
            print(f"Mistral API error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return _fallback_unit(prompt)

    return _fallback_unit(prompt)


def _calculate_prompt_penalty(prompt: str) -> int:
    """
    プロンプトの長さに応じたコストペナルティを計算

    長いプロンプト = より複雑な要望 = より高いコスト

    Args:
        prompt: ユーザーのプロンプト

    Returns:
        追加コスト (0-3)
    """
    # 単語数でカウント（スペース、カンマ、ピリオドで分割）
    import re
    words = re.findall(r'\w+', prompt.lower())
    word_count = len(words)

    # 文字数も考慮
    char_count = len(prompt.strip())

    # ペナルティ計算
    penalty = 0

    # 単語数ベースのペナルティ
    if word_count >= 30:  # 30単語以上
        penalty += 3
    elif word_count >= 20:  # 20単語以上
        penalty += 2
    elif word_count >= 10:  # 10単語以上
        penalty += 1

    # 文字数ベースの追加ペナルティ（日本語など単語区切りがない言語対応）
    if char_count >= 150:  # 150文字以上
        penalty = max(penalty, 3)
    elif char_count >= 100:  # 100文字以上
        penalty = max(penalty, 2)
    elif char_count >= 50:  # 50文字以上
        penalty = max(penalty, 1)

    return min(3, penalty)  # 最大ペナルティ+3


def _create_sprite_prompt_text(unit_data: dict) -> str:
    """スプライトプロンプトテキスト生成（ログ用）"""
    name = unit_data.get("name", "unit")
    return f"pixel art, 32x32, {name}"


def _create_card_prompt_text(unit_data: dict) -> str:
    """カードプロンプトテキスト生成（ログ用）"""
    name = unit_data.get("name", "unit")
    return f"detailed pixel art, 256x256, {name}"


def _fallback_unit(prompt: str) -> Dict:
    """
    フォールバックユニット生成（LLM失敗時）

    プロンプトから簡単なキーワードマッチングでユニットを生成する。
    """
    prompt_lower = prompt.lower()

    # デフォルト値
    unit_data = {
        "name": prompt[:20] if len(prompt) <= 20 else prompt[:17] + "...",
        "max_hp": 15,
        "atk": 7,
        "speed": 1.0,
        "range": 2.0,
        "atk_interval": 2.0
    }

    # キーワードベースの調整
    if any(word in prompt_lower for word in ["fast", "quick", "swift", "agile"]):
        unit_data["speed"] = 1.8
        unit_data["max_hp"] = 8
        unit_data["atk"] = 4

    if any(word in prompt_lower for word in ["tank", "heavy", "armor", "shield"]):
        unit_data["max_hp"] = 25
        unit_data["speed"] = 0.5
        unit_data["atk"] = 3

    if any(word in prompt_lower for word in ["sniper", "archer", "ranger", "long"]):
        unit_data["range"] = 6.0
        unit_data["max_hp"] = 8
        unit_data["atk"] = 6
        unit_data["atk_interval"] = 3.0

    if any(word in prompt_lower for word in ["strong", "powerful", "damage"]):
        unit_data["atk"] = 12
        unit_data["max_hp"] = 12

    return unit_data


async def generate_images_background(unit_id: UUID, unit_data: Dict, prompt: str):
    """
    バックグラウンドでユニット画像を生成してDBを更新

    Args:
        unit_id: ユニットID
        unit_data: ユニット統計データ
        prompt: 元のプロンプト
    """
    import asyncio

    async def _generate_with_timeout():
        try:
            from app.llm.image_gen import generate_unit_images

            print(f"[Background] Starting image generation for unit {unit_id}")

            # 同期関数を別スレッドで実行（600秒タイムアウト）
            loop = asyncio.get_event_loop()
            sprite_url, battle_sprite_url, card_url = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    generate_unit_images,
                    unit_id,
                    unit_data,
                    prompt
                ),
                timeout=600.0
            )

            # DB更新
            await update_unit_images(unit_id, sprite_url, battle_sprite_url, card_url)

            print(f"[Background] Image generation completed for unit {unit_id}")
        except asyncio.TimeoutError:
            print(f"[Background] Image generation timed out (600s) for unit {unit_id}")
        except Exception as e:
            print(f"[Background] Image generation failed for unit {unit_id}: {e}")
            import traceback
            traceback.print_exc()

    await _generate_with_timeout()
