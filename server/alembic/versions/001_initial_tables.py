"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-02-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """データベーステーブルを作成"""

    # unitsテーブル
    op.execute("""
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
            card_url VARCHAR(255) NOT NULL,
            image_prompt TEXT,
            original_prompt TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_units_created_at ON units(created_at DESC)
    """)

    # decksテーブル
    op.execute("""
        CREATE TABLE IF NOT EXISTS decks (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            unit_spec_ids JSONB NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_decks_created_at ON decks(created_at DESC)
    """)

    # matchesテーブル
    op.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id VARCHAR(36) PRIMARY KEY,
            player_deck_id VARCHAR(36),
            ai_deck_id VARCHAR(36),
            winner VARCHAR(10),
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            finished_at TIMESTAMP
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_matches_created_at ON matches(created_at DESC)
    """)


def downgrade() -> None:
    """テーブルを削除"""
    op.execute("DROP TABLE IF EXISTS matches")
    op.execute("DROP TABLE IF EXISTS decks")
    op.execute("DROP TABLE IF EXISTS units")
