"""
Workshop 解答：從圖片到事件 JSON（整合版）

整合 YOLO 推論 + 事件轉換，一支程式搞定：
  輸入圖片 → YOLO 偵測 → 事件 JSON 陣列

目錄結構：
event_schema/
├── workshop.py          ← 學生填空版
├── solution_simple.py   ← 本檔案（解答）
├── best.pt              ← 訓練好的 YOLO 模型
└── sample_data/
    ├── test.jpg         ← 輸入：測試圖片
    └── test.txt         ← 參考：YOLO 標註格式

執行方式：
  python solution_simple.py
"""

from ultralytics import YOLO
from datetime import datetime, timezone
import json
import os

LABEL_MAP = {0: "head", 1: "helmet"}


def detect_and_convert(image_path, model_path="best.pt", min_confidence=0.0):
    """
    輸入圖片路徑，回傳事件 JSON 陣列

    Args:
        image_path: 圖片路徑
        model_path: YOLO 模型路徑
        min_confidence: 最低信心閾值（延伸題：設為 0.5）

    Returns:
        事件 dict 的 list
    """
    # 1. 載入模型
    model = YOLO(model_path)

    # 2. 對圖片推論
    results = model(image_path)

    # 3. 遍歷偵測結果，組成事件陣列
    events = []
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        # 過濾低信心結果
        if confidence < min_confidence:
            continue

        label = LABEL_MAP.get(class_id, f"unknown_{class_id}")

        event = {
            "event_type": f"{label}_detected",
            "confidence": round(confidence, 4),
            "bbox": {
                "x1": round(x1, 2),
                "y1": round(y1, 2),
                "x2": round(x2, 2),
                "y2": round(y2, 2),
            },
            "source_image": os.path.basename(image_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        events.append(event)

    return events


if __name__ == "__main__":
    events = detect_and_convert("sample_data/test.jpg")
    print(json.dumps(events, indent=2, ensure_ascii=False))
    print(f"\n共 {len(events)} 筆事件")
