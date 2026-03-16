"""
Workshop：批次偵測 API Server（填空版）

目錄結構：
batch_detection/
├── workshop_server.py ← 你正在寫的檔案
├── workshop_client.py ← 搭配的 client
├── server.py          ← 解答（先不要看！）
├── client.py          ← 解答（先不要看！）
├── best.pt            ← YOLO 模型
└── images/            ← 測試圖片
    └── *.jpg

啟動方式：
  uvicorn workshop_server:app --reload

題目：
1. 完成 POST /detect endpoint
2. 接收上傳圖片，存成 temp.jpg
3. 跑 YOLO 偵測，組成事件 JSON 陣列
4. 如果有 head_detected → response 加上 alert: true
"""

from fastapi import FastAPI, UploadFile
from ultralytics import YOLO
from datetime import datetime, timezone
import os

app = FastAPI()

# PPE 模型：0=head（沒戴安全帽）, 1=helmet（有戴安全帽）
LABEL_MAP = {0: "head", 1: "helmet"}
model = YOLO("best.pt")


@app.post("/detect")
async def detect(file: UploadFile):
    """
    接收圖片，回傳偵測事件 JSON

    TODO: 完成以下步驟
    1. 用 await file.read() 讀取上傳的圖片內容
    2. 用 open("temp.jpg", "wb") 存到本地
    3. 用 model("temp.jpg") 跑 YOLO 推論
    4. 遍歷 results[0].boxes，組成事件 dict 陣列
       - label = LABEL_MAP[class_id]
    5. 如果 label == "head" → 設 has_alert = True
    6. 用 os.remove("temp.jpg") 清理暫存檔
    7. 回傳 {"source_image": ..., "event_count": ..., "alert": ..., "events": [...]}
    """
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---
    return {
        "source_image": file.filename,
        "event_count": 0,
        "alert": False,
        "events": [],
    }
