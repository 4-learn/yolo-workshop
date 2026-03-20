"""
批次偵測 Client — 三種情境示範

使用方式：
  1. 先啟動 server: uvicorn server:app --reload
  2. 執行: python client0.py

情境：
  1. POST /detect  — 批次送圖片偵測，結果自動存入 server 端 CSV
  2. GET /events   — 查詢所有已儲存的事件
  3. GET /events?min_confidence=0.8 — 只查高信心度事件
"""

import requests
import json
import os
import sys
import time
from datetime import datetime

BASE_URL = "http://localhost:8002"
IMAGE_DIR = "images"


# === 情境 1：批次送圖片偵測 ===

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
    print("  情境 1：POST /detect — 批次偵測圖片")
    print("=" * 50)

    if not os.path.isdir(IMAGE_DIR):
        print(f"找不到 {IMAGE_DIR}/ 目錄")
        return

    image_files = sorted(
        f for f in os.listdir(IMAGE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )

    if not image_files:
        print(f"{IMAGE_DIR}/ 是空的")
        return

    total = len(image_files)
    total_start = time.time()

    for i, filename in enumerate(image_files, 1):
        ts = datetime.now().strftime("%H:%M:%S")
        t0 = time.time()
        result = detect_image(filename)
        elapsed = time.time() - t0

        count = result["event_count"]
        alert_flag = " ⚠️ ALERT" if result["alert"] else ""
        print(f"  [{i}/{total}] {ts} {filename} → {count} events ({elapsed:.2f}s){alert_flag}")

    total_elapsed = time.time() - total_start
    print(f"\n  總耗時: {total_elapsed:.2f}s")
    print(f"  事件已自動存入 server 端 events.csv\n")


# === 情境 2：查詢所有事件 ===

def query_all_events():
    """GET /events — 查詢全部事件"""
    print("=" * 50)
    print("  情境 2：GET /events — 查詢所有事件")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/events")
    data = response.json()

    print(f"  共 {data['total']} 筆事件\n")

    # 列出前 5 筆
    for event in data["events"][:5]:
        print(f"  {event['source_image']} | {event['event_type']} | {event['confidence']:.4f}")

    if data["total"] > 5:
        print(f"  ... 還有 {data['total'] - 5} 筆\n")
    else:
        print()

    return data


# === 情境 3：查詢高信心度事件 ===

def query_high_confidence(min_confidence=0.8):
    """GET /events?min_confidence=0.8 — 只看高信心度"""
    print("=" * 50)
    print(f"  情境 3：GET /events?min_confidence={min_confidence}")
    print("=" * 50)

    response = requests.get(
        f"{BASE_URL}/events",
        params={"min_confidence": min_confidence},
    )
    data = response.json()

    print(f"  信心度 >= {min_confidence} 的事件：{data['total']} 筆\n")

    for event in data["events"]:
        label = "🚨" if event["event_type"] == "head_detected" else "✅"
        print(f"  {label} {event['source_image']} | {event['event_type']} | {event['confidence']:.4f}")

    print()
    return data


# === 主程式 ===

if __name__ == "__main__":
    # 情境 1：批次送圖片
    batch_detect()

    # 情境 2：查詢全部事件
    query_all_events()

    # 情境 3：查詢高信心度事件
    query_high_confidence(0.8)
