"""
Workshop 解答：從圖片到事件

題目：
1. 使用 yolo predict 對一張圖片進行推論
2. 產生 .txt 標註檔
3. 撰寫 Python 程式，把標註轉成事件 JSON
4. 輸出一個事件陣列

步驟 1-2（在終端機執行）：
yolo predict model=best.pt source=sample_data/test.jpg save_txt=True

執行後會在 runs/detect/predict/labels/ 產生 .txt 檔，
每行格式：class_id x_center y_center width height

也可以直接用附的範例標註檔 sample_data/test.txt

步驟 3-4（執行本程式）：
python solution_simple.py
"""

from datetime import datetime, timezone
import json

# 類別對應表（對應 PPE 模型：0=head, 1=helmet）
LABEL_MAP = {
    0: "head",
    1: "helmet",
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

    # 優先讀取 YOLO 產出，其次用附的範例檔
    label_dir = "runs/detect/predict/labels"
    sample_file = "sample_data/test.txt"

    if os.path.isdir(label_dir):
        print("=== 讀取 YOLO 標註檔 ===\n")
        events = []
        for filename in sorted(os.listdir(label_dir)):
            if filename.endswith(".txt"):
                image_name = filename.replace(".txt", ".jpg")
                filepath = os.path.join(label_dir, filename)
                events.extend(convert_file(filepath, image_name))

    elif os.path.isfile(sample_file):
        print("=== 讀取範例標註檔 sample_data/test.txt ===\n")
        events = convert_file(sample_file, "test.jpg")

    else:
        print("找不到標註檔，請先執行：")
        print("  yolo predict model=best.pt source=sample_data/test.jpg save_txt=True")
        exit(1)

    print(json.dumps(events, indent=2, ensure_ascii=False))
    print(f"\n共 {len(events)} 筆事件")
