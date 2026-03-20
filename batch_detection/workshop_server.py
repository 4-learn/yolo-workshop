"""
Workshop：批次偵測 API Server（填空版）

目錄結構：
batch_detection/
├── workshop_server.py  ← 你正在寫的檔案
├── server.py           ← 解答（先不要看！）
├── client0.py          ← 測試用 client
└── images/             ← 測試圖片

啟動方式：
  uvicorn workshop_server:app --reload

題目：
1. 完成 POST /detect：接收圖片 → YOLO 推論 → 回傳事件 → 存 CSV
2. 完成 save_to_csv()：把事件追加寫入 CSV
3. 完成 GET /events：讀 CSV 回傳事件，支援 min_confidence 篩選
"""

from fastapi import FastAPI, UploadFile
from ultralytics import YOLO
from datetime import datetime, timezone
import csv
import os
import pandas as pd

app = FastAPI()

LABEL_MAP = {0: "head", 1: "helmet"}
model = YOLO("best.pt")

CSV_FILE = "events.csv"
CSV_COLUMNS = [
    "source_image", "event_type", "confidence",
    "x1", "y1", "x2", "y2", "timestamp",
]


def save_to_csv(events):
    """
    把事件追加寫入 CSV

    TODO: 完成以下步驟
    1. 用 os.path.exists(CSV_FILE) 判斷檔案是否存在
    2. 用 open(CSV_FILE, "a") 開檔（追加模式）
    3. 用 csv.DictWriter 寫入每筆事件
    4. 如果檔案不存在，要先寫 header

    提示：
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            if not file_exists:
                writer.writeheader()
            for event in events:
                writer.writerow({
                    "source_image": event["source_image"],
                    "event_type": event["event_type"],
                    "confidence": event["confidence"],
                    "x1": event["bbox"]["x1"],
                    ...
                })
    """
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---


@app.post("/detect")
async def detect(file: UploadFile):
    """
    接收圖片，YOLO 推論，回傳事件

    TODO: 完成以下步驟
    1. 用 await file.read() 讀取圖片內容
    2. 存成 temp.jpg
    3. 用 model("temp.jpg") 推論
    4. 遍歷 results[0].boxes，組成事件陣列
    5. 刪除 temp.jpg
    6. 呼叫 save_to_csv(events) 存入 CSV
    7. 回傳結果

    提示：
        content = await file.read()
        with open("temp.jpg", "wb") as f:
            f.write(content)
        results = model("temp.jpg")

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            label = LABEL_MAP[class_id]
    """
    # --- 你的程式碼寫在這裡 ---

    return {
        "source_image": file.filename,
        "event_count": 0,
        "alert": False,
        "events": [],
    }
    # --- 結束 ---


@app.get("/events")
async def get_events(min_confidence: float = 0.0):
    """
    查詢已儲存的事件

    TODO: 完成以下步驟
    1. 用 pd.read_csv(CSV_FILE) 讀取 CSV
    2. 如果 min_confidence > 0，篩選 df["confidence"] >= min_confidence
    3. 用 df.to_dict(orient="records") 轉成 list of dict
    4. 回傳 {"total": ..., "events": ...}

    提示：
        df = pd.read_csv(CSV_FILE)
        if min_confidence > 0:
            df = df[df["confidence"] >= min_confidence]
    """
    if not os.path.exists(CSV_FILE):
        return {"total": 0, "events": []}

    # --- 你的程式碼寫在這裡 ---

    return {"total": 0, "events": []}
    # --- 結束 ---
