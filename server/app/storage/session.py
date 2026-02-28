"""
インメモリセッション管理

対戦状態（GameState）をメモリ内で管理する。
サーバー再起動で失われるが、短期対戦なので許容範囲。
"""
from typing import Dict, Optional
from uuid import UUID

from app.schemas.game import GameState


class SessionManager:
    """GameStateを管理するシングルトンマネージャー"""

    def __init__(self):
        self._sessions: Dict[UUID, GameState] = {}

    def create_match(self, match_id: UUID, initial_state: GameState) -> None:
        """
        新しいマッチを作成

        Args:
            match_id: マッチID
            initial_state: 初期ゲーム状態
        """
        self._sessions[match_id] = initial_state

    def get_match(self, match_id: UUID) -> Optional[GameState]:
        """
        マッチ状態を取得

        Args:
            match_id: マッチID

        Returns:
            ゲーム状態（存在しない場合はNone）
        """
        return self._sessions.get(match_id)

    def update_match(self, match_id: UUID, state: GameState) -> None:
        """
        マッチ状態を更新

        Args:
            match_id: マッチID
            state: 新しいゲーム状態
        """
        self._sessions[match_id] = state

    def delete_match(self, match_id: UUID) -> None:
        """
        マッチを削除

        Args:
            match_id: マッチID
        """
        if match_id in self._sessions:
            del self._sessions[match_id]

    def list_matches(self) -> Dict[UUID, GameState]:
        """
        全マッチを取得

        Returns:
            マッチID -> GameStateのマッピング
        """
        return self._sessions.copy()

    def count_matches(self) -> int:
        """
        アクティブなマッチ数を取得

        Returns:
            マッチ数
        """
        return len(self._sessions)


# グローバルシングルトン
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """SessionManagerのシングルトンインスタンスを取得"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
