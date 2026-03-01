# フロントエンド・バックエンド統合ガイド

## 概要

このドキュメントは、バックエンド（FastAPI on port 8000）とフロントエンド（React on port 5173）の統合実装の完了を示します。

## 実装内容

### 1. 環境設定

#### 環境変数ファイル
- `web/.env` - 実API使用の設定
  ```
  VITE_API_BASE_URL=http://localhost:8000
  VITE_USE_REAL_API=true
  ```
- `web/.env.example` - テンプレート（モックAPI使用）

#### 環境変数アクセス
- `web/src/config/env.ts` - タイプセーフな環境変数アクセス

### 2. APIクライアント層

#### HTTPクライアント基盤
- `web/src/api/client.ts`
  - リトライロジック（最大3回、指数バックオフ）
  - タイムアウト処理（デフォルト30秒）
  - エラーハンドリングミドルウェア

#### エラーハンドリング
- `web/src/api/errors.ts`
  - カスタムエラークラス（ApiError, NetworkError, TimeoutError）
  - バックエンド例外からユーザー向けメッセージへのマッピング

#### API実装
- `web/src/api/realApi.ts` - 実APIとの通信
  - `matchStart(playerDeckId, aiDeckId?)` - ゲーム開始
  - `matchTick(matchId)` - ゲーム状態更新
  - `matchSpawn(matchId, side, unitSpecId)` - ユニット召喚
  - `matchAiDecide(matchId)` - AI判断（自律動作）
  - `unitsCreate(prompt)` - ユニット作成（新規）
  - `galleryList(limit?, offset?)` - ギャラリー一覧
  - `deckSave(name, unitSpecIds)` - デッキ保存
  - `deckList()` - デッキ一覧
  - `deckGet(deckId)` - デッキ取得

- `web/src/api/index.ts` - APIエクスポート

### 3. UIコンポーネント

#### カスタムフック
- `web/src/hooks/useApi.ts`
  - loading/error状態管理
  - 標準化されたエラーハンドリング

#### エラー通知
- `web/src/components/ErrorNotification.tsx`
  - トースト形式のエラー表示
  - 自動消去（5秒）
  - ErrorProviderコンテキスト

#### デッキ選択
- `web/src/components/DeckSelector.tsx`
  - デッキ一覧表示
  - デッキ選択UI
  - ゲーム開始フロー

#### ユニット作成（新規）
- `web/src/components/UnitCreator.tsx`
  - プロンプト入力フォーム
  - Mistral API呼び出し
  - 生成結果プレビュー
  - エラーハンドリング

### 4. 画面統合

#### ゲーム画面
- `web/src/screens/GameScreen.tsx`
  - デッキ選択モーダル統合
  - 適応型ティックループ（レスポンス時間を考慮）
  - デバウンス付きユニット召喚
  - グローバルエラー通知

#### ギャラリー画面
- `web/src/screens/GalleryScreen.tsx`
  - 実APIからのユニット読み込み
  - ユニット作成ボタン追加
  - UnitCreatorコンポーネント統合
  - 作成後のリフレッシュ

#### デッキ編成画面
- `web/src/screens/DeckScreen.tsx`
  - 実APIでのデッキ保存
  - バリデーション（5枚必須）
  - 成功/エラー通知

#### アプリケーションルート
- `web/src/App.tsx`
  - ErrorProviderでアプリ全体をラップ
  - グローバルエラーハンドリング

### 5. バックエンド拡張

#### デッキAPI
- `server/app/api/deck.py`
  - `GET /deck/list` エンドポイント追加
  - ページネーション対応（limit/offset）

### 6. 型定義の更新

- `web/src/types/game.ts`
  - GameStateに追加フィールド:
    - `max_cost: number`
    - `cost_recovery_per_tick: number`
    - `player_deck_id: string`
    - `ai_deck_id: string`
  - ApiError型定義追加

## 起動手順

### 1. PostgreSQL起動
```bash
# Dockerを使用する場合
docker-compose up -d postgres
```

### 2. バックエンド起動
```bash
cd server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. フロントエンド起動
```bash
cd web
npm run dev
```

### 4. 動作確認
- バックエンドヘルスチェック: http://localhost:8000/health
- フロントエンド: http://localhost:5173

## 使用方法

### ギャラリー画面でユニット作成
1. ギャラリー画面に移動
2. 「新しいユニットを作成」ボタンをクリック
3. プロンプト入力（例: "fast ninja with high speed"）
4. 「ユニットを生成」をクリック
5. 10秒程度待機（Mistral APIで画像とステータス生成）
6. 生成されたユニットがギャラリーに追加される

### デッキ編成
1. デッキ編成画面に移動
2. ギャラリーから5枚のユニットを選択
3. デッキ名を入力
4. 「デッキを保存」をクリック

### ゲームプレイ
1. ゲーム画面に移動
2. デッキ選択モーダルでデッキを選択
3. 「ゲーム開始」をクリック
4. 自動的にティックループが開始
5. **AIは同じデッキを使用して自動的に対戦相手として動作**
6. デッキカードをクリックしてユニット召喚
7. 勝敗が決まるまで待機

**注意**: AIはプレイヤーと同じデッキを使用します。純粋な戦略対決です。

## 必須要件

バックエンドAPIが常に必要です（モックAPIは削除済み）:

- PostgreSQL起動
- FastAPIサーバー起動（ポート8000）
- Mistral API キー設定

## エラーハンドリング

### レイヤー1: APIクライアント
- ネットワークエラー
- HTTPエラーレスポンス
- タイムアウト

### レイヤー2: API関数
- API固有のエラー
- コンテキスト追加

### レイヤー3: 画面コンポーネント
- UI状態更新
- ユーザー通知
- リカバリーアクション

### レイヤー4: グローバルハンドラー
- 未キャッチエラー
- クリティカルエラー表示

## パフォーマンス目標

- ギャラリー読み込み: < 2秒
- ユニット作成: < 10秒（Mistral API含む）
- ゲーム開始: < 1秒
- ティックレスポンス: < 200ms
- スポーンレスポンス: < 500ms

## トラブルシューティング

### CORS エラー
- バックエンドのCORS設定を確認
- `server/app/main.py` で `http://localhost:5173` が許可されているか確認

### 環境変数が反映されない
- フロントエンドを再起動
- `.env` ファイルの構文を確認
- ブラウザのキャッシュをクリア

### API接続エラー
- バックエンドが起動しているか確認
- ポート8000が使用可能か確認
- ファイアウォール設定を確認

### データベース接続エラー
- PostgreSQLが起動しているか確認
- 接続情報が正しいか確認（`server/.env`）

## 今後の改善提案

1. WebSocket接続（ポーリングの代わり）
2. リクエストキャッシング
3. オプティミスティックUI更新
4. オフラインモード
5. アナリティクス
6. レート制限

## 参考

- バックエンドAPI仕様: `server/README.md`
- フロントエンド設定: `web/README.md`
- 環境変数: `web/.env.example`
