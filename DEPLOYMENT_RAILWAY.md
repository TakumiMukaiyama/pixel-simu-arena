# Railway デプロイガイド

このガイドでは、Pixel Simulation ArenaをRailwayにデプロイする手順を説明します。

## 概要

このプロジェクトはmonorepo構成で、以下の2つのサービスとしてデプロイします:
- **Backend**: FastAPI (Python) サーバー
- **Frontend**: React + Vite (静的サイト)

## 前提条件

- [Railway](https://railway.app/) アカウント（GitHubでログイン可能）
- Mistral APIキー（[Mistral Console](https://console.mistral.ai/)で取得）
- このリポジトリがGitHubにプッシュされていること

## デプロイ手順

### 1. Railwayプロジェクトの作成

1. [Railway Dashboard](https://railway.app/dashboard) にアクセス
2. "New Project" をクリック
3. "Deploy from GitHub repo" を選択
4. このリポジトリ (`pixel-simu-arena`) を選択

### 2. バックエンドサービスの設定

#### 2.1 サービスの追加

1. プロジェクト画面で "New" → "GitHub Repo" をクリック
2. 同じリポジトリを選択
3. サービス名を `backend` に変更

#### 2.2 ルートディレクトリの設定

1. バックエンドサービスの "Settings" タブを開く
2. "Service" セクションで以下を設定:
   - **Root Directory**: `server`
   - **Dockerfile Path**: `server/Dockerfile`

#### 2.3 環境変数の設定

"Variables" タブで以下の環境変数を追加:

```bash
MISTRAL_API_KEY=your_mistral_api_key_here
DATABASE_URL=sqlite:///./data/pixel_arena.db
ENVIRONMENT=production
```

#### 2.4 ボリュームの設定（永続化）

画像とデータベースを永続化するため、ボリュームを追加:

1. "Settings" → "Volumes" をクリック
2. 以下のボリュームを追加:
   - **Mount Path**: `/app/static`
   - **Mount Path**: `/app/data`

#### 2.5 デプロイ

設定完了後、自動的にデプロイが開始されます。
"Deployments" タブでログを確認できます。

#### 2.6 URLの確認

デプロイ完了後、"Settings" → "Networking" で公開URLを確認します。
例: `https://backend-production-xxxx.up.railway.app`

### 3. フロントエンドサービスの設定

#### 3.1 サービスの追加

1. プロジェクト画面で "New" → "GitHub Repo" をクリック
2. 同じリポジトリを選択
3. サービス名を `frontend` に変更

#### 3.2 ルートディレクトリの設定

1. フロントエンドサービスの "Settings" タブを開く
2. "Service" セクションで以下を設定:
   - **Root Directory**: `web`
   - **Dockerfile Path**: `web/Dockerfile`

#### 3.3 環境変数の設定

"Variables" タブで以下の環境変数を追加:

```bash
VITE_API_BASE_URL=https://backend-production-xxxx.up.railway.app
```

**重要**: `backend-production-xxxx.up.railway.app` を実際のバックエンドURLに置き換えてください。

#### 3.4 デプロイ

設定完了後、自動的にデプロイが開始されます。

#### 3.5 URLの確認

デプロイ完了後、"Settings" → "Networking" で公開URLを確認します。
例: `https://frontend-production-yyyy.up.railway.app`

このURLでアプリケーションにアクセスできます。

### 4. CORSの設定確認

バックエンドのCORS設定を確認します。

`server/app/main.py` で以下のような設定があることを確認:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のドメインに制限推奨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## デプロイ後の確認

### 1. バックエンドの動作確認

ブラウザで以下にアクセス:
```
https://backend-production-xxxx.up.railway.app/docs
```

Swagger UIが表示されれば成功です。

### 2. フロントエンドの動作確認

ブラウザでフロントエンドURLにアクセス:
```
https://frontend-production-yyyy.up.railway.app
```

アプリケーションが表示されれば成功です。

### 3. 動作テスト

1. ユニット作成画面でプロンプトを入力
2. ユニットが生成されることを確認
3. デッキを作成して対戦を開始
4. ゲームが正常に動作することを確認

## トラブルシューティング

### ビルドエラー

**症状**: デプロイが失敗する

**解決方法**:
1. "Deployments" タブでログを確認
2. 依存関係の問題の場合:
   - `server/pyproject.toml` または `web/package.json` を確認
   - ローカルでビルドが通るか確認: `docker build -t test .`

### CORS エラー

**症状**: ブラウザコンソールに "CORS policy" エラーが表示される

**解決方法**:
1. バックエンドの環境変数に `FRONTEND_URL` を追加:
   ```
   FRONTEND_URL=https://frontend-production-yyyy.up.railway.app
   ```
2. `server/app/main.py` のCORS設定を更新:
   ```python
   allow_origins=[os.getenv("FRONTEND_URL", "*")]
   ```

### APIエラー

**症状**: フロントエンドからAPIを呼び出せない

**解決方法**:
1. フロントエンドの環境変数 `VITE_API_BASE_URL` が正しいか確認
2. バックエンドが起動しているか確認
3. ネットワークタブでリクエストURLを確認

### 画像が表示されない

**症状**: ユニット画像が表示されない

**解決方法**:
1. バックエンドのボリュームが正しくマウントされているか確認
2. `/static` ディレクトリへの書き込み権限を確認
3. ログで画像生成エラーがないか確認

### データベースがリセットされる

**症状**: デプロイごとにデータが消える

**解決方法**:
1. バックエンドの "Settings" → "Volumes" でボリュームが設定されているか確認
2. `/app/data` にマウントされているか確認

## 自動デプロイの設定

GitHubにpushすると自動的にデプロイされます。

### ブランチの設定

特定のブランチのみデプロイする場合:

1. サービスの "Settings" → "Source" を開く
2. "Branch" で `main` または `production` を指定

### デプロイトリガーの設定

1. "Settings" → "Deploys" を開く
2. "Deploy on Push" を有効化

## コスト管理

Railwayの無料プラン:
- $5/月の無料クレジット
- 使用量に応じた従量課金

**推定コスト**:
- バックエンド（小規模）: ~$2-3/月
- フロントエンド（静的）: ~$1/月
- 合計: ~$3-4/月（無料枠内）

使用量は Dashboard の "Usage" で確認できます。

## カスタムドメインの設定（オプション）

独自ドメインを使用する場合:

1. サービスの "Settings" → "Networking" を開く
2. "Custom Domain" をクリック
3. ドメインを入力してDNS設定を行う

## バックアップ

### データベースバックアップ

1. Railway CLIをインストール:
   ```bash
   npm install -g @railway/cli
   ```

2. ログイン:
   ```bash
   railway login
   ```

3. バックエンドサービスに接続:
   ```bash
   railway link
   railway service backend
   ```

4. データベースをダウンロード:
   ```bash
   railway run bash
   # コンテナ内で
   sqlite3 data/pixel_arena.db .dump > backup.sql
   exit
   ```

### 画像バックアップ

同様にボリュームの内容をダウンロードできます。

## 参考リンク

- [Railway Documentation](https://docs.railway.app/)
- [Railway GitHub Integration](https://docs.railway.app/deploy/github-triggers)
- [Railway Volumes](https://docs.railway.app/reference/volumes)
- [Mistral API Documentation](https://docs.mistral.ai/)

## サポート

問題が発生した場合:
1. [Railway Discord](https://discord.gg/railway) で質問
2. [Railway Community](https://community.railway.app/) でサポート
3. GitHubのIssueで報告
