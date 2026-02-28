"""
画像生成

Mistral Image APIを使用してユニットのスプライトとカード絵を生成する。
"""
import base64
import os
from typing import Optional, Tuple
from uuid import UUID

from mistralai import Mistral

from app.config import get_settings

settings = get_settings()


def generate_unit_images(
    unit_id: UUID,
    unit_data: dict,
    original_prompt: str
) -> Tuple[str, str]:
    """
    ユニットの画像を生成

    1. 画像プロンプト自動生成
    2. Mistral Image API呼び出し（32x32スプライト + 256x256カード絵）
    3. ダウンロードして保存
    4. URL生成

    Args:
        unit_id: ユニットID
        unit_data: ユニットステータス辞書
        original_prompt: 元のプロンプト

    Returns:
        (sprite_url, card_url) のタプル
    """
    # 1. 画像プロンプト生成
    sprite_prompt = _create_sprite_prompt(unit_data, original_prompt)
    card_prompt = _create_card_prompt(unit_data, original_prompt)

    # 2. 画像生成（エラー時はプレースホルダー）
    try:
        sprite_path = _generate_and_save_image(
            prompt=sprite_prompt,
            output_path=f"static/sprites/{unit_id}.png",
            description="32x32 pixel art sprite, side view"
        )
        sprite_url = f"/static/sprites/{unit_id}.png"
    except Exception as e:
        print(f"Sprite generation failed: {e}")
        sprite_url = "/static/sprites/placeholder.png"

    try:
        card_path = _generate_and_save_image(
            prompt=card_prompt,
            output_path=f"static/cards/{unit_id}.png",
            description="256x256 detailed pixel art portrait"
        )
        card_url = f"/static/cards/{unit_id}.png"
    except Exception as e:
        print(f"Card generation failed: {e}")
        card_url = "/static/cards/placeholder.png"

    return sprite_url, card_url


def _create_sprite_prompt(unit_data: dict, original_prompt: str) -> str:
    """
    スプライト用の画像プロンプトを生成

    Args:
        unit_data: ユニットステータス
        original_prompt: ユーザーの元プロンプト

    Returns:
        画像生成プロンプト
    """
    name = unit_data.get("name", "unit")
    speed = unit_data.get("speed", 1.0)
    atk = unit_data.get("atk", 5)

    # 特徴的な修飾語を追加
    modifiers = []
    if speed >= 1.5:
        modifiers.append("fast-moving")
    elif speed <= 0.5:
        modifiers.append("slow-moving")

    if atk >= 10:
        modifiers.append("powerful")

    modifier_str = ", ".join(modifiers) if modifiers else ""

    prompt = f"pixel art, 32x32, side view, {name}"
    if modifier_str:
        prompt += f", {modifier_str}"
    prompt += f", simple design, game sprite, clear silhouette"

    return prompt


def _create_card_prompt(unit_data: dict, original_prompt: str) -> str:
    """
    カード絵用の画像プロンプトを生成

    Args:
        unit_data: ユニットステータス
        original_prompt: ユーザーの元プロンプト

    Returns:
        画像生成プロンプト
    """
    name = unit_data.get("name", "unit")
    hp = unit_data.get("max_hp", 10)
    range_val = unit_data.get("range", 2.0)

    # 特徴的な修飾語を追加
    modifiers = []
    if hp >= 20:
        modifiers.append("heavily armored")
    elif hp <= 10:
        modifiers.append("agile")

    if range_val >= 5.0:
        modifiers.append("long-range")
    elif range_val <= 1.5:
        modifiers.append("melee")

    modifier_str = ", ".join(modifiers) if modifiers else ""

    prompt = f"detailed pixel art, 256x256, front view, {name}"
    if modifier_str:
        prompt += f", {modifier_str}"
    prompt += f", portrait, game card art, fantasy style"

    return prompt


def _generate_and_save_image(
    prompt: str,
    output_path: str,
    description: str,
    max_retries: int = 2
) -> str:
    """
    Mistral Image APIで画像を生成して保存

    Args:
        prompt: 画像生成プロンプト
        output_path: 保存先パス
        description: 画像の説明（サイズなど）
        max_retries: 最大リトライ回数

    Returns:
        保存したファイルパス

    Raises:
        Exception: 生成失敗時
    """
    from mistralai.models import ToolFileChunk

    client = Mistral(api_key=settings.mistral_api_key)

    for attempt in range(max_retries):
        try:
            # 1. エージェント作成（image_generation tool使用）
            agent = client.beta.agents.create(
                model="mistral-medium-2505",
                name="Image Generator",
                tools=[{"type": "image_generation"}]
            )

            # 2. エージェント実行（画像生成）
            full_prompt = f"{description}. {prompt}"
            response = client.beta.conversations.start(
                agent_id=agent.id,
                inputs=full_prompt
            )

            # 3. file_idを探す（response.outputs[-1].content から）
            file_id = None
            if response.outputs and len(response.outputs) > 0:
                last_output = response.outputs[-1]
                if hasattr(last_output, 'content'):
                    for chunk in last_output.content:
                        if isinstance(chunk, ToolFileChunk):
                            file_id = chunk.file_id
                            break

            if not file_id:
                raise Exception("No file_id in response")

            # 4. ファイルダウンロード
            file_bytes = client.files.download(file_id=file_id).read()

            # 5. 保存
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(file_bytes)

            print(f"Image saved: {output_path}")
            return output_path

        except Exception as e:
            print(f"Image generation attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                raise

    raise Exception("Image generation failed after all retries")


def _save_base64_image(base64_str: str, output_path: str) -> None:
    """
    Base64文字列をデコードして画像として保存

    Args:
        base64_str: Base64エンコードされた画像データ
        output_path: 保存先パス
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Base64デコード
    image_data = base64.b64decode(base64_str)

    # ファイル保存
    with open(output_path, "wb") as f:
        f.write(image_data)
