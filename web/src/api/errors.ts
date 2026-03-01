/**
 * APIエラーハンドリング
 */

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public errorType?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'ネットワークエラーが発生しました') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends Error {
  constructor(message: string = 'リクエストがタイムアウトしました') {
    super(message);
    this.name = 'TimeoutError';
  }
}

/**
 * バックエンドの例外メッセージからユーザー向けメッセージにマッピング
 */
export function mapErrorToUserMessage(error: unknown): string {
  if (error instanceof ApiError) {
    // バックエンドの例外タイプに基づいてメッセージをマッピング
    if (error.statusCode === 404 || error.errorType === 'MatchNotFoundException') {
      return 'ゲームセッションが見つかりません';
    }
    if (error.statusCode === 400) {
      if (error.errorType === 'InsufficientCostException' || error.message.includes('cost')) {
        return 'コストが不足しています';
      }
      if (error.errorType === 'MatchAlreadyFinishedException' || error.message.includes('finished')) {
        return 'ゲームは既に終了しています';
      }
      return error.message || 'リクエストが無効です';
    }
    if (error.statusCode >= 500) {
      return 'サーバーエラーが発生しました。しばらくしてから再度お試しください';
    }
    return error.message || '予期しないエラーが発生しました';
  }

  if (error instanceof NetworkError) {
    return error.message;
  }

  if (error instanceof TimeoutError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return '予期しないエラーが発生しました';
}
