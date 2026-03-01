# Pixel Simulation Arena - Web Frontend

React + PixiJS + TypeScript で実装されたリアルタイム1レーンバトルゲーム。

## 技術スタック

- **React**: 18.3.1
- **TypeScript**: 5.4.5
- **Vite**: 5.2.0
- **PixiJS**: 8.0.0
- **@pixi/react**: 7.1.2
- **React Router**: 6.22.0

## セットアップ

```bash
cd web
npm install
```

## 開発サーバー起動

```bash
npm run dev
```

ブラウザで http://localhost:5173 を開きます。

## ビルド

```bash
npm run build
```

ビルド結果は `dist/` ディレクトリに出力されます。

## プレビュー

```bash
npm run preview
```

## 画面構成

### ホーム画面 (/)
- タイトル表示
- ゲームルール・操作方法の説明
- 各画面へのナビゲーション

### ゲーム画面 (/game)
- リアルタイム1レーンバトル
- PixiJSでレーン、拠点、ユニットを描画
- デッキカードからユニット召喚
- コストは時間経過で自動回復
- 勝敗判定

### ギャラリー画面 (/gallery)
- 全ユニットの一覧表示
- ユニット詳細モーダル
- ステータス確認

### デッキ編成画面 (/deck)
- 5体のユニットを選択
- デッキ保存機能
- ドラッグ不要のシンプルUI

## API統合

バックエンドAPIと完全統合済み。`src/api/realApi.ts` を使用します。

- `matchStart(playerDeckId, aiDeckId?)`: 対戦開始
- `matchTick(matchId)`: ゲーム状態更新（200msごと）
- `matchSpawn(matchId, side, unitSpecId)`: ユニット召喚
- `matchAiDecide(matchId)`: AI判断（自律動作）
- `unitsCreate(prompt)`: ユニット作成
- `galleryList(limit?, offset?)`: ユニット一覧取得
- `deckSave(name, unitSpecIds)`: デッキ保存
- `deckList()`: デッキ一覧
- `deckGet(deckId)`: デッキ取得

**注意**: バックエンドAPI（ポート8000）が必須です。

## ファイル構成

```
web/
├── src/
│   ├── types/          # 型定義
│   │   └── game.ts
│   ├── api/            # APIクライアント
│   │   ├── client.ts     # HTTPクライアント基盤
│   │   ├── errors.ts     # エラーハンドリング
│   │   ├── realApi.ts    # バックエンドAPI実装
│   │   └── index.ts      # APIエクスポート
│   ├── config/         # 環境設定
│   │   └── env.ts
│   ├── hooks/          # カスタムフック
│   │   └── useApi.ts
│   ├── game/           # PixiJSゲーム描画
│   │   └── GameScene.tsx
│   ├── screens/        # 画面コンポーネント
│   │   ├── HomeScreen.tsx
│   │   ├── GameScreen.tsx
│   │   ├── GalleryScreen.tsx
│   │   └── DeckScreen.tsx
│   ├── components/     # 共通コンポーネント
│   │   ├── DeckCard.tsx
│   │   └── StatsDisplay.tsx
│   ├── App.tsx         # ルーティング
│   ├── main.tsx        # エントリーポイント
│   └── index.css       # グローバルスタイル
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## ゲームルール

1. **1レーンバトル**: 21マス（0-20）の直線レーンでバトル
2. **拠点HP**: プレイヤー・AI それぞれ100HP
3. **コスト**: 最大20、時間経過で自動回復（200ms = +0.6）
4. **ユニット召喚**: デッキカードをクリックで召喚
5. **勝利条件**: 相手の拠点HPを0にする

## 注意事項

- バックエンドAPIは未実装（モックAPI使用）
- 画像は幾何学形（色付き円）で表現
- AI対戦は簡易ロジック（モック）
- セーブデータは永続化されません

## トラブルシューティング

### PixiJSが動かない
```bash
rm -rf node_modules
npm install
npm run dev
```

### TypeScriptエラー
```bash
npm run build
```
でエラー内容を確認してください。

### 画面が真っ白
ブラウザコンソール（F12）でエラーを確認してください。

## ライセンス

MIT
