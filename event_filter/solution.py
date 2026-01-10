"""
Workshop 解答：事件過濾與聚合

題目要求：
1. 實作過濾器：FilterFactory.create() 方法
2. 實作聚合器：EventAggregator 類別
3. 實作 API 端點（模擬）
"""

import random
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable
import uuid

from pydantic import BaseModel, Field


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


# === 過濾器 ===

class EventFilter(ABC):
    """事件過濾器基類"""

    @abstractmethod
    def match(self, event: PPEDetectionEvent) -> bool:
        pass

    def __and__(self, other: "EventFilter") -> "AndFilter":
        return AndFilter(self, other)

    def __or__(self, other: "EventFilter") -> "OrFilter":
        return OrFilter(self, other)

    def __invert__(self) -> "NotFilter":
        return NotFilter(self)


class TrueFilter(EventFilter):
    def match(self, event: PPEDetectionEvent) -> bool:
        return True


class ObjectFilter(EventFilter):
    def __init__(self, objects: list[str]):
        self.objects = set(objects)

    def match(self, event: PPEDetectionEvent) -> bool:
        return event.object in self.objects


class ConfidenceFilter(EventFilter):
    def __init__(self, min_conf: float = 0.0, max_conf: float = 1.0):
        self.min_conf = min_conf
        self.max_conf = max_conf

    def match(self, event: PPEDetectionEvent) -> bool:
        return self.min_conf <= event.confidence <= self.max_conf


class TimeRangeFilter(EventFilter):
    def __init__(self, start: Optional[datetime] = None, end: Optional[datetime] = None):
        self.start = start
        self.end = end

    def match(self, event: PPEDetectionEvent) -> bool:
        if self.start and event.timestamp < self.start:
            return False
        if self.end and event.timestamp > self.end:
            return False
        return True


class SourceFilter(EventFilter):
    def __init__(self, sources: list[str]):
        self.sources = set(sources)

    def match(self, event: PPEDetectionEvent) -> bool:
        return event.source in self.sources


class ZoneFilter(EventFilter):
    def __init__(self, zones: list[str], zone_map: dict):
        self.zones = set(zones)
        self.zone_map = zone_map

    def _get_zone(self, bbox: list) -> Optional[str]:
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        for zone_name, regions in self.zone_map.items():
            for region in regions:
                if region[0] <= cx <= region[2] and region[1] <= cy <= region[3]:
                    return zone_name
        return None

    def match(self, event: PPEDetectionEvent) -> bool:
        zone = self._get_zone(event.bbox)
        return zone in self.zones


class AndFilter(EventFilter):
    def __init__(self, *filters: EventFilter):
        self.filters = filters

    def match(self, event: PPEDetectionEvent) -> bool:
        return all(f.match(event) for f in self.filters)


class OrFilter(EventFilter):
    def __init__(self, *filters: EventFilter):
        self.filters = filters

    def match(self, event: PPEDetectionEvent) -> bool:
        return any(f.match(event) for f in self.filters)


class NotFilter(EventFilter):
    def __init__(self, filter: EventFilter):
        self.filter = filter

    def match(self, event: PPEDetectionEvent) -> bool:
        return not self.filter.match(event)


class FilterFactory:
    """過濾器工廠"""

    def __init__(self, zone_map: dict = None):
        self.zone_map = zone_map or {}

    def create(self, config: dict) -> EventFilter:
        """
        從設定建立過濾器

        Args:
            config: {
                "objects": ["no_helmet"],
                "confidence_min": 0.7,
                "confidence_max": 1.0,
                "sources": ["camera_01"],
                "zones": ["construction"],
                "time_start": "2024-01-15T00:00:00",
                "time_end": "2024-01-15T23:59:59"
            }
        """
        filters = []

        if "objects" in config:
            filters.append(ObjectFilter(config["objects"]))

        if "confidence_min" in config or "confidence_max" in config:
            filters.append(ConfidenceFilter(
                min_conf=config.get("confidence_min", 0.0),
                max_conf=config.get("confidence_max", 1.0)
            ))

        if "sources" in config:
            filters.append(SourceFilter(config["sources"]))

        if "zones" in config:
            filters.append(ZoneFilter(config["zones"], self.zone_map))

        if "time_start" in config or "time_end" in config:
            start = None
            end = None
            if "time_start" in config:
                start = datetime.fromisoformat(config["time_start"])
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
            if "time_end" in config:
                end = datetime.fromisoformat(config["time_end"])
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
            filters.append(TimeRangeFilter(start, end))

        if not filters:
            return TrueFilter()

        return AndFilter(*filters)


