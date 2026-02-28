"""
Deck API エンドポイント

デッキの保存と取得を提供する。
"""
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException

from app.schemas.api import DeckGetResponse, DeckSaveRequest, DeckSaveResponse
from app.schemas.deck import Deck
from app.storage.db import get_deck, get_units_by_ids, save_deck

router = APIRouter()


@router.post("/save", response_model=DeckSaveResponse)
async def save_deck_endpoint(request: DeckSaveRequest):
    """
    デッキを保存

    1. 全ユニットの存在確認
    2. Deck作成
    3. DB保存
    """
    # 全ユニットの存在確認
    units = await get_units_by_ids(request.unit_spec_ids)
    if len(units) != 5:
        raise HTTPException(
            status_code=400,
            detail=f"Some units not found. Expected 5, got {len(units)}"
        )

    # Deck作成
    deck = Deck(
        id=uuid4(),
        name=request.name,
        unit_spec_ids=request.unit_spec_ids
    )

    # DB保存
    await save_deck(deck)

    return DeckSaveResponse(deck_id=deck.id)


@router.get("/{deck_id}", response_model=DeckGetResponse)
async def get_deck_endpoint(deck_id: UUID):
    """
    デッキを取得

    デッキ情報と含まれるユニット一覧を返す。
    """
    deck = await get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    # ユニット一覧取得
    units = await get_units_by_ids(deck.unit_spec_ids)

    return DeckGetResponse(
        deck=deck,
        units=units
    )
