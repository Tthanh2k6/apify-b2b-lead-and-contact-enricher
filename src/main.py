"""
Apify Store Actor: B2B Website Contact, Social Links, JSON-LD & Tech Stack Enricher
Extracts verified business emails (filtering out Sentry/Wix/asset noise), phone numbers,
social media handles, Schema.org JSON-LD entities, and technology stack fingerprints.
"""
import asyncio
import json
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Any, Set

import httpx
from bs4 import BeautifulSoup

try:
    from apify import Actor
    HAS_APIFY = True
except ImportError:
    HAS_APIFY = False

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,10}")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}")

JUNK_EMAIL_DOMAINS = {
    "sentry.io", "sentry.wixpress.com", "sentry-next.wixpress.com",
    "example.com", "domain.com", "email.com", "yoursite.com", "wix.com"
}
JUNK_EMAIL_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js", ".woff", ".ttf")

SOCIAL_PATTERNS = {
    "linkedin": re.compile(r"https?://(?:[\w]+\.)?linkedin\.com/(?:company|in)/[^\s\"'<>?]+", re.I),
    "facebook": re.compile(r"https?://(?:[\w]+\.)?facebook\.com/(?!sharer|share|dialog)[^\s\"'<>?]+", re.I),
    "instagram": re.compile(r"https?://(?:[\w]+\.)?instagram\.com/[^\s\"'<>?]+", re.I),
    "twitter_x": re.compile(r"https?://(?:[\w]+\.)?(?:twitter\.com|x\.com)/(?!intent|share)[^\s\"'<>?]+", re.I),
    "youtube": re.compile(r"https?://(?:[\w]+\.)?youtube\.com/(?:@|channel/|c/|user/)[^\s\"'<>?]+", re.I),
    "tiktok": re.compile(r"https?://(?:[\w]+\.)?tiktok\.com/@[^\s\"'<>?]+", re.I),
}

TECH_SIGNATURES = {
    "Shopify": [r"cdn\.shopify\.com", r"Shopify\.theme"],
    "WooCommerce": [r"woocommerce", r"wc-api"],
    "WordPress": [r"wp-content/", r"wp-includes/"],
    "Next.js": [r"/_next/static/", r"__NEXT_DATA__"],
    "Nuxt.js": [r"/_nuxt/", r"__NUXT__"],
    "React": [r"react-dom", r"data-reactroot"],
    "Vue.js": [r"vue\.runtime", r"data-v-"],
    "Webflow": [r"webflow\.com", r"data-wf-site"],
    "HubSpot": [r"js\.hs-scripts\.com", r"js\.hsforms\.net"],
    "Google Tag Manager": [r"googletagmanager\.com/gtm\.js"],
    "Google Analytics 4": [r"googletagmanager\.com/gtag/js"],
    "Meta Pixel": [r"connect\.facebook\.net/.*/fbevents\.js"],
    "Cloudflare": [r"cdnjs\.cloudflare\.com", r"__cf_bm"],
    "Stripe": [r"js\.stripe\.com"],
    "Intercom": [r"widget\.intercom\.io"],
}


def clean_emails(raw_emails: List[str]) -> List[str]:
    valid: Set[str] = set()
    for e in raw_emails:
        email = e.strip().lower().rstrip(".")
        if any(email.endswith(ext) for ext in JUNK_EMAIL_EXTS):
            continue
        parts = email.split("@")
        if len(parts) != 2:
            continue
        domain = parts[1]
        if domain in JUNK_EMAIL_DOMAINS or "sentry" in domain:
            continue
        valid.add(email)
    return sorted(valid)


def detect_tech_stack(html: str, headers: Dict[str, str]) -> List[str]:
    detected: Set[str] = set()
    server_hdr = (headers.get("server") or "").lower()
    powered_hdr = (headers.get("x-powered-by") or "").lower()
    if "cloudflare" in server_hdr:
        detected.add("Cloudflare")
    if "nginx" in server_hdr:
        detected.add("Nginx")
    if "express" in powered_hdr:
        detected.add("Express / Node.js")

    for tech, patterns in TECH_SIGNATURES.items():
        for pat in patterns:
            if re.search(pat, html, re.I):
                detected.add(tech)
                break
    return sorted(detected)


def parse_json_ld(soup: BeautifulSoup) -> List[str]:
    types: Set[str] = set()
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "{}")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    t = item.get("@type")
                    if isinstance(t, str):
                        types.add(t)
                    elif isinstance(t, list):
                        types.update(str(x) for x in t)
        except Exception:
            continue
    return sorted(types)


def discover_contact_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    base_host = urlparse(base_url).netloc
    candidates: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = (a.get_text(" ", strip=True) or "").lower()
        if any(k in href.lower() or k in text for k in ("contact", "about", "impressum", "support", "team")):
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            if parsed.netloc == base_host and parsed.scheme in ("http", "https"):
                if full_url not in candidates and full_url != base_url:
                    candidates.append(full_url)
        if len(candidates) >= 2:
            break
    return candidates


