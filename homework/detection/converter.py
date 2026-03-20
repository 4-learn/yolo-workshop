"""Event JSON 轉換器"""


class EventConverter:
    def convert(self, detector_result):
        """將 SafetyDetector 輸出轉成 event list"""
        return detector_result["events"]
