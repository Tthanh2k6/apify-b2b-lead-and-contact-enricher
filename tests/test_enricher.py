import asyncio
import json

import httpx

from src.main import (
    _coerce_positive_int,
    _dedupe_social,
    _extract_start_urls,
    clean_emails,
    detect_tech_stack,
    discover_contact_links,
    enrich_single_url,
    parse_json_ld,
)
from bs4 import BeautifulSoup


def test_coerce_positive_int_handles_null_empty_invalid_and_non_positive():
    assert _coerce_positive_int(None, 25) == 25
    assert _coerce_positive_int("", 25) == 25
    assert _coerce_positive_int("  ", 5) == 5
    assert _coerce_positive_int(False, 5) == 5
    assert _coerce_positive_int("abc", 25) == 25
    assert _coerce_positive_int(0, 5) == 5
    assert _coerce_positive_int(-3, 25) == 25
    assert _coerce_positive_int("10", 5) == 10
    assert _coerce_positive_int(12, 25) == 12


def test_extract_start_urls_skips_malformed_and_blank():
    raw = [
        {},
        {"url": ""},
        {"url": "   "},
        {"url": 123},
        {"url": " https://example.org "},
        "https://books.toscrape.com",
        None,
    ]
    assert _extract_start_urls(raw) == ["https://example.org", "https://books.toscrape.com"]


def test_clean_emails_drops_telemetry_assets_and_normalizes():
    raw = [
        "Sales@Acme.com.",
        "sales@acme.com",
        "123@sentry.io",
        "err@sentry.wixpress.com",
        "logo@2x.png",
        "hero@banner.webp",
    ]
    assert clean_emails(raw) == ["sales@acme.com"]


def test_dedupe_social_strips_trailing_slash_and_backslash():
    urls = [
        "https://www.facebook.com/acmecorp/",
        "https://facebook.com/acmecorp\\",
        "https://linkedin.com/company/acme-inc/",
    ]
    assert _dedupe_social(urls) == [
        "https://linkedin.com/company/acme-inc/",
        "https://www.facebook.com/acmecorp/",
    ]


def test_detect_tech_stack_reads_headers_and_html():
    html = '<script src="https://cdn.shopify.com/s/files/app.js"></script><script src="/_next/static/chunk.js"></script>'
    headers = {"server": "cloudflare", "x-powered-by": "Express"}
    assert detect_tech_stack(html, headers) == ["Cloudflare", "Express / Node.js", "Next.js", "Shopify"]


def test_parse_json_ld_and_discover_contact_links():
    html = """
    <html>
      <script type="application/ld+json">{"@type": "Organization"}</script>
      <script type="application/ld+json">not json</script>
      <script type="application/ld+json">[{"@type": ["Product", "Thing"]}]</script>
      <a href="/contact">Contact Us</a>
      <a href="https://other.com/about">External</a>
      <a href="/team">Our Team</a>
      <a href="/support">Support</a>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    assert parse_json_ld(soup) == ["Organization", "Product", "Thing"]
    assert discover_contact_links(soup, "https://acme.example") == [
        "https://acme.example/contact",
        "https://acme.example/team",
    ]


def test_enrich_single_url_aggregates_home_and_contact_pages_offline():
    pages = {
        "https://acme.example": (
            200,
            {"server": "nginx", "x-powered-by": "Express"},
            """
            <html>
              <head><title>Acme Corp</title><meta name="description" content="B2B widgets"></head>
              <body>
                <a href="mailto:hello@acme.example">Email</a>
                <a href="/contact">Contact</a>
                <script type="application/ld+json">{"@type": "Organization"}</script>
                <a href="https://linkedin.com/company/acme-corp">LI</a>
              </body>
            </html>
            """,
        ),
        "https://acme.example/contact": (
            200,
            {},
            "<html><body>Reach sales@acme.example or (415) 555-0199</body></html>",
        ),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        status, hdrs, body = pages[str(request.url)]
        return httpx.Response(status, headers=hdrs, text=body)

    async def _run():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await enrich_single_url(client, "https://acme.example", follow_contact_pages=True)

    result = asyncio.run(_run())
    assert result["company_name"] == "Acme Corp"
    assert result["meta_description"] == "B2B widgets"
    assert result["emails"] == ["hello@acme.example", "sales@acme.example"]
    assert result["phones"] == ["(415) 555-0199"]
    assert result["social_profiles"] == {"linkedin": ["https://linkedin.com/company/acme-corp"]}
    assert result["tech_stack"] == ["Express / Node.js", "Nginx"]
    assert result["json_ld_types"] == ["Organization"]
    assert result["pages_crawled"] == 2
    assert result["status_code"] == 200
    assert result["error"] is None
