"""
Workshop 解答：系統整合示範

題目要求：
1. 建立整合管線：SafetyMonitoringPipeline
2. 實作告警管理：AlertManager
3. 產生報表
4. 模擬測試
"""

import random
import json
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable
import uuid

from pydantic import BaseModel, Field
from enum import Enum


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


# === Rule Engine ===

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
    severity: Severity = Severity.MEDIUM
    message: str = ""
    priority: int = 0


@dataclass
class RuleResult:
    matched: bool
    rule: Optional[Rule] = None
    action: Optional[Action] = None
    severity: Optional[Severity] = None
    message: str = ""


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
            return RuleResult(
                matched=True,
                rule=rule,
                action=rule.action,
                severity=rule.severity,
                message=rule.message
            )
        return RuleResult(matched=False)


# === Deduplicator ===

def calculate_iou(box1: list, box2: list) -> float:
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    if x2 <= x1 or y2 <= y1:
        return 0.0
    intersection = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    return intersection / union if union > 0 else 0.0


class EventDeduplicator:
    def __init__(self, iou_threshold: float = 0.5, time_window: timedelta = timedelta(seconds=2)):
        self.iou_threshold = iou_threshold
        self.time_window = time_window
        self.recent_events: list[PPEDetectionEvent] = []

    def is_duplicate(self, event: PPEDetectionEvent) -> bool:
        now = event.timestamp
        self.recent_events = [
            e for e in self.recent_events
            if now - e.timestamp < self.time_window
        ]
        for recent in self.recent_events:
            if recent.object != event.object:
                continue
            iou = calculate_iou(recent.bbox, event.bbox)
            if iou > self.iou_threshold:
                return True
        return False

    def process(self, event: PPEDetectionEvent) -> Optional[PPEDetectionEvent]:
        if self.is_duplicate(event):
            return None
        self.recent_events.append(event)
        return event


# === Aggregator ===

class SlidingWindowStats:
    def __init__(self, window: timedelta, group_by: Optional[Callable] = None):
        self.window = window
        self.group_by = group_by
        self.events: deque = deque()

    def add(self, event: PPEDetectionEvent) -> None:
        self.events.append(event)
        self._cleanup(event.timestamp)

    def _cleanup(self, current_time: datetime) -> None:
        cutoff = current_time - self.window
        while self.events and self.events[0].timestamp < cutoff:
            self.events.popleft()

    def get_count(self) -> int:
        return len(self.events)

    def get_counts_by_group(self) -> dict[str, int]:
        if not self.group_by:
            return {"total": len(self.events)}
        counts = defaultdict(int)
        for event in self.events:
            key = self.group_by(event)
            counts[key] += 1
        return dict(counts)

    def get_rate(self) -> float:
        if not self.events:
            return 0.0
        return len(self.events) / (self.window.total_seconds() / 60)

    def clear(self) -> None:
        self.events.clear()


# === Processing Result ===

@dataclass
class ProcessingResult:
    event: PPEDetectionEvent
    is_duplicate: bool
    action: Action
    severity: Optional[Severity]
    reason: str
    ml_probability: Optional[float] = None


# === Alert ===

@dataclass
class Alert:
    id: str
    timestamp: datetime
    event: PPEDetectionEvent
    action: Action
    severity: Severity
    reason: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class AlertManager:
    def __init__(self, max_alerts: int = 1000):
        self.alerts: list[Alert] = []
        self.max_alerts = max_alerts
        self.alert_count = 0

    def create_alert(self, result: ProcessingResult) -> Alert:
        self.alert_count += 1
        alert = Alert(
            id=f"alert_{self.alert_count:06d}",
            timestamp=datetime.now(timezone.utc),
            event=result.event,
            action=result.action,
            severity=result.severity or Severity.MEDIUM,
            reason=result.reason,
        )
        self.alerts.append(alert)
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        return alert

    def get_unacknowledged(self) -> list[Alert]:
        return [a for a in self.alerts if not a.acknowledged]

    def acknowledge(self, alert_id: str, by: str) -> bool:
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = by
                alert.acknowledged_at = datetime.now(timezone.utc)
                return True
        return False

    def get_stats(self) -> dict:
        by_severity = {}
        for alert in self.alerts:
            sev = alert.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return {
            "total": len(self.alerts),
            "unacknowledged": len(self.get_unacknowledged()),
            "by_severity": by_severity,
        }


