"""
Workshop：系統整合 — 動態門檻管線

目錄結構：
integration/
├── workshop.py          ← 你正在寫的檔案
├── solution.py          ← 解答（先不要看！）
../rule_engine/
├── sample_results.json  ← 原始偵測結果
└── rules.yaml           ← 舊門檻（人工設定）

執行方式：
  python workshop.py

情境：
  sklearn 算出了新門檻，但只是一份 YAML，還沒人用它跑過。
  你要建一條動態管線：每 N 筆事件自動用 KMeans 校準門檻，
  用新門檻跑規則比對 + 分析，最後跟舊門檻比較差異。

題目：
1. 完成 recalibrate()：KMeans 分群算門檻
2. 完成 make_rules_config()：用門檻產生 rules config
3. 完成動態管線邏輯：每 N 筆觸發校準
4. 完成 generate_report()：產生比較報告
"""

import yaml
import json
import pandas as pd
from sklearn.cluster import KMeans


# --- 規則比對（已完成，不用改） ---

def load_rules(yaml_path):
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def check_event(event, rules):
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


def summarize(results):
    df = pd.DataFrame(results)
    return {
        "total": len(df),
        "alert": int(df[df["action"] == "alert"].shape[0]),
        "warning": int(df[df["action"] == "warning"].shape[0]),
        "ok": int(df[df["action"] == "ok"].shape[0]),
        "ignore": int(df[df["action"] == "ignore"].shape[0]),
        "alert_images": df[df["action"] == "alert"]["source_image"].unique().tolist(),
    }


# --- 題目 1：sklearn 校準 ---

def recalibrate(events):
    """
    用 KMeans 對 confidence 分群，回傳建議門檻

    TODO: 完成以下步驟
    1. 用 pd.DataFrame(events) 建立 DataFrame
    2. 取出 X = df[["confidence"]]
    3. KMeans(n_clusters=3, random_state=42).fit(X)
    4. 排序群中心，算相鄰中心的中點

    提示：
        df = pd.DataFrame(events)
        X = df[["confidence"]]
        kmeans = KMeans(n_clusters=3, random_state=42)
        kmeans.fit(X)
        centers = sorted(kmeans.cluster_centers_.flatten())
        threshold_low = round(float((centers[0] + centers[1]) / 2), 4)
        threshold_high = round(float((centers[1] + centers[2]) / 2), 4)
    """
    # --- 你的程式碼寫在這裡 ---

    return {
        "centers": [],
        "threshold_low": 0.5,
        "threshold_high": 0.7,
    }
    # --- 結束 ---


# --- 題目 2：用門檻產生 rules config ---

def make_rules_config(thresholds):
    """
    用門檻產生 rules config dict

    TODO: 用 thresholds["threshold_low"] 和 thresholds["threshold_high"]
    組成跟 rules.yaml 一樣格式的 dict

    提示：
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
    """
    # --- 你的程式碼寫在這裡 ---

    return {"rules": [], "alert_threshold": 2}
    # --- 結束 ---


# --- 題目 4：產生報告 ---

def generate_report(label, stats, thresholds=None):
    """
    產生報告

    TODO: 印出 label、門檻、各 action 數量、alert 圖片

    提示：
        print(f"  總事件: {stats['total']}")
        print(f"    alert: {stats['alert']}")
        ...
    """
    print(f"\n{'=' * 50}")
    print(f"  {label}")
    print(f"{'=' * 50}")
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---


# === 主程式 ===

if __name__ == "__main__":
    RECALIBRATE_EVERY = 7

    # 1. 載入偵測結果
    with open("../rule_engine/sample_results.json") as f:
        events = json.load(f)
    print(f"讀取 {len(events)} 筆偵測事件")
    print(f"每 {RECALIBRATE_EVERY} 筆重新校準門檻\n")

    # 2. 舊門檻基準
    old_config = load_rules("../rule_engine/rules.yaml")
    old_results = process_events(events, old_config)
    old_stats = summarize(old_results)
    generate_report("基準：舊門檻（人工設定 0.5 / 0.7）", old_stats)

    # 3. 題目 3：動態管線 — 每 N 筆校準一次
    #
    # TODO: 完成以下步驟
    # - 用 for loop 逐筆處理 events
    # - 累積到 accumulated list
    # - 每 RECALIBRATE_EVERY 筆且 >= 10 筆時，呼叫 recalibrate()
    # - 用 make_rules_config() 更新 current_config
    #
    # 提示：
    #     accumulated = []
    #     current_config = old_config
    #     for i, event in enumerate(events):
    #         accumulated.append(event)
    #         if len(accumulated) % RECALIBRATE_EVERY == 0 and len(accumulated) >= 10:
    #             thresholds = recalibrate(accumulated)
    #             current_config = make_rules_config(thresholds)

    print(f"\n\n{'#' * 50}")
    print(f"  動態管線開始")
    print(f"{'#' * 50}")

    accumulated = []
    current_config = old_config
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---

    # 4. 用最終門檻跑全部事件
    new_results = process_events(events, current_config)
    new_stats = summarize(new_results)
    generate_report("結果：動態門檻（sklearn 校準）", new_stats)

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

    print()
