"""
Units API エンドポイント

ユニット生成を提供する。
"""
from fastapi import APIRouter, HTTPException

from app.llm.unit_gen import generate_unit_from_prompt
from app.schemas.api import UnitCreateRequest, UnitCreateResponse

router = APIRouter()


@router.post("/create", response_model=UnitCreateResponse)
async def create_unit(request: UnitCreateRequest):
    """
    ユニットを生成

    1. Mistral LLMでJSON生成
    2. パワースコア計算 → コスト調整
    3. プレースホルダー画像設定
    4. DB保存
    """
    try:
        unit_spec = await generate_unit_from_prompt(request.prompt)
        return UnitCreateResponse(unit_spec=unit_spec)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate unit: {str(e)}"
        )
