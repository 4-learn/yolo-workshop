"""
解答：批次偵測 API Server

啟動方式：
  uvicorn server:app --reload

測試：
  # 偵測圖片（會自動存入 CSV）
  curl -X POST http://localhost:8000/detect \
    -F "file=@images/mixed1.jpg"

  # 查詢所有事件
  curl http://localhost:8000/events

  # 查詢信心度 >= 0.8 的事件
  curl "http://localhost:8000/events?min_confidence=0.8"
"""

from fastapi import FastAPI, UploadFile
from ultralytics import YOLO
from datetime import datetime, timezone
import csv
import os
import pandas as pd

app = FastAPI()

# PPE 模型：0=head（沒戴安全帽）, 1=helmet（有戴安全帽）
LABEL_MAP = {0: "head", 1: "helmet"}
model = YOLO("best.pt")

CSV_FILE = "events.csv"
CSV_COLUMNS = [
    "source_image", "event_type", "confidence",
    "x1", "y1", "x2", "y2", "timestamp",
]


def save_to_csv(events):
    """把事件追加寫入 CSV"""
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
                "y1": event["bbox"]["y1"],
                "x2": event["bbox"]["x2"],
                "y2": event["bbox"]["y2"],
                "timestamp": event["timestamp"],
            })


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

    # 6. 存入 CSV
    save_to_csv(events)

    return {
        "source_image": file.filename,
        "event_count": len(events),
        "alert": has_alert,
        "events": events,
    }


@app.get("/events")
async def get_events(min_confidence: float = 0.0):
    """
    查詢已儲存的事件

    Query parameters:
      min_confidence: 最低信心度（預設 0.0，回傳全部）

    範例：
      GET /events                      → 全部事件
      GET /events?min_confidence=0.8   → 信心度 >= 0.8 的事件
    """
    if not os.path.exists(CSV_FILE):
        return {"total": 0, "events": []}

    df = pd.read_csv(CSV_FILE)

    # 篩選信心度
    if min_confidence > 0:
        df = df[df["confidence"] >= min_confidence]

    return {
        "total": len(df),
        "events": df.to_dict(orient="records"),
    }
