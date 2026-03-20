"""完整 Pipeline：偵測 → 轉換 → 校準 → 規則 → 報告"""

from .detector import SafetyDetector
from .converter import EventConverter
from .calibrator import ThresholdCalibrator
from .engine import RuleEngine


class DetectionPipeline:
    def __init__(self, model_path="best.pt", use_mock=False, recalibrate_every=3):
        self.detector = SafetyDetector(model_path=model_path, use_mock=use_mock)
        self.converter = EventConverter()
        self.calibrator = ThresholdCalibrator(n_clusters=3)
        self.engine = None
        self.recalibrate_every = recalibrate_every
        self.detect_count = 0
        self.all_events = []

    def process(self, image_path):
        """處理單張圖片"""
        self.detect_count += 1

        # 1. 偵測
        result = self.detector.detect(image_path)

        # 2. 轉換
        events = self.converter.convert(result)
        self.all_events.extend(events)

        # 3. 自動校準
        calibration = None
        if self.detect_count % self.recalibrate_every == 0 and len(self.all_events) >= 10:
            calibration = self._recalibrate()

        # 4. 規則比對
        alerts = 0
        if self.engine:
            processed = self.engine.process(events)
            alerts = sum(1 for r in processed if r["action"] == "alert")

        return {
            "image_path": image_path,
            "total": result["total"],
            "violations": result["violations"],
            "alerts": alerts,
            "calibration": calibration,
        }

    def process_batch(self, image_paths):
        """批次處理多張圖片"""
        results = []
        for path in image_paths:
            result = self.process(path)
            results.append(result)

        # 最終分析
        stats = None
        alert_events = []
        if self.engine:
            all_processed = self.engine.process(self.all_events)
            stats = self.engine.analyze(all_processed)
            alert_events = [
                self.all_events[i] for i, r in enumerate(all_processed)
                if r["action"] == "alert"
            ]

        return {
            "results": results,
            "total_events": len(self.all_events),
            "calibration": self.calibrator.thresholds,
            "stats": stats,
            "alert_events": alert_events,
        }

    def _recalibrate(self):
        """校準門檻並更新規則引擎"""
        result = self.calibrator.fit(self.all_events)
        self.calibrator.export_rules("rules_suggested.yaml")
        self.engine = RuleEngine("rules_suggested.yaml")
        return result


if __name__ == "__main__":
    print("=" * 60)
    print("  工安偵測 Pipeline")
    print("=" * 60)

    pipeline = DetectionPipeline(use_mock=True, recalibrate_every=3)

    # 模擬圖片
    images = ["worksite_001.jpg", "worksite_002.jpg", "worksite_003.jpg"]

    print(f"\n處理 {len(images)} 張圖片...\n")
    summary = pipeline.process_batch(images)

    if summary["calibration"]:
        t = summary["calibration"]
        print(f"校準門檻: {float(t[0]):.4f} / {float(t[1]):.4f}")

    if summary["stats"]:
        s = summary["stats"]
        print(f"\n統計報告:")
        print(f"  總事件: {s['total']}")
        print(f"  alert: {s['alert_count']}")
        print(f"  warning: {s['warning_count']}")
        print(f"  ok: {s['ok_count']}")
        if s["top_violation_image"]:
            print(f"  最多違規: {s['top_violation_image']}")

    print(f"\n要上報的事件: {len(summary['alert_events'])} 筆")
    for event in summary["alert_events"][:5]:
        print(f"  {event['event_type']}: {event['confidence']}")
