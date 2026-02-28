"""
エンドツーエンドテスト

ユニット生成からAI対戦までの完全なフローをテストする。
"""
import time
import requests
import json

BASE_URL = "http://localhost:8000"


def print_section(title):
    """セクションタイトルを表示"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def create_units():
    """5体のユニットを生成"""
    print_section("STEP 1: Creating 5 units")

    prompts = [
        "fast ninja assassin",
        "heavy armored tank",
        "long range archer sniper",
        "balanced warrior fighter",
        "support healer with magic"
    ]

    unit_ids = []
    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}/5] Creating: {prompt}")
        response = requests.post(
            f"{BASE_URL}/units/create",
            json={"prompt": prompt}
        )

        if response.status_code == 200:
            unit = response.json()["unit_spec"]
            unit_ids.append(unit["id"])
            print(f"  ✓ {unit['name']}: cost={unit['cost']}, hp={unit['max_hp']}, atk={unit['atk']}, speed={unit['speed']}")
        else:
            print(f"  ✗ Failed: {response.status_code}")
            return None

        time.sleep(1)  # Rate limit対策

    return unit_ids


def create_deck(unit_ids, name):
    """デッキを作成"""
    print_section(f"STEP 2: Creating deck '{name}'")

    response = requests.post(
        f"{BASE_URL}/deck/save",
        json={
            "name": name,
            "unit_spec_ids": unit_ids
        }
    )

    if response.status_code == 200:
        deck_id = response.json()["deck_id"]
        print(f"✓ Deck created: {deck_id}")
        return deck_id
    else:
        print(f"✗ Failed: {response.status_code}")
        return None


def start_match(player_deck_id, ai_deck_id):
    """マッチを開始"""
    print_section("STEP 3: Starting match")

    response = requests.post(
        f"{BASE_URL}/match/start",
        json={
            "player_deck_id": player_deck_id,
            "ai_deck_id": ai_deck_id
        }
    )

    if response.status_code == 200:
        data = response.json()
        match_id = data["match_id"]
        game_state = data["game_state"]
        print(f"✓ Match started: {match_id}")
        print(f"  Player: HP={game_state['player_base_hp']}, Cost={game_state['player_cost']:.1f}")
        print(f"  AI:     HP={game_state['ai_base_hp']}, Cost={game_state['ai_cost']:.1f}")
        return match_id, game_state
    else:
        print(f"✗ Failed: {response.status_code}")
        return None, None


def spawn_unit(match_id, side, unit_spec_id):
    """ユニットを召喚"""
    response = requests.post(
        f"{BASE_URL}/match/spawn",
        json={
            "match_id": match_id,
            "side": side,
            "unit_spec_id": unit_spec_id
        }
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"  ✗ Spawn failed: {response.status_code}")
        return None


def ai_decide(match_id):
    """AIの召喚決定"""
    response = requests.post(
        f"{BASE_URL}/match/ai_decide",
        json={"match_id": match_id}
    )

    if response.status_code == 200:
        return response.json()
    else:
        return None


def process_tick(match_id):
    """tick処理を実行"""
    response = requests.post(
        f"{BASE_URL}/match/tick",
        json={"match_id": match_id}
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"  ✗ Tick failed: {response.status_code}")
        return None


def run_battle(match_id, game_state, player_deck_id, ai_deck_id):
    """バトルを実行"""
    print_section("STEP 4: Running battle")

    # デッキからユニット情報を取得
    player_deck_response = requests.get(f"{BASE_URL}/deck/{player_deck_id}")
    player_units = player_deck_response.json()["units"] if player_deck_response.status_code == 200 else []

    tick_count = 0
    max_ticks = 300  # 60秒 (200ms * 300 = 60s)
    last_ai_decide_time = 0

    print(f"Starting battle simulation (max {max_ticks} ticks = {max_ticks * 0.2}s)...\n")

    while tick_count < max_ticks:
        # tick処理
        tick_response = process_tick(match_id)
        if not tick_response:
            break

        game_state = tick_response["game_state"]
        events = tick_response["events"]
        tick_count += 1

        # 1秒ごとに状態を表示
        if tick_count % 5 == 0:
            time_sec = game_state["time_ms"] / 1000
            player_units_count = len([u for u in game_state["units"] if u["side"] == "player"])
            ai_units_count = len([u for u in game_state["units"] if u["side"] == "ai"])

            print(f"[{time_sec:5.1f}s] Player: HP={game_state['player_base_hp']:3d} Cost={game_state['player_cost']:4.1f} Units={player_units_count} | "
                  f"AI: HP={game_state['ai_base_hp']:3d} Cost={game_state['ai_cost']:4.1f} Units={ai_units_count}")

        # イベント表示（重要なもののみ）
        for event in events:
            if event["type"] == "BASE_DAMAGE":
                side = event["data"]["side"]
                damage = event["data"]["damage"]
                remaining = event["data"]["remaining_hp"]
                print(f"  ⚔️  {side.upper()} base damaged! -{damage} HP (remaining: {remaining})")
            elif event["type"] == "DEATH":
                side = event["data"]["side"]
                print(f"  💀 {side} unit died at pos {event['data']['pos']}")

        # 勝敗判定
        if game_state["winner"]:
            print(f"\n🏆 {game_state['winner'].upper()} WINS!")
            print(f"   Final scores:")
            print(f"   Player: HP={game_state['player_base_hp']}")
            print(f"   AI:     HP={game_state['ai_base_hp']}")
            break

        # プレイヤー召喚（コストが十分なら）
        if game_state["player_cost"] >= 3 and player_units:
            # コスト範囲内のユニットから選択
            available = [u for u in player_units if u["cost"] <= game_state["player_cost"]]
            if available:
                # ランダムに選択
                import random
                unit_to_spawn = random.choice(available)
                spawn_response = spawn_unit(match_id, "player", unit_to_spawn["id"])
                if spawn_response:
                    print(f"  🔵 Player spawned: {unit_to_spawn['name']} (cost {unit_to_spawn['cost']})")

        # AI召喚決定（1秒に1回）
        current_time = game_state["time_ms"]
        if current_time - last_ai_decide_time >= 1000:
            ai_decision = ai_decide(match_id)
            if ai_decision and ai_decision.get("spawn_unit_spec_id"):
                spawn_response = spawn_unit(match_id, "ai", ai_decision["spawn_unit_spec_id"])
                if spawn_response:
                    print(f"  🔴 AI spawned unit (reason: {ai_decision.get('reason', 'N/A')})")
            last_ai_decide_time = current_time

        # 短い待機（リアルタイム感）
        time.sleep(0.05)

    if tick_count >= max_ticks:
        print(f"\n⏱️  Time limit reached ({max_ticks} ticks)")


def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("  PIXEL SIMULATION ARENA - E2E TEST")
    print("="*60)

    # ヘルスチェック
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server is not responding. Please start the server first.")
            return
    except:
        print("❌ Cannot connect to server. Please start the server at http://localhost:8000")
        return

    # 1. ユニット生成
    unit_ids = create_units()
    if not unit_ids:
        print("❌ Failed to create units")
        return

    # 2. デッキ作成（プレイヤーとAI用）
    player_deck_id = create_deck(unit_ids, "Player Deck")
    if not player_deck_id:
        print("❌ Failed to create player deck")
        return

    ai_deck_id = create_deck(unit_ids, "AI Deck")
    if not ai_deck_id:
        print("❌ Failed to create AI deck")
        return

    # 3. マッチ開始
    match_id, game_state = start_match(player_deck_id, ai_deck_id)
    if not match_id:
        print("❌ Failed to start match")
        return

    # 4. バトル実行
    run_battle(match_id, game_state, player_deck_id, ai_deck_id)

    print_section("TEST COMPLETED")
    print("✅ All systems operational!")


if __name__ == "__main__":
    main()
