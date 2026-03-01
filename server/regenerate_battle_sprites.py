"""
既存ユニットのバトルスプライトを再生成するスクリプト
"""
import asyncio
import os
from pathlib import Path

from app.config import get_settings
from app.llm.image_gen import _create_battle_sprite_prompt, _generate_and_save_image, BATTLE_SPRITE_PARAMS, _create_placeholder_image
from app.storage.db import create_db_pool, list_unit_specs, update_unit_images

settings = get_settings()


async def regenerate_battle_sprites():
    """全ユニットのバトルスプライトを再生成"""
    # DB接続
    await create_db_pool()

    # 全ユニット取得
    units = await list_unit_specs(limit=1000)

    print(f"Found {len(units)} units to process")

    for unit in units:
        battle_sprite_path = f"static/battle_sprites/{unit.id}.png"

        # プレースホルダーファイルかどうかをサイズで判定
        is_placeholder = False
        if os.path.exists(battle_sprite_path):
            file_size = os.path.getsize(battle_sprite_path)
            # プレースホルダーは約2-3KB、本物の画像は通常10KB以上
            if file_size < 5000:
                is_placeholder = True
                print(f"[Detect] {unit.name} - placeholder detected (size: {file_size} bytes)")
            else:
                print(f"[Skip] {unit.name} - real image exists (size: {file_size} bytes)")
                continue

        if not is_placeholder and not os.path.exists(battle_sprite_path):
            print(f"[Generate] {unit.name} - file not found")
        elif is_placeholder:
            print(f"[Regenerate] {unit.name}")

        # ユニットデータを辞書に変換
        unit_data = {
            "name": unit.name,
            "speed": unit.speed,
            "max_hp": unit.max_hp,
            "atk": unit.atk,
            "range": unit.range,
        }

        # バトルスプライト生成
        try:
            battle_sprite_prompt = _create_battle_sprite_prompt(unit_data, unit.original_prompt or "")
            _generate_and_save_image(
                prompt=battle_sprite_prompt,
                output_path=battle_sprite_path,
                params=BATTLE_SPRITE_PARAMS
            )
            battle_sprite_url = f"/static/battle_sprites/{unit.id}.png"
            print(f"  ✓ Generated: {battle_sprite_path}")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            _create_placeholder_image(battle_sprite_path, size=128)
            battle_sprite_url = f"/static/battle_sprites/{unit.id}.png"

        # DB更新
        await update_unit_images(unit.id, unit.sprite_url, battle_sprite_url, unit.card_url)
        print(f"  ✓ DB updated")

    print(f"\nCompleted: {len(units)} units processed")


if __name__ == "__main__":
    asyncio.run(regenerate_battle_sprites())
