"""
Workshop：從圖片到事件 JSON（整合版）

情境：
你已經會用 YOLO 偵測安全帽了，也學會把 .txt 標註轉成事件 JSON。
但目前是兩個獨立的步驟：先跑 YOLO，再跑轉換。
現在要把它們整合成一支程式：輸入圖片 → 輸出事件 JSON。

目錄結構：
event_schema/
├── workshop.py          ← 你正在寫的檔案
├── solution_simple.py   ← 解答（先不要看！）
├── best.pt              ← 訓練好的 YOLO 模型
└── sample_data/
    ├── test.jpg         ← 輸入：測試圖片
    └── test.txt         ← 參考：YOLO 標註格式

題目：
1. 觀察 sample_data/ 中的範例檔案，理解輸入輸出
2. 完成下方 detect_and_convert() 函式
3. 執行程式：python workshop.py
4.（延伸）加入 confidence 過濾：只保留 > 0.5 的事件
"""

from ultralytics import YOLO
from datetime import datetime, timezone
import json
import os

LABEL_MAP = {0: "head", 1: "helmet"}


def detect_and_convert(image_path, model_path="best.pt"):
    """
    輸入圖片路徑，回傳事件 JSON 陣列

    TODO: 完成以下步驟
    1. 用 YOLO(model_path) 載入模型
    2. 用 model(image_path) 對圖片推論
    3. 遍歷 results[0].boxes，取出每個偵測的：
       - cls（類別 ID）
       - conf（信心分數）
       - xyxy（bbox 座標）
    4. 組成事件 dict，加入 events 陣列
       事件格式：
       {
           "event_type": "{label}_detected",
           "confidence": 0.69,
           "bbox": {"x1": ..., "y1": ..., "x2": ..., "y2": ...},
           "source_image": "test.jpg",
           "timestamp": "2026-..."
       }
    """
    events = []
    # --- 你的程式碼寫在這裡 ---

    # --- 結束 ---
    return events


if __name__ == "__main__":
    events = detect_and_convert("sample_data/test.jpg")
    print(json.dumps(events, indent=2, ensure_ascii=False))
    print(f"\n共 {len(events)} 筆事件")
