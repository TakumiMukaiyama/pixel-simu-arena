"""
Gallery API エンドポイント

ユニット一覧を提供する。
"""
from fastapi import APIRouter, Query

from app.schemas.api import GalleryListResponse
from app.storage.db import count_unit_specs, list_unit_specs

router = APIRouter()


@router.get("/list", response_model=GalleryListResponse)
async def list_gallery(
    limit: int = Query(default=20, ge=1, le=100, description="取得件数"),
    offset: int = Query(default=0, ge=0, description="オフセット")
):
    """
    保存済みユニット一覧を取得

    ページネーションをサポートする。
    """
    units = await list_unit_specs(limit=limit, offset=offset)
    total = await count_unit_specs()

    return GalleryListResponse(
        unit_specs=units,
        total=total
    )