# === 聚合器 ===

@dataclass
class AggregateResult:
    group_key: str
    count: int = 0
    events: list[PPEDetectionEvent] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


class EventAggregator:
    """事件聚合器"""

    def __init__(
        self,
        group_by: Callable[[PPEDetectionEvent], str],
        filter: Optional[EventFilter] = None
    ):
        self.group_by = group_by
        self.filter = filter
        self.groups: dict[str, list[PPEDetectionEvent]] = defaultdict(list)

    def add(self, event: PPEDetectionEvent) -> None:
        if self.filter and not self.filter.match(event):
            return
        key = self.group_by(event)
        self.groups[key].append(event)

    def add_batch(self, events: list[PPEDetectionEvent]) -> None:
        for event in events:
            self.add(event)

    def get_results(self) -> list[AggregateResult]:
        results = []
        for key, events in sorted(self.groups.items()):
            confidences = [e.confidence for e in events]
            results.append(AggregateResult(
                group_key=key,
                count=len(events),
                events=events,
                stats={
                    "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
                    "min_confidence": min(confidences) if confidences else 0,
                    "max_confidence": max(confidences) if confidences else 0,
                }
            ))
        return results

    def get_counts(self) -> dict[str, int]:
        return {key: len(events) for key, events in self.groups.items()}

    def clear(self) -> None:
        self.groups.clear()


# === 分組函數 ===

def group_by_object(event: PPEDetectionEvent) -> str:
    return event.object


def group_by_source(event: PPEDetectionEvent) -> str:
    return event.source or "unknown"


def group_by_hour(event: PPEDetectionEvent) -> str:
    return event.timestamp.strftime("%Y-%m-%d %H:00")


