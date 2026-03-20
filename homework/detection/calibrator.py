"""sklearn KMeans 門檻校準器"""

import pandas as pd
from sklearn.cluster import KMeans
import yaml


class ThresholdCalibrator:
    def __init__(self, n_clusters=3):
        self.n_clusters = n_clusters
        self.centers = None
        self.thresholds = None

    def fit(self, events):
        """用 KMeans 對 confidence 分群，算出門檻"""
        df = pd.DataFrame(events)
        X = df[["confidence"]]

        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
        kmeans.fit(X)

        self.centers = sorted(kmeans.cluster_centers_.flatten())
        self.thresholds = []
        for i in range(len(self.centers) - 1):
            mid = round((self.centers[i] + self.centers[i + 1]) / 2, 4)
            self.thresholds.append(mid)

        return {
            "centers": [round(c, 4) for c in self.centers],
            "threshold_low": self.thresholds[0],
            "threshold_high": self.thresholds[1],
        }

    def export_rules(self, yaml_path):
        """匯出建議的 rules.yaml"""
        rules = {
            "rules": [
                {"name": "低信心忽略", "max_confidence": float(self.thresholds[0]), "action": "ignore"},
                {"name": "沒戴安全帽（高信心）", "event_type": "head_detected",
                 "min_confidence": float(self.thresholds[1]), "action": "alert", "severity": "high"},
                {"name": "沒戴安全帽（中信心）", "event_type": "head_detected",
                 "action": "warning", "severity": "low"},
                {"name": "預設", "action": "ok"},
            ],
            "alert_threshold": 2,
        }
        with open(yaml_path, "w") as f:
            yaml.dump(rules, f, allow_unicode=True, default_flow_style=False)
