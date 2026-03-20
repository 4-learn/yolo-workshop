"""YOLO 偵測器"""

import random
from datetime import datetime, timezone

LABEL_MAP = {0: "head", 1: "helmet"}


class SafetyDetector:
    def __init__(self, model_path="best.pt", use_mock=False):
        self.use_mock = use_mock
        if not use_mock:
            from ultralytics import YOLO
            self.model = YOLO(model_path)

    def detect(self, image_path):
        if self.use_mock:
            return self._mock_detect(image_path)
        return self._real_detect(image_path)

    def _real_detect(self, image_path):
        results = self.model(image_path)
        events = []
        violations = 0

        for box in results[0].boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            label = LABEL_MAP[class_id]

            event = {
                "event_type": f"{label}_detected",
                "confidence": round(confidence, 4),
                "bbox": {"x1": round(x1, 2), "y1": round(y1, 2),
                         "x2": round(x2, 2), "y2": round(y2, 2)},
                "source_image": image_path,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            events.append(event)
            if label == "head":
                violations += 1

        return {
            "image_path": image_path,
            "total": len(events),
            "violations": violations,
            "events": events,
        }

    def _mock_detect(self, image_path):
        """模擬偵測結果（測試用）"""
        random.seed(hash(image_path) % 2**32)
        n = random.randint(2, 8)
        events = []
        violations = 0

        for _ in range(n):
            is_head = random.random() < 0.35
            label = "head" if is_head else "helmet"
            confidence = round(random.uniform(0.4, 0.95), 4)
            x1 = round(random.uniform(10, 300), 2)
            y1 = round(random.uniform(10, 200), 2)

            event = {
                "event_type": f"{label}_detected",
                "confidence": confidence,
                "bbox": {"x1": x1, "y1": y1,
                         "x2": round(x1 + random.uniform(20, 80), 2),
                         "y2": round(y1 + random.uniform(30, 100), 2)},
                "source_image": image_path,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            events.append(event)
            if is_head:
                violations += 1

        return {
            "image_path": image_path,
            "total": len(events),
            "violations": violations,
            "events": events,
        }
