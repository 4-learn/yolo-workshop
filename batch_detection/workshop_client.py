"""
Workshop：批次偵測 Client（填空版）

使用方式：
  1. 先啟動 server: uvicorn workshop_server:app --reload
  2. 把圖片放到 images/ 目錄
  3. 執行: python workshop_client.py

題目：
1. 完成 detect_image()：用 requests.post 送圖片給 API
2. 在 main() 中逐一送圖片，收集結果
3. 寫入 results.json
4. 印出 alert 摘要
"""

import requests
import json
import os
import sys
import time
from datetime import datetime

API_URL = "http://localhost:8000/detect"
IMAGE_DIR = "images"
OUTPUT_FILE = "results.json"


def detect_image(filename):
    """
    送一張圖片給 API，回傳偵測結果

    TODO: 完成以下步驟
    1. 用 os.path.join(IMAGE_DIR, filename) 組出完整路徑
    2. 用 open(..., "rb") 讀取圖片
    3. 用 requests.post(API_URL, files={"file": (filename, f, "image/jpeg")}) 送出
    4. 回傳 response.json()
    """
    # --- 你的程式碼寫在這裡 ---

    return {}
    # --- 結束 ---


def main():
    # 1. 收集所有圖片
    if not os.path.isdir(IMAGE_DIR):
        print(f"找不到 {IMAGE_DIR}/ 目錄，請建立並放入測試圖片")
        sys.exit(1)

    image_files = sorted(os.listdir(IMAGE_DIR))
    total = len(image_files)
    all_events = []
    alerts = []

    """
    TODO: 完成以下步驟
    2. 用 for loop 逐一送圖片（呼叫 detect_image）
    3. 印出每張圖的結果和 alert 狀態
    4. 收集所有 events 到 all_events
    5. 用 json.dump 寫入 results.json
    6. 印出 alert 摘要
    """
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---

    print(f"\n=== 結果 ===")
    print(f"共 {len(all_events)} 筆事件，已寫入 {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