# === YOLO Simulator ===

class YOLOSimulator:
    def __init__(self, frame_width: int = 800, frame_height: int = 600, violation_rate: float = 0.3):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.violation_rate = violation_rate
        self.frame_count = 0

    def detect(self, num_objects: int = None) -> list[PPEDetectionEvent]:
        if num_objects is None:
            num_objects = random.randint(1, 5)
        self.frame_count += 1
        events = []
        for _ in range(num_objects):
            is_violation = random.random() < self.violation_rate
            if is_violation:
                obj = random.choice(["no_helmet", "no_vest"])
                confidence = random.uniform(0.6, 0.95)
            else:
                obj = random.choice(["helmet", "vest", "person"])
                confidence = random.uniform(0.7, 0.99)
            width = random.uniform(50, 150)
            height = random.uniform(100, 300)
            x1 = random.uniform(0, self.frame_width - width)
            y1 = random.uniform(0, self.frame_height - height)
            events.append(PPEDetectionEvent(
                timestamp=datetime.now(timezone.utc),
                object=obj,
                confidence=confidence,
                bbox=[x1, y1, x1 + width, y1 + height],
                source="camera_01",
                metadata={"frame_id": self.frame_count}
            ))
        return events


# === LLM Interface ===

class LLMInterface(ABC):
    @abstractmethod
    def generate_alert_message(self, alert: Alert) -> str:
        pass

    @abstractmethod
    def suggest_regulations(self, violation_type: str) -> list[str]:
        pass


class SimpleLLMPlaceholder(LLMInterface):
    MESSAGES = {
        "no_helmet": "偵測到人員未配戴安全帽，請立即處理。",
        "no_vest": "偵測到人員未穿著反光背心，請注意安全。",
    }
    REGULATIONS = {
        "no_helmet": [
            "職業安全衛生設施規則 第 281 條",
            "營造安全衛生設施標準 第 11-1 條",
        ],
        "no_vest": [
            "職業安全衛生設施規則 第 21 條",
        ],
    }

    def generate_alert_message(self, alert: Alert) -> str:
        base_msg = self.MESSAGES.get(alert.event.object, "偵測到安全違規。")
        return f"[{alert.severity.value.upper()}] {base_msg}"

    def suggest_regulations(self, violation_type: str) -> list[str]:
        return self.REGULATIONS.get(violation_type, [])


# === Pipeline ===

class SafetyMonitoringPipeline:
    def __init__(
        self,
        rules: list[Rule],
        zone_map: dict,
        on_violation: Optional[Callable[[ProcessingResult], None]] = None,
    ):
        self.zone_map = zone_map
        self.deduplicator = EventDeduplicator(iou_threshold=0.5, time_window=timedelta(seconds=2))
        self.rule_engine = RuleEngine(rules, zone_map)
        self.realtime_window = SlidingWindowStats(
            window=timedelta(minutes=5),
            group_by=lambda e: e.object
        )
        self.on_violation = on_violation
        self.total_events = 0
        self.deduped_events = 0
        self.violations = 0
        self.by_object: dict[str, int] = defaultdict(int)
        self.by_zone: dict[str, int] = defaultdict(int)
        self.by_severity: dict[str, int] = defaultdict(int)

    def _get_zone(self, bbox: list) -> str:
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        for zone_name, regions in self.zone_map.items():
            for region in regions:
                if region[0] <= cx <= region[2] and region[1] <= cy <= region[3]:
                    return zone_name
        return "unknown"

    def process(self, event: PPEDetectionEvent) -> ProcessingResult:
        self.total_events += 1

        # 1. 去重
        deduped = self.deduplicator.process(event)
        if deduped is None:
            return ProcessingResult(
                event=event,
                is_duplicate=True,
                action=Action.IGNORE,
                severity=None,
                reason="重複事件"
            )

        self.deduped_events += 1

        # 2. 規則判斷
        rule_result = self.rule_engine.evaluate(event)
        action = rule_result.action if rule_result.matched else Action.IGNORE
        severity = rule_result.severity if rule_result.matched else None
        reason = rule_result.message if rule_result.matched else "無匹配規則"

        # 3. 統計
        self.realtime_window.add(event)

        if action == Action.VIOLATION:
            self.violations += 1
            self.by_object[event.object] += 1
            zone = self._get_zone(event.bbox)
            self.by_zone[zone] += 1
            if severity:
                self.by_severity[severity.value] += 1

        result = ProcessingResult(
            event=event,
            is_duplicate=False,
            action=action,
            severity=severity,
            reason=reason,
        )

        if action == Action.VIOLATION and self.on_violation:
            self.on_violation(result)

        return result

    def get_stats(self) -> dict:
        return {
            "total_events": self.total_events,
            "deduped_events": self.deduped_events,
            "violations": self.violations,
            "by_object": dict(self.by_object),
            "by_zone": dict(self.by_zone),
            "by_severity": dict(self.by_severity),
            "realtime_5min": self.realtime_window.get_count(),
            "rate": self.realtime_window.get_rate(),
        }


