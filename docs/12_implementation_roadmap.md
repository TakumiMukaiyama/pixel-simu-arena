# 実装ロードマップ（1レーンリアルタイムMVP）

最終更新: 2026-02-28

## 方針転換について

既存の9×9盤面・ターン制から、1レーン・リアルタイム制に方針転換しました。
Unity + FastAPIの構成からReact + PixiJS + FastAPIに変更します。

**画像生成機能は維持します**: ユニット生成時に自動的に32×32スプライト + 256×256カード絵を生成し、ギャラリーで閲覧・デッキ編成できるようにします。

## 新しい方針

- **1レーン（0-20の21マス）**: 9×9から大幅に簡素化
- **リアルタイム（200ms tick）**: ターン制から変更
- **React + PixiJS**: Unityから変更
- **シンプルなコスト**: 初期10、上限20、回復+0.6/tick
- **デッキ5体**: 変更なし
- **Mistral AI**: 1秒に1回召喚決定
- **画像生成**: ユニット作成時に1回
- **勝利条件**: 敵拠点HP=0

## 実装ロードマップ

### Phase 1: サーバーエンジン（最優先）

#### 目標
tick処理の実装とAPIの基本動作確認。

#### タスク
1. **データモデル実装**（`server/app/schemas/`）
   - UnitSpec
   - UnitInstance
   - GameState
   - Event
   - API入出力モデル

2. **ゲームエンジン実装**（`server/app/engine/`）
   - `tick.py`: tick処理のメインループ
   - `movement.py`: 移動・攻撃・死亡判定
   - `victory.py`: 拠点ダメージ・勝敗判定
   - `balance.py`: パワースコア・コスト計算

3. **API実装**（`server/app/api/`）
   - `POST /match/start`: 対戦開始
   - `POST /match/tick`: tick実行
   - `POST /match/spawn`: ユニット召喚
   - `POST /units/create`: ユニット生成（フォールバック）

4. **状態管理**（`server/app/storage/`）
   - インメモリセッション管理
   - SQLiteデータベース（ユニット・デッキ保存）

#### 完了条件
- `POST /match/tick`を叩くと、ユニットが移動・攻撃し、GameState + Eventsが返ってくる
- pytest でtick処理のロジックをテスト済み

---

### Phase 2: React + PixiJS統合

#### 目標
最小限の描画で盤面を表示し、tickごとに状態を更新。

#### タスク
1. **Reactセットアップ**（`web/`）
   - Vite + React + TypeScript
   - PixiJS + @pixi/react のインストール

2. **API クライアント**（`web/src/api/`）
   - fetch ベースの API クライアント
   - matchStart, matchTick, matchSpawn のラッパー

3. **PixiJS レーン描画**（`web/src/game/`）
   - レーン（0-20）の背景
   - 拠点（プレイヤー側・AI側）
   - 仮ユニット（丸や四角）
   - イベントアニメーション（攻撃・死亡）

4. **React UI**（`web/src/screens/`）
   - コスト表示
   - 拠点HP表示
   - デッキカード（5枚）
   - 召喚ボタン

5. **ゲームループ**
   - 200msごとに`POST /match/tick`を呼ぶ
   - GameStateを受け取ってPixiJSを更新
   - Eventsを受け取ってアニメーション再生

#### 完了条件
- ブラウザでレーンが表示される
- ユニットが自動的に移動・攻撃する様子が見える
- プレイヤーがデッキからユニットを召喚できる

---

### Phase 3: Mistral統合

#### 目標
AI召喚決定とユニット生成＋画像生成。

#### タスク
1. **AI召喚決定**（`server/app/llm/ai_decide.py`）
   - `POST /match/ai_decide`の実装
   - 盤面状態を見て、次に召喚するユニットを決定
   - システムプロンプト（1レーン用）

2. **ユニット生成**（`server/app/llm/unit_gen.py`）
   - `POST /units/create`の実装
   - プロンプトからUnitSpec JSONを生成
   - パワースコア計算→コスト調整

3. **画像生成**（`server/app/llm/image_gen.py`）
   - **画像プロンプト自動生成**
     - ユニット名・特徴からピクセルアート風のプロンプト生成
     - 例: "pixel art, 32x32, ninja character, black outfit, fast movement, side view"
   - **Mistral Image API（Pixtral Large）で画像生成**
     - 32×32スプライト: ゲーム内ユニット表示用
     - 256×256カード絵: デッキ・ギャラリー表示用
   - **画像保存**
     - ローカルストレージに保存（`server/static/sprites/{unit_id}.png`, `server/static/cards/{unit_id}.png`）
     - URLパス生成（`/static/sprites/{unit_id}.png`）
   - **エラーハンドリング**
     - 画像生成失敗時はプレースホルダー画像を使用
     - リトライロジック（最大3回）

4. **ギャラリー**（`server/app/api/gallery.py`）
   - `GET /gallery/list`: 保存済みユニット一覧

5. **デッキ管理**（`server/app/api/deck.py`）
   - `POST /deck/save`: デッキ保存
   - `GET /deck/{deck_id}`: デッキ取得

#### 完了条件
- AIが1秒に1回、盤面を見てユニット召喚を決定
- プロンプトからユニットを生成できる
- 生成したユニットの画像が表示される
- ギャラリーでユニット一覧を見られる

---

### Phase 4: 最終調整

#### 目標
バランス調整、バグ修正、演出強化。

