"""
Match API エンドポイント

対戦の開始、tick処理、ユニット召喚、AI決定を提供する。
"""
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException

from app.api.exceptions import (
    DeckNotFoundException,
    InsufficientCostException,
    MatchAlreadyFinishedException,
    MatchNotFoundException,
    UnitNotFoundException
)

from app.config import get_settings
from app.engine.tick import process_tick, spawn_unit_in_game
from app.schemas.api import (
    AIDecideRequest,
    AIDecideResponse,
    MatchSpawnRequest,
    MatchSpawnResponse,
    MatchStartRequest,
    MatchStartResponse,
    MatchTickRequest,
    MatchTickResponse
)
from app.schemas.game import Event, GameState
from app.schemas.unit import UnitInstance
from app.storage.db import get_deck, get_unit_spec, save_match, update_match_result
from app.storage.session import get_session_manager

router = APIRouter()
settings = get_settings()


@router.post("/start", response_model=MatchStartResponse)
async def start_match(request: MatchStartRequest):
    """
    対戦を開始する

    1. デッキをDBから読み込み
    2. 初期GameStateを作成
    3. セッションマネージャーに保存
    4. matchesテーブルに記録
    """
    # デッキ取得
    player_deck = await get_deck(request.player_deck_id)
    if not player_deck:
        raise DeckNotFoundException(str(request.player_deck_id))

    # AIデッキ取得（指定されていない場合はランダム生成）
    ai_deck_id = request.ai_deck_id
    if ai_deck_id:
        ai_deck = await get_deck(ai_deck_id)
        if not ai_deck:
            raise DeckNotFoundException(str(ai_deck_id))
    else:
        # TODO: ランダムデッキ生成（今は同じデッキを使用）
        ai_deck = player_deck
        ai_deck_id = player_deck.id

    # 初期GameState作成
    match_id = uuid4()
    game_state = GameState(
        match_id=match_id,
        tick_ms=settings.tick_ms,
        time_ms=0,
        player_base_hp=settings.initial_base_hp,
        ai_base_hp=settings.initial_base_hp,
        player_cost=settings.initial_cost,
        ai_cost=settings.initial_cost,
        max_cost=settings.max_cost,
        cost_recovery_per_tick=settings.cost_recovery_per_tick,
        units=[],
        winner=None,
        player_deck_id=request.player_deck_id,
        ai_deck_id=ai_deck_id
    )

    # セッションに保存
    session_manager = get_session_manager()
    session_manager.create_match(match_id, game_state)

    # DB記録
    await save_match(match_id, request.player_deck_id, ai_deck_id)

    return MatchStartResponse(
        match_id=match_id,
        game_state=game_state
    )


@router.post("/tick", response_model=MatchTickResponse)
async def tick_match(request: MatchTickRequest):
    """
    tick処理を実行

    1. セッションからGameState取得
    2. process_tick()実行
    3. セッションに保存
    4. 勝敗が決まった場合はDB更新とセッション削除
    5. 古い試合を定期的にクリーンアップ
    """
    session_manager = get_session_manager()

    # 定期的に古い試合をクリーンアップ（30秒以上更新がない試合を削除）
    # tickは頻繁に呼ばれるので、ここでクリーンアップを実行
    import random
    if random.random() < 0.01:  # 1%の確率で実行（約100tickに1回）
        cleaned = session_manager.cleanup_inactive_matches(timeout_seconds=30)
        if cleaned > 0:
            print(f"[Cleanup] Removed {cleaned} inactive matches")

    game_state = session_manager.get_match(request.match_id)

    if not game_state:
        # マッチが見つからない場合（削除済みまたは存在しない）
        raise MatchNotFoundException(str(request.match_id))

    # tick処理
    events = process_tick(game_state)

    # 勝敗が決まった場合はDB更新してセッションから削除
    if game_state.winner:
        await update_match_result(request.match_id, game_state.winner)
        # セッションから削除してリソースを解放
        session_manager.delete_match(request.match_id)
        print(f"[Match] Match {request.match_id} finished with winner: {game_state.winner}. Session deleted.")
    else:
        # セッションに保存（継続中の場合のみ）
        session_manager.update_match(request.match_id, game_state)

    return MatchTickResponse(
        game_state=game_state,
        events=events
    )


