"""
解答：系統整合 — 動態門檻管線

每 N 筆事件用 sklearn KMeans 重新算門檻，
用新門檻跑規則比對 + pandas 分析 + 報告。

執行方式：
  python solution.py
"""

import yaml
import json
import pandas as pd
from sklearn.cluster import KMeans


# === 規則比對 ===

def load_rules(yaml_path):
    """讀取 YAML 規則檔"""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def check_event(event, rules):
    """用規則比對一筆事件"""
    for rule in rules:
        if "event_type" in rule:
            if event["event_type"] != rule["event_type"]:
                continue
        if "min_confidence" in rule:
            if event["confidence"] < rule["min_confidence"]:
                continue
        if "max_confidence" in rule:
            if event["confidence"] > rule["max_confidence"]:
                continue
        return rule
    return None


def process_events(events, config):
    """對所有事件跑規則比對"""
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


# === sklearn 校準 ===

def recalibrate(events):
    """用 KMeans 對 confidence 分群，回傳建議門檻"""
    df = pd.DataFrame(events)
    X = df[["confidence"]]

    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(X)
    centers = sorted(kmeans.cluster_centers_.flatten())

    threshold_low = round(float((centers[0] + centers[1]) / 2), 4)
    threshold_high = round(float((centers[1] + centers[2]) / 2), 4)

    return {
        "centers": [round(float(c), 4) for c in centers],
        "threshold_low": threshold_low,
        "threshold_high": threshold_high,
    }


def make_rules_config(thresholds):
    """用門檻產生 rules config（不寫檔，直接用）"""
    return {
        "rules": [
            {"name": "低信心忽略", "max_confidence": thresholds["threshold_low"], "action": "ignore"},
            {"name": "沒戴安全帽（高信心）", "event_type": "head_detected",
             "min_confidence": thresholds["threshold_high"], "action": "alert", "severity": "high"},
            {"name": "沒戴安全帽（中信心）", "event_type": "head_detected",
             "action": "warning", "severity": "low"},
            {"name": "預設", "action": "ok"},
        ],
        "alert_threshold": 2,
    }


# === pandas 分析 ===

def summarize(results):
    """統計摘要"""
    df = pd.DataFrame(results)
    return {
        "total": len(df),
        "alert": int(df[df["action"] == "alert"].shape[0]),
        "warning": int(df[df["action"] == "warning"].shape[0]),
        "ok": int(df[df["action"] == "ok"].shape[0]),
        "ignore": int(df[df["action"] == "ignore"].shape[0]),
        "alert_images": df[df["action"] == "alert"]["source_image"].unique().tolist(),
    }


def generate_report(label, stats, thresholds=None):
    """產生報告"""
    print(f"\n{'=' * 50}")
    print(f"  {label}")
    print(f"{'=' * 50}")

    if thresholds:
        print(f"  門檻: max_confidence={thresholds['threshold_low']}, min_confidence={thresholds['threshold_high']}")

    print(f"\n  總事件: {stats['total']}")
    print(f"    alert:   {stats['alert']}")
    print(f"    warning: {stats['warning']}")
    print(f"    ok:      {stats['ok']}")
    print(f"    ignore:  {stats['ignore']}")
    print(f"  alert 圖片: {stats['alert_images']}")


# === 主程式：動態門檻管線 ===

if __name__ == "__main__":
    RECALIBRATE_EVERY = 7  # 每 7 筆事件重新校準

    # 1. 載入偵測結果
    with open("../rule_engine/sample_results.json") as f:
        events = json.load(f)
    print(f"讀取 {len(events)} 筆偵測事件")
    print(f"每 {RECALIBRATE_EVERY} 筆重新校準門檻\n")

    # 2. 先用舊門檻跑一次（基準）
    old_config = load_rules("../rule_engine/rules.yaml")
    old_results = process_events(events, old_config)
    old_stats = summarize(old_results)
    generate_report("基準：舊門檻（人工設定 0.5 / 0.7）", old_stats)

    # 3. 動態管線：逐筆處理，每 N 筆校準一次
    print(f"\n\n{'#' * 50}")
    print(f"  動態管線開始")
    print(f"{'#' * 50}")

    accumulated = []
    current_config = old_config
    calibration_count = 0

    for i, event in enumerate(events):
        accumulated.append(event)

        # 每 N 筆觸發校準
        if len(accumulated) % RECALIBRATE_EVERY == 0 and len(accumulated) >= 10:
            calibration_count += 1
            thresholds = recalibrate(accumulated)
            current_config = make_rules_config(thresholds)
            print(f"\n  🔄 第 {len(accumulated)} 筆，校準 #{calibration_count}")
            print(f"     群中心: {thresholds['centers']}")
            print(f"     新門檻: {thresholds['threshold_low']} / {thresholds['threshold_high']}")

    # 4. 用最終門檻跑全部事件
    new_results = process_events(events, current_config)
    new_stats = summarize(new_results)

    thresholds = recalibrate(accumulated)
    generate_report("結果：動態門檻（sklearn 校準）", new_stats, thresholds)

    # 5. 比較
    print(f"\n\n{'=' * 50}")
    print(f"  新舊比較")
    print(f"{'=' * 50}")
    print(f"\n{'':>15} {'舊門檻':>8} {'新門檻':>8} {'差異':>8}")
    print("-" * 45)
    for key in ["alert", "warning", "ok", "ignore"]:
        old_val = old_stats[key]
        new_val = new_stats[key]
        diff = new_val - old_val
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print(f"{key:>15} {old_val:>8} {new_val:>8} {diff_str:>8}")

    diff_alert = new_stats["alert"] - old_stats["alert"]
    if diff_alert < 0:
        print(f"\n  新門檻較嚴格：alert 減少 {abs(diff_alert)} 筆")
    elif diff_alert > 0:
        print(f"\n  新門檻較寬鬆：alert 增加 {diff_alert} 筆")
    else:
        print(f"\n  alert 數量相同，但門檻有資料依據了")

    print()
