"""
Units API エンドポイント

ユニット生成を提供する。
"""
import os
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.llm.unit_gen import generate_unit_from_prompt, generate_images_background
from app.schemas.api import UnitCreateRequest, UnitCreateResponse
from app.storage.db import get_unit_spec, delete_unit_spec

router = APIRouter()


@router.post("/create", response_model=UnitCreateResponse)
async def create_unit(request: UnitCreateRequest, background_tasks: BackgroundTasks):
    """
    ユニットを生成

    1. Mistral LLMでJSON生成
    2. パワースコア計算 → コスト調整
    3. プレースホルダー画像設定（即座にレスポンス）
    4. DB保存
    5. バックグラウンドで画像生成 → DB更新
    """
    try:
        # ユニット統計を生成してすぐにレスポンス
        unit_spec = await generate_unit_from_prompt(request.prompt)

        # バックグラウンドで画像生成
        unit_data = {
            "name": unit_spec.name,
            "max_hp": unit_spec.max_hp,
            "atk": unit_spec.atk,
            "speed": unit_spec.speed,
            "range": unit_spec.range,
            "atk_interval": unit_spec.atk_interval,
            "cost": unit_spec.cost
        }
        background_tasks.add_task(
            generate_images_background,
            unit_spec.id,
            unit_data,
            request.prompt
        )

        return UnitCreateResponse(unit_spec=unit_spec)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate unit: {str(e)}"
        )


@router.delete("/{unit_id}")
async def delete_unit(unit_id: UUID):
    """
    ユニットを削除

    1. データベースからユニットを取得
    2. 画像ファイルを削除
    3. データベースからユニットを削除
    """
    try:
        # ユニット取得
        unit = await get_unit_spec(unit_id)
        if unit is None:
            raise HTTPException(status_code=404, detail="Unit not found")

        # 画像ファイル削除
        _delete_image_files(unit.sprite_url, unit.card_url)

        # DB削除
        deleted = await delete_unit_spec(unit_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Unit not found")

        return {"message": "Unit deleted successfully", "unit_id": str(unit_id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete unit: {str(e)}"
        )


def _delete_image_files(sprite_url: str, card_url: str):
    """画像ファイルを削除（プレースホルダーは除く）"""
    for url in [sprite_url, card_url]:
        # プレースホルダーはスキップ
        if "placeholder" in url:
            continue

        # URLから相対パスを取得（/static/sprites/xxx.png -> static/sprites/xxx.png）
        file_path = url.lstrip("/")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted image file: {file_path}")
        except Exception as e:
            print(f"Failed to delete image file {file_path}: {e}")
