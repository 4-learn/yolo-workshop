# Workshop：批次偵測與告警

用 FastAPI 接收圖片、跑 YOLO 偵測，再用 async client 批次送圖並收集結果。

## 目錄結構

```
batch_detection/
├── workshop_server.py ← 學生填空版（server）
├── workshop_client.py ← 學生填空版（client）
├── server.py          ← 解答（server）
├── client.py          ← 解答（client）
└── images/            ← 測試圖片放這裡
    └── *.jpg
```

## 環境準備

```bash
pip install fastapi uvicorn httpx python-multipart ultralytics
```

模型 `yolov8n.pt` 會在第一次執行時自動下載。

## 放入測試圖片

```bash
mkdir -p images
# 放入任意 .jpg 圖片，例如從 event_schema/sample_data/ 複製
cp ../event_schema/sample_data/test.jpg images/test1.jpg
```

## 執行方式

需要開兩個 terminal。

### Terminal 1：啟動 Server

```bash
# 學生版
uvicorn workshop_server:app --reload

# 或解答版
uvicorn server:app --reload
```

啟動成功會看到：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

可以用 curl 單獨測試：

```bash
curl -X POST http://localhost:8000/detect -F "file=@images/test1.jpg"
```

### Terminal 2：執行 Client

```bash
# 學生版
python workshop_client.py

# 或解答版
python client.py
```

### 預期輸出

```
[1/3] test1.jpg → 9 events ⚠️ ALERT: person_detected
[2/3] test2.jpg → 9 events ⚠️ ALERT: person_detected
[3/3] test3.jpg → 9 events ⚠️ ALERT: person_detected

=== 結果 ===
共 27 筆事件，已寫入 results.json

=== Alert 摘要 ===
⚠️ test1.jpg: 8 筆 person_detected
⚠️ test2.jpg: 8 筆 person_detected
⚠️ test3.jpg: 8 筆 person_detected
```

結果會寫入 `results.json`。

## API 規格

### `POST /detect`

| 參數 | 位置 | 型別 | 說明 |
|------|------|------|------|
| `file` | Body | UploadFile | 上傳的圖片 |
| `min_confidence` | Query | float (0-1) | 最低信心閾值，預設 0.0 |

Response：

```json
{
  "source_image": "test1.jpg",
  "event_count": 9,
  "alert": true,
  "events": [
    {
      "event_type": "person_detected",
      "confidence": 0.8214,
      "bbox": { "x1": 53.73, "y1": 82.58, "x2": 167.67, "y2": 298.1 },
      "source_image": "test1.jpg",
      "timestamp": "2026-03-16T14:50:02+00:00"
    }
  ]
}
```

## 講義

- [HackMD 講義](https://hackmd.io/@yillkid/r1y_9qScWe)
