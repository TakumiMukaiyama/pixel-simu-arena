"""
画像生成

PixelLab APIを使用してユニットのスプライトとカード絵を生成する。
"""
import base64
from pathlib import Path
from typing import Tuple
from uuid import UUID

from PIL import Image, ImageDraw
from pixellab import Client as PixelLabClient

from app.config import get_settings

settings = get_settings()

# スプライト用パラメータ (32x32, 透明背景) - ギャラリー表示用
SPRITE_PARAMS = {
    "image_size": {"width": 32, "height": 32},
    "no_background": True,
    "view": "side",
    "direction": "east",
    "outline": "single color black outline",
    "shading": "basic shading",
    "detail": "low detail",
    "text_guidance_scale": 8.0,
}

# バトルスプライト用パラメータ (128x128, 透明背景) - バトル表示用
BATTLE_SPRITE_PARAMS = {
    "image_size": {"width": 128, "height": 128},
    "no_background": True,
    "view": "low top-down",
    "direction": "east",  # 右向き
    "outline": "single color black outline",
    "shading": "basic shading",
    "detail": "medium detail",
    "text_guidance_scale": 8.0,
}

# カード絵用パラメータ (256x256)
CARD_PARAMS = {
    "image_size": {"width": 256, "height": 256},
    "no_background": False,
    "view": "side",
    "outline": "single color black outline",
    "shading": "detailed shading",
    "detail": "highly detailed",
    "text_guidance_scale": 9.0,
}


def _get_pixellab_client() -> PixelLabClient:
    """PixelLabクライアントのシングルトンを取得"""
    return PixelLabClient(secret=settings.pixellab_api_key)


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


def _create_battle_sprite_prompt(unit_data: dict, original_prompt: str) -> str:
    """
    バトルスプライト用の画像プロンプトを生成（128x128、コマ風）

    Args:
        unit_data: ユニットステータス
        original_prompt: ユーザーの元プロンプト

    Returns:
        画像生成プロンプト
    """
    name = unit_data.get("name", "unit")
    speed = unit_data.get("speed", 1.0)
    hp = unit_data.get("max_hp", 10)

    # 特徴的な修飾語を追加
    modifiers = []
    if speed >= 1.5:
        modifiers.append("fast")
    elif speed <= 0.5:
        modifiers.append("slow")

    if hp >= 20:
        modifiers.append("armored")
    elif hp <= 10:
        modifiers.append("agile")

    modifier_str = ", ".join(modifiers) if modifiers else ""

    prompt = f"pixel art, 128x128, low angle top-down view, {name}"
    if modifier_str:
        prompt += f", {modifier_str}"
    prompt += f", game token, board game piece, clear design, fantasy style"

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
    params: dict,
    max_retries: int = 2
) -> str:
    """
    PixelLab APIで画像を生成してファイルに保存

    Args:
        prompt: 画像生成プロンプト
        output_path: 保存先パス
        params: PixelLabパラメータ（サイズ、スタイルなど）
        max_retries: 最大リトライ回数

    Returns:
        保存したファイルパス

    Raises:
        Exception: 全リトライ失敗時
    """
    client = _get_pixellab_client()

    # ディレクトリ作成
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(max_retries):
        try:
            # PixelLab API呼び出し
            result = client.generate_image_pixflux(
                description=prompt,
                image_size=params["image_size"],
                no_background=params["no_background"],
                view=params["view"],
                direction=params.get("direction"),
                outline=params["outline"],
                shading=params["shading"],
                detail=params["detail"],
                text_guidance_scale=params["text_guidance_scale"],
            )

            # Base64デコード
            # PixelLabのレスポンス構造: result.image.base64
            if not hasattr(result, 'image') or not hasattr(result.image, 'base64'):
                raise Exception("レスポンスにimage.base64データがありません")

            base64_data = result.image.base64

            # data:image/png;base64,プレフィックスを削除
            if base64_data.startswith("data:image/png;base64,"):
                base64_data = base64_data.split(",", 1)[1]

            # ファイル保存
            image_data = base64.b64decode(base64_data)
            with open(output_path, "wb") as f:
                f.write(image_data)

            print(f"[PixelLab] 画像生成成功: {output_path}")
            return output_path

        except Exception as e:
            print(f"[PixelLab] 試行 {attempt + 1}/{max_retries} 失敗: {e}")
            if attempt == max_retries - 1:
                raise

    raise Exception("PixelLab API: 全リトライ失敗")


def _create_placeholder_image(output_path: str, size: int):
    """
    エラー時のプレースホルダー画像を生成

    Args:
        output_path: 保存先パス
        size: 画像サイズ（正方形）
    """
    img = Image.new('RGBA', (size, size), (200, 200, 200, 255))
    draw = ImageDraw.Draw(img)

    # 簡単な図形を描画
    draw.ellipse([size//4, size//4, size*3//4, size*3//4], fill=(150, 150, 150, 255))

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


def generate_unit_images(
    unit_id: UUID,
    unit_data: dict,
    original_prompt: str
) -> Tuple[str, str, str]:
    """
    ユニット画像を生成（バトルスプライトのみ）

    Args:
        unit_id: ユニットUUID
        unit_data: ユニット統計辞書
        original_prompt: ユーザーの元プロンプト

    Returns:
        (sprite_url, battle_sprite_url, card_url)のタプル
        ※全て同じURLを返す（後方互換性のため）
    """
    # 1. プロンプト生成
    battle_sprite_prompt = _create_battle_sprite_prompt(unit_data, original_prompt)

    # 2. バトルスプライト生成（128x128、透明背景、コマ風）
    try:
        battle_sprite_path = f"static/battle_sprites/{unit_id}.png"
        _generate_and_save_image(
            prompt=battle_sprite_prompt,
            output_path=battle_sprite_path,
            params=BATTLE_SPRITE_PARAMS
        )
        battle_sprite_url = f"/static/battle_sprites/{unit_id}.png"
        print(f"[PixelLab] バトルスプライト生成成功: {battle_sprite_path}")
    except Exception as e:
        print(f"[PixelLab] バトルスプライト生成失敗: {e}")
        _create_placeholder_image(f"static/battle_sprites/{unit_id}.png", size=128)
        battle_sprite_url = f"/static/battle_sprites/{unit_id}.png"

    # sprite_url と card_url も同じ画像を使用（後方互換性）
    sprite_url = battle_sprite_url
    card_url = battle_sprite_url

    return sprite_url, battle_sprite_url, card_url
