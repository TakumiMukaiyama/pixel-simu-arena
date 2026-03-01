/**
 * HTTPクライアント基盤
 */

import env from '../config/env';
import { ApiError, NetworkError, TimeoutError } from './errors';

interface RequestOptions extends RequestInit {
  timeout?: number;
  retries?: number;
}

/**
 * fetchラッパー - リトライとタイムアウト機能付き
 */
async function fetchWithRetry(
  url: string,
  options: RequestOptions = {},
  attempt: number = 1
): Promise<Response> {
  const { timeout = 30000, retries = 3, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error && error.name === 'AbortError') {
      throw new TimeoutError();
    }

    // リトライロジック（指数バックオフ）
    if (attempt < retries) {
      const backoffDelay = Math.min(1000 * Math.pow(2, attempt - 1), 5000);
      await new Promise((resolve) => setTimeout(resolve, backoffDelay));
      return fetchWithRetry(url, options, attempt + 1);
    }

    throw new NetworkError();
  }
}

/**
 * APIリクエストの基本処理
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const url = `${env.apiBaseUrl}${endpoint}`;

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const response = await fetchWithRetry(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  // レスポンスの処理
  if (!response.ok) {
    let errorMessage = 'リクエストが失敗しました';
    let errorType: string | undefined;

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
      errorType = errorData.error_type;
    } catch {
      // JSONパースに失敗した場合はデフォルトメッセージを使用
    }

    throw new ApiError(errorMessage, response.status, errorType);
  }

  // 204 No Content の場合
  if (response.status === 204) {
    return {} as T;
  }

  try {
    return await response.json();
  } catch (error) {
    throw new ApiError('レスポンスのパースに失敗しました', 500);
  }
}

/**
 * GET リクエスト
 */
export async function get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'GET',
  });
}

/**
 * POST リクエスト
 */
export async function post<T>(
  endpoint: string,
  data?: unknown,
  options?: RequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * PUT リクエスト
 */
export async function put<T>(
  endpoint: string,
  data?: unknown,
  options?: RequestOptions
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * DELETE リクエスト
 */
export async function del<T>(endpoint: string, options?: RequestOptions): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'DELETE',
  });
}
