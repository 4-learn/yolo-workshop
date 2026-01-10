"""
Workshop 解答：Rule-based 事件判斷

題目要求：
1. 基本規則：施工區必須戴安全帽和反光背心，低信心忽略
2. 時間規則：夜間升級為 CRITICAL，午休只發 WARNING
3. 區域規則：辦公區不強制安全帽，入口區只需安全帽
4. 攝影機規則：camera_vip 直接 ALERT
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional
import uuid

from pydantic import BaseModel, Field


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


class RuleConditions(BaseModel):
    object: Optional[str] = None
    confidence_gte: Optional[float] = None
    confidence_lte: Optional[float] = None
    zone: Optional[str] = None
    source: Optional[str] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None


class Rule(BaseModel):
    id: str
    name: str
    conditions: RuleConditions
    action: Action = Action.VIOLATION
    severity: Severity = Severity.MEDIUM
    message: str = ""
    enabled: bool = True
    priority: int = 0


@dataclass
class RuleResult:
    matched: bool
    rule: Optional[Rule] = None
    action: Optional[Action] = None
    severity: Optional[Severity] = None
    message: str = ""


# === Rule Matcher ===

class RuleMatcher:
    def __init__(self, zone_map: dict[str, list] = None):
        self.zone_map = zone_map or {}

    def get_zone(self, bbox: list) -> Optional[str]:
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        for zone_name, regions in self.zone_map.items():
            for region in regions:
                if region[0] <= cx <= region[2] and region[1] <= cy <= region[3]:
                    return zone_name
        return None

    def match(self, event: PPEDetectionEvent, rule: Rule) -> bool:
        cond = rule.conditions

        if cond.object is not None and event.object != cond.object:
            return False

        if cond.confidence_gte is not None and event.confidence < cond.confidence_gte:
            return False

        if cond.confidence_lte is not None and event.confidence > cond.confidence_lte:
            return False

        if cond.zone is not None:
            event_zone = self.get_zone(event.bbox)
            if event_zone != cond.zone:
                return False

        if cond.source is not None and event.source != cond.source:
            return False

        if cond.time_start is not None and cond.time_end is not None:
            event_time = event.timestamp.strftime("%H:%M")
            if cond.time_start <= cond.time_end:
                if not (cond.time_start <= event_time <= cond.time_end):
                    return False
            else:
                if not (event_time >= cond.time_start or event_time <= cond.time_end):
                    return False

        return True


class RuleEngine:
    def __init__(self, rules: list[Rule], zone_map: dict = None):
        self.rules = sorted(rules, key=lambda r: -r.priority)
        self.matcher = RuleMatcher(zone_map)

    def evaluate(self, event: PPEDetectionEvent) -> RuleResult:
        for rule in self.rules:
            if not rule.enabled:
                continue
            if self.matcher.match(event, rule):
                return RuleResult(
                    matched=True,
                    rule=rule,
                    action=rule.action,
                    severity=rule.severity,
                    message=rule.message or f"違反規則: {rule.name}"
                )
        return RuleResult(matched=False)


# === 規則定義 ===

zone_map = {
    "construction": [[0, 0, 400, 600]],
    "office": [[400, 0, 800, 600]],
    "entrance": [[350, 500, 450, 600]],
}

rules = [
    # 最高優先級：低信心忽略
    Rule(
        id="rule_low_conf",
        name="低信心偵測忽略",
        conditions=RuleConditions(confidence_lte=0.6),
        action=Action.IGNORE,
        message="信心分數過低",
        priority=200
    ),

    # 高優先級：VIP 攝影機
    Rule(
        id="rule_vip_camera",
        name="VIP 攝影機違規",
        conditions=RuleConditions(
            object="no_helmet",
            source="camera_vip",
            confidence_gte=0.6
        ),
        action=Action.ALERT,
        severity=Severity.CRITICAL,
        message="VIP 區域違規立即告警",
        priority=150
    ),
    Rule(
        id="rule_vip_camera_vest",
        name="VIP 攝影機違規（反光背心）",
        conditions=RuleConditions(
            object="no_vest",
            source="camera_vip",
            confidence_gte=0.6
        ),
        action=Action.ALERT,
        severity=Severity.CRITICAL,
        message="VIP 區域違規立即告警",
        priority=150
    ),

    # 時間規則：夜間升級
    Rule(
        id="rule_night_helmet",
        name="夜間施工區違規（安全帽）",
        conditions=RuleConditions(
            object="no_helmet",
            zone="construction",
            confidence_gte=0.6,
            time_start="18:00",
            time_end="06:00"
        ),
        action=Action.VIOLATION,
        severity=Severity.CRITICAL,
        message="夜間施工區違規",
        priority=100
    ),
    Rule(
        id="rule_night_vest",
        name="夜間施工區違規（反光背心）",
        conditions=RuleConditions(
            object="no_vest",
            zone="construction",
            confidence_gte=0.6,
            time_start="18:00",
            time_end="06:00"
        ),
        action=Action.VIOLATION,
        severity=Severity.CRITICAL,
        message="夜間施工區違規",
        priority=100
    ),

    # 時間規則：午休警告
    Rule(
        id="rule_lunch_helmet",
        name="午休時間違規（安全帽）",
        conditions=RuleConditions(
            object="no_helmet",
            zone="construction",
            confidence_gte=0.6,
            time_start="12:00",
            time_end="13:00"
        ),
        action=Action.WARNING,
        severity=Severity.LOW,
        message="午休時間違規，僅警告",
        priority=90
    ),

    # 區域規則：辦公區忽略安全帽
    Rule(
        id="rule_office_helmet",
        name="辦公區不強制安全帽",
        conditions=RuleConditions(
            object="no_helmet",
            zone="office"
        ),
        action=Action.IGNORE,
        message="辦公區不強制安全帽",
        priority=50
    ),

    # 區域規則：入口區只需安全帽
    Rule(
        id="rule_entrance_vest",
        name="入口區不強制反光背心",
        conditions=RuleConditions(
            object="no_vest",
            zone="entrance"
        ),
        action=Action.IGNORE,
        message="入口區不強制反光背心",
        priority=50
    ),

    # 基本規則：施工區違規
    Rule(
        id="rule_construction_helmet",
        name="施工區必須戴安全帽",
        conditions=RuleConditions(
            object="no_helmet",
            zone="construction",
            confidence_gte=0.6
        ),
        action=Action.VIOLATION,
        severity=Severity.HIGH,
        message="施工區域未配戴安全帽",
        priority=10
    ),
    Rule(
        id="rule_construction_vest",
        name="施工區必須穿反光背心",
        conditions=RuleConditions(
            object="no_vest",
            zone="construction",
            confidence_gte=0.6
        ),
        action=Action.VIOLATION,
        severity=Severity.MEDIUM,
        message="施工區域未穿著反光背心",
        priority=10
    ),

    # 入口區必須戴安全帽
    Rule(
        id="rule_entrance_helmet",
        name="入口區必須戴安全帽",
        conditions=RuleConditions(
            object="no_helmet",
            zone="entrance",
            confidence_gte=0.6
        ),
        action=Action.VIOLATION,
        severity=Severity.MEDIUM,
        message="入口區域未配戴安全帽",
        priority=10
    ),
]


# === 測試 ===

def run_tests():
    engine = RuleEngine(rules, zone_map)

    print("=== 規則測試結果 ===\n")

    test_cases = [
        # 測試 1: 施工區沒戴安全帽 (日間)
        (
            "施工區沒戴安全帽 (日間)",
            PPEDetectionEvent(
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                object="no_helmet",
                confidence=0.85,
                bbox=[100, 100, 200, 300],
                source="camera_01"
            ),
            Action.VIOLATION,
            Severity.HIGH,
        ),
        # 測試 2: 施工區沒戴安全帽 (夜間)
        (
            "施工區沒戴安全帽 (夜間)",
            PPEDetectionEvent(
                timestamp=datetime(2024, 1, 15, 22, 0, 0, tzinfo=timezone.utc),
                object="no_helmet",
                confidence=0.85,
                bbox=[100, 100, 200, 300],
                source="camera_01"
            ),
            Action.VIOLATION,
            Severity.CRITICAL,
        ),
        # 測試 3: 辦公區沒戴安全帽
        (
            "辦公區沒戴安全帽",
            PPEDetectionEvent(
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                object="no_helmet",
                confidence=0.85,
                bbox=[500, 100, 600, 300],
                source="camera_01"
            ),
            Action.IGNORE,
            None,
        ),
        # 測試 4: 低信心偵測
        (
            "低信心偵測",
            PPEDetectionEvent(
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                object="no_helmet",
                confidence=0.5,
                bbox=[100, 100, 200, 300],
                source="camera_01"
            ),
            Action.IGNORE,
            None,
        ),
        # 測試 5: VIP 攝影機違規
        (
            "VIP 攝影機違規",
            PPEDetectionEvent(
                timestamp=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
                object="no_helmet",
                confidence=0.85,
                bbox=[100, 100, 200, 300],
                source="camera_vip"
            ),
            Action.ALERT,
            Severity.CRITICAL,
        ),
    ]

    passed = 0
    for i, (desc, event, expected_action, expected_severity) in enumerate(test_cases, 1):
        result = engine.evaluate(event)

        print(f"測試 {i}: {desc}")

        if result.matched:
            print(f"  → {result.action.value}", end="")
            if result.severity:
                print(f" ({result.severity.value})", end="")
            print(f": {result.message}")

            # 驗證
            action_ok = result.action == expected_action
            severity_ok = expected_severity is None or result.severity == expected_severity

            if action_ok and severity_ok:
                passed += 1
            else:
                print(f"  ✗ 期望: {expected_action.value}, 得到: {result.action.value}")
        else:
            print(f"  → 無匹配規則")
            if expected_action == Action.IGNORE:
                passed += 1

        print()

    print(f"共測試 {len(test_cases)} 個案例，通過 {passed} 個")


if __name__ == "__main__":
    run_tests()
