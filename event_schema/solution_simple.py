"""
Workshop 解答：從圖片到事件

題目：
1. 使用 yolo predict 對一張圖片進行推論
2. 產生 .txt 標註檔
3. 撰寫 Python 程式，把標註轉成事件 JSON
4. 輸出一個事件陣列

步驟 1-2（在終端機執行）：
yolo predict model=best.pt source=test.jpg save_txt=True

執行後會在 runs/detect/predict/labels/ 產生 .txt 檔，
每行格式：class_id x_center y_center width height

步驟 3-4（執行本程式）：
python solution_simple.py
"""

from datetime import datetime, timezone
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def convert_file(txt_path, image_name):
    """讀取整個 .txt 標註檔，回傳事件陣列"""
    events = []
    with open(txt_path) as f:
        for line in f:
            if line.strip():
                events.append(label_to_event(line, image_name))
    return events


# === 主程式 ===
if __name__ == "__main__":
    import os

    # 如果有真的 YOLO 產出，讀取 .txt 檔
    label_dir = "runs/detect/predict/labels"

    if os.path.isdir(label_dir):
        print("=== 讀取 YOLO 標註檔 ===\n")
        events = []
        for filename in sorted(os.listdir(label_dir)):
            if filename.endswith(".txt"):
                image_name = filename.replace(".txt", ".jpg")
                filepath = os.path.join(label_dir, filename)
                events.extend(convert_file(filepath, image_name))
        print(json.dumps(events, indent=2, ensure_ascii=False))
        print(f"\n共 {len(events)} 筆事件")

    else:
        # 沒有 YOLO 產出，用模擬資料示範
        print("=== 模擬 YOLO 標註（尚未執行 yolo predict）===\n")
        mock_labels = [
            "0 0.45 0.32 0.12 0.28",  # helmet
            "1 0.60 0.35 0.10 0.25",  # no_helmet
            "0 0.20 0.40 0.11 0.30",  # helmet
        ]
        events = []
        for line in mock_labels:
            events.append(label_to_event(line, "frame_001.jpg"))
        print(json.dumps(events, indent=2, ensure_ascii=False))
        print(f"\n共 {len(events)} 筆事件")
        print("\n提示：執行 yolo predict model=best.pt source=test.jpg save_txt=True 產生真的標註檔")
