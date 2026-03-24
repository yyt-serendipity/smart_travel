from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook


HEADERS = (
    "名字",
    "链接",
    "地址",
    "介绍",
    "开放时间",
    "图片链接",
    "评分",
    "建议游玩时间",
    "建议季节",
    "门票",
    "小贴士",
    "Page",
)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0 Safari/537.36",
    "Referer": "https://you.ctrip.com/",
}

SEARCH_HEADERS = {
    **DEFAULT_HEADERS,
    "Referer": "https://www.ctrip.com/",
    "Origin": "https://www.ctrip.com",
}

SEARCH_ENDPOINT = "https://m.ctrip.com/restapi/soa2/30668/search"
RETRYABLE_EXCEPTIONS = (requests.RequestException, ValueError)
ALLOWED_RESULT_TYPES = {"district", "sight"}
GENERIC_ADMIN_SUFFIXES = ("市", "州", "地区", "盟", "县", "林区")
CANONICAL_SUFFIXES = tuple(
    sorted(
        {
            "特别行政区",
            "土家族苗族自治州",
            "藏族羌族自治州",
            "蒙古族藏族自治州",
            "壮族苗族自治州",
            "哈萨克自治州",
            "朝鲜族自治州",
            "柯尔克孜自治州",
            "蒙古自治州",
            "回族自治州",
            "彝族自治州",
            "藏族自治州",
            "自治州",
            "地区",
            "林区",
            "风景名胜区",
            "国家森林公园",
            "国家湿地公园",
            "旅游度假区",
            "森林公园",
            "湿地公园",
            "风景区",
            "景区",
            "旅游区",
            "度假区",
            "古镇",
            "古城",
            "山水画廊",
            "乐园",
            "市",
            "州",
            "盟",
            "区",
            "县",
        },
        key=len,
        reverse=True,
    )
)

# 这些名字在携程搜索里更适合用行政区简称或全称去查。
QUERY_ALIAS_OVERRIDES = {
    "阿坝": ("阿坝藏族羌族自治州",),
    "博尔塔拉": ("博尔塔拉蒙古自治州",),
    "昌吉": ("昌吉回族自治州",),
    "楚雄州": ("楚雄彝族自治州",),
    "大兴安岭": ("大兴安岭地区",),
    "恩施": ("恩施州", "恩施土家族苗族自治州"),
    "甘孜": ("甘孜藏族自治州",),
    "海西": ("海西蒙古族藏族自治州",),
    "和田": ("和田地区",),
    "黄山": ("黄山市",),
    "喀什": ("喀什市",),
    "克孜勒苏柯尔克孜": ("克孜勒苏",),
    "莱芜": ("莱芜区",),
    "凉山": ("凉山彝族自治州",),
    "塔城": ("塔城地区",),
    "文山": ("文山壮族苗族自治州",),
    "湘西": ("湘西土家族苗族自治州",),
    "伊犁": ("伊犁哈萨克自治州",),
    "阿克苏": ("阿克苏地区",),
    "阿勒泰": ("阿勒泰地区",),
}


@dataclass
class ResolvedSource:
    target_name: str
    query: str
    matched_word: str
    matched_type: str
    matched_child_type: str
    source_url: str
    city_url: str
    score: int


