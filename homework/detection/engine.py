"""規則引擎 + pandas 分析"""

import yaml
import pandas as pd


class RuleEngine:
    def __init__(self, yaml_path):
        with open(yaml_path) as f:
            config = yaml.safe_load(f)
        self.rules = config["rules"]
        self.alert_threshold = config.get("alert_threshold", 2)

    def _check_event(self, event):
        """比對一筆事件，回傳第一條符合的規則"""
        for rule in self.rules:
            if "event_type" in rule:
                if event["event_type"] != rule["event_type"]:
                    continue
            if "min_confidence" in rule:
                if event["confidence"] < rule["min_confidence"]:
                    continue
            if "max_confidence" in rule:
                if event["confidence"] > rule["max_confidence"]:
                    continue
            return rule
        return None

    def process(self, events):
        """對所有事件跑規則比對"""
        results = []
        for event in events:
            matched = self._check_event(event)
            results.append({
                "source_image": event["source_image"],
                "event_type": event["event_type"],
                "confidence": event["confidence"],
                "rule": matched["name"] if matched else "無匹配",
                "action": matched["action"] if matched else "unknown",
                "severity": matched.get("severity", "-"),
            })
        return results

    def analyze(self, results):
        """用 pandas 統計分析"""
        df = pd.DataFrame(results)

        action_counts = df["action"].value_counts().to_dict()
        alert_count = action_counts.get("alert", 0)
        warning_count = action_counts.get("warning", 0)

        # 最多違規的圖片
        alerts = df[df["action"] == "alert"]
        top_image = None
        if len(alerts) > 0:
            top_image = alerts["source_image"].value_counts().index[0]

        # 聚合告警
        alert_images = alerts["source_image"].unique().tolist() if len(alerts) > 0 else []
        should_alert = len(alert_images) >= self.alert_threshold

        return {
            "total": len(df),
            "alert_count": alert_count,
            "warning_count": warning_count,
            "ok_count": action_counts.get("ok", 0),
            "top_violation_image": top_image,
            "alert_images": alert_images,
            "should_alert": should_alert,
            "results": results,
        }