@router.post("/spawn", response_model=MatchSpawnResponse)
async def spawn_unit(request: MatchSpawnRequest):
    """
    ユニットを召喚

    1. コスト検証
    2. UnitInstance作成
    3. ゲームに追加
    4. コスト消費
    """
    session_manager = get_session_manager()
    game_state = session_manager.get_match(request.match_id)

    if not game_state:
        raise MatchNotFoundException(str(request.match_id))

    if game_state.is_finished():
        raise MatchAlreadyFinishedException(str(request.match_id))

    # ユニットスペック取得
    unit_spec = await get_unit_spec(request.unit_spec_id)
    if not unit_spec:
        raise UnitNotFoundException(str(request.unit_spec_id))

    # コスト確認
    if request.side == "player":
        current_cost = game_state.player_cost
    elif request.side == "ai":
        current_cost = game_state.ai_cost
    else:
        raise HTTPException(status_code=400, detail="Invalid side (must be 'player' or 'ai')")

    if current_cost < unit_spec.cost:
        raise InsufficientCostException(required=unit_spec.cost, available=current_cost)

    # UnitInstance作成
    initial_pos = 0.0 if request.side == "player" else 20.0
    unit_instance = UnitInstance.from_spec(
        spec=unit_spec,
        side=request.side,  # type: ignore
        initial_pos=initial_pos
    )

    # ゲームに追加
    spawn_event = spawn_unit_in_game(game_state, unit_instance, game_state.time_ms)

    # コスト消費
    if request.side == "player":
        game_state.player_cost -= unit_spec.cost
    else:
        game_state.ai_cost -= unit_spec.cost

    # セッションに保存
    session_manager.update_match(request.match_id, game_state)

    return MatchSpawnResponse(
        game_state=game_state,
        events=[spawn_event]
    )


@router.post("/end")
async def end_match(request: MatchTickRequest):
    """
    マッチを明示的に終了する

    ユーザーが画面を閉じたときなど、途中でマッチを終了する場合に使用。
    セッションからマッチを削除してリソースを解放する。
    """
    session_manager = get_session_manager()
    try:
        game_state = session_manager.get_match(request.match_id)

        if game_state:
            # 勝敗が決まっていない場合でも削除
            session_manager.delete_match(request.match_id)
            print(f"[Match] Match {request.match_id} ended by user. Session deleted.")
            return {"message": "Match ended successfully", "match_id": str(request.match_id)}
        else:
            # 既に削除されている場合も成功として扱う
            return {"message": "Match already ended", "match_id": str(request.match_id)}
    except Exception as e:
        print(f"[Match] Error ending match {request.match_id}: {e}")
        # エラーでも成功として扱う（冪等性）
        return {"message": "Match end processed", "match_id": str(request.match_id)}


@router.post("/ai_decide", response_model=AIDecideResponse)
async def ai_decide_spawn_endpoint(request: AIDecideRequest):
    """
    AIの召喚決定

    Mistral LLMを使用して盤面を分析し、次に召喚するユニットを決定する。
    """
    from app.llm.ai_decide import ai_decide_spawn

    session_manager = get_session_manager()
    game_state = session_manager.get_match(request.match_id)

    if not game_state:
        raise MatchNotFoundException(str(request.match_id))

    if game_state.is_finished():
        return AIDecideResponse(
            spawn_unit_spec_id=None,
            wait_ms=600,
            reason="Match is finished"
        )

    if not game_state.ai_deck_id:
        return AIDecideResponse(
            spawn_unit_spec_id=None,
            wait_ms=600,
            reason="AI deck not set"
        )

    # AIデッキ取得
    ai_deck = await get_deck(game_state.ai_deck_id)
    if not ai_deck:
        return AIDecideResponse(
            spawn_unit_spec_id=None,
            wait_ms=600,
            reason="AI deck not found"
        )

    # AI決定
    try:
        decision = await ai_decide_spawn(game_state, ai_deck)
        return AIDecideResponse(**decision)
    except Exception as e:
        print(f"AI decision error: {e}")
        # フォールバック
        return AIDecideResponse(
            spawn_unit_spec_id=None,
            wait_ms=600,
            reason=f"AI decision failed: {str(e)}"
        )
