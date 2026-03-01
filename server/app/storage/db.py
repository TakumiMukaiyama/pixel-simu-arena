"""
PostgreSQLデータベース接続とテーブル操作

asyncpgを使用した非同期データベース操作を提供する。
コネクションプールで接続を管理し、効率的にクエリを実行する。
"""
import json
from typing import List, Optional
from uuid import UUID

import asyncpg

from app.config import get_settings
from app.schemas.deck import Deck
from app.schemas.unit import UnitSpec

# グローバルコネクションプール
_pool: Optional[asyncpg.Pool] = None


# ========== コネクションプール管理 ==========

async def create_db_pool() -> None:
    """データベースコネクションプールを作成"""
    global _pool
    settings = get_settings()
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,
        max_size=20,
        command_timeout=30,
        max_inactive_connection_lifetime=300  # 5分でアイドル接続を閉じる
    )


def get_db_pool() -> asyncpg.Pool:
    """コネクションプールを取得"""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call create_db_pool() first.")
    return _pool


async def close_db_pool() -> None:
    """コネクションプールをクローズ"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ========== テーブル初期化 ==========

async def init_database() -> None:
    """データベーステーブルを作成（存在しない場合）"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        # unitsテーブル
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS units (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                cost INTEGER NOT NULL CHECK (cost >= 1 AND cost <= 8),
                max_hp INTEGER NOT NULL CHECK (max_hp >= 5 AND max_hp <= 30),
                atk INTEGER NOT NULL CHECK (atk >= 1 AND atk <= 15),
                speed REAL NOT NULL CHECK (speed >= 0.2 AND speed <= 2.0),
                range REAL NOT NULL CHECK (range >= 1.0 AND range <= 7.0),
                atk_interval REAL NOT NULL CHECK (atk_interval >= 1.0 AND atk_interval <= 5.0),
                sprite_url VARCHAR(255) NOT NULL,
                battle_sprite_url VARCHAR(255) NOT NULL DEFAULT '/static/battle_sprites/placeholder.png',
                card_url VARCHAR(255) NOT NULL,
                image_prompt TEXT,
                original_prompt TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_units_created_at ON units(created_at DESC)
        """)

        # battle_sprite_urlカラムを追加（既存テーブル用）
        try:
            await conn.execute("""
                ALTER TABLE units
                ADD COLUMN IF NOT EXISTS battle_sprite_url VARCHAR(255)
                NOT NULL DEFAULT '/static/battle_sprites/placeholder.png'
            """)
        except Exception:
            pass  # カラムが既に存在する場合はスキップ

        # decksテーブル
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS decks (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                unit_spec_ids JSONB NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_decks_created_at ON decks(created_at DESC)
        """)

        # matchesテーブル
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id VARCHAR(36) PRIMARY KEY,
                player_deck_id VARCHAR(36),
                ai_deck_id VARCHAR(36),
                winner VARCHAR(10),
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                finished_at TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_matches_created_at ON matches(created_at DESC)
        """)


# ========== Units CRUD ==========

async def save_unit_spec(unit_spec: UnitSpec) -> None:
    """ユニットをデータベースに保存"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO units (
                id, name, cost, max_hp, atk, speed, range, atk_interval,
                sprite_url, battle_sprite_url, card_url, image_prompt, original_prompt, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
            str(unit_spec.id),
            unit_spec.name,
            unit_spec.cost,
            unit_spec.max_hp,
            unit_spec.atk,
            unit_spec.speed,
            unit_spec.range,
            unit_spec.atk_interval,
            unit_spec.sprite_url,
            unit_spec.battle_sprite_url,
            unit_spec.card_url,
            unit_spec.image_prompt,
            unit_spec.original_prompt,
            unit_spec.created_at
        )


async def get_unit_spec(unit_id: UUID) -> Optional[UnitSpec]:
    """ユニットをIDで取得"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM units WHERE id = $1",
            str(unit_id)
        )
        if row is None:
            return None
        return UnitSpec(**dict(row))


async def list_unit_specs(limit: int = 20, offset: int = 0) -> List[UnitSpec]:
    """ユニット一覧を取得（ページネーション）"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM units ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit, offset
        )
        return [UnitSpec(**dict(row)) for row in rows]


