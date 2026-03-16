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
2. 接收上傳圖片 + min_confidence query parameter
3. 跑 YOLO 偵測，組成事件 JSON 陣列
4. 如果有 head_detected → response 加上 alert: true
"""

from fastapi import FastAPI, UploadFile, Query
from ultralytics import YOLO
from datetime import datetime, timezone
import tempfile
import os

app = FastAPI(title="PPE Detection API")

# yolov8n 預設模型：0=person, ...（80 類 COCO）
# 偵測到 person → alert（代表有人但不確定是否穿戴 PPE）
ALERT_CLASSES = {"person"}
MODEL_PATH = "yolov8n.pt"

# 啟動時載入模型（只載入一次）
model = YOLO(MODEL_PATH)


@app.post("/detect")
async def detect(
    file: UploadFile,
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
):
    """
    接收圖片，回傳偵測事件 JSON

    TODO: 完成以下步驟
    1. 把上傳的圖片存成暫存檔（提示：tempfile.NamedTemporaryFile）
    2. 用 model() 對暫存檔跑 YOLO 推論
    3. 遍歷 results[0].boxes，組成事件 dict 陣列
       提示：label = results[0].names[class_id]
    4. 如果 label in ALERT_CLASSES → 設 has_alert = True
    5. 回傳 {"source_image": ..., "event_count": ..., "alert": ..., "events": [...]}
    6. 記得刪除暫存檔
    """
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---
    return {
        "source_image": file.filename,
        "event_count": 0,
        "alert": False,
        "events": [],
    }
