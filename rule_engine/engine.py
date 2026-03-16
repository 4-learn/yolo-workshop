"""
解答：Rule-based 事件判斷

讀取 rules.yaml 規則，對 results.json 逐筆比對，
聚合後判斷是否發佈 alert。

執行方式：
  python engine.py
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

    規則由上往下比對，第一條符合就回傳。
    """
    for rule in rules:
        # 檢查 event_type
        if "event_type" in rule:
            if event["event_type"] != rule["event_type"]:
                continue

        # 檢查 min_confidence
        if "min_confidence" in rule:
            if event["confidence"] < rule["min_confidence"]:
                continue

        # 檢查 max_confidence
        if "max_confidence" in rule:
            if event["confidence"] > rule["max_confidence"]:
                continue

        # 全部條件都通過 → 符合這條規則
        return rule

    return None


def process_events(events, config):
    """
    對所有事件跑規則比對，回傳每筆事件的判斷結果
    """
    rules = config["rules"]
    results = []

    for event in events:
        matched = check_event(event, rules)
        results.append({
            "source_image": event["source_image"],
            "event_type": event["event_type"],
            "confidence": event["confidence"],
            "rule": matched["name"] if matched else "無匹配",
            "action": matched["action"] if matched else "unknown",
            "severity": matched.get("severity", "-"),
        })

    return results


def aggregate_alerts(results, threshold):
    """
    聚合：統計每張圖的 alert 數，
    連續 N 張圖都有 alert 才發佈。
    """
    # 按圖片統計
    image_stats = {}
    for r in results:
        img = r["source_image"]
        if img not in image_stats:
            image_stats[img] = {"alert": 0, "warning": 0, "ignore": 0, "ok": 0}
        action = r["action"]
        if action in image_stats[img]:
            image_stats[img][action] += 1

    # 有 alert 的圖片
    alert_images = [img for img, stats in image_stats.items() if stats["alert"] > 0]

    return {
        "image_stats": image_stats,
        "alert_images": alert_images,
        "should_alert": len(alert_images) >= threshold,
        "threshold": threshold,
    }


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
        icon = {"alert": "🚨", "warning": "⚠️", "ignore": "⏭️", "ok": "✅"}.get(r["action"], "?")
        print(f"  {icon} {r['source_image']} | {r['event_type']} ({r['confidence']:.2f}) → {r['action']} [{r['rule']}]")

    # 4. 聚合判斷
    agg = aggregate_alerts(results, config["alert_threshold"])

    print(f"\n=== 聚合結果 ===")
    for img, stats in agg["image_stats"].items():
        print(f"  {img}: {stats}")

    print(f"\n有 alert 的圖片: {agg['alert_images']}")
    print(f"門檻: {agg['threshold']} 張")

    if agg["should_alert"]:
        print(f"\n🚨 發佈 ALERT：{len(agg['alert_images'])} 張圖偵測到違規（>= {agg['threshold']}）")
    else:
        print(f"\n✅ 不發佈：只有 {len(agg['alert_images'])} 張圖有 alert，未達門檻 {agg['threshold']}")

    # 5. 存檔（給 pandas 用）
    with open("rule_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n已寫入 rule_results.json（{len(results)} 筆）")