async def count_unit_specs() -> int:
    """ユニット総数を取得"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT COUNT(*) FROM units")
        return result or 0


async def get_units_by_ids(unit_ids: List[UUID]) -> List[UnitSpec]:
    """複数のユニットをIDで一括取得"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM units WHERE id = ANY($1::varchar[])",
            [str(uid) for uid in unit_ids]
        )
        return [UnitSpec(**dict(row)) for row in rows]


async def update_unit_images(unit_id: UUID, sprite_url: str, battle_sprite_url: str, card_url: str) -> None:
    """ユニットの画像URLを更新"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE units
            SET sprite_url = $2, battle_sprite_url = $3, card_url = $4
            WHERE id = $1
            """,
            str(unit_id),
            sprite_url,
            battle_sprite_url,
            card_url
        )
        print(f"[DB] Updated images for unit {unit_id}: sprite={sprite_url}, battle_sprite={battle_sprite_url}, card={card_url}, result={result}")


async def delete_unit_spec(unit_id: UUID) -> bool:
    """
    ユニットを削除

    Args:
        unit_id: 削除するユニットID

    Returns:
        削除成功時True、ユニットが存在しない場合False
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM units WHERE id = $1",
            str(unit_id)
        )
        # DELETEコマンドは "DELETE n" という形式を返す
        return result.split()[-1] != "0"


# ========== Decks CRUD ==========

async def save_deck(deck: Deck) -> None:
    """デッキをデータベースに保存"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO decks (id, name, unit_spec_ids, created_at)
            VALUES ($1, $2, $3, $4)
            """,
            str(deck.id),
            deck.name,
            json.dumps([str(uid) for uid in deck.unit_spec_ids]),
            deck.created_at
        )


async def get_deck(deck_id: UUID) -> Optional[Deck]:
    """デッキをIDで取得"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM decks WHERE id = $1",
            str(deck_id)
        )
        if row is None:
            return None

        # JSONBから unit_spec_ids を復元
        unit_ids_json = row["unit_spec_ids"]
        unit_ids = [UUID(uid) for uid in json.loads(unit_ids_json)]

        return Deck(
            id=UUID(row["id"]),
            name=row["name"],
            unit_spec_ids=unit_ids,
            created_at=row["created_at"]
        )


async def list_decks(limit: int = 20, offset: int = 0) -> List[Deck]:
    """デッキ一覧を取得（ページネーション）"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM decks ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit, offset
        )
        decks = []
        for row in rows:
            unit_ids_json = row["unit_spec_ids"]
            unit_ids = [UUID(uid) for uid in json.loads(unit_ids_json)]
            decks.append(Deck(
                id=UUID(row["id"]),
                name=row["name"],
                unit_spec_ids=unit_ids,
                created_at=row["created_at"]
            ))
        return decks


async def update_deck(deck_id: UUID, name: str, unit_spec_ids: List[UUID]) -> None:
    """デッキを更新"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE decks
            SET name = $2, unit_spec_ids = $3
            WHERE id = $1
            """,
            str(deck_id),
            name,
            json.dumps([str(uid) for uid in unit_spec_ids])
        )


async def delete_deck(deck_id: UUID) -> bool:
    """
    デッキを削除

    Args:
        deck_id: 削除するデッキID

    Returns:
        削除成功時True、デッキが存在しない場合False
    """
    pool = get_db_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM decks WHERE id = $1",
            str(deck_id)
        )
        # DELETEコマンドは "DELETE n" という形式を返す
        return result.split()[-1] != "0"


# ========== Matches CRUD ==========

async def save_match(
    match_id: UUID,
    player_deck_id: Optional[UUID] = None,
    ai_deck_id: Optional[UUID] = None
) -> None:
    """マッチをデータベースに保存"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO matches (match_id, player_deck_id, ai_deck_id, created_at)
            VALUES ($1, $2, $3, NOW())
            """,
            str(match_id),
            str(player_deck_id) if player_deck_id else None,
            str(ai_deck_id) if ai_deck_id else None
        )


async def update_match_result(match_id: UUID, winner: str) -> None:
    """マッチ結果を更新"""
    pool = get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE matches
            SET winner = $2, finished_at = NOW()
            WHERE match_id = $1
            """,
            str(match_id),
            winner
        )
