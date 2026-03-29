from __future__ import annotations

from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

from apps.community.models import TravelPost


ALLOWED_RICH_TEXT_TAGS = {
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "ul",
    "ol",
    "li",
    "blockquote",
    "h2",
    "h3",
    "a",
}

SELF_CLOSING_RICH_TEXT_TAGS = {"br"}


class RichTextSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.output: list[str] = []
        self.stack: list[str] = []
        self.ignored_tag_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.ignored_tag_depth += 1
            return
        if tag not in ALLOWED_RICH_TEXT_TAGS:
            return

        if tag == "a":
            href = ""
            for name, value in attrs:
                if name == "href":
                    href = sanitize_link_url(value)
                    break
            if not href:
                return
            self.output.append(
                f'<a href="{escape(href, quote=True)}" target="_blank" rel="noopener noreferrer">'
            )
            self.stack.append(tag)
            return

        self.output.append(f"<{tag}>")
        if tag not in SELF_CLOSING_RICH_TEXT_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.ignored_tag_depth = max(0, self.ignored_tag_depth - 1)
            return
        if tag not in ALLOWED_RICH_TEXT_TAGS or tag in SELF_CLOSING_RICH_TEXT_TAGS:
            return
        if not self.stack:
            return
        if self.stack[-1] != tag:
            return
        self.stack.pop()
        self.output.append(f"</{tag}>")

    def handle_data(self, data):
        if self.ignored_tag_depth:
            return
        self.output.append(escape(data))

    def handle_entityref(self, name):
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        self.output.append(f"&#{name};")

    def get_html(self) -> str:
        output = list(self.output)
        for tag in reversed(self.stack):
            output.append(f"</{tag}>")
        return "".join(output)


def sanitize_link_url(value: str | None) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("/"):
        return raw

    parsed = urlparse(raw)
    if parsed.scheme.lower() not in {"http", "https", "mailto", "tel"}:
        return ""
    return raw


def sanitize_post_content(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""

    sanitizer = RichTextSanitizer()
    sanitizer.feed(raw)
    sanitizer.close()
    return sanitizer.get_html().strip()


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
    return f"{text[: max_length - 1].rstrip()}…"


def refresh_post_counters(post: TravelPost) -> TravelPost:
    post.likes_count = post.likes.count()
    post.save(update_fields=["likes_count", "updated_at"])
    return post
