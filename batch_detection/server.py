"""
解答：批次偵測 API Server

啟動方式：
  uvicorn server:app --reload

測試：
  curl -X POST http://localhost:8000/detect \
    -F "file=@images/mixed1.jpg"
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
    # 1. 把上傳的圖片存到本地
    content = await file.read()
    with open("temp.jpg", "wb") as f:
        f.write(content)

    # 2. YOLO 推論
    results = model("temp.jpg")

    # 3. 組成事件陣列
    events = []
    has_alert = False

    for box in results[0].boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        label = LABEL_MAP[class_id]

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

        # 4. 沒戴安全帽 → alert
        if label == "head":
            has_alert = True

    # 5. 清理暫存檔
    os.remove("temp.jpg")

    return {
        "source_image": file.filename,
        "event_count": len(events),
        "alert": has_alert,
        "events": events,
    }