def group_by_interval(interval_minutes: int = 10) -> Callable:
    def _group(event: PPEDetectionEvent) -> str:
        ts = event.timestamp
        interval_start = ts.replace(
            minute=(ts.minute // interval_minutes) * interval_minutes,
            second=0,
            microsecond=0
        )
        return interval_start.strftime("%H:%M")
    return _group


def group_by_zone(zone_map: dict) -> Callable:
    def _get_zone(bbox: list) -> str:
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        for zone_name, regions in zone_map.items():
            for region in regions:
                if region[0] <= cx <= region[2] and region[1] <= cy <= region[3]:
                    return zone_name
        return "unknown"

    return lambda event: _get_zone(event.bbox)


# === 滑動視窗 ===

class SlidingWindowStats:
    """滑動視窗統計"""

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


# === 模擬 API ===

class EventStore:
    """事件儲存庫（模擬）"""

    def __init__(self, zone_map: dict):
        self.events: list[PPEDetectionEvent] = []
        self.zone_map = zone_map
        self.factory = FilterFactory(zone_map)
        self.realtime = SlidingWindowStats(
            window=timedelta(minutes=5),
            group_by=group_by_object
        )

    def add(self, event: PPEDetectionEvent) -> None:
        self.events.append(event)
        self.realtime.add(event)

    def filter_events(self, config: dict) -> list[PPEDetectionEvent]:
        """GET /api/events/filter"""
        filter = self.factory.create(config)
        return [e for e in self.events if filter.match(e)]

    def aggregate_events(self, group_by_name: str, filter_config: dict = None) -> list[dict]:
        """GET /api/events/aggregate"""
        # 選擇分組函數
        group_funcs = {
            "object": group_by_object,
            "source": group_by_source,
            "hour": group_by_hour,
            "zone": group_by_zone(self.zone_map),
            "interval_10min": group_by_interval(10),
        }
        group_func = group_funcs.get(group_by_name, group_by_object)

        # 建立過濾器
        filter = self.factory.create(filter_config) if filter_config else None

        # 聚合
        aggregator = EventAggregator(group_by=group_func, filter=filter)
        aggregator.add_batch(self.events)

        return [
            {
                "group": r.group_key,
                "count": r.count,
                "avg_confidence": r.stats["avg_confidence"],
            }
            for r in aggregator.get_results()
        ]

    def get_realtime_stats(self) -> dict:
        """GET /api/dashboard/realtime"""
        return {
            "violations_5min": self.realtime.get_counts_by_group(),
            "rate": round(self.realtime.get_rate(), 2),
        }


# === 主程式 ===

def main():
    print("=== 事件過濾與聚合 Workshop 解答 ===\n")

    # 區域定義
    zone_map = {
        "construction": [[0, 0, 400, 600]],
        "office": [[400, 0, 700, 600]],
        "entrance": [[700, 0, 800, 600]],
    }

    # 產生測試資料
    base_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    events = []

    for i in range(1000):
        obj = random.choice(["no_helmet", "no_vest", "helmet", "vest"])
        conf = random.uniform(0.4, 0.99)

        # 依區域分配 bbox
        zone = random.choices(
            ["construction", "office", "entrance"],
            weights=[0.5, 0.3, 0.2]
        )[0]

        if zone == "construction":
            x1 = random.uniform(0, 300)
        elif zone == "office":
            x1 = random.uniform(400, 600)
        else:
            x1 = random.uniform(700, 750)

        y1 = random.uniform(0, 400)

        events.append(PPEDetectionEvent(
            timestamp=base_time + timedelta(minutes=random.randint(0, 60)),
            object=obj,
            confidence=conf,
            bbox=[x1, y1, x1 + 80, y1 + 150],
            source=random.choice(["camera_01", "camera_02", "camera_03"])
        ))

    # 建立事件儲存庫
    store = EventStore(zone_map)
    for event in events:
        store.add(event)

    # === 過濾測試 ===
    print("=== 過濾測試 ===")
    print(f"原始事件: {len(events)} 筆")

    # 高信心違規
    high_conf_violations = store.filter_events({
        "objects": ["no_helmet", "no_vest"],
        "confidence_min": 0.7
    })
    print(f"高信心違規 (confidence >= 0.7): {len(high_conf_violations)} 筆")

    # 施工區違規
    construction_violations = store.filter_events({
        "objects": ["no_helmet", "no_vest"],
        "zones": ["construction"]
    })
    print(f"施工區違規: {len(construction_violations)} 筆")

    # 組合條件
    combined = store.filter_events({
        "objects": ["no_helmet", "no_vest"],
        "confidence_min": 0.7,
        "zones": ["construction"]
    })
    print(f"施工區高信心違規: {len(combined)} 筆")

    # === 聚合測試 ===
    print("\n=== 聚合測試 ===")

    # 依物件類別
    print("\n依物件類別:")
    by_object = store.aggregate_events("object")
    for item in by_object:
        print(f"  {item['group']}: {item['count']} 筆")

    # 依區域（只看違規）
    print("\n依區域:")
    by_zone = store.aggregate_events("zone", {
        "objects": ["no_helmet", "no_vest"],
        "confidence_min": 0.6
    })
    for item in by_zone:
        print(f"  {item['group']}: {item['count']} 筆 (avg_conf={item['avg_confidence']:.2f})")

    # 每 10 分鐘統計
    print("\n每 10 分鐘統計:")
    by_interval = store.aggregate_events("interval_10min", {
        "objects": ["no_helmet", "no_vest"]
    })
    for item in sorted(by_interval, key=lambda x: x['group']):
        bar = "█" * (item['count'] // 2)
        print(f"  {item['group']}: {bar} {item['count']}")

    # === 即時統計 ===
    print("\n=== 即時統計 ===")
    realtime = store.get_realtime_stats()
    print(f"過去 5 分鐘:")
    for obj, count in realtime["violations_5min"].items():
        print(f"  {obj}: {count}")
    print(f"違規速率: {realtime['rate']} 次/分鐘")


if __name__ == "__main__":
    main()
