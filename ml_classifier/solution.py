"""
Workshop 解答：ML-based 事件分類

題目要求：
1. 特徵工程：從事件中提取至少 8 個特徵
2. 模型訓練：使用 Random Forest
3. 模型評估：計算各項指標
4. 整合測試：實作 HybridClassifier
"""

import numpy as np
import random
from datetime import datetime, timezone, timedelta
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import uuid

from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


# === Enums ===

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Action(str, Enum):
    VIOLATION = "violation"
    WARNING = "warning"
    IGNORE = "ignore"
    ALERT = "alert"


# === Schema ===

class PPEDetectionEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str = "ppe_detection"
    source: Optional[str] = None
    object: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: list[float] = Field(min_length=4, max_length=4)
    metadata: Optional[dict] = None


# === 特徵工程 ===

FEATURE_NAMES = [
    "confidence",       # YOLO 信心分數
    "bbox_width",       # 邊界框寬度
    "bbox_height",      # 邊界框高度
    "bbox_area",        # 邊界框面積
    "bbox_aspect_ratio", # 寬高比
    "bbox_center_x",    # 中心點 X
    "bbox_center_y",    # 中心點 Y
    "hour_of_day",      # 小時
    "is_weekend",       # 是否週末
]


def extract_features(event: PPEDetectionEvent) -> np.ndarray:
    """
    從事件中提取特徵

    特徵說明：
    1. confidence: YOLO 信心分數，低信心可能是誤判
    2. bbox_width: 邊界框寬度，太小可能是遠處或部分遮擋
    3. bbox_height: 邊界框高度，同上
    4. bbox_area: 面積，反映物件大小
    5. bbox_aspect_ratio: 寬高比，異常比例可能是誤判
    6. bbox_center_x: 中心點 X，邊緣位置可能是誤判
    7. bbox_center_y: 中心點 Y，同上
    8. hour_of_day: 小時，不同時段的違規模式不同
    9. is_weekend: 是否週末，週末的工作模式不同
    """
    x1, y1, x2, y2 = event.bbox
    width = x2 - x1
    height = y2 - y1
    area = width * height
    aspect_ratio = width / height if height > 0 else 0
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    hour = event.timestamp.hour
    is_weekend = 1 if event.timestamp.weekday() >= 5 else 0

    return np.array([
        event.confidence,
        width,
        height,
        area,
        aspect_ratio,
        center_x,
        center_y,
        hour,
        is_weekend,
    ])


# === 模型 ===

class ViolationClassifier:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.is_trained = False

    def train(self, X: np.ndarray, y: np.ndarray) -> dict:
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        return {
            "train_accuracy": self.model.score(X_scaled, y),
            "n_samples": len(y),
            "n_features": X.shape[1],
        }

    def predict(self, event: PPEDetectionEvent) -> dict:
        features = extract_features(event)
        features_scaled = self.scaler.transform([features])
        prediction = self.model.predict(features_scaled)[0]
        probability = self.model.predict_proba(features_scaled)[0]
        return {
            "is_violation": bool(prediction),
            "probability": float(probability[1]),
            "features": dict(zip(FEATURE_NAMES, features.tolist())),
        }

    def get_feature_importance(self) -> dict:
        return dict(zip(FEATURE_NAMES, self.model.feature_importances_.tolist()))


# === 規則引擎（簡化版）===

class RuleConditions(BaseModel):
    object: Optional[str] = None
    confidence_gte: Optional[float] = None
    confidence_lte: Optional[float] = None
    zone: Optional[str] = None


class Rule(BaseModel):
    id: str
    name: str
    conditions: RuleConditions
    action: Action = Action.VIOLATION
    priority: int = 0


@dataclass
class RuleResult:
    matched: bool
    rule: Optional[Rule] = None
    action: Optional[Action] = None


class RuleEngine:
    def __init__(self, rules: list[Rule], zone_map: dict = None):
        self.rules = sorted(rules, key=lambda r: -r.priority)
        self.zone_map = zone_map or {}

    def _get_zone(self, bbox: list) -> Optional[str]:
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        for zone_name, regions in self.zone_map.items():
            for region in regions:
                if region[0] <= cx <= region[2] and region[1] <= cy <= region[3]:
                    return zone_name
        return None

    def evaluate(self, event: PPEDetectionEvent) -> RuleResult:
        for rule in self.rules:
            cond = rule.conditions
            if cond.object and event.object != cond.object:
                continue
            if cond.confidence_gte and event.confidence < cond.confidence_gte:
                continue
            if cond.confidence_lte and event.confidence > cond.confidence_lte:
                continue
            if cond.zone and self._get_zone(event.bbox) != cond.zone:
                continue
            return RuleResult(matched=True, rule=rule, action=rule.action)
        return RuleResult(matched=False)


# === 混合分類器 ===

