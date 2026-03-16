"""
Workshop：Rule-based 事件判斷（填空版）

目錄結構：
rule_engine/
├── workshop.py         ← 你正在寫的檔案
├── engine.py           ← 解答（先不要看！）
├── rules.yaml          ← 規則設定檔
└── sample_results.json ← 偵測結果（從 batch_detection 來）

執行方式：
  python workshop.py

題目：
1. 完成 check_event()：用 if-else 比對一筆事件是否符合規則
2. 完成 process_events()：對所有事件跑規則比對
3. 完成 aggregate_alerts()：統計每張圖的 alert 數，判斷是否發佈
"""

import yaml
import json


def load_rules(yaml_path):
    """讀取 YAML 規則檔"""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def check_event(event, rules):
    """
    用規則比對一筆事件，回傳第一條符合的規則

    TODO: 完成以下邏輯
    對每條 rule，依序檢查：
    1. 如果 rule 有 "event_type" → event["event_type"] 要相同，否則 continue
    2. 如果 rule 有 "min_confidence" → event["confidence"] 要 >= 它，否則 continue
    3. 如果 rule 有 "max_confidence" → event["confidence"] 要 <= 它，否則 continue
    4. 全部條件通過 → return rule

    提示：
        for rule in rules:
            if "event_type" in rule:
                if event["event_type"] != rule["event_type"]:
                    continue
            ...
            return rule
    """
    # --- 你的程式碼寫在這裡 ---

    return None
    # --- 結束 ---


def process_events(events, config):
    """
    對所有事件跑規則比對

    TODO: 完成以下步驟
    1. 取出 config["rules"]
    2. 對每筆 event 呼叫 check_event(event, rules)
    3. 把結果收集成 list，每筆包含：
       source_image, event_type, confidence, rule(name), action, severity
    """
    results = []
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---
    return results


def aggregate_alerts(results, threshold):
    """
    統計每張圖有幾筆 alert，
    如果有 alert 的圖片數量 >= threshold → 發佈

    TODO: 完成以下步驟
    1. 用 dict 統計每張圖（source_image）的 alert 數量
    2. 列出有 alert 的圖片
    3. 判斷是否 >= threshold
    """
    # --- 你的程式碼寫在這裡 ---

    return {
        "alert_images": [],
        "should_alert": False,
        "threshold": threshold,
    }
    # --- 結束 ---


if __name__ == "__main__":
    # 1. 載入規則
    config = load_rules("rules.yaml")
    print(f"載入 {len(config['rules'])} 條規則")
    print(f"聚合門檻: {config['alert_threshold']} 張圖\n")

    # 2. 載入偵測結果
    with open("sample_results.json") as f:
        events = json.load(f)
    print(f"讀取 {len(events)} 筆事件\n")

    # 3. 逐筆比對規則
    results = process_events(events, config)

    print("=== 規則比對結果 ===")
    for r in results:
        icon = {"alert": "🚨", "warning": "⚠️", "ignore": "⏭️", "ok": "✅"}.get(r.get("action", ""), "?")
        print(f"  {icon} {r['source_image']} | {r['event_type']} ({r['confidence']:.2f}) → {r.get('action', '?')} [{r.get('rule', '?')}]")

    # 4. 聚合判斷
    agg = aggregate_alerts(results, config["alert_threshold"])

    print(f"\n有 alert 的圖片: {agg['alert_images']}")

    if agg["should_alert"]:
        print(f"\n🚨 發佈 ALERT：{len(agg['alert_images'])} 張圖偵測到違規（>= {agg['threshold']}）")
    else:
        print(f"\n✅ 不發佈：只有 {len(agg['alert_images'])} 張圖有 alert，未達門檻 {agg['threshold']}")

    # 5. 存檔（給 pandas 用）
    with open("rule_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n已寫入 rule_results.json（{len(results)} 筆）")
