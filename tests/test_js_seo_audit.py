"""JS Labs page check: scoring stays local, and private addresses never connect."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "web" / "py" / "js_seo_audit.py"


def _load():
    spec = importlib.util.spec_from_file_location("js_seo_audit", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = _load()

STRONG = """<!doctype html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Garden benches for small Cape Town courtyards</title>
<meta name="description" content="Solid timber benches sized for a courtyard, with seat height, timber and lead time spelled out before you enquire.">
<link rel="canonical" href="https://example.com/benches">
<meta property="og:title" content="Garden benches for small courtyards">
<meta property="og:description" content="Timber benches with the seat height and lead time written out.">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product","name":"Bench"}</script>
</head>
<body>
<h1>Garden benches for small courtyards</h1>
<p>BODY</p>
<img src="/bench.jpg" alt="Saligna bench in a courtyard">
<a href="/care">How to oil the bench</a>
<a href="https://example.org/timber">Timber notes</a>
</body>
</html>
"""

WEAK = """<!doctype html>
<html>
<head>
<meta name="robots" content="noindex, nofollow">
</head>
<body>
<p>Hello.</p>
<img src="/plain.jpg">
</body>
</html>
"""


def _with_body(html: str) -> str:
    paragraph = "The bench uses saligna slats, a steel frame, and a 450 millimetre seat. " * 40
    return html.replace("BODY", paragraph)


def test_strong_page_scores_above_a_broken_page() -> None:
    strong = audit.audit_html(_with_body(STRONG), url="https://example.com/benches")
    weak = audit.audit_html(WEAK, url="http://example.com/thin")
    assert strong["ok"] is True
    assert weak["ok"] is True
    assert strong["score"] > weak["score"]
    assert strong["counts"]["fix"] == 0
    assert weak["counts"]["fix"] >= 3
    assert 0 <= strong["score"] <= 100
    assert 0 <= weak["score"] <= 100


def test_missing_title_heading_and_noindex_are_fixes() -> None:
    report = audit.audit_html(WEAK, url="https://example.com/thin")
    by_id = {item["id"]: item for item in report["checks"]}
    assert by_id["title"]["status"] == "fix"
    assert by_id["h1"]["status"] == "fix"
    assert by_id["description"]["status"] == "fix"
    assert by_id["robots"]["status"] == "fix"
    assert by_id["alt"]["status"] == "fix"
    assert by_id["https"]["status"] == "clear"


def test_templated_snippet_is_a_fix() -> None:
    html = _with_body(STRONG).replace(
        'content="Solid timber benches sized for a courtyard, with seat height, timber and lead time spelled out before you enquire.">',
        'content="Garden benches for small Cape Town courtyards. Learn more now.">',
    )
    report = audit.audit_html(html, url="https://example.com/benches")
    by_id = {item["id"]: item for item in report["checks"]}
    assert by_id["metadata"]["status"] == "fix"


def test_private_address_is_refused() -> None:
    result = audit.audit_url("http://127.0.0.1/secret")
    assert result["ok"] is False
    assert result["code"] == "unsafe_url"
    assert "127.0.0.1" not in result["error"]


def test_cli_json_reads_a_file(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    page.write_text(_with_body(STRONG), encoding="utf-8")
    from io import StringIO

    buffer = StringIO()
    original = audit.sys.stdout
    audit.sys.stdout = buffer
    try:
        code = audit.main(["https://example.com/benches", "--html", str(page), "--json"])
    finally:
        audit.sys.stdout = original
    payload = json.loads(buffer.getvalue())
    assert code == 0
    assert payload["ok"] is True
    assert payload["page"]["schema_types"] == ["Product"]
