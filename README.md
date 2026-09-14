# ScheduleData

## 熱食部菜單自動更新

`.github/workflows/update-menu.yml` 每天台灣時間 02:00 執行（也可以在 Actions 頁面手動 Run workflow）：

1. 用 Google Drive API 讀取[熱食部雲端資料夾](https://drive.google.com/drive/folders/1jZTQNkQVCoDVmMPQaG2Ov_Zwu4o4cmQQ)中最新兩個學期資料夾（如 `115-1`）的 xlsx。
2. `scripts/menu_scraper.py` 解析「週菜單」工作表，週一日期取自表格本身（不看檔名）。
3. `scripts/menu_visualizer.py` 產生本週及之後的 `menus/{週一}_{1-5}.png`，並另存一份 `{週日}_{1-5}.png` 相容舊版 App。
4. `menus/` 有變更才 commit；平日若本週菜單缺檔，workflow 會失敗並寄信通知。

### 設定

- GCP：建立專案 → 啟用 **Google Drive API** → 建立 API key（建議限制只能呼叫 Drive API）。
- 本 repo → Settings → Secrets and variables → Actions：
  - Secret `GOOGLE_DRIVE_API_KEY`（必填）
  - Variable `DRIVE_ROOT_FOLDER_ID`（選填，雲端資料夾換位置時再設）

### 本機執行

```sh
pip install -r scripts/requirements.txt   # macOS 另需 brew install cairo
GOOGLE_DRIVE_API_KEY=... python scripts/update_menu.py            # 寫入 menus/
GOOGLE_DRIVE_API_KEY=... python scripts/update_menu.py --dry-run  # 只解析
GOOGLE_DRIVE_API_KEY=... python scripts/update_menu.py --all      # 連過去的週也重畫
```