async def enrich_single_url(
    client: httpx.AsyncClient,
    url: str,
    follow_contact_pages: bool = True,
) -> Dict[str, Any]:
    emails: Set[str] = set()
    phones: Set[str] = set()
    socials: Dict[str, List[str]] = {}
    tech_stack: Set[str] = set()
    json_ld_types: Set[str] = set()
    company_name = ""
    meta_description = ""
    status_code = 0
    pages_crawled = 0

    try:
        resp = await client.get(url)
        status_code = resp.status_code
        pages_crawled += 1
        html = resp.text
        headers = {k.lower(): v for k, v in resp.headers.items()}
        soup = BeautifulSoup(html, "html.parser")

        if soup.title and soup.title.string:
            company_name = soup.title.string.strip()
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if meta_tag and meta_tag.get("content"):
            meta_description = meta_tag["content"].strip()

        emails.update(clean_emails(EMAIL_REGEX.findall(html)))
        for a in soup.select("a[href^='mailto:']"):
            addr = a["href"].replace("mailto:", "").split("?")[0]
            emails.update(clean_emails([addr]))

        phones.update(m.strip() for m in PHONE_REGEX.findall(soup.get_text(" ", strip=True)))
        tech_stack.update(detect_tech_stack(html, headers))
        json_ld_types.update(parse_json_ld(soup))

        for platform, rx in SOCIAL_PATTERNS.items():
            found = sorted(set(rx.findall(html)))
            if found:
                socials[platform] = found[:3]

        if follow_contact_pages:
            sub_links = discover_contact_links(soup, str(resp.url))
            for sub_url in sub_links:
                try:
                    sub_resp = await client.get(sub_url)
                    if sub_resp.status_code == 200:
                        pages_crawled += 1
                        sub_html = sub_resp.text
                        sub_soup = BeautifulSoup(sub_html, "html.parser")
                        emails.update(clean_emails(EMAIL_REGEX.findall(sub_html)))
                        phones.update(m.strip() for m in PHONE_REGEX.findall(sub_soup.get_text(" ", strip=True)))
                        for platform, rx in SOCIAL_PATTERNS.items():
                            found = sorted(set(rx.findall(sub_html)))
                            if found:
                                existing = set(socials.get(platform, []))
                                existing.update(found)
                                socials[platform] = sorted(existing)[:3]
                except Exception:
                    continue
    except Exception as exc:
        return {
            "url": url,
            "company_name": company_name,
            "meta_description": meta_description,
            "emails": [],
            "phones": [],
            "social_profiles": {},
            "tech_stack": [],
            "json_ld_types": [],
            "pages_crawled": pages_crawled,
            "status_code": status_code,
            "error": str(exc),
        }

    return {
        "url": url,
        "company_name": company_name,
        "meta_description": meta_description,
        "emails": sorted(emails),
        "phones": sorted(phones)[:5],
        "social_profiles": socials,
        "tech_stack": sorted(tech_stack),
        "json_ld_types": sorted(json_ld_types),
        "pages_crawled": pages_crawled,
        "status_code": status_code,
        "error": None,
    }


async def run_enrichment_batch(
    urls: List[str],
    follow_contact_pages: bool = True,
    max_concurrency: int = 5,
) -> List[Dict[str, Any]]:
    sem = asyncio.Semaphore(max_concurrency)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; B2BLeadEnricherBot/1.0; +https://github.com/Tthanh2k6)"
    }
    async with httpx.AsyncClient(headers=headers, timeout=15.0, follow_redirects=True) as client:
        async def _worker(u: str) -> Dict[str, Any]:
            async with sem:
                return await enrich_single_url(client, u, follow_contact_pages=follow_contact_pages)

        return await asyncio.gather(*[_worker(u) for u in urls])


async def main() -> None:
    if HAS_APIFY:
        async with Actor:
            actor_input = await Actor.get_input() or {}
            raw_urls = actor_input.get("startUrls") or [
                {"url": "https://books.toscrape.com"},
                {"url": "https://quotes.toscrape.com"},
            ]
            follow_contact = bool(actor_input.get("followContactPages", True))
            concurrency = int(actor_input.get("maxConcurrency", 5))

            urls = [item["url"] if isinstance(item, dict) else str(item) for item in raw_urls if item]
            Actor.log.info(f"Enriching {len(urls)} target URLs (followContactPages={follow_contact})...")
            results = await run_enrichment_batch(urls, follow_contact, concurrency)
            await Actor.push_data(results)
            Actor.log.info(f"Successfully enriched and pushed {len(results)} B2B records.")
    else:
        sample_urls = ["https://books.toscrape.com", "https://quotes.toscrape.com"]
        results = await run_enrichment_batch(sample_urls, follow_contact_pages=True, max_concurrency=4)
        print(json.dumps(results, indent=2))