class HybridClassifier:
    def __init__(self, rule_engine: RuleEngine, ml_classifier: ViolationClassifier, ml_threshold: float = 0.7):
        self.rule_engine = rule_engine
        self.ml_classifier = ml_classifier
        self.ml_threshold = ml_threshold

    def classify(self, event: PPEDetectionEvent) -> dict:
        rule_result = self.rule_engine.evaluate(event)

        if rule_result.matched and rule_result.action == Action.IGNORE:
            return {"action": Action.IGNORE, "reason": "規則忽略"}

        if rule_result.matched and rule_result.action == Action.VIOLATION:
            ml_result = self.ml_classifier.predict(event)
            if ml_result["probability"] >= self.ml_threshold:
                return {"action": Action.VIOLATION, "probability": ml_result["probability"], "reason": "規則+ML確認"}
            else:
                return {"action": Action.WARNING, "probability": ml_result["probability"], "reason": "ML信心不足"}

        ml_result = self.ml_classifier.predict(event)
        if ml_result["probability"] >= self.ml_threshold:
            return {"action": Action.WARNING, "probability": ml_result["probability"], "reason": "ML偵測"}

        return {"action": Action.IGNORE, "reason": "無違規"}


# === 資料生成 ===

def generate_training_data(n_samples: int = 10000) -> list[dict]:
    """產生訓練資料"""
    labeled_events = []
    base_time = datetime.now(timezone.utc)

    for i in range(n_samples):
        confidence = random.uniform(0.4, 0.99)
        width = random.uniform(30, 250)
        height = random.uniform(60, 450)
        x1 = random.uniform(0, 600)
        y1 = random.uniform(0, 400)
        hour = random.randint(0, 23)
        day_offset = random.randint(0, 6)

        event = PPEDetectionEvent(
            timestamp=base_time + timedelta(hours=hour, days=day_offset),
            object="no_helmet",
            confidence=confidence,
            bbox=[x1, y1, x1 + width, y1 + height],
            source="camera_01"
        )

        # 標籤邏輯
        is_violation = (
            confidence > 0.65 and
            width > 70 and
            height > 120 and
            width * height > 15000 and
            random.random() > 0.15
        )

        labeled_events.append({"event": event, "is_violation": is_violation})

    return labeled_events


# === 主程式 ===

def main():
    print("=== 模型訓練結果 ===")

    # 產生資料
    labeled_events = generate_training_data(10000)

    # 準備資料集
    X = np.array([extract_features(item["event"]) for item in labeled_events])
    y = np.array([1 if item["is_violation"] else 0 for item in labeled_events])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"訓練樣本: {len(X_train)}")
    print(f"測試樣本: {len(X_test)}")
    print(f"特徵數量: {X.shape[1]}")

    # 訓練
    classifier = ViolationClassifier()
    classifier.train(X_train, y_train)

    # 評估
    print("\n=== 模型評估 ===")
    X_test_scaled = classifier.scaler.transform(X_test)
    y_pred = classifier.model.predict(X_test_scaled)

    print(f"Accuracy:  {accuracy_score(y_test, y_pred):.3f}")
    print(f"Precision: {precision_score(y_test, y_pred):.3f}")
    print(f"Recall:    {recall_score(y_test, y_pred):.3f}")
    print(f"F1 Score:  {f1_score(y_test, y_pred):.3f}")

    cm = confusion_matrix(y_test, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"              Predicted")
    print(f"              Non-Vio  Violation")
    print(f"Actual Non-Vio   {cm[0][0]:4d}      {cm[0][1]:4d}")
    print(f"       Violation {cm[1][0]:4d}      {cm[1][1]:4d}")

    # 特徵重要性
    print("\n=== 特徵重要性 ===")
    importance = classifier.get_feature_importance()
    for name, score in sorted(importance.items(), key=lambda x: -x[1]):
        bar = "█" * int(score * 40)
        print(f"{name:20} {bar} {score:.3f}")

    # 混合分類器測試
    print("\n=== 混合分類器測試 ===")

    zone_map = {"construction": [[0, 0, 400, 600]]}
    rules = [
        Rule(id="r1", name="施工區違規", conditions=RuleConditions(object="no_helmet", zone="construction", confidence_gte=0.6), action=Action.VIOLATION, priority=10),
        Rule(id="r2", name="低信心忽略", conditions=RuleConditions(confidence_lte=0.5), action=Action.IGNORE, priority=100),
    ]

    rule_engine = RuleEngine(rules, zone_map)
    hybrid = HybridClassifier(rule_engine, classifier, ml_threshold=0.7)

    # 比較純 Rule vs Rule+ML
    test_events = [item["event"] for item in labeled_events[-200:]]
    test_labels = [item["is_violation"] for item in labeled_events[-200:]]

    # 純 Rule
    rule_preds = []
    for event in test_events:
        result = rule_engine.evaluate(event)
        rule_preds.append(1 if result.matched and result.action == Action.VIOLATION else 0)

    # Rule + ML
    hybrid_preds = []
    for event in test_events:
        result = hybrid.classify(event)
        hybrid_preds.append(1 if result["action"] == Action.VIOLATION else 0)

    rule_precision = precision_score(test_labels, rule_preds, zero_division=0)
    rule_recall = recall_score(test_labels, rule_preds, zero_division=0)
    hybrid_precision = precision_score(test_labels, hybrid_preds, zero_division=0)
    hybrid_recall = recall_score(test_labels, hybrid_preds, zero_division=0)

    print(f"純 Rule:    Precision={rule_precision:.2f}, Recall={rule_recall:.2f}")
    print(f"Rule + ML:  Precision={hybrid_precision:.2f}, Recall={hybrid_recall:.2f}")


if __name__ == "__main__":
    main()
