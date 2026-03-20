"""
解答：工安監控系統 MVP Server

啟動方式：
  uvicorn server:app --reload

API：
  POST /detect                     → 偵測圖片，存 CSV
  GET  /events                     → 查詢所有事件
  GET  /events?min_confidence=0.8  → 篩選高信心事件
  GET  /recalibrate                → sklearn 重算門檻
"""

from fastapi import FastAPI, UploadFile
from ultralytics import YOLO
from datetime import datetime, timezone
from sklearn.cluster import KMeans
import csv
import os
import shutil
import pandas as pd

app = FastAPI()

# PPE 模型：0=head（沒戴安全帽）, 1=helmet（有戴安全帽）
LABEL_MAP = {0: "head", 1: "helmet"}
model = YOLO("best.pt")

CSV_FILE = "events.csv"
SEED_FILE = "events_seed.csv"

# 啟動時載入 seed 資料（模擬歷史累積）
if os.path.exists(SEED_FILE) and not os.path.exists(CSV_FILE):
    shutil.copy(SEED_FILE, CSV_FILE)
    print(f"✅ 載入 seed 資料（{SEED_FILE}）")
CSV_COLUMNS = [
    "source_image", "event_type", "confidence",
    "x1", "y1", "x2", "y2", "timestamp",
]

# 偵測計數器（每 N 次自動校準）
detect_count = 0
RECALIBRATE_EVERY = 3  # 預設 3 次（方便測試，實務上可改 100）


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


def run_recalibrate():
    """用 KMeans 分群，算出建議門檻"""
    if not os.path.exists(CSV_FILE):
        return None

    df = pd.read_csv(CSV_FILE)
    if len(df) < 10:
        return None

    X = df[["confidence"]]
    kmeans = KMeans(n_clusters=3, random_state=42)
    kmeans.fit(X)
    centers = sorted(kmeans.cluster_centers_.flatten())

    return {
        "total_events": len(df),
        "centers": [round(c, 4) for c in centers],
        "threshold_low": round((centers[0] + centers[1]) / 2, 4),
        "threshold_high": round((centers[1] + centers[2]) / 2, 4),
    }


@app.post("/detect")
async def detect(file: UploadFile):
    global detect_count
    detect_count += 1

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

    # 7. 每 100 次自動校準
    calibration = None
    if detect_count % RECALIBRATE_EVERY == 0:
        calibration = run_recalibrate()
        print(f"🔄 第 {detect_count} 次偵測，自動校準：{calibration}")

    return {
        "source_image": file.filename,
        "event_count": len(events),
        "alert": has_alert,
        "events": events,
        "detect_count": detect_count,
        "calibration": calibration,
    }


@app.get("/events")
async def get_events(min_confidence: float = 0.0):
    """
    查詢已儲存的事件

    範例：
      GET /events                      → 全部事件
      GET /events?min_confidence=0.8   → 信心度 >= 0.8 的事件
    """
    if not os.path.exists(CSV_FILE):
        return {"total": 0, "events": []}

    df = pd.read_csv(CSV_FILE)

    if min_confidence > 0:
        df = df[df["confidence"] >= min_confidence]

    return {
        "total": len(df),
        "events": df.to_dict(orient="records"),
    }


@app.get("/recalibrate")
async def recalibrate():
    """
    手動觸發 sklearn 校準

    用 KMeans 分群，回傳建議的 confidence 門檻。

    範例：
      GET /recalibrate
    """
    result = run_recalibrate()
    if result is None:
        return {"error": "資料不足（需要至少 10 筆）"}
    return result
