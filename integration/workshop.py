"""
Workshop：系統整合 — 從偵測結果到分析報告

目錄結構：
integration/
├── workshop.py          ← 你正在寫的檔案
├── solution.py          ← 解答（先不要看！）
../rule_engine/
├── sample_results.json  ← 原始偵測結果
└── rules.yaml           ← 規則設定檔

執行方式：
  python workshop.py

題目：
把前面學的模組串起來，完成一條完整的管線：
  偵測結果 → 規則比對 → pandas 分析 → 告警報告

1. 完成 process_events()：對所有事件跑規則比對
2. 完成 analyze()：用 pandas 做統計分析
3. 完成 aggregate_alerts()：判斷是否發佈告警
4. 完成 generate_report()：產生最終報告
"""

import yaml
import json
import pandas as pd


# --- 規則比對（你在 rule_engine 章節寫過） ---

def load_rules(yaml_path):
    """讀取 YAML 規則檔"""
    with open(yaml_path) as f:
        return yaml.safe_load(f)


def check_event(event, rules):
    """用規則比對一筆事件（已完成，不用改）"""
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
    """
    對所有事件跑規則比對

    TODO: 完成以下步驟
    1. 取出 config["rules"]
    2. 對每筆 event 呼叫 check_event(event, rules)
    3. 收集結果，每筆包含：
       source_image, event_type, confidence, rule, action, severity

    提示：
        rules = config["rules"]
        for event in events:
            matched = check_event(event, rules)
            results.append({
                "source_image": event["source_image"],
                ...
                "rule": matched["name"] if matched else "無匹配",
                "action": matched["action"] if matched else "unknown",
            })
    """
    results = []
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---
    return results


def analyze(results):
    """
    用 pandas 做統計分析

    TODO: 完成以下步驟
    1. 用 pd.DataFrame(results) 建立 DataFrame
    2. 印出 df["action"].value_counts()
    3. 印出 df.groupby("source_image")["action"].count()
    4. 篩選違規事件（action 為 alert 或 warning）
    5. 印出違規事件的 source_image, event_type, confidence, action

    提示：
        df = pd.DataFrame(results)
        violations = df[df["action"].isin(["alert", "warning"])]
    """
    df = pd.DataFrame(results)
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---
    return df


def aggregate_alerts(df, threshold):
    """
    統計有 alert 的圖片，判斷是否發佈

    TODO: 完成以下步驟
    1. 篩選 action == "alert" 的事件
    2. 用 .unique() 取出不重複的圖片名稱
    3. 判斷圖片數量是否 >= threshold

    提示：
        alerts = df[df["action"] == "alert"]
        alert_images = alerts["source_image"].unique().tolist()
    """
    # --- 你的程式碼寫在這裡 ---

    return {
        "alert_images": [],
        "alert_image_count": 0,
        "should_alert": False,
        "threshold": threshold,
    }
    # --- 結束 ---


def generate_report(df, agg):
    """
    產生最終報告

    TODO: 完成以下步驟
    1. 印出總偵測事件數
    2. 分別印出 alert / warning / ok 的數量
    3. 印出有 alert 的圖片和門檻
    4. 判斷是否發佈告警

    提示：
        total = len(df)
        alerts = len(df[df["action"] == "alert"])
        print(f"總偵測事件: {total}")
        print(f"  alert: {alerts}")
    """
    print("=" * 50)
    print("          工安監控系統 — 分析報告")
    print("=" * 50)
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---


if __name__ == "__main__":
    # 1. 載入原始偵測結果
    with open("../rule_engine/sample_results.json") as f:
        events = json.load(f)
    print(f"讀取 {len(events)} 筆偵測事件\n")

    # 2. 載入規則
    config = load_rules("../rule_engine/rules.yaml")
    print(f"載入 {len(config['rules'])} 條規則")
    print(f"聚合門檻: {config['alert_threshold']} 張圖\n")

    # 3. 規則比對
    results = process_events(events, config)
    print(f"完成規則比對: {len(results)} 筆\n")

    # 4. pandas 分析
    df = analyze(results)

    # 5. 聚合告警
    agg = aggregate_alerts(df, config["alert_threshold"])

    # 6. 產生報告
    generate_report(df, agg)
