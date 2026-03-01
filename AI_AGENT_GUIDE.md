# AI対戦相手エージェント実装ガイド

## 概要

対戦相手AIは、Mistral LLMを使用した完全自律型エージェントとして実装されています。

## AIのデッキ構成

**AIはプレイヤーと同じデッキを使用します**。

これにより:
- ✅ 純粋な戦略対決が可能
- ✅ AIの判断力を公平に評価できる
- ✅ 同じユニット構成でどちらが優れた戦術を取れるかの勝負

将来的には以下のオプションも検討可能:
- ランダムなデッキ選択
- ユーザーがAIのデッキも選択
- 固定の強力なAIデッキ

## AI動作フロー

### 1. 戦況把握（自動）
AIは600msごと（約3tick）に以下の情報を収集・分析します:

- **コスト状況**: 現在のコスト、最大コスト
- **拠点HP**: 自分と敵の拠点HP
- **フィールド状況**:
  - 自分のユニット数、位置、HP、攻撃力、射程
  - 敵ユニット数、位置、HP、攻撃力、射程
- **召喚可能なユニット**: コスト範囲内のユニット一覧

### 2. 戦術判断（Mistral LLM）
収集した情報をMistral LLM（`mistral-large-latest`）に送信し、以下を判断:

```
戦術的考慮事項:
1. 攻守バランス
2. 敵構成への対策（例: 高火力敵にはタンクを出す）
3. コストの効率的管理
4. タイミング（例: 重要な瞬間のためにコストを温存）
```

### 3. 行動実行（自動）
Mistralの判断に基づき、自動的にユニットを召喚:

- **召喚する場合**: `spawn_unit_spec_id`が返される → 自動召喚
- **待機する場合**: `spawn_unit_spec_id`がnull → コスト温存
- **判断理由**: `reason`フィールドに戦術的理由が記載

### 4. フォールバック戦略
Mistral APIが失敗した場合の貪欲戦略:
- 最も高コストのユニットを召喚

## 実装アーキテクチャ

### バックエンド（FastAPI）

#### AIエンドポイント
```python
POST /match/ai_decide
Request: { "match_id": "uuid" }
Response: {
  "spawn_unit_spec_id": "uuid" or null,
  "wait_ms": 600,
  "reason": "Brief tactical reason"
}
```

#### AI判断ロジック（`app/llm/ai_decide.py`）
1. `ai_decide_spawn()` - メイン関数
   - デッキからコスト範囲内のユニットを取得
   - ゲーム状態サマリー作成
   - Mistral LLM呼び出し
   - レスポンス検証・返却

2. `_create_game_summary()` - 戦況サマリー作成
   - 時間、コスト、HP
   - フィールド上の全ユニット詳細
   - 召喚可能なユニット一覧

3. `_call_mistral_for_decision()` - Mistral API呼び出し
   - システムプロンプト: ゲームルール、戦術的考慮事項
   - ユーザープロンプト: 現在の戦況サマリー
   - JSON形式レスポンス強制（`response_format: json_object`）
   - リトライロジック（最大2回）

4. `_fallback_decision()` - フォールバック戦略
   - 最高コストユニット選択

### フロントエンド（React）

#### ゲームループ統合（`GameScreen.tsx`）
```typescript
// 200msごとにtick実行
const result = await matchTick(matchId);

// 600msごとにAI判断（約3tick）
if (aiDecisionTimerRef.current >= 600) {
  const aiDecision = await matchAiDecide(matchId);

  // AIが召喚を決定した場合
  if (aiDecision.spawn_unit_spec_id) {
    await matchSpawn(matchId, 'ai', aiDecision.spawn_unit_spec_id);
    console.log(`AI spawned unit: ${aiDecision.reason}`);
  } else {
    console.log(`AI waiting: ${aiDecision.reason}`);
  }
}
```

