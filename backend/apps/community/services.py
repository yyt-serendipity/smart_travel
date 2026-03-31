from html import escape
from html.parser import HTMLParser

from apps.community.models import TravelPost


def sanitize_post_content(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""

    paragraphs = [line.strip() for line in raw.splitlines() if line.strip()]
    if not paragraphs:
        return ""

    return "".join(f"<p>{escape(paragraph)}</p>" for paragraph in paragraphs)


def strip_html(value: str) -> str:
    plain_parts: list[str] = []

    class PlainTextParser(HTMLParser):
        def handle_data(self, data):
            plain_parts.append(data)

        def handle_starttag(self, tag, attrs):
            if tag in {"p", "br", "li", "blockquote", "h2", "h3"}:
                plain_parts.append(" ")

        def handle_endtag(self, tag):
            if tag in {"p", "li", "blockquote", "h2", "h3"}:
                plain_parts.append(" ")

    parser = PlainTextParser()
    parser.feed(str(value or ""))
    parser.close()
    return " ".join("".join(plain_parts).split())


def build_post_excerpt(value: str, *, max_length: int = 120) -> str:
    text = strip_html(value)
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3].rstrip()}..."


def refresh_post_counters(post: TravelPost) -> TravelPost:
    post.likes_count = post.likes.count()
    post.save(update_fields=["likes_count", "updated_at"])
    return post
