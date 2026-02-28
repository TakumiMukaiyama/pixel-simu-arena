# Changelog

## [0.1.0] - 2026-02-28

### Added

#### Phase 1: 基盤構築
- Pydanticスキーマ（UnitSpec, UnitInstance, GameState, Event, Deck, API）
- バランス計算システム（パワースコア、コスト自動算出）
- PostgreSQL統合（asyncpg使用）
- Alembicマイグレーション
- ユニットテスト（balance.py）

#### Phase 2: ゲームエンジン
- tick処理（200ms単位の状態更新）
- 移動・攻撃ロジック（1次元レーン）
- 拠点ダメージと勝敗判定
- インメモリセッション管理
- ユニットテスト（engine.py）

#### Phase 3: 基本API
- FastAPI初期化（CORS、静的ファイル配信）
- Match API: `/start`, `/tick`, `/spawn`, `/ai_decide`
- Units API: `/create`
- Gallery API: `/list`
- Deck API: `/save`, `/{id}`
- Swagger UI（`/docs`）

#### Phase 4: Mistral連携
- ユニット生成（mistral-large-latest）
  - JSON mode使用
  - プロンプトからステータス生成
  - 自動バランス調整
- AI決定ロジック（mistral-large-latest）
  - 盤面分析
  - 戦略的判断
  - 理由付き応答

#### Phase 5: 画像生成
- Mistral Image API統合（mistral-medium-2505）
- エージェントベース画像生成
- スプライト（32x32）自動生成
- カード絵（256x256）自動生成
- プレースホルダーフォールバック

#### Phase 6: E2Eテスト + AI対戦
- エンドツーエンドテストスクリプト
- AI対戦シミュレーション（60秒間）
- リアルタイムイベントログ
- 統合テスト

#### Phase 7: 最終調整
- カスタム例外クラス
  - MatchNotFoundException
  - DeckNotFoundException
  - UnitNotFoundException
  - InsufficientCostException
  - MatchAlreadyFinishedException
- エラーハンドリング改善
- 詳細ドキュメント
  - README.md
  - DEPLOYMENT.md
  - CHANGELOG.md
- ヘルスチェック拡張（アクティブマッチ数表示）

### Technical Details

#### ゲームバランス
- パワースコア計算式:
  ```
  power = HP×0.4 + ATK×1.4 + (RANGE^1.5)×8 + SPEED×6 + (1/ATK_INTERVAL)×10
  cost = clamp(ceil(power / 20), 1, 8)
  ```
- 射程を指数的に重視（1レーンでは射程が戦略的に重要）

#### API設計
- REST API
- JSON形式
- 非同期処理（asyncio）
- 200msごとのtick処理

#### Mistral API使用
- **ユニット生成**: mistral-large-latest + JSON mode
- **AI決定**: mistral-large-latest + JSON mode
- **画像生成**: mistral-medium-2505 + エージェントツール
- Rate limit対策: リトライ + フォールバック

#### データベース
- PostgreSQL 16
- asyncpg（非同期ドライバ）
- Alembicマイグレーション
- インメモリセッション（スケール時はRedis推奨）

### Performance
- tick処理: <50ms（目標達成）
- ユニット生成: 2-5秒（Mistral API呼び出し）
- 画像生成: 5-10秒（Rate limit時はスキップ）
- 23/23 ユニットテスト合格

### Known Limitations
- セッション管理: インメモリ（サーバー再起動で消失）
- 画像生成: Rate limit頻発（プレースホルダー使用）
- ゲームバランス: 膠着状態になりやすい（調整予定）

### Dependencies
- fastapi>=0.100.0
- uvicorn[standard]>=0.23.0
- pydantic>=2.0.0
- mistralai>=1.0.0
- asyncpg>=0.29.0
- alembic>=1.13.0
- pillow>=10.0.0

### Future Enhancements
- WebSocket対応（リアルタイム通信）
- Redis統合（セッション管理）
- ユーザー認証（JWT）
- マッチ履歴保存
- ランキングシステム
- バランス調整UI
- 画像キャッシング
- CDN統合

### Contributors
- Pixel Simulation Arena チーム
