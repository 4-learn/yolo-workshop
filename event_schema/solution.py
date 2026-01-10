"""
Workshop 解答：Event 結構設計

題目要求：
1. 定義 PPEDetectionEvent Schema（使用 Pydantic）
2. 實作 convert_yolo_output 函式
3. 過濾 confidence < 0.5 的結果
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


# 類別對應表
CLASS_NAMES = {
    0: "person",
    1: "helmet",
    2: "no_helmet",
    3: "vest",
    4: "no_vest"
}


class PPEDetectionEvent(BaseModel):
    """PPE 偵測事件結構"""

    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    event_type: str = "ppe_detection"
    source: Optional[str] = None
    object: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: List[float] = Field(min_length=4, max_length=4)
    metadata: Optional[Dict[str, Any]] = None


def convert_yolo_output(
    yolo_results: list[dict],
    source: str = None,
    min_confidence: float = 0.5
) -> list[PPEDetectionEvent]:
    """
    將 YOLO 輸出轉換成 PPEDetectionEvent 列表

    Args:
        yolo_results: YOLO 偵測結果列表
        source: 攝影機來源 ID
        min_confidence: 最低信心閾值

    Returns:
        PPEDetectionEvent 列表
    """
    events = []

    for detection in yolo_results:
        # 過濾低信心結果
        if detection["confidence"] < min_confidence:
            continue

        # 轉換成 Event
        event = PPEDetectionEvent(
            source=source,
            object=CLASS_NAMES.get(
                detection["class_id"],
                f"unknown_{detection['class_id']}"
            ),
            confidence=detection["confidence"],
            bbox=detection["bbox"],
            metadata={"class_id": detection["class_id"]}
        )
        events.append(event)

    return events


# === 測試 ===
if __name__ == "__main__":
    # 模擬 YOLO 輸出
    yolo_output = [
        {"class_id": 0, "confidence": 0.92, "bbox": [100, 50, 200, 300]},
        {"class_id": 2, "confidence": 0.78, "bbox": [150, 60, 220, 280]},
        {"class_id": 4, "confidence": 0.35, "bbox": [300, 100, 400, 350]},
    ]

    # 轉換
    events = convert_yolo_output(yolo_output, source="camera_01")

    # 輸出 JSON
    print(f"共 {len(events)} 筆事件（已過濾 confidence < 0.5）\n")

    for event in events:
        print(event.model_dump_json(indent=2))
        print()
