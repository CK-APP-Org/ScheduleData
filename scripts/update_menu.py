"""
Sync cafeteria menus from the 熱食部 Google Drive folder into menus/*.png.

Env:
  GOOGLE_DRIVE_API_KEY   Google API key with the Drive API enabled (required)
  DRIVE_ROOT_FOLDER_ID   Root folder containing semester folders like `115-1`
"""
import argparse
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from drive import DriveClient
from menu_scraper import scrape_menu
from menu_visualizer import get_monday_date, save_menu_visualizations

DEFAULT_ROOT_FOLDER_ID = "1jZTQNkQVCoDVmMPQaG2Ov_Zwu4o4cmQQ"
TAIPEI = timezone(timedelta(hours=8))
REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=str(REPO_ROOT / "menus"), help="output directory (default: menus/)")
    parser.add_argument("--dry-run", action="store_true", help="parse only, do not write PNGs")
    parser.add_argument("--all", action="store_true", help="also re-render weeks before the current week")
    args = parser.parse_args()

    client = DriveClient(os.environ.get("GOOGLE_DRIVE_API_KEY", ""))
    root_id = os.environ.get("DRIVE_ROOT_FOLDER_ID") or DEFAULT_ROOT_FOLDER_ID

    today = datetime.now(TAIPEI).replace(tzinfo=None)
    this_monday = get_monday_date(today).replace(hour=0, minute=0, second=0, microsecond=0)
    print(f"Today (Asia/Taipei): {today:%Y-%m-%d %a}, current week starts {this_monday:%Y-%m-%d}")

    folders = client.semester_folders(root_id)
    if not folders:
        print("::error::No semester folders found in Drive root")
        return 1

    weeks: dict[datetime, tuple[dict, list]] = {}
    for folder in folders:
        for file in client.list_spreadsheets(folder["id"]):
            label = f"{folder['name']}/{file['name']}"
            with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp:
                tmp.write(client.download_xlsx(file))
                tmp.flush()
                try:
                    menu = scrape_menu(tmp.name)
                except Exception as e:  # malformed or unrelated spreadsheet
                    print(f"::warning::Skipping {label}: {e}")
                    continue
            if not menu:
                print(f"::warning::Skipping {label}: no menu items")
                continue

            monday = get_monday_date(min(item["date"] for item in menu))
            if monday < this_monday and not args.all:
                continue
            previous = weeks.get(monday)
            if previous and previous[0]["modifiedTime"] >= file["modifiedTime"]:
                print(f"::warning::{label} duplicates week {monday:%Y-%m-%d}; keeping newer {previous[0]['name']}")
                continue
            if previous:
                print(f"::warning::{previous[0]['name']} duplicates week {monday:%Y-%m-%d}; keeping newer {file['name']}")
            weeks[monday] = (file, menu)

    for monday in sorted(weeks):
        file, menu = weeks[monday]
        print(f"Week {monday:%Y-%m-%d}: {file['name']} ({len(menu)} items)")
        if not args.dry_run:
            save_menu_visualizations(menu, args.out)

    if not args.dry_run and today.weekday() < 5:
        expected = Path(args.out) / f"{this_monday:%Y-%m-%d}_1.png"
        if not expected.exists():
            print(f"::error::Menu for current week is missing ({expected.name}); check the Drive folder")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
