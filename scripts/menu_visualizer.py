"""Render daily menu PNGs (420x1000) in the format MenuPage expects."""
import os
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

import cairosvg

# cairosvg only uses the first family in font-family (no fallback list), so the font
# must be installed under exactly this name. CI sets MENU_FONT_FAMILY=Noto Sans CJK TC.
FONT_FAMILY = f"'{os.environ.get('MENU_FONT_FAMILY', 'Microsoft JhengHei')}'"
HIGHLIGHT_AFTER_ITEM = 4  # thicker divider between rice (1-5) and noodle (6+) items


def get_monday_date(date: datetime) -> datetime:
    return date - timedelta(days=date.weekday())


def _svg_header(date: datetime) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="420" height="1000" viewBox="0 0 420 1000" xmlns="http://www.w3.org/2000/svg">
    <rect width="420" height="1000" fill="#f8f9fa"/>
    <rect x="0" y="0" width="420" height="80" fill="#9C9C9C"/>
    <text x="30" y="52" font-family="{FONT_FAMILY}" font-size="36" fill="white" font-weight="bold" dominant-baseline="middle">
        {date.month}月{date.day}日 菜單
    </text>'''


def _format_price(price) -> str:
    if price is None:
        return ""
    if isinstance(price, (int, float)):
        return f"${int(price)}"
    return escape(str(price))


def create_menu_svg(date: datetime, menu_items: list[dict]) -> str:
    svg = _svg_header(date)
    y_position, row_height = 120, 80
    for idx, item in enumerate(menu_items):
        text_y = y_position + row_height / 2
        highlight = idx == HIGHLIGHT_AFTER_ITEM
        svg += f'''
    <g>
        <text x="40" y="{text_y}" font-family="{FONT_FAMILY}" font-size="28" fill="#333" font-weight="500" dominant-baseline="middle">
            {item['dish_number']}. {escape(item['dish_name'])}
        </text>
        <text x="380" y="{text_y}" font-family="{FONT_FAMILY}" font-size="28" fill="#c10015" font-weight="bold" text-anchor="end" dominant-baseline="middle">
            {_format_price(item['price'])}
        </text>
        <line x1="{20 if highlight else 40}" y1="{y_position + row_height}" x2="{400 if highlight else 380}" y2="{y_position + row_height}"
            stroke="{'#333' if highlight else '#dee2e6'}" stroke-width="{2.5 if highlight else 1.5}"/>
    </g>'''
        y_position += row_height
    return svg + "\n</svg>"


def create_empty_menu_svg(date: datetime) -> str:
    return _svg_header(date) + f'''
    <text x="210" y="500" font-family="{FONT_FAMILY}" font-size="36" fill="#333" font-weight="bold" text-anchor="middle" dominant-baseline="middle">
        本日無菜單
    </text>
</svg>'''


def save_menu_visualizations(menu_data: list[dict], output_dir: str) -> list[str]:
    """
    Writes `{monday}_{1-5}.png` plus a duplicate `{sunday}_{1-5}.png` set, because
    older app builds compute the week start one day early (UTC offset bug).
    Returns the written file paths.
    """
    menu_by_date: dict[datetime, list[dict]] = {}
    for item in menu_data:
        menu_by_date.setdefault(item["date"], []).append(item)
    if not menu_by_date:
        return []

    monday = get_monday_date(min(menu_by_date))
    os.makedirs(output_dir, exist_ok=True)

    written = []
    for offset in range(5):
        date = monday + timedelta(days=offset)
        items = sorted(menu_by_date.get(date, []), key=lambda i: i["dish_number"])
        png = cairosvg.svg2png(
            bytestring=(create_menu_svg(date, items) if items else create_empty_menu_svg(date)).encode("utf-8")
        )
        for base in (monday, monday - timedelta(days=1)):
            path = os.path.join(output_dir, f"{base:%Y-%m-%d}_{offset + 1}.png")
            with open(path, "wb") as f:
                f.write(png)
            written.append(path)
    return written
