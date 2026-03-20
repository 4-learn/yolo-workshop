"""
解答：工安監控系統 MVP Client

完整流程：
  1. 批次送圖偵測（POST /detect）
  2. 查詢全部事件（GET /events）
  3. 查詢高信心事件（GET /events?min_confidence=0.8）
  4. 手動校準門檻（GET /recalibrate）
  5. 用 pandas 產生分析報告

使用方式：
  1. 先啟動 server: uvicorn server:app --reload
  2. 執行: python client.py
"""

import requests
import json
import os
import time
import pandas as pd
from datetime import datetime

BASE_URL = "http://localhost:8000"
IMAGE_DIR = "images"


# === Step 1：批次送圖偵測 ===

def detect_image(filename):
    """送一張圖片給 POST /detect"""
    image_path = os.path.join(IMAGE_DIR, filename)
    with open(image_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/detect",
            files={"file": (filename, f, "image/jpeg")},
        )
    response.raise_for_status()
    return response.json()


def batch_detect():
    """批次偵測所有圖片"""
    print("=" * 50)
    print("  Step 1：POST /detect — 批次偵測圖片")
    print("=" * 50)

    image_files = sorted(
        f for f in os.listdir(IMAGE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )

    total = len(image_files)
    total_start = time.time()

    for i, filename in enumerate(image_files, 1):
        ts = datetime.now().strftime("%H:%M:%S")
        t0 = time.time()
        result = detect_image(filename)
        elapsed = time.time() - t0

        count = result["event_count"]
        alert_flag = " ⚠️ ALERT" if result["alert"] else ""
        detect_n = result["detect_count"]
        print(f"  [{i}/{total}] {ts} {filename} → {count} events ({elapsed:.2f}s) #{detect_n}{alert_flag}")

        # 如果有自動校準
        if result.get("calibration"):
            cal = result["calibration"]
            print(f"  🔄 自動校準！建議門檻: {cal['threshold_low']} / {cal['threshold_high']}")

    total_elapsed = time.time() - total_start
    print(f"\n  總耗時: {total_elapsed:.2f}s\n")


# === Step 2：查詢全部事件 ===

def query_all_events():
    """GET /events"""
    print("=" * 50)
    print("  Step 2：GET /events — 查詢所有事件")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/events")
    data = response.json()
    print(f"  共 {data['total']} 筆事件\n")
    return data


# === Step 3：查詢高信心事件 ===

def query_high_confidence(min_confidence=0.8):
    """GET /events?min_confidence=0.8"""
    print("=" * 50)
    print(f"  Step 3：GET /events?min_confidence={min_confidence}")
    print("=" * 50)

    response = requests.get(
        f"{BASE_URL}/events",
        params={"min_confidence": min_confidence},
    )
    data = response.json()
    print(f"  信心度 >= {min_confidence}: {data['total']} 筆\n")
    return data


# === Step 4：手動校準門檻 ===

def recalibrate():
    """GET /recalibrate"""
    print("=" * 50)
    print("  Step 4：GET /recalibrate — sklearn 校準門檻")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/recalibrate")
    data = response.json()

    if "error" in data:
        print(f"  {data['error']}\n")
        return data

    print(f"  資料量: {data['total_events']} 筆")
    print(f"  群中心: {data['centers']}")
    print(f"  建議門檻:")
    print(f"    低/中界線: {data['threshold_low']}")
    print(f"    中/高界線: {data['threshold_high']}")
    print()
    return data


# === Step 5：pandas 分析報告 ===

def generate_report():
    """從 GET /events 拿資料，用 pandas 產生報告"""
    print("=" * 50)
    print("  Step 5：pandas 分析報告")
    print("=" * 50)

    # 從 API 拿資料
    response = requests.get(f"{BASE_URL}/events")
    data = response.json()

    if data["total"] == 0:
        print("  沒有資料\n")
        return

    df = pd.DataFrame(data["events"])

    # 各 event_type 數量
    print("\n  各類型數量:")
    counts = df["event_type"].value_counts()
    for event_type, count in counts.items():
        print(f"    {event_type}: {count}")

    # 每張圖的事件數
    print("\n  每張圖的事件數:")
    image_counts = df.groupby("source_image")["event_type"].count()
    for image, count in image_counts.items():
        print(f"    {image}: {count}")

    # 違規事件（head_detected）
    violations = df[df["event_type"] == "head_detected"]
    print(f"\n  違規事件（head_detected）: {len(violations)} 筆")

    if len(violations) > 0:
        # 違規的信心度分佈
        print(f"    信心度: {violations['confidence'].min():.4f} ~ {violations['confidence'].max():.4f}")
        print(f"    平均: {violations['confidence'].mean():.4f}")

        # 哪張圖最多違規
        top_image = violations["source_image"].value_counts().index[0]
        top_count = violations["source_image"].value_counts().iloc[0]
        print(f"    最多違規: {top_image}（{top_count} 筆）")

    print()


# === 主程式 ===

if __name__ == "__main__":
    print("\n🏗️ 工安監控系統 MVP — 完整流程\n")

    # Step 1: 批次送圖
    batch_detect()

    # Step 2: 查詢全部
    query_all_events()

    # Step 3: 高信心篩選
    query_high_confidence(0.8)

    # Step 4: sklearn 校準
    recalibrate()

    # Step 5: pandas 報告
    generate_report()

    print("✅ 完成！")
