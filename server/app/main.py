"""
FastAPIアプリケーション

サーバーのエントリーポイント。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.storage.db import close_db_pool, create_db_pool, init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    settings = get_settings()
    print(f"Starting Pixel Simulation Arena API (env: {settings.environment})")

    # データベース初期化
    await create_db_pool()
    await init_database()
    print("Database initialized")

    # プレースホルダー画像作成
    create_placeholder_images()
    print("Placeholder images created")

    yield

    # シャットダウン時
    await close_db_pool()
    print("Database connection closed")


app = FastAPI(
    title="Pixel Simulation Arena API",
    description="Backend API for real-time 1-lane battle game with AI-generated units",
    version="0.1.0",
    lifespan=lifespan
)

# CORS設定
settings = get_settings()
allowed_origins = settings.cors_origins.split(",") if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイル配信
app.mount("/static", StaticFiles(directory="static"), name="static")


# ルーター登録
from app.api import deck, gallery, match, units

app.include_router(match.router, prefix="/match", tags=["match"])
app.include_router(units.router, prefix="/units", tags=["units"])
app.include_router(gallery.router, prefix="/gallery", tags=["gallery"])
app.include_router(deck.router, prefix="/deck", tags=["deck"])


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    from app.storage.session import get_session_manager

    session_manager = get_session_manager()
    active_matches = session_manager.count_matches()

    return {
        "status": "ok",
        "service": "pixel-simu-arena",
        "active_matches": active_matches,
        "environment": get_settings().environment
    }


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Pixel Simulation Arena API",
        "docs": "/docs",
        "health": "/health"
    }


def create_placeholder_images():
    """プレースホルダー画像を作成"""
    import os
    from PIL import Image, ImageDraw

    # スプライト用プレースホルダー（32x32）
    sprite_path = "static/sprites/placeholder.png"
    if not os.path.exists(sprite_path):
        os.makedirs(os.path.dirname(sprite_path), exist_ok=True)
        img = Image.new("RGBA", (32, 32), (100, 100, 100, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([8, 8, 24, 24], fill=(200, 200, 200, 255))
        img.save(sprite_path)

    # バトルスプライト用プレースホルダー（128x128）
    battle_sprite_path = "static/battle_sprites/placeholder.png"
    if not os.path.exists(battle_sprite_path):
        os.makedirs(os.path.dirname(battle_sprite_path), exist_ok=True)
        img = Image.new("RGBA", (128, 128), (100, 100, 100, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([32, 32, 96, 96], fill=(200, 200, 200, 255))
        img.save(battle_sprite_path)

    # カード用プレースホルダー（256x256）
    card_path = "static/cards/placeholder.png"
    if not os.path.exists(card_path):
        os.makedirs(os.path.dirname(card_path), exist_ok=True)
        img = Image.new("RGBA", (256, 256), (80, 80, 80, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([64, 64, 192, 192], fill=(180, 180, 180, 255))
        img.save(card_path)


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development"
    )
