"""
Workshop：批次偵測 Client（填空版）

使用方式：
  1. 先啟動 server: uvicorn workshop_server:app --reload
  2. 把圖片放到 images/ 目錄
  3. 執行: python workshop_client.py

題目：
1. 讀取 images/ 目錄下所有 .jpg 檔案
2. 用 httpx.AsyncClient 對每張圖呼叫 POST /detect
3. 用 asyncio.gather() 同時送出所有請求
4. 收集結果，寫入 results.json
5. 印出 alert 摘要
"""

import asyncio
import httpx
import json
import os
import sys

API_URL = "http://localhost:8000/detect"
IMAGE_DIR = "images"
OUTPUT_FILE = "results.json"


async def detect_image(client: httpx.AsyncClient, image_path: str) -> dict:
    """
    送一張圖片給 API，回傳偵測結果

    TODO: 完成以下步驟
    1. 用 open() 讀取圖片檔案（binary mode）
    2. 用 client.post() 送到 API_URL
       提示：files={"file": (filename, f, "image/jpeg")}
    3. 回傳 response.json()
    """
    filename = os.path.basename(image_path)
    # --- 你的程式碼寫在這裡 ---

    return {}
    # --- 結束 ---


async def main():
    # 1. 收集所有圖片
    if not os.path.isdir(IMAGE_DIR):
        print(f"找不到 {IMAGE_DIR}/ 目錄，請建立並放入測試圖片")
        sys.exit(1)

    image_files = sorted(
        f for f in os.listdir(IMAGE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )

    if not image_files:
        print(f"{IMAGE_DIR}/ 目錄是空的，請放入測試圖片")
        sys.exit(1)

    total = len(image_files)
    all_events = []
    alerts = []

    """
    TODO: 完成以下步驟
    2. 建立 httpx.AsyncClient（提示：async with httpx.AsyncClient() as client:）
    3. 用 asyncio.gather() 同時送出所有圖片
    4. 遍歷結果，收集 events 和 alerts
    5. 寫入 results.json
    6. 印出 alert 摘要
    """
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---

    print(f"\n=== 結果 ===")
    print(f"共 {len(all_events)} 筆事件，已寫入 {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