#### タスク
1. **バランス調整**
   - パワースコア計算式の調整
   - コスト回復レートの調整
   - ユニットステータスの範囲調整

2. **演出強化**
   - 攻撃アニメーション（弾スプライト）
   - ダメージ数字ポップ
   - 死亡エフェクト
   - 拠点ダメージエフェクト

3. **バグ修正**
   - 召喚時のコストチェック
   - 移動範囲のクランプ
   - 攻撃対象の選定（最も近い敵）
   - 勝敗判定の正確性

4. **テスト**
   - エンドツーエンドテスト
   - パフォーマンステスト（200msごとのtick）

#### 完了条件
- ゲームが最後まで正常に動作
- バランスが取れている
- 演出が映える

---

## 推奨実装順序（詳細）

### ステップ1: サーバーのtick処理を通す（1-2日）

1. `server/app/schemas/`にデータモデルを実装
2. `server/app/engine/tick.py`でtick処理を実装
3. `server/app/api/match.py`で`POST /match/start`と`POST /match/tick`を実装
4. pytestで動作確認

### ステップ2: React + Pixiで盤面表示（1-2日）

1. `web/`にVite + React + TypeScriptをセットアップ
2. PixiJSでレーンと仮ユニット（丸）を描画
3. 200msごとに`POST /match/tick`を呼んで状態を更新
4. ブラウザで動作確認

### ステップ3: ユニット召喚（半日）

1. `server/app/api/match.py`で`POST /match/spawn`を実装
2. React UIでデッキカードと召喚ボタンを実装
3. プレイヤーがユニットを召喚できることを確認

### ステップ4: AI召喚決定（半日-1日）

1. `server/app/llm/ai_decide.py`で`POST /match/ai_decide`を実装
2. システムプロンプト（1レーン用）を作成
3. クライアントで1秒に1回AI召喚を呼ぶ

### ステップ5: ユニット生成＋画像生成（1-2日）

1. **ユニット生成API実装**（`server/app/llm/unit_gen.py`）
   - Mistralでユニット名・ステータス生成
   - パワースコア計算→コスト調整
   - 画像プロンプト自動生成

2. **画像生成実装**（`server/app/llm/image_gen.py`）
   - Mistral Image API連携
   - 32×32スプライト + 256×256カード絵の同時生成
   - ローカルストレージへの保存
   - URL生成

3. **ギャラリー・デッキ管理API実装**
   - `GET /gallery/list`: 画像付きユニット一覧
   - `POST /deck/save`: デッキ保存
   - `GET /deck/{deck_id}`: デッキ取得

4. **React UIでユニット生成画面作成**
   - プロンプト入力フォーム
   - 生成中のローディング表示
   - 生成結果（カード絵・ステータス）表示
   - ギャラリー一覧（カードグリッド）
   - デッキ編成UI

---

## 画像生成の重要性

画像生成はこのプロジェクトの**コア機能**です。以下の理由で優先度が高いです:

1. **UXの決定的要素**: ユニットが視覚的に表現されることで、プレイヤーの愛着と理解が深まる
2. **差別化要因**: プロンプトから自動生成される独自のビジュアルがこのゲームの魅力
3. **デッキ編成の動機**: ギャラリーでカード絵を見ることがデッキ編成のモチベーション
4. **生成AIの体験**: Mistralの画像生成能力を直接体験できる

### 実装上の注意点
- ユニット生成APIは画像生成完了までブロッキング（同期処理）
- 画像生成失敗時のフォールバック（プレースホルダー画像）を必ず実装
- ローカルストレージへの保存とURL生成を確実に行う
- ギャラリーUIは早めに実装し、視覚的なフィードバックを得る

### 推奨実装タイミング
Phase 2（React + PixiJS統合）と並行して、ユニット生成＋画像生成の基本動作を確認することを推奨します。これにより、早い段階でビジュアルを確認でき、モチベーション維持につながります。

---

## 既存実装との関係

### 保持するもの
- FastAPI基盤
- Pydanticモデル
- Mistral連携の基本構造
- テストフレームワーク（pytest）

### 破棄・大幅修正するもの
- 9×9盤面 → 1レーン
- ターン制 → リアルタイムtick
- 同時解決システム → シンプルな移動・攻撃
- 視界制限（Fog of War） → なし（MVP）
- スキルシステム → なし（MVP）
- Unity クライアント → React + PixiJS

---

## リスクと対策

### リスク1: tick処理が200msで間に合わない
- **対策**: 処理を最適化、tick間隔を300-500msに延長

### リスク2: PixiJSの学習コスト
- **対策**: @pixi/reactを使って最小限の実装から始める

### リスク3: Mistral APIのレートリミット
- **対策**: フォールバックロジック、ローカルキャッシュ

### リスク4: バランス調整に時間がかかる
- **対策**: パワースコア計算式を柔軟に調整できる設計

---

## 次のアクション

1. `server/app/schemas/`にデータモデルを実装
2. `server/app/engine/tick.py`でtick処理を実装
3. `POST /match/start`と`POST /match/tick`を実装
4. pytestで動作確認
5. React + PixiJSのセットアップ

---

## 参考リンク

- PixiJS: https://pixijs.com/
- @pixi/react: https://github.com/inlet/react-pixi
- Mistral API: https://docs.mistral.ai/
- FastAPI: https://fastapi.tiangolo.com/
