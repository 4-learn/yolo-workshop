"""
Workshop 解答：事件去重、累積、計數

題目要求：
1. 實作 ViolationReport 類別
2. 產出每小時違規報告
3. 包含違規類型分布和時段分布
"""

from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional
import random
import uuid

from pydantic import BaseModel, Field


# === Schema (從 yolo-demo 複製) ===

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
    bbox: list[float] = Field(min_length=4, max_length=4)
    metadata: Optional[dict] = None


# === IoU 計算 ===

def calculate_iou(box1: list, box2: list) -> float:
    """計算兩個 bounding box 的 IoU"""
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


# === 去重器 ===

class EventDeduplicator:
    """事件去重器"""

    def __init__(
        self,
        iou_threshold: float = 0.5,
        time_window: timedelta = timedelta(seconds=2)
    ):
        self.iou_threshold = iou_threshold
        self.time_window = time_window
        self.recent_events: list[PPEDetectionEvent] = []

    def process(self, event: PPEDetectionEvent) -> Optional[PPEDetectionEvent]:
        """處理事件，重複則返回 None"""
        now = event.timestamp

        # 清理過期事件
        self.recent_events = [
            e for e in self.recent_events
            if now - e.timestamp < self.time_window
        ]

        # 檢查重複
        for recent in self.recent_events:
            if recent.object != event.object:
                continue
            if calculate_iou(recent.bbox, event.bbox) > self.iou_threshold:
                return None

        self.recent_events.append(event)
        return event


# === 違規報告 ===

class ViolationReport:
    """
    違規報告產生器

    統計每小時的違規情況，包含：
    - 總違規次數（去重後）
    - 違規類型分布
    - 時段分布（每 10 分鐘）
    """

    def __init__(
        self,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 10
    ):
        self.start_time = start_time
        self.end_time = end_time
        self.interval_minutes = interval_minutes

        self.deduplicator = EventDeduplicator(
            iou_threshold=0.5,
            time_window=timedelta(seconds=2)
        )

        self.violations: list[PPEDetectionEvent] = []

    def add_event(self, event: PPEDetectionEvent) -> bool:
        """
        加入事件

        Returns:
            True 如果是新違規事件，否則 False
        """
        # 只處理違規事件
        if event.object not in ["no_helmet", "no_vest"]:
            return False

        # 去重
        deduped = self.deduplicator.process(event)
        if deduped is None:
            return False

        self.violations.append(deduped)
        return True

    def _get_interval_key(self, timestamp: datetime) -> str:
        """取得時段 key"""
        minutes = timestamp.minute
        interval_start = (minutes // self.interval_minutes) * self.interval_minutes
        interval_end = interval_start + self.interval_minutes

        hour = timestamp.strftime("%H")
        return f"{hour}:{interval_start:02d}-{hour}:{interval_end:02d}"

    def generate_report(self) -> dict:
        """
        產生報告

        Returns:
            {
                "period": str,
                "total_violations": int,
                "by_type": dict[str, int],
                "by_interval": dict[str, int]
            }
        """
        # 統計類型分布
        by_type = defaultdict(int)
        for v in self.violations:
            by_type[v.object] += 1

        # 統計時段分布
        by_interval = defaultdict(int)
        for v in self.violations:
            key = self._get_interval_key(v.timestamp)
            by_interval[key] += 1

        # 排序時段
        sorted_intervals = dict(sorted(by_interval.items()))

        return {
            "period": f"{self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')}",
            "total_violations": len(self.violations),
            "by_type": dict(by_type),
            "by_interval": sorted_intervals,
        }

    def print_report(self) -> None:
        """印出格式化報告"""
        report = self.generate_report()

        print("=== 違規報告 ===")
        print(f"時段: {report['period']}")
        print(f"總違規次數: {report['total_violations']}（去重後）")

        print("\n違規類型分布:")
        total = report["total_violations"]
        for vtype, count in report["by_type"].items():
            pct = (count / total * 100) if total > 0 else 0
            print(f"  - {vtype}: {count} ({pct:.1f}%)")

        print("\n時段分布:")
        max_count = max(report["by_interval"].values()) if report["by_interval"] else 0
        for interval, count in report["by_interval"].items():
            bar_len = int(count / max_count * 20) if max_count > 0 else 0
            bar = "█" * bar_len
            print(f"  {interval}: {bar} {count}")


# === 測試資料產生 ===

def generate_test_events(
    start_time: datetime,
    duration_minutes: int = 60,
    num_events: int = 100,
    duplicate_ratio: float = 0.3
) -> list[PPEDetectionEvent]:
    """
    產生測試事件

    Args:
        start_time: 開始時間
        duration_minutes: 時間範圍（分鐘）
        num_events: 事件數量
        duplicate_ratio: 重複事件比例

    Returns:
        事件列表
    """
    events = []

    for i in range(num_events):
        # 隨機時間
        offset = random.randint(0, duration_minutes * 60)
        timestamp = start_time + timedelta(seconds=offset)

        # 隨機類型（70% no_helmet, 30% no_vest）
        obj = "no_helmet" if random.random() < 0.7 else "no_vest"

        # 隨機 bbox
        x = random.randint(50, 500)
        y = random.randint(50, 400)
        bbox = [x, y, x + 100, y + 200]

        # 部分事件是重複的（微調 bbox）
        if i > 0 and random.random() < duplicate_ratio:
            prev = events[-1]
            bbox = [
                prev.bbox[0] + random.randint(-5, 5),
                prev.bbox[1] + random.randint(-5, 5),
                prev.bbox[2] + random.randint(-5, 5),
                prev.bbox[3] + random.randint(-5, 5),
            ]
            timestamp = prev.timestamp + timedelta(milliseconds=33)
            obj = prev.object

        event = PPEDetectionEvent(
            timestamp=timestamp,
            object=obj,
            confidence=random.uniform(0.7, 0.95),
            bbox=bbox,
            source="camera_01"
        )
        events.append(event)

    # 按時間排序
    events.sort(key=lambda e: e.timestamp)
    return events


# === 主程式 ===

if __name__ == "__main__":
    # 設定時間範圍
    start_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)

    # 建立報告產生器
    report = ViolationReport(start_time, end_time)

    # 產生測試資料
    print("產生測試資料...")
    events = generate_test_events(
        start_time=start_time,
        duration_minutes=60,
        num_events=100,
        duplicate_ratio=0.3
    )
    print(f"共產生 {len(events)} 筆事件\n")

    # 處理事件
    new_count = 0
    dup_count = 0
    for event in events:
        if report.add_event(event):
            new_count += 1
        else:
            dup_count += 1

    print(f"新事件: {new_count}, 重複/非違規: {dup_count}\n")

    # 產出報告
    report.print_report()
