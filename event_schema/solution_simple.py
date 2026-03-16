"""
Workshop 解答：從圖片到事件

題目：
1. 使用 yolo predict 對一張圖片進行推論，產生 .txt 標註檔
2. 撰寫 Python 程式，把標註轉成事件 JSON
3. 輸出一個事件陣列

執行方式：
python solution_simple.py
"""

from datetime import datetime
import json

# 類別對應表（依你的 YOLO 模型而定）
LABEL_MAP = {
    0: "helmet",
    1: "no_helmet",
    2: "vest",
    3: "no_vest",
}


def label_to_event(label_line, image_name):
    """把一行 YOLO .txt 標註轉成事件 dict"""
    parts = label_line.strip().split()
    class_id = int(parts[0])

    return {
        "event_type": f"{LABEL_MAP.get(class_id, 'unknown')}_detected",
        "source_image": image_name,
        "bbox": {
            "x_center": float(parts[1]),
            "y_center": float(parts[2]),
            "width": float(parts[3]),
            "height": float(parts[4]),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def convert_file(txt_path, image_name):
    """讀取整個 .txt 標註檔，回傳事件陣列"""
    events = []
    with open(txt_path) as f:
        for line in f:
            if line.strip():
                events.append(label_to_event(line, image_name))
    return events


# === 測試（不需要真的跑 YOLO，用模擬資料）===
if __name__ == "__main__":
    # 模擬 YOLO 產生的 .txt 內容（每行：class_id x_center y_center width height）
    mock_labels = [
        "0 0.45 0.32 0.12 0.28",  # helmet
        "1 0.60 0.35 0.10 0.25",  # no_helmet
        "0 0.20 0.40 0.11 0.30",  # helmet
    ]

    print("=== YOLO 標註轉事件 JSON ===\n")

    events = []
    for line in mock_labels:
        events.append(label_to_event(line, "frame_001.jpg"))

    print(json.dumps(events, indent=2, ensure_ascii=False))
    print(f"\n共 {len(events)} 筆事件")
