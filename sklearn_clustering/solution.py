"""
解答：用 KMeans 找 confidence 門檻

讀取偵測結果 → KMeans 分群 → 算門檻 → 產生新的 rules.yaml

執行方式：
  python solution.py
"""

import json
import pandas as pd
from sklearn.cluster import KMeans


def load_data(json_path):
    """讀取 JSON，回傳 DataFrame"""
    with open(json_path) as f:
        data = json.load(f)
    return pd.DataFrame(data)


def cluster_confidence(df, n_clusters=3):
    """用 KMeans 對 confidence 分群"""
    X = df[["confidence"]]
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    df = df.copy()
    df["cluster"] = kmeans.fit_predict(X)
    centers = sorted(kmeans.cluster_centers_.flatten())
    return df, centers


def calculate_thresholds(centers):
    """從群中心算門檻（相鄰中心的中點）"""
    thresholds = []
    for i in range(len(centers) - 1):
        mid = round((centers[i] + centers[i + 1]) / 2, 4)
        thresholds.append(mid)
    return thresholds


def generate_rules_yaml(thresholds):
    """用門檻產生新的 rules.yaml 內容"""
    yaml_content = f"""rules:
  - name: 低信心忽略
    max_confidence: {thresholds[0]}
    action: ignore

  - name: 沒戴安全帽（高信心）
    event_type: head_detected
    min_confidence: {thresholds[1]}
    action: alert
    severity: high

  - name: 沒戴安全帽（中信心）
    event_type: head_detected
    action: warning
    severity: low

  - name: 預設
    action: ok

alert_threshold: 2"""
    return yaml_content


if __name__ == "__main__":
    # 1. 讀取資料
    df = load_data("rule_results_large.json")
    print(f"共 {len(df)} 筆事件")
    print(f"confidence 範圍: {df['confidence'].min():.4f} ~ {df['confidence'].max():.4f}\n")

    # 2. KMeans 分群
    df, centers = cluster_confidence(df, n_clusters=3)

    labels = ["低信心", "中信心", "高信心"]
    print("=== 分群結果 ===")
    for i, center in enumerate(centers):
        count = len(df[df["cluster"] == i])
        print(f"  {labels[i]}: 中心 = {center:.4f}（{count} 筆）")

    # 3. 算門檻
    thresholds = calculate_thresholds(centers)
    print(f"\n=== 建議門檻 ===")
    print(f"  低/中界線: {thresholds[0]}")
    print(f"  中/高界線: {thresholds[1]}")

    # 4. 對照原本
    print(f"\n=== 對照 ===")
    print(f"  原本: max_confidence=0.5, min_confidence=0.7")
    print(f"  建議: max_confidence={thresholds[0]}, min_confidence={thresholds[1]}")

    # 5. 產生新的 rules.yaml
    yaml_content = generate_rules_yaml(thresholds)
    print(f"\n=== 建議的 rules.yaml ===")
    print(yaml_content)

    # 6. 寫入檔案
    with open("rules_suggested.yaml", "w") as f:
        f.write(yaml_content)
    print(f"\n已寫入 rules_suggested.yaml")
