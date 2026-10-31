# B2B Website Contact, Social Links, JSON-LD and Tech Stack Enricher (Apify Actor)

An Apify actor in async Python (`httpx` + `BeautifulSoup4`). For each company or shop URL you give it, it fetches the homepage and, if `followContactPages` is on, up to two internal pages whose link or text mentions contact, about, impressum, support or team. It returns:

- the page title and meta description;
- email addresses found in the HTML (regex plus `mailto:` links on the homepage). Asset filenames (`.png`, `.svg`, `.webp`...) and placeholder or telemetry domains (`sentry.io`, `wixpress.com`, `example.com`...) are dropped. The emails are not verified: there is no DNS, MX or SMTP check;
- phone-number-like strings from the visible text (up to 5, not normalized);
- social links for LinkedIn, Instagram, Facebook, X/Twitter, YouTube and TikTok (up to 3 each);
- Schema.org JSON-LD `@type` values (for example `Organization`, `LocalBusiness`, `Product`);
- a tech-stack guess from regex signatures in the HTML and the `Server` / `X-Powered-By` headers: Shopify, WooCommerce, WordPress, Next.js, Nuxt.js, React, Vue.js, Webflow, HubSpot, Google Tag Manager, GA4, Meta Pixel, Stripe, Intercom, Cloudflare, Nginx, Express.

It does not use a headless browser, so content that only appears after JavaScript runs is not seen.

## Input

```json
{
  "startUrls": [
    { "url": "https://books.toscrape.com" },
    { "url": "https://quotes.toscrape.com" }
  ],
  "maxItems": 25,
  "followContactPages": true,
  "maxConcurrency": 5
}
```

Runs on the Apify free tier are capped at 25 URLs.

## Output record

```json
{
  "url": "https://books.toscrape.com",
  "company_name": "All products | Books to Scrape - Sandbox",
  "meta_description": "",
  "emails": [],
  "phones": [],
  "social_profiles": {},
  "tech_stack": ["Nginx"],
  "json_ld_types": [],
  "pages_crawled": 1,
  "status_code": 200,
  "error": null
}
```

If a request fails, the record is returned with empty fields and the exception text in `error`.

## Calling it from Python

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_APIFY_TOKEN")
run = client.actor("thanh81646/apify-b2b-lead-and-contact-enricher").call(
    run_input={"startUrls": [{"url": "https://books.toscrape.com"}]}
)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)
```

In n8n or Make.com, use the Apify "Run an Actor" node/module with the same actor ID (`thanh81646/apify-b2b-lead-and-contact-enricher`) and map the dataset items to Google Sheets, a CRM or a database.

## Running your own copy

In the Apify Console, create a new actor from a Git repository, paste `https://github.com/Tthanh2k6/apify-b2b-lead-and-contact-enricher`, then build and start it. Locally, without the `apify` package installed, `python src/main.py` runs the two sample URLs and prints the JSON.

## Author

Trung Thanh Tran: [Upwork](https://www.upwork.com/freelancers/trungthanhtrandev) · [GitHub](https://github.com/Tthanh2k6) · [Apify](https://apify.com/thanh81646)

## Legal note

The actor only reads public, non-authenticated web pages at the user's direction. It does not bypass logins or access controls. Technology and platform names are trademarks of their owners and are used only to identify them. You are responsible for making sure your target URLs, request rates and use of the data comply with applicable law (including GDPR and CCPA).