#### AI判断のタイミング
- ゲームループは200ms間隔
- AI判断は600ms間隔（レスポンス時間を考慮）
- 非同期で実行（ゲームループをブロックしない）
- エラー時はログのみ（ゲーム継続）

## AI動作の確認方法

### 1. コンソールログ
ブラウザのDevToolsコンソールを開くと、AIの判断が表示されます:

```
AI spawned unit: Countering high damage enemies with tank
AI waiting: Saving cost for critical moment
AI spawned unit: Building offensive pressure
```

### 2. 実際のプレイで確認
- ゲーム画面に移動
- デッキを選択してゲーム開始
- 何もせずに待機
- **AIが自動的にユニットを召喚し始める**（約600ms間隔）

### 3. AIの思考プロセス
AIは以下のような戦術を実行します:
- 敵ユニットが多い場合: タンクや範囲攻撃を出す
- コストが低い場合: 待機してコスト回復
- 拠点が危険な場合: 防衛優先
- 優勢な場合: 攻撃的なユニットを出す

## AI戦術の例

### シナリオ1: 敵の攻勢
```json
{
  "spawn_unit_spec_id": "tank-unit-id",
  "reason": "Spawning tank to defend base from 3 enemy units"
}
```

### シナリオ2: コスト温存
```json
{
  "spawn_unit_spec_id": null,
  "reason": "Saving cost (5.2/20) for stronger unit"
}
```

### シナリオ3: 反撃
```json
{
  "spawn_unit_spec_id": "attacker-unit-id",
  "reason": "Enemy base low (30 HP), pushing for victory"
}
```

## カスタマイズ

### AI判断頻度の変更
`GameScreen.tsx`で変更可能:

```typescript
// 600msごと → 1000msごとに変更
if (aiDecisionTimerRef.current >= 1000) {
  // ...
}
```

### AI戦略の変更
`server/app/llm/ai_decide.py`の`AI_DECISION_SYSTEM_PROMPT`を編集:

```python
AI_DECISION_SYSTEM_PROMPT = """You are an AGGRESSIVE AI player...

Strategy considerations:
1. Always push aggressively
2. Prioritize high damage units
3. Never save cost
...
"""
```

### フォールバック戦略の変更
`_fallback_decision()`を編集:

```python
# 最高コスト → ランダム選択に変更
selected = random.choice(available_units)
```

## トラブルシューティング

### AIが動作しない
1. **Mistral APIキーを確認**
   ```bash
   # server/.env
   MISTRAL_API_KEY=your-api-key
   ```

2. **バックエンドログを確認**
   ```bash
   # サーバーコンソールにエラーが表示される
   AI decision error: ...
   ```

3. **フロントエンドコンソールを確認**
   ```javascript
   // AIのログが表示されるはず
   AI spawned unit: ...
   AI waiting: ...
   ```

### AIが同じユニットしか出さない
- デッキの構成を確認（複数の戦略的なユニットが必要）
- Mistralのtemperatureを調整（`ai_decide.py`で`temperature=0.8` → `1.0`）

### AI判断が遅い
- Mistral APIのレスポンス時間が原因
- 判断頻度を下げる（600ms → 1000ms）
- または`max_tokens`を減らす（300 → 150）

## パフォーマンス最適化

### 現在の設定
- AI判断: 600msごと
- Mistral API: `mistral-large-latest`, temperature=0.8, max_tokens=300
- リトライ: 最大2回

### 推奨設定
- **高速プレイ**: 判断間隔1000ms、`mistral-small-latest`使用
- **高品質判断**: 判断間隔600ms、`mistral-large-latest`使用（現在の設定）
- **コスト削減**: 判断間隔1000ms、max_tokens=150

## まとめ

AIは完全に自律動作します:
- ✅ 戦況把握（フィールド、コスト、HP）
- ✅ Mistral LLMによる戦術判断
- ✅ 自動ユニット召喚
- ✅ エラー時のフォールバック戦略
- ✅ ゲームループと統合

プレイヤーは何もせずに、AIが自動的に対戦相手として機能します。
