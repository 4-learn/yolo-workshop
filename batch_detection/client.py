"""
解答：批次偵測 Client

使用方式：
  1. 先啟動 server: uvicorn server:app --reload
  2. 把圖片放到 images/ 目錄
  3. 執行: python client.py

會對 images/ 中每張圖片呼叫 POST /detect，
收集所有事件，寫入 results.json。
"""

import requests
import json
import os
import sys

API_URL = "http://localhost:8000/detect"
IMAGE_DIR = "images"
OUTPUT_FILE = "results.json"


def detect_image(image_path):
    """送一張圖片給 API，回傳偵測結果"""
    filename = os.path.basename(image_path)
    with open(image_path, "rb") as f:
        response = requests.post(
            API_URL,
            files={"file": (filename, f, "image/jpeg")},
        )
    response.raise_for_status()
    return response.json()


def main():
    # 1. 收集所有圖片
    if not os.path.isdir(IMAGE_DIR):
        print(f"找不到 {IMAGE_DIR}/ 目錄，請建立並放入測試圖片")
        sys.exit(1)

    image_files = sorted(
        f for f in os.listdir(IMAGE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )

    if not image_files:
        print(f"{IMAGE_DIR}/ 目錄是空的，請放入測試圖片")
        sys.exit(1)

    total = len(image_files)
    all_events = []
    alerts = []

    # 2. 逐一送圖片
    for i, filename in enumerate(image_files, 1):
        image_path = os.path.join(IMAGE_DIR, filename)
        result = detect_image(image_path)

        count = result["event_count"]
        alert_flag = " ⚠️ ALERT: person_detected" if result["alert"] else ""
        print(f"[{i}/{total}] {filename} → {count} events{alert_flag}")

        all_events.extend(result["events"])

        if result["alert"]:
            person_count = sum(
                1 for e in result["events"]
                if e["event_type"] == "person_detected"
            )
            alerts.append({"image": filename, "person_count": person_count})

    # 3. 寫入 JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    print(f"\n=== 結果 ===")
    print(f"共 {len(all_events)} 筆事件，已寫入 {OUTPUT_FILE}")

    # 4. Alert 摘要
    if alerts:
        print(f"\n=== Alert 摘要 ===")
        for a in alerts:
            print(f"⚠️ {a['image']}: {a['person_count']} 筆 person_detected")
    else:
        print("\n✅ 所有圖片皆配戴安全帽，無 alert")


if __name__ == "__main__":
    main()
