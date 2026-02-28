"""
カスタム例外クラス

アプリケーション全体で使用する例外を定義する。
"""
from fastapi import HTTPException, status


class MatchNotFoundException(HTTPException):
    """マッチが見つからない"""
    def __init__(self, match_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match not found: {match_id}"
        )


class DeckNotFoundException(HTTPException):
    """デッキが見つからない"""
    def __init__(self, deck_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deck not found: {deck_id}"
        )


class UnitNotFoundException(HTTPException):
    """ユニットが見つからない"""
    def __init__(self, unit_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit not found: {unit_id}"
        )


class InsufficientCostException(HTTPException):
    """コスト不足"""
    def __init__(self, required: float, available: float):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient cost: required {required}, available {available}"
        )


class MatchAlreadyFinishedException(HTTPException):
    """マッチが既に終了している"""
    def __init__(self, match_id: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Match already finished: {match_id}"
        )


class InvalidDeckException(HTTPException):
    """無効なデッキ"""
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid deck: {reason}"
        )


class UnitGenerationException(HTTPException):
    """ユニット生成失敗"""
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate unit: {reason}"
        )


class AIDecisionException(HTTPException):
    """AI決定失敗"""
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI decision failed: {reason}"
        )
