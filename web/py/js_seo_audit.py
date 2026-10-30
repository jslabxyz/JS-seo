#!/usr/bin/env python3
"""Page check for the JS Labs SEO tool.

Reads one public URL, or a saved HTML file, and returns a short JSON report:
what is missing, what is thin, and what is already clear. Fetching goes
through the Claude SEO URL safety checks, so private and loopback addresses
are refused before a connection is opened.

The report describes the HTML the server sent. It does not run page scripts.

Usage:
    python js_seo_audit.py https://example.com --json
    python js_seo_audit.py https://example.com --html page.html --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Optional
from urllib.parse import urlparse

_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from content_quality import analyse as analyse_content  # noqa: E402
from fetch_page import fetch_page  # noqa: E402
from metadata_template import analyse as analyse_metadata  # noqa: E402
from parse_html import parse_html  # noqa: E402

_STATUS_WEIGHT = {"clear": 1.0, "review": 0.55, "fix": 0.0}
_HTML_LANG_RE = re.compile(r"<html\b([^>]*)>", re.IGNORECASE)
_LANG_ATTR_RE = re.compile(r"""\blang\s*=\s*['"]([^'"]+)['"]""", re.IGNORECASE)
_META_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
_VIEWPORT_RE = re.compile(r"""\bname\s*=\s*['"]viewport['"]""", re.IGNORECASE)
_MAX_URL_LENGTH = 2000
_MAX_TEXT_CHARS = 100_000


def _error(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "error": message}


def _clip(value: Optional[str], limit: int) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _header(headers: Optional[dict], name: str) -> str:
    wanted = name.lower()
    for key, value in (headers or {}).items():
        if str(key).lower() == wanted:
            return str(value)
    return ""


def _has_noindex(*values: str) -> bool:
    for value in values:
        tokens = re.split(r"[\s,;]+", (value or "").lower())
        if "noindex" in tokens or "none" in tokens:
            return True
    return False


def _language(html: str) -> str:
    match = _HTML_LANG_RE.search(html or "")
    if not match:
        return ""
    found = _LANG_ATTR_RE.search(match.group(1))
    return found.group(1).strip() if found else ""


def _has_viewport(html: str) -> bool:
    return any(_VIEWPORT_RE.search(tag) for tag in _META_RE.findall(html or ""))


def _visible_text(html: str) -> str:
    from bs4 import BeautifulSoup

    try:
        import lxml  # noqa: F401

        parser = "lxml"
    except ImportError:
        parser = "html.parser"
    soup = BeautifulSoup(html or "", parser)
    for element in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        element.decompose()
    return soup.get_text(separator=" ", strip=True)[:_MAX_TEXT_CHARS]