def clean_text(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\r", "\n").split())


def html_to_text(value: str) -> str:
    if not value:
        return ""
    return BeautifulSoup(value, "html.parser").get_text("\n", strip=True)


def sleep_if_needed(seconds: float) -> None:
    if seconds > 0:
        time.sleep(seconds)


def request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    retries: int = 3,
    retry_sleep: float = 1.0,
    **kwargs,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = session.request(method=method, url=url, **kwargs)
            response.raise_for_status()
            return response
        except RETRYABLE_EXCEPTIONS as exc:
            last_error = exc
            if attempt >= retries:
                break
            print(f"[RETRY] {method.upper()} {url} ({attempt}/{retries}) -> {exc}")
            sleep_if_needed(retry_sleep * attempt)
    raise RuntimeError(f"请求失败: {url}") from last_error


def fetch_html(url: str, session: requests.Session) -> str:
    response = request_with_retries(
        session,
        "GET",
        url,
        headers=DEFAULT_HEADERS,
        timeout=30,
    )
    return response.text


def fetch_json_via_post(url: str, session: requests.Session, data: dict) -> dict:
    response = request_with_retries(
        session,
        "POST",
        url,
        headers=SEARCH_HEADERS,
        data=data,
        timeout=20,
    )
    return response.json()


def extract_next_data(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script or not script.string:
        raise ValueError("未找到页面内的 __NEXT_DATA__ 数据。")
    return json.loads(script.string)


def build_city_page_url(city_url: str, page_no: int) -> str:
    if page_no <= 1:
        return city_url
    base = city_url.rstrip("/")
    if base.endswith(".html"):
        base = base[:-5]
    return f"{base}/s0-p{page_no}.html"


def parse_city_page(city_url: str, page_no: int, session: requests.Session) -> tuple[str, list[dict], bool]:
    html = fetch_html(build_city_page_url(city_url, page_no), session)
    data = extract_next_data(html)
    init_data = data["props"]["pageProps"]["initialState"]["listInitData"]
    city_name = init_data.get("districtName", "")

    attractions = []
    for item in init_data.get("attractionList", []):
        card = item.get("card") or {}
        detail_url = card.get("detailUrl") or card.get("detailUrlInfo", {}).get("url", "")
        if not detail_url:
            continue
        attractions.append(
            {
                "name": card.get("poiName", ""),
                "detail_url": normalize_ctrip_url(detail_url),
                "image_url": card.get("dynamicCoverImageUrl") or card.get("coverImageUrl", ""),
                "rating": card.get("commentScore") or "",
                "address": "",
                "ticket": "免费" if card.get("isFree") else (f"{card.get('price')}元起" if card.get("price") else ""),
                "page_no": page_no,
            }
        )
    return city_name, attractions, bool(init_data.get("hasMore"))


def parse_ticket_info(poi_detail: dict, card_fallback: dict) -> str:
    ticket_lines = [card_fallback["ticket"]] if card_fallback.get("ticket") else []

    for policy in (poi_detail.get("policyInfoList") or [])[:4]:
        name = clean_text(policy.get("name"))
        desc = clean_text(policy.get("policyDesc"))
        if name or desc:
            ticket_lines.append(f"{name} {desc}".strip())

    if not ticket_lines and not poi_detail.get("needTicket", True):
        ticket_lines.append("免费")
    return "\n".join(ticket_lines)


def parse_detail_page(card: dict, session: requests.Session) -> list[str]:
    html = fetch_html(card["detail_url"], session)
    data = extract_next_data(html)
    poi_detail = data["props"]["pageProps"]["initialState"]["poiDetail"]

    images = poi_detail.get("imageInfo", {}).get("poiPhotoImageList") or []
    image_url = images[0].get("imageUrl", "") if images else card.get("image_url", "")
    notice = poi_detail.get("noticeInfo", {}) or {}
    open_info = poi_detail.get("openInfo", {}) or {}

    return [
        clean_text(poi_detail.get("poiName") or card.get("name")),
        card["detail_url"],
        clean_text(poi_detail.get("address") or card.get("address")),
        html_to_text(poi_detail.get("introduction", "")),
        clean_text(open_info.get("openTime") or open_info.get("latelyOpenTime")),
        image_url,
        str(poi_detail.get("commentScore") or card.get("rating") or ""),
        clean_text(open_info.get("playSpendTime")),
        "",
        parse_ticket_info(poi_detail, card),
        html_to_text(notice.get("poiNoticeContent", ""))[:4000],
        card["page_no"],
    ]


def save_to_excel(rows: list[list[str]], output_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(row)
    workbook.save(output_path)


def read_city_sources(path: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line:
            city_name, city_url = [part.strip() for part in line.split(",", 1)]
        else:
            city_name, city_url = "", line
        entries.append((city_name, city_url))
    return entries


def read_city_names(path: Path) -> list[str]:
    names: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "," in line:
            line = line.split(",", 1)[0].strip()
        names.append(line)
    return names


def read_city_names_from_directory(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"目录不存在: {path}")
    return sorted({item.stem for item in path.glob("*.xlsx")})


def normalize_ctrip_url(url: str) -> str:
    text = clean_text(url)
    if not text:
        return ""
    if text.startswith("//"):
        text = f"https:{text}"
    elif text.startswith("/"):
        text = f"https://you.ctrip.com{text}"
    elif text.startswith("http://"):
        text = f"https://{text[7:]}"
    return text


def canonicalize_name(value: str) -> str:
    text = re.sub(r"[\s·•・()（）\[\]【】]", "", clean_text(value))
    while True:
        for suffix in CANONICAL_SUFFIXES:
            if text.endswith(suffix) and len(text) > len(suffix):
                text = text[: -len(suffix)]
                break
        else:
            return text


def has_admin_suffix(name: str) -> bool:
    return any(name.endswith(suffix) for suffix in GENERIC_ADMIN_SUFFIXES)


def dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def build_generic_admin_variants(target_name: str) -> list[str]:
    if has_admin_suffix(target_name):
        return []
    return dedupe_strings([f"{target_name}{suffix}" for suffix in GENERIC_ADMIN_SUFFIXES])


def score_search_candidate(target_name: str, query: str, item: dict) -> int:
    raw_url = normalize_ctrip_url(item.get("url", ""))
    if not raw_url:
        return -10_000

    parsed = urlparse(raw_url)
    if parsed.netloc and "ctrip.com" not in parsed.netloc:
        return -10_000

    path = parsed.path.lower()
    item_type = str(item.get("type") or "").lower()
    child_type = str(item.get("childType") or "").upper()
    word = clean_text(item.get("word"))
    target_norm = canonicalize_name(target_name)
    query_norm = canonicalize_name(query)
    word_norm = canonicalize_name(word)

    if item_type not in ALLOWED_RESULT_TYPES and not (path.startswith("/place/") or path.startswith("/sight/")):
        return -10_000

    score = 0
    if item_type == "district" or path.startswith("/place/"):
        score += 100
    elif item_type == "sight" or path.startswith("/sight/"):
        score += 60

    if child_type == "CITY":
        score += 30
    elif child_type == "SIGHTZONE":
        score += 20
    elif child_type:
        score += 5

    if word == target_name:
        score += 80
    elif word_norm == target_norm:
        score += 60

    if word == query:
        score += 25
    elif word_norm == query_norm:
        score += 15

    if target_name and target_name in word:
        score += 20
    if target_norm and target_norm in word_norm:
        score += 15
    if word_norm and word_norm in target_norm:
        score += 10

    if item_type == "district" and child_type == "CITY" and word_norm == target_norm:
        score += 15
    return score


def search_ctrip_candidates(query: str, session: requests.Session) -> list[dict]:
    payload = fetch_json_via_post(
        SEARCH_ENDPOINT,
        session,
        data={"action": "online", "source": "globalonline", "keyword": query},
    )
    return payload.get("data") or []


def extract_last_int(text: str) -> int | None:
    matches = re.findall(r"(\d+)", text)
    if not matches:
        return None
    return int(matches[-1])


def extract_detail_district_id(detail_url: str, session: requests.Session) -> int | None:
    try:
        html = fetch_html(detail_url, session)
        data = extract_next_data(html)
        poi_detail = data["props"]["pageProps"]["initialState"]["poiDetail"]
    except Exception:
        return None
    district_id = poi_detail.get("districtId")
    return int(district_id) if district_id else None


def build_city_list_url_from_candidate(source_url: str, session: requests.Session) -> str | None:
    normalized = normalize_ctrip_url(source_url)
    if not normalized:
        return None

    parsed = urlparse(normalized)
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return None

    district_id: int | None = None
    section = parts[0].lower()
    if section == "place" and len(parts) >= 2:
        district_id = extract_last_int(parts[1])
    elif section == "sight" and len(parts) >= 2:
        district_id = extract_last_int(parts[1])
        if district_id is None and len(parts) >= 3:
            district_id = extract_last_int(parts[2])
        if district_id is None:
            district_id = extract_detail_district_id(normalized, session)

    if district_id is None:
        return None
    return f"https://you.ctrip.com/sight/{district_id}.html"


def is_confident_resolution(target_name: str, resolution: ResolvedSource) -> bool:
    target_norm = canonicalize_name(target_name)
    word_norm = canonicalize_name(resolution.matched_word)
    return resolution.matched_type == "district" and word_norm == target_norm


def is_better_resolution(candidate: ResolvedSource, current_best: ResolvedSource | None) -> bool:
    if current_best is None:
        return True
    if candidate.score != current_best.score:
        return candidate.score > current_best.score
    if candidate.matched_type != current_best.matched_type:
        return candidate.matched_type == "district"
    return len(candidate.matched_word) > len(current_best.matched_word)


def resolve_city_source_from_queries(
    target_name: str,
    queries: list[str],
    session: requests.Session,
    search_delay: float,
    current_best: ResolvedSource | None = None,
) -> ResolvedSource | None:
    best = current_best
    for query in dedupe_strings(queries):
        try:
            candidates = search_ctrip_candidates(query, session)
        except Exception as exc:
            print(f"[WARN] 搜索失败 {target_name} <- {query}: {exc}")
            sleep_if_needed(search_delay)
            continue

        for item in candidates:
            score = score_search_candidate(target_name, query, item)
            if score < 0:
                continue
            source_url = normalize_ctrip_url(item.get("url", ""))
            city_url = build_city_list_url_from_candidate(source_url, session)
            if not city_url:
                continue
            resolved = ResolvedSource(
                target_name=target_name,
                query=query,
                matched_word=clean_text(item.get("word")),
                matched_type=str(item.get("type") or ""),
                matched_child_type=str(item.get("childType") or ""),
                source_url=source_url,
                city_url=city_url,
                score=score,
            )
            if is_better_resolution(resolved, best):
                best = resolved

        if best and is_confident_resolution(target_name, best):
            break
        sleep_if_needed(search_delay)
    return best


def resolve_city_source(target_name: str, session: requests.Session, search_delay: float) -> ResolvedSource | None:
    best = resolve_city_source_from_queries(target_name, [target_name], session, search_delay)

    alias_queries = list(QUERY_ALIAS_OVERRIDES.get(target_name, ()))
    if alias_queries:
        best = resolve_city_source_from_queries(target_name, alias_queries, session, search_delay, current_best=best)
        if best and (is_confident_resolution(target_name, best) or best.score >= 150):
            return best

    if best and is_confident_resolution(target_name, best):
        return best

    if best is None or best.score < 150:
        best = resolve_city_source_from_queries(
            target_name,
            build_generic_admin_variants(target_name),
            session,
            search_delay,
            current_best=best,
        )
    return best


def write_city_source_map(entries: list[ResolvedSource], output_path: Path) -> None:
    lines = [f"{item.target_name},{item.city_url}" for item in entries]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_missing_names(names: list[str], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(names) + ("\n" if names else ""), encoding="utf-8")


def write_discovery_report(entries: list[ResolvedSource], output_path: Path) -> None:
    lines = ["target_name\tquery\tmatched_word\tmatched_type\tmatched_child_type\tsource_url\tcity_url\tscore"]
    lines.extend(
        "\t".join(
            [
                item.target_name,
                item.query,
                item.matched_word,
                item.matched_type,
                item.matched_child_type,
                item.source_url,
                item.city_url,
                str(item.score),
            ]
        )
        for item in entries
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def import_to_database(excel_path: Path) -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_travel.settings")
    os.chdir(Path(__file__).resolve().parents[1])
    import django

    django.setup()

    from apps.destinations.importers import import_excel_file

    import_excel_file(excel_path, overwrite=True)


def crawl_city(
    city_name_hint: str,
    city_url: str,
    output_dir: Path,
    session: requests.Session,
    max_pages: int,
    max_attractions: int,
    delay: float,
    import_db: bool,
) -> Path | None:
    seen_urls: set[str] = set()
    cards: list[dict] = []
    detected_name = city_name_hint
    page_no = 1

    while True:
        if max_pages > 0 and page_no > max_pages:
            break

        detected_name, page_cards, has_more = parse_city_page(city_url, page_no, session)
        for card in page_cards:
            if card["detail_url"] in seen_urls:
                continue
            seen_urls.add(card["detail_url"])
            cards.append(card)
            if max_attractions > 0 and len(cards) >= max_attractions:
                break

        if (max_attractions > 0 and len(cards) >= max_attractions) or not has_more:
            break

        page_no += 1
        sleep_if_needed(delay)

    if not cards:
        return None

    rows: list[list[str]] = []
    for index, card in enumerate(cards, start=1):
        try:
            rows.append(parse_detail_page(card, session))
            print(f"[OK] {city_name_hint or detected_name} #{index}: {card['name']}")
        except Exception as exc:
            print(f"[WARN] 详情抓取失败 {card['detail_url']}: {exc}")
        sleep_if_needed(delay)

    output_name = city_name_hint or detected_name or Path(urlparse(city_url).path).stem
    output_path = output_dir / f"{output_name}.xlsx"
    save_to_excel(rows, output_path)
    print(f"[SAVE] {output_path}")

    if import_db:
        import_to_database(output_path)
        print(f"[DB] 已导入 {output_name}")

    return output_path


def build_name_list(args: argparse.Namespace, output_dir: Path) -> list[str]:
    if args.discover_from_directory:
        names = read_city_names_from_directory(Path(args.discover_from_directory))
    elif args.city_names_file:
        names = read_city_names(Path(args.city_names_file))
    else:
        return []

    if args.skip_existing:
        names = [name for name in names if not (output_dir / f"{name}.xlsx").exists()]
    if args.max_cities and args.max_cities > 0:
        names = names[: args.max_cities]
    return names


def discover_city_sources(names: list[str], session: requests.Session, search_delay: float) -> tuple[list[ResolvedSource], list[str]]:
    resolved: list[ResolvedSource] = []
    missing: list[str] = []
    for index, name in enumerate(names, start=1):
        result = resolve_city_source(name, session, search_delay)
        if result:
            resolved.append(result)
            print(
                f"[MAP] {index}/{len(names)} {name} <- {result.matched_word} "
                f"({result.matched_type}/{result.matched_child_type or '-'})"
            )
        else:
            missing.append(name)
            print(f"[MISS] {index}/{len(names)} {name}")
    return resolved, missing


def main() -> None:
    parser = argparse.ArgumentParser(description="从携程抓取城市/景区景点及详情，并导出为项目兼容的 Excel。")
    parser.add_argument("--city-url", help="单个景点列表页，例如 https://you.ctrip.com/sight/chengdu104.html")
    parser.add_argument("--city-name", default="", help="单个输出文件名，可选")
    parser.add_argument(
        "--city-urls-file",
        default=str(Path(__file__).with_name("ctrip_city_urls_sample.txt")),
        help="多城市配置文件，每行格式为 `城市名,城市URL`。",
    )
    parser.add_argument("--city-names-file", help="待搜索的城市名文件，每行一个名字。")
    parser.add_argument("--discover-from-directory", help="从目录内的 xlsx 文件名自动提取城市名。")
    parser.add_argument("--list-only", action="store_true", help="只生成城市 URL 映射，不执行抓取。")
    parser.add_argument("--output-city-urls-file", help="将自动发现出的 `城市名,城市URL` 写入文件。")
    parser.add_argument("--missing-city-names-file", help="将未匹配到的城市名写入文件。")
    parser.add_argument("--discovery-report-file", help="将匹配明细写入 TSV 报告。")
    parser.add_argument("--output-dir", default=str(Path("crawled_city_excels")))
    parser.add_argument("--skip-existing", action="store_true", help="如果输出文件已存在则跳过。")
    parser.add_argument("--max-cities", type=int, default=0, help="最多处理多少个城市，0 表示不限制。")
    parser.add_argument("--max-pages", type=int, default=3, help="每个城市最多抓取多少个列表页，0 表示全部。")
    parser.add_argument("--max-attractions", type=int, default=30, help="每个城市最多抓取多少个景点，0 表示全部。")
    parser.add_argument("--delay", type=float, default=0.5, help="景点列表/详情请求间隔秒数。")
    parser.add_argument("--search-delay", type=float, default=0.1, help="城市搜索请求间隔秒数。")
    parser.add_argument("--import-db", action="store_true", help="抓取后直接导入 Django/MySQL。")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    sources: list[tuple[str, str]] = []
    resolved_entries: list[ResolvedSource] = []
    missing_names: list[str] = []

    if args.city_url:
        sources.append((args.city_name, normalize_ctrip_url(args.city_url)))
    else:
        names = build_name_list(args, output_dir)
        if names:
            resolved_entries, missing_names = discover_city_sources(names, session, args.search_delay)
            if args.output_city_urls_file:
                write_city_source_map(resolved_entries, Path(args.output_city_urls_file))
            if args.missing_city_names_file:
                write_missing_names(missing_names, Path(args.missing_city_names_file))
            if args.discovery_report_file:
                write_discovery_report(resolved_entries, Path(args.discovery_report_file))
            if args.list_only:
                print(
                    f"[DONE] 城市发现完成：成功 {len(resolved_entries)}，失败 {len(missing_names)}。"
                )
                return
            sources = [(item.target_name, item.city_url) for item in resolved_entries]
        else:
            source_file = Path(args.city_urls_file)
            if not source_file.exists():
                raise SystemExit(f"城市 URL 文件不存在: {source_file}")
            sources = read_city_sources(source_file)
            if args.max_cities and args.max_cities > 0:
                sources = sources[: args.max_cities]

    created: list[Path] = []
    for city_name, city_url in sources:
        output_path = output_dir / f"{city_name}.xlsx" if city_name else None
        if args.skip_existing and output_path and output_path.exists():
            print(f"[SKIP] {city_name} 已存在")
            continue
        try:
            result = crawl_city(
                city_name_hint=city_name,
                city_url=city_url,
                output_dir=output_dir,
                session=session,
                max_pages=args.max_pages,
                max_attractions=args.max_attractions,
                delay=args.delay,
                import_db=args.import_db,
            )
            if result:
                created.append(result)
        except Exception as exc:
            print(f"[WARN] 城市抓取失败 {city_name or city_url}: {exc}")

    print(f"[DONE] 共生成 {len(created)} 个文件，目录：{output_dir}")
    if missing_names:
        print(f"[DONE] 仍有 {len(missing_names)} 个名字未匹配。")


if __name__ == "__main__":
    main()
