"""
バトル背景画像を生成するスクリプト

PixelLab APIを使用して800x200のバトル背景を生成する。
"""
import base64
import os
from pathlib import Path

from pixellab import Client as PixelLabClient

from app.config import get_settings

settings = get_settings()


def generate_battle_background():
    """バトル背景画像を生成"""
    output_path = "static/backgrounds/battle_field.png"

    # すでに存在する場合はスキップ
    if os.path.exists(output_path):
        print(f"[Background] Already exists: {output_path}")
        return output_path

    print("[Background] Generating battle field background...")

    # ディレクトリ作成
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    client = PixelLabClient(secret=settings.pixellab_api_key)

    # 背景画像生成プロンプト (400x200でタイル可能)
    prompt = """pixel art battlefield landscape,
medieval fantasy battlefield, tileable,
ground with grass and dirt, distant mountains,
sky with clouds, no characters, empty battlefield,
side view, seamless edges, game background"""

    try:
        result = client.generate_image_pixflux(
            description=prompt,
            image_size={"width": 400, "height": 200},
            no_background=False,
            view="side",
            outline="single color outline",
            shading="detailed shading",
            detail="highly detailed",
            text_guidance_scale=7.0,
        )

        # Base64デコード
        base64_data = result.image.base64
        if base64_data.startswith("data:image/png;base64,"):
            base64_data = base64_data.split(",", 1)[1]

        # ファイル保存
        image_data = base64.b64decode(base64_data)
        with open(output_path, "wb") as f:
            f.write(image_data)

        print(f"[Background] Generated: {output_path}")
        return output_path

    except Exception as e:
        print(f"[Background] Generation failed: {e}")
        print("[Background] Creating placeholder...")

        # フォールバック: プレースホルダー画像
        from PIL import Image, ImageDraw

        img = Image.new('RGB', (800, 200), (40, 50, 60))
        draw = ImageDraw.Draw(img)

        # シンプルな地平線
        draw.rectangle([0, 140, 800, 200], fill=(60, 80, 60))

        img.save(output_path)
        print(f"[Background] Placeholder created: {output_path}")
        return output_path


if __name__ == "__main__":
    generate_battle_background()