def _schema_types(items: list) -> list[str]:
    found: list[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        raw = item.get("@type")
        values = raw if isinstance(raw, list) else [raw]
        for value in values:
            if isinstance(value, str) and value and value not in found:
                found.append(value)
    return found[:8]


def _check(check_id: str, group: str, status: str, label: str, detail: str) -> dict:
    return {
        "id": check_id,
        "group": group,
        "status": status,
        "label": label,
        "detail": _clip(detail, 400),
    }


def _title_check(title: str) -> dict:
    length = len(title)
    if not title:
        return _check(
            "title", "Index", "fix", "Title",
            "Add a title that says what this page is.",
        )
    if length < 30:
        return _check(
            "title", "Index", "review", "Title",
            f"The title is {length} characters. Results usually have room for 30 to 60.",
        )
    if length > 60:
        return _check(
            "title", "Index", "review", "Title",
            f"The title is {length} characters, so a result may cut the end off.",
        )
    return _check(
        "title", "Index", "clear", "Title",
        f"The title is {length} characters, inside the usual result length.",
    )


def _description_check(description: str) -> dict:
    length = len(description)
    if not description:
        return _check(
            "description", "Index", "fix", "Description",
            "Add a description that says what the title does not.",
        )
    if length < 70:
        return _check(
            "description", "Index", "review", "Description",
            f"The description is {length} characters, shorter than a usual snippet.",
        )
    if length > 160:
        return _check(
            "description", "Index", "review", "Description",
            f"The description is {length} characters, so a snippet may cut it.",
        )
    return _check(
        "description", "Index", "clear", "Description",
        f"The description is {length} characters, a comfortable snippet length.",
    )


def _score(checks: list[dict]) -> int:
    if not checks:
        return 0
    total = sum(_STATUS_WEIGHT[item["status"]] for item in checks)
    return int(round(100 * total / len(checks)))


def _summary(checks: list[dict]) -> str:
    fixes = sum(1 for item in checks if item["status"] == "fix")
    reviews = sum(1 for item in checks if item["status"] == "review")
    if fixes == 0 and reviews == 0:
        return "Nothing in this check needs a change."
    if fixes == 0:
        return "No hard gaps. A few items are worth a look."
    if fixes == 1:
        return "One thing to fix first."
    return f"{fixes} things to fix first."


def _looks_like_html(html: str, content_type: str) -> bool:
    kind = (content_type or "").lower()
    if kind and "html" not in kind and "xml" not in kind:
        sample = (html or "")[:800].lower()
        return "<html" in sample or "<!doctype html" in sample
    return True


def audit_html(
    html: str,
    *,
    url: str,
    status_code: int = 200,
    headers: Optional[dict] = None,
    too_large: bool = False,
    requested_url: Optional[str] = None,
) -> dict:
    """Score HTML that has already been fetched."""
    headers = headers or {}
    page_url = url or requested_url or ""
    parsed_url = urlparse(page_url)
    content_type = _header(headers, "content-type")
    if not _looks_like_html(html, content_type):
        return _error("not_html", "That address did not return a web page.")

    parsed = parse_html(html or "", page_url or None)
    title = (parsed.get("title") or "").strip()
    description = (parsed.get("meta_description") or "").strip()
    robots = (parsed.get("meta_robots") or "").strip()
    x_robots = _header(headers, "x-robots-tag")
    canonical = (parsed.get("canonical") or "").strip()
    language = _language(html or "")
    h1s = [item for item in (parsed.get("h1") or []) if isinstance(item, str)]
    images = parsed.get("images") or []
    missing_alt = sum(1 for image in images if image.get("alt") is None)
    internal = (parsed.get("links") or {}).get("internal") or []
    external = (parsed.get("links") or {}).get("external") or []
    schema_types = _schema_types(parsed.get("schema") or [])
    open_graph = parsed.get("open_graph") or {}
    word_count = int(parsed.get("word_count") or 0)

    visible = _visible_text(html or "")
    quality = analyse_content(visible)
    metadata = analyse_metadata(title, description, page_url or None)

    checks: list[dict] = []
    if status_code == 200:
        checks.append(_check("status", "Index", "clear", "Response", "The server returned 200."))
    else:
        checks.append(_check(
            "status", "Index", "fix", "Response",
            f"The server returned {status_code}.",
        ))

    scheme = (parsed_url.scheme or "").lower()
    if scheme == "https":
        checks.append(_check("https", "Index", "clear", "HTTPS", "The page is served over HTTPS."))
    else:
        checks.append(_check(
            "https", "Index", "review", "HTTPS",
            "The page is not on HTTPS.",
        ))

    checks.append(_title_check(title))
    checks.append(_description_check(description))

    if _has_noindex(robots, x_robots):
        checks.append(_check(
            "robots", "Index", "fix", "Indexing",
            "The page asks search engines not to index it.",
        ))
    else:
        checks.append(_check(
            "robots", "Index", "clear", "Indexing",
            "Nothing in the HTML asks search engines to skip this page.",
        ))

    if canonical:
        checks.append(_check(
            "canonical", "Index", "clear", "Canonical",
            f"Canonical address: {_clip(canonical, 180)}",
        ))
    else:
        checks.append(_check(
            "canonical", "Index", "review", "Canonical",
            "No canonical link. Add one when more than one address can open this page.",
        ))

    if language:
        checks.append(_check(
            "language", "Index", "clear", "Language",
            f"The page declares {language}.",
        ))
    else:
        checks.append(_check(
            "language", "Index", "review", "Language",
            "The html element has no lang attribute.",
        ))

    if _has_viewport(html or ""):
        checks.append(_check(
            "viewport", "Index", "clear", "Viewport",
            "A viewport tag is present, so phones can size the page.",
        ))
    else:
        checks.append(_check(
            "viewport", "Index", "review", "Viewport",
            "No viewport tag, so phones may show a desktop layout.",
        ))

    if too_large:
        checks.append(_check(
            "size", "Index", "review", "Page size",
            "The download was cut at the size cap, so markup after that point was not read.",
        ))

    if len(h1s) == 1:
        checks.append(_check("h1", "Copy", "clear", "Heading", f"One H1: {_clip(h1s[0], 140)}"))
    elif len(h1s) == 0:
        checks.append(_check("h1", "Copy", "fix", "Heading", "The page has no H1."))
    else:
        checks.append(_check(
            "h1", "Copy", "review", "Heading",
            f"The page has {len(h1s)} H1 headings. One clear heading is easier to follow.",
        ))

    if word_count < 50:
        length_status = "review"
        length_detail = (
            f"{word_count} words of visible copy. That is thin for most pages, "
            "though some pages are short on purpose."
        )
    elif word_count < 300:
        length_status = "review"
        length_detail = f"{word_count} words of visible copy. Enough for a short page, thin for an article."
    else:
        length_status = "clear"
        length_detail = f"{word_count} words of visible copy."
    checks.append(_check("length", "Copy", length_status, "Length", length_detail))

    quality_score = int(quality.get("overall_quality") or 0)
    flag_words = {
        "thin-content": "the copy is short",
        "filler": "filler phrases",
        "ai-patterns": "stock phrasing",
        "low-density": "few specifics",
        "repetitive": "repeated lines",
    }
    flags = [flag_words.get(flag, flag) for flag in (quality.get("flags") or []) if flag != "empty-input"]
    if not visible.strip():
        checks.append(_check(
            "quality", "Copy", "review", "Copy quality",
            "There is not enough visible copy to score.",
        ))
    elif quality_score >= 70 and not flags:
        checks.append(_check(
            "quality", "Copy", "clear", "Copy quality",
            f"Quality score {quality_score} out of 100. No filler or repetition flags.",
        ))
    else:
        flag_text = f" Notes: {', '.join(flags)}." if flags else ""
        checks.append(_check(
            "quality", "Copy", "review", "Copy quality",
            f"Quality score {quality_score} out of 100.{flag_text} This is a heuristic, not a verdict.",
        ))

    severity = metadata.get("severity") or "none"
    if severity == "high":
        checks.append(_check(
            "metadata", "Copy", "fix", "Snippet wording",
            "The description repeats the title and ends on a stock call to action.",
        ))
    elif severity in ("medium", "low"):
        checks.append(_check(
            "metadata", "Copy", "review", "Snippet wording",
            "The description echoes the title, so the result says the same thing twice.",
        ))
    elif not title or not description:
        checks.append(_check(
            "metadata", "Copy", "review", "Snippet wording",
            "Title and description need to both exist before the wording can be compared.",
        ))
    else:
        checks.append(_check(
            "metadata", "Copy", "clear", "Snippet wording",
            "The description does not simply repeat the title.",
        ))

    image_count = len(images)
    if image_count == 0:
        checks.append(_check("alt", "Images", "clear", "Alt text", "No images in the HTML."))
    elif missing_alt == 0:
        checks.append(_check(
            "alt", "Images", "clear", "Alt text",
            f"All {image_count} images have an alt attribute.",
        ))
    elif missing_alt * 2 >= image_count:
        checks.append(_check(
            "alt", "Images", "fix", "Alt text",
            f"{missing_alt} of {image_count} images have no alt attribute.",
        ))
    else:
        checks.append(_check(
            "alt", "Images", "review", "Alt text",
            f"{missing_alt} of {image_count} images have no alt attribute.",
        ))

    if internal:
        checks.append(_check(
            "internal", "Links", "clear", "Internal links",
            f"{len(internal)} links stay on this host. {len(external)} leave it.",
        ))
    else:
        checks.append(_check(
            "internal", "Links", "review", "Internal links",
            "No links to other pages on this host were found in the HTML.",
        ))

    if schema_types:
        checks.append(_check(
            "schema", "Markup", "clear", "Structured data",
            "JSON-LD types: " + ", ".join(schema_types) + ".",
        ))
    else:
        checks.append(_check(
            "schema", "Markup", "review", "Structured data",
            "No JSON-LD. Add the type that matches the page, such as Article or Product.",
        ))

    og_title = (open_graph.get("og:title") or "").strip()
    og_description = (open_graph.get("og:description") or "").strip()
    if og_title and og_description:
        checks.append(_check(
            "open_graph", "Markup", "clear", "Link preview",
            "Open Graph title and description are both set.",
        ))
    elif og_title or og_description:
        checks.append(_check(
            "open_graph", "Markup", "review", "Link preview",
            "The link preview is only partly set. Add both a title and a description.",
        ))
    else:
        checks.append(_check(
            "open_graph", "Markup", "review", "Link preview",
            "No Open Graph title or description, so shares fall back to whatever the platform guesses.",
        ))

    counts = {name: sum(1 for item in checks if item["status"] == name) for name in ("fix", "review", "clear")}
    return {
        "ok": True,
        "requested_url": requested_url or page_url,
        "url": page_url,
        "status_code": status_code,
        "score": _score(checks),
        "summary": _summary(checks),
        "note": "This reads the HTML the server sends. It does not run scripts in the browser.",
        "counts": counts,
        "page": {
            "title": _clip(title, 180),
            "title_length": len(title),
            "description": _clip(description, 240),
            "description_length": len(description),
            "canonical": _clip(canonical, 180),
            "robots": _clip(robots or x_robots, 120),
            "language": language,
            "h1": [_clip(item, 140) for item in h1s[:4]],
            "h1_count": len(h1s),
            "word_count": word_count,
            "images": image_count,
            "images_missing_alt": missing_alt,
            "internal_links": len(internal),
            "external_links": len(external),
            "schema_types": schema_types,
        },
        "checks": checks,
        "engine": {
            "name": "Claude SEO",
            "license": "MIT",
            "url": "https://github.com/AgriciDaniel/claude-seo",
        },
    }


def audit_url(url: str, timeout: int = 15) -> dict:
    """Fetch one public URL and score the HTML."""
    raw = (url or "").strip()
    if not raw or len(raw) > _MAX_URL_LENGTH or any(char in raw for char in "\r\n\x00"):
        return _error("bad_url", "Enter a public http or https address.")
    candidate = raw if "://" in raw else f"https://{raw}"
    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return _error("bad_url", "Enter a public http or https address.")
    if parsed.username or parsed.password:
        return _error("bad_url", "Enter a public http or https address.")

    fetched = fetch_page(candidate, timeout=max(1, min(timeout, 30)))
    error = fetched.get("error")
    if error:
        text = str(error)
        if text.startswith("url_safety:"):
            return _error("unsafe_url", "That address is not a public web page.")
        if "timed out" in text.lower():
            return _error("timeout", "The page took too long to respond.")
        if text.startswith("SSL error"):
            return _error("tls", "The page certificate could not be checked.")
        return _error("unreachable", "The page could not be reached.")

    html = fetched.get("content") or ""
    if not html.strip():
        return _error("empty", "The page came back empty.")

    return audit_html(
        html,
        url=str(fetched.get("url") or candidate),
        status_code=int(fetched.get("status_code") or 0),
        headers=fetched.get("headers") or {},
        too_large=bool(fetched.get("too_large")),
        requested_url=candidate,
    )


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="JS Labs page check. Prints a JSON report.")
    parser.add_argument("url", nargs="?", help="Public page URL")
    parser.add_argument("--html", help="Read this HTML file instead of fetching the URL")
    parser.add_argument("--json", action="store_true", help="Print JSON (always on)")
    parser.add_argument("--timeout", type=int, default=15, help="Fetch timeout in seconds")
    args = parser.parse_args(argv)

    if args.html:
        if not args.url:
            payload = _error("bad_url", "Pass a URL with --html so links can be resolved.")
        elif not os.path.isfile(args.html):
            payload = _error("bad_file", "That HTML file could not be read.")
        else:
            with open(args.html, encoding="utf-8", errors="replace") as handle:
                html = handle.read()
            payload = audit_html(html, url=args.url, requested_url=args.url)
    elif not args.url:
        payload = _error("bad_url", "Enter a public http or https address.")
    else:
        payload = audit_url(args.url, timeout=args.timeout)

    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
