# Vercel フロントエンドデプロイガイド（代替案）

Railwayでフロントエンドのデプロイが難しい場合、**Vercelでフロントエンドのみデプロイ**する方法を推奨します。

## メリット

- ✅ 設定が非常に簡単
- ✅ Vercelは静的サイトに最適化されている
- ✅ 無料プランで十分
- ✅ CDNによる高速配信
- ✅ 自動的にHTTPS対応

## 構成

- **バックエンド**: Railway
- **フロントエンド**: Vercel

## デプロイ手順

### 1. バックエンドをRailwayにデプロイ

1. [Railway Dashboard](https://railway.app/dashboard) にアクセス
2. "New Project" → "Empty Project"
3. "+ New" → "Service" → "GitHub Repo"
4. リポジトリを選択
5. **Settings** → **Source** → **Root Directory**: `server`
6. **Variables** タブで環境変数を設定:
   ```
   MISTRAL_API_KEY=your_key
   PIXELLAB_API_KEY=your_key
   DATABASE_URL=sqlite:///./data/pixel_arena.db
   ENVIRONMENT=production
   CORS_ORIGINS=*
   ```

   **注意**: 後でVercelのURLが分かったら、`CORS_ORIGINS` を更新します。

7. デプロイ完了後、URLをコピー（例: `https://backend-production-xxxx.up.railway.app`）

### 2. フロントエンドをVercelにデプロイ

1. [Vercel Dashboard](https://vercel.com/dashboard) にアクセス
2. "Add New..." → "Project" をクリック
3. GitHubリポジトリをインポート
4. **Framework Preset**: `Vite` を選択
5. **Root Directory**: `web` を設定
6. **Build Command**: `npm run build`
7. **Output Directory**: `dist`
8. **Environment Variables** セクションで追加:
   - **Key**: `VITE_API_BASE_URL`
   - **Value**: `https://backend-production-xxxx.up.railway.app` （RailwayのURL）
9. "Deploy" をクリック

### 3. CORS設定の更新

Vercelのデプロイが完了したら:

1. VercelのURLをコピー（例: `https://pixel-simu-arena.vercel.app`）
2. Railwayに戻る
3. バックエンドサービスの **Variables** タブ
4. `CORS_ORIGINS` を更新:
   ```
   CORS_ORIGINS=https://pixel-simu-arena.vercel.app
   ```
5. サービスを再デプロイ

### 4. 動作確認

VercelのURLにアクセスして、アプリケーションが動作することを確認します。

## 環境変数まとめ

### Railway（バックエンド）
```bash
MISTRAL_API_KEY=your_mistral_key
PIXELLAB_API_KEY=your_pixellab_key
DATABASE_URL=sqlite:///./data/pixel_arena.db
ENVIRONMENT=production
CORS_ORIGINS=https://your-app.vercel.app
HOST=0.0.0.0
PORT=8000
```

### Vercel（フロントエンド）
```bash
VITE_API_BASE_URL=https://backend-production-xxxx.up.railway.app
```

## カスタムドメインの設定（オプション）

### Vercelでカスタムドメイン設定

1. Vercelプロジェクトの **Settings** → **Domains**
2. ドメインを追加
3. DNSレコードを設定

### RailwayのCORS更新

カスタムドメインを追加した場合、RailwayのCORS設定を更新:
```bash
CORS_ORIGINS=https://your-app.vercel.app,https://your-custom-domain.com
```

## トラブルシューティング

### フロントエンドからAPIを呼び出せない

**症状**: CORS エラー

**解決方法**:
1. RailwayのバックエンドURLが正しいか確認
2. VercelのビルドログでVITE_API_BASE_URLが設定されているか確認
3. RailwayのCORS_ORIGINSにVercelのURLが含まれているか確認

### ビルドエラー

**症状**: Vercelでビルドが失敗

**解決方法**:
1. Root Directoryが `web` になっているか確認
2. Build Commandが `npm run build` になっているか確認
3. Output Directoryが `dist` になっているか確認

## コスト

- **Railway（バックエンド）**: 無料プラン $5/月クレジット → 約 $2-3/月
- **Vercel（フロントエンド）**: 完全無料（Hobbyプラン）
- **合計**: 約 $2-3/月

## 自動デプロイ

GitHubにpushすると、RailwayとVercel両方が自動的にデプロイされます。

## 参考リンク

- [Vercel Documentation](https://vercel.com/docs)
- [Vite on Vercel](https://vercel.com/guides/deploying-vite-with-vercel)
- [Railway Documentation](https://docs.railway.app/)
