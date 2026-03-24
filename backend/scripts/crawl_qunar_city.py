from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook


HEADERS = ("名字", "链接", "地址", "介绍", "开放时间", "图片链接", "评分", "建议游玩时间", "建议季节", "门票", "小贴士", "Page")
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0 Safari/537.36"
}


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def extract_label_value(text: str, label: str) -> str:
    pattern = rf"{label}[:：]\s*(.+?)(?=(地址|介绍|开放时间|门票|建议游玩时间|建议季节|小贴士|电话|官网|$))"
    match = re.search(pattern, text, flags=re.S)
    return clean_text(match.group(1)) if match else ""


def fetch_html(url: str, cookies: str = "") -> str:
    session = requests.Session()
    headers = dict(DEFAULT_HEADERS)
    if cookies:
        headers["Cookie"] = cookies
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parse_list_page(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for anchor in soup.select("a[href*='/p-oi']"):
        href = anchor.get("href")
        if not href:
            continue
        full = urljoin(base_url, href)
        if full not in links:
            links.append(full)
    return links


def parse_detail_page(url: str, html: str, page_no: int) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text("\n", strip=True)

    title = ""
    for selector in ("h1", ".tit h1", ".cn_tit", ".title"):
        node = soup.select_one(selector)
        if node:
            title = clean_text(node.get_text(" ", strip=True))
            break

    image_url = ""
    for selector in ("meta[property='og:image']", ".swiper img", ".hero img", "img"):
        node = soup.select_one(selector)
        if node:
            image_url = node.get("content") or node.get("src") or ""
            if image_url:
                break

    rating = ""
    rating_match = re.search(r"评分[:：]?\s*([0-5](?:\.\d)?)", page_text)
    if rating_match:
        rating = rating_match.group(1)

    return [
        title,
        url,
        extract_label_value(page_text, "地址"),
        extract_label_value(page_text, "介绍") or extract_label_value(page_text, "景点介绍"),
        extract_label_value(page_text, "开放时间"),
        image_url,
        rating,
        extract_label_value(page_text, "建议游玩时间"),
        extract_label_value(page_text, "建议季节"),
        extract_label_value(page_text, "门票"),
        extract_label_value(page_text, "小贴士"),
        page_no,
    ]


def save_to_excel(rows: list[list[str]], output_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(row)
    workbook.save(output_path)


def import_to_database(excel_path: Path) -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_travel.settings")
    os.chdir(Path(__file__).resolve().parents[1])
    import django

    django.setup()

    from apps.destinations.importers import import_excel_file

    import_excel_file(excel_path, overwrite=True)


def main():
    parser = argparse.ArgumentParser(description="Crawl Qunar travel pages into workbook and optionally import into Django.")
    parser.add_argument("--city-name", required=True, help="City name for the output workbook, e.g. 阿坝")
    parser.add_argument("--list-url", help="Qunar city list page URL. The script will extract /p-oi detail links.")
    parser.add_argument("--detail-urls-file", help="Fallback text file with one Qunar detail URL per line.")
    parser.add_argument("--cookies", default="", help="Optional Cookie header copied from browser if direct requests are blocked.")
    parser.add_argument("--excel-output", default="", help="Output .xlsx path. Defaults to <city-name>.xlsx in current directory.")
    parser.add_argument("--import-db", action="store_true", help="Import the generated workbook into Django/MySQL after crawling.")
    args = parser.parse_args()

    detail_urls: list[str] = []
    if args.list_url:
        list_html = fetch_html(args.list_url, cookies=args.cookies)
        detail_urls = parse_list_page(list_html, args.list_url)
    elif args.detail_urls_file:
        detail_urls = [line.strip() for line in Path(args.detail_urls_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        parser.error("At least one of --list-url or --detail-urls-file is required.")

    rows = []
    for index, url in enumerate(detail_urls, start=1):
        try:
            html = fetch_html(url, cookies=args.cookies)
            rows.append(parse_detail_page(url, html, page_no=((index - 1) // 10) + 1))
            print(f"[OK] {url}")
        except Exception as exc:
            print(f"[WARN] failed to crawl {url}: {exc}")

    output_path = Path(args.excel_output) if args.excel_output else Path(f"{args.city_name}.xlsx")
    save_to_excel(rows, output_path)
    print(f"Saved workbook: {output_path}")

    if args.import_db:
        import_to_database(output_path)
        print("Imported into Django database.")


if __name__ == "__main__":
    main()