# === Main ===

def main():
    print("=== 工安監控系統整合測試 ===\n")

    # 區域
    zone_map = {
        "construction": [[0, 0, 400, 600]],
        "office": [[400, 0, 700, 600]],
        "entrance": [[700, 0, 800, 600]],
    }

    # 規則
    rules = [
        Rule(
            id="r1", name="施工區安全帽",
            conditions=RuleConditions(object="no_helmet", zone="construction", confidence_gte=0.6),
            action=Action.VIOLATION, severity=Severity.HIGH,
            message="施工區未配戴安全帽", priority=10
        ),
        Rule(
            id="r2", name="施工區反光背心",
            conditions=RuleConditions(object="no_vest", zone="construction", confidence_gte=0.6),
            action=Action.VIOLATION, severity=Severity.MEDIUM,
            message="施工區未穿著反光背心", priority=10
        ),
        Rule(
            id="r3", name="入口區安全帽",
            conditions=RuleConditions(object="no_helmet", zone="entrance", confidence_gte=0.7),
            action=Action.VIOLATION, severity=Severity.LOW,
            message="入口區未配戴安全帽", priority=5
        ),
        Rule(
            id="r4", name="低信心忽略",
            conditions=RuleConditions(confidence_lte=0.5),
            action=Action.IGNORE, priority=100
        ),
    ]

    # 告警管理
    alert_manager = AlertManager()

    def on_violation(result: ProcessingResult):
        alert_manager.create_alert(result)

    # 管線
    pipeline = SafetyMonitoringPipeline(
        rules=rules,
        zone_map=zone_map,
        on_violation=on_violation,
    )

    # 模擬
    simulator = YOLOSimulator(frame_width=800, frame_height=600, violation_rate=0.4)

    print("模擬 100 個影格...\n")
    for _ in range(100):
        events = simulator.detect(num_objects=3)
        for event in events:
            pipeline.process(event)

    # 統計
    stats = pipeline.get_stats()

    print("=== 處理統計 ===")
    print(f"總事件: {stats['total_events']}")
    print(f"去重後: {stats['deduped_events']}")
    print(f"違規: {stats['violations']}")
    print(f"告警: 0")

    print("\n=== 違規分布 ===")
    print("依物件:")
    total_v = stats['violations'] if stats['violations'] > 0 else 1
    for obj, count in stats['by_object'].items():
        pct = count / total_v * 100
        print(f"  {obj}: {count} ({pct:.1f}%)")

    print("\n依區域:")
    for zone, count in stats['by_zone'].items():
        pct = count / total_v * 100
        print(f"  {zone}: {count} ({pct:.1f}%)")

    print("\n依嚴重度:")
    for sev, count in stats['by_severity'].items():
        print(f"  {sev.upper()}: {count}")

    print("\n=== 即時監控 ===")
    print(f"過去 5 分鐘違規: {stats['realtime_5min']}")
    print(f"違規速率: {stats['rate']:.1f} 次/分鐘")

    print("\n=== 告警管理 ===")
    alert_stats = alert_manager.get_stats()
    print(f"待處理告警: {alert_stats['unacknowledged']}")
    print(f"已確認: {alert_stats['total'] - alert_stats['unacknowledged']}")

    print("\n=== LLM 介面測試 ===")
    llm = SimpleLLMPlaceholder()
    unack = alert_manager.get_unacknowledged()
    if unack:
        alert = unack[0]
        print(f"告警訊息: {llm.generate_alert_message(alert)}")
        print(f"相關法規: {llm.suggest_regulations(alert.event.object)}")


if __name__ == "__main__":
    main()
