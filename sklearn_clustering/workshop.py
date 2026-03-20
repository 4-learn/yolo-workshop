"""
Workshop：用 KMeans 找 confidence 門檻

目錄結構：
sklearn_clustering/
├── workshop.py               ← 你正在寫的檔案
├── solution.py               ← 解答（先不要看！）
├── rule_results_small.json   ← 21 筆資料（來自 rule_engine）
└── rule_results_large.json   ← 100 筆模擬資料

執行方式：
  python workshop.py

題目：
1. 完成 cluster_confidence()：用 KMeans 對 confidence 分群
2. 完成 calculate_thresholds()：從群中心算出門檻
3. 完成 generate_rules_yaml()：用門檻產生新的 rules.yaml
"""

import json
import pandas as pd
from sklearn.cluster import KMeans


def load_data(json_path):
    """讀取 JSON，回傳 DataFrame（已完成，不用改）"""
    with open(json_path) as f:
        data = json.load(f)
    return pd.DataFrame(data)


def cluster_confidence(df, n_clusters=3):
    """
    用 KMeans 對 confidence 分群

    TODO: 完成以下步驟
    1. 取出 confidence 欄位：X = df[["confidence"]]
    2. 建立 KMeans：kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    3. 訓練 + 預測：df["cluster"] = kmeans.fit_predict(X)
    4. 取出群中心並排序：centers = sorted(kmeans.cluster_centers_.flatten())
    5. 回傳 df 和 centers

    提示：
        X = df[["confidence"]]          ← 注意雙層中括號
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        df = df.copy()
        df["cluster"] = kmeans.fit_predict(X)
        centers = sorted(kmeans.cluster_centers_.flatten())
    """
    df = df.copy()
    # --- 你的程式碼寫在這裡 ---

    centers = []
    # --- 結束 ---
    return df, centers


def calculate_thresholds(centers):
    """
    從群中心算門檻（相鄰兩群中心的中點）

    TODO: 完成以下步驟
    例如 centers = [0.45, 0.68, 0.86]
    → 門檻 = [(0.45+0.68)/2, (0.68+0.86)/2] = [0.565, 0.77]

    提示：
        thresholds = []
        for i in range(len(centers) - 1):
            mid = round((centers[i] + centers[i + 1]) / 2, 4)
            thresholds.append(mid)
    """
    thresholds = []
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---
    return thresholds


def generate_rules_yaml(thresholds):
    """
    用門檻產生新的 rules.yaml 內容

    TODO: 完成以下步驟
    用 thresholds[0] 當 max_confidence（低信心界線）
    用 thresholds[1] 當 min_confidence（高信心界線）
    組成 YAML 字串

    提示：
        yaml_content = f\"\"\"rules:
          - name: 低信心忽略
            max_confidence: {thresholds[0]}
            action: ignore
          ...\"\"\"
    """
    # --- 你的程式碼寫在這裡 ---

    return ""
    # --- 結束 ---


if __name__ == "__main__":
    # 1. 讀取資料
    df = load_data("rule_results_large.json")
    print(f"共 {len(df)} 筆事件")
    print(f"confidence 範圍: {df['confidence'].min():.4f} ~ {df['confidence'].max():.4f}\n")

    # 2. KMeans 分群
    df, centers = cluster_confidence(df, n_clusters=3)

    if centers:
        labels = ["低信心", "中信心", "高信心"]
        print("=== 分群結果 ===")
        for i, center in enumerate(centers):
            count = len(df[df["cluster"] == i])
            print(f"  {labels[i]}: 中心 = {center:.4f}（{count} 筆）")

        # 3. 算門檻
        thresholds = calculate_thresholds(centers)
        if thresholds:
            print(f"\n=== 建議門檻 ===")
            print(f"  低/中界線: {thresholds[0]}")
            print(f"  中/高界線: {thresholds[1]}")

            # 4. 對照原本
            print(f"\n=== 對照 ===")
            print(f"  原本: max_confidence=0.5, min_confidence=0.7")
            print(f"  建議: max_confidence={thresholds[0]}, min_confidence={thresholds[1]}")

            # 5. 產生 rules.yaml
            yaml_content = generate_rules_yaml(thresholds)
            if yaml_content:
                print(f"\n=== 建議的 rules.yaml ===")
                print(yaml_content)

                with open("rules_suggested.yaml", "w") as f:
                    f.write(yaml_content)
                print(f"\n已寫入 rules_suggested.yaml")
            else:
                print("\n請完成 generate_rules_yaml()")
        else:
            print("\n請完成 calculate_thresholds()")
    else:
        print("請完成 cluster_confidence()")
