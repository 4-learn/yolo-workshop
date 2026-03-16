"""
解答：批次偵測 API Server

啟動方式：
  uvicorn server:app --reload

測試：
  curl -X POST http://localhost:8000/detect \
    -F "file=@images/test1.jpg"
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

    - file: 上傳的圖片
    - min_confidence: 最低信心閾值（Query parameter）
    """
    # 1. 存成暫存檔
    suffix = os.path.splitext(file.filename or "img.jpg")[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 2. YOLO 推論
        results = model(tmp_path)

        # 3. 組成事件陣列
        events = []
        has_alert = False

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            if confidence < min_confidence:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            label = results[0].names[class_id]

            event = {
                "event_type": f"{label}_detected",
                "confidence": round(confidence, 4),
                "bbox": {
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2),
                },
                "source_image": file.filename,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            events.append(event)

            # 4. 偵測到 person → alert
            if label in ALERT_CLASSES:
                has_alert = True

        return {
            "source_image": file.filename,
            "event_count": len(events),
            "alert": has_alert,
            "events": events,
        }
    finally:
        os.unlink(tmp_path)
