"""
Workshop：用 pandas 分析規則比對結果

目錄結構：
pandas_analysis/
├── workshop.py         ← 你正在寫的檔案
├── solution.py         ← 解答（先不要看！）
└── rule_results.json   ← 規則比對結果（從 rule_engine 來）

執行方式：
  python workshop.py

題目：
1. 完成 load_data()：讀取 JSON，轉成 DataFrame
2. 完成 count_by_action()：統計每種 action 的數量
3. 完成 count_by_image()：統計每張圖的事件數和 alert 數
4. 完成 confidence_stats()：計算信心度的基本統計
5. 完成 find_violations()：篩選出違規事件
"""

import pandas as pd
import json


def load_data(json_path):
    """
    讀取 JSON 檔，回傳 DataFrame

    TODO: 完成以下步驟
    1. 用 open + json.load 讀取 JSON 檔
    2. 用 pd.DataFrame(data) 轉成 DataFrame
    3. 回傳 DataFrame

    提示：
        with open(json_path) as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    """
    # --- 你的程式碼寫在這裡 ---

    return pd.DataFrame()
    # --- 結束 ---


def count_by_action(df):
    """
    統計每種 action 的數量

    TODO: 用 df["action"].value_counts() 印出每種 action 各有幾筆

    提示：
        counts = df["action"].value_counts()
        print(counts)
    """
    print("=== 各 action 數量 ===")
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---


def count_by_image(df):
    """
    統計每張圖的事件數和 alert 數

    TODO: 完成以下步驟
    1. 用 df.groupby("source_image")["action"].count() 算每張圖的事件數
    2. 先篩選 alert：alerts = df[df["action"] == "alert"]
    3. 再用 groupby 算每張圖的 alert 數

    提示：
        image_counts = df.groupby("source_image")["action"].count()
        alerts = df[df["action"] == "alert"]
        alert_counts = alerts.groupby("source_image")["action"].count()
    """
    print("=== 每張圖的統計 ===")
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---


def confidence_stats(df):
    """
    信心度統計

    TODO: 完成以下步驟
    1. 用 df["confidence"].describe() 印出基本統計
    2. 用 df.groupby("event_type")["confidence"].mean() 算各類型平均信心度

    提示：
        print(df["confidence"].describe())
        avg = df.groupby("event_type")["confidence"].mean()
        print(avg)
    """
    print("=== 信心度統計 ===")
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---


def find_violations(df):
    """
    找出所有違規事件（action 為 alert 或 warning）

    TODO: 完成以下步驟
    1. 用 df[df["action"].isin(["alert", "warning"])] 篩選
    2. 印出 source_image, event_type, confidence, action 這幾欄
    3. 印出共幾筆違規

    提示：
        violations = df[df["action"].isin(["alert", "warning"])]
        print(violations[["source_image", "event_type", "confidence", "action"]])
    """
    print("=== 違規事件 ===")
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---


if __name__ == "__main__":
    # 1. 讀取資料
    df = load_data("rule_results.json")
    print(f"讀取 {len(df)} 筆資料\n")

    # 2. 看前幾筆
    print("=== 前 5 筆 ===")
    print(df.head())
    print()

    # 3. 按 action 統計
    count_by_action(df)

    # 4. 按圖片統計
    count_by_image(df)

    # 5. 信心度統計
    confidence_stats(df)

    # 6. 找出違規
    find_violations(df)
