# B2B Website Contact, Social Links, JSON-LD & Tech Stack Enricher (Apify Actor)

Fast, lightweight **Python Async (`httpx` + `BeautifulSoup4`) Apify Actor** that enriches any list of company or e-commerce URLs with verified public emails, phone numbers, social media profiles, Schema.org `JSON-LD` entities, and technology stack fingerprints.

## ✨ Key Features

- **Smart Contact Page Discovery:** Automatically detects and crawls up to 2 internal `/contact`, `/about`, or `/support` pages per domain when `followContactPages` is enabled.
- **Noise-Free Email Filtering:** Strips false-positive asset strings (`.png`, `.svg`, `.webp`) and telemetry domains (`sentry.io`, `wixpress.com`, `example.com`).
- **6-Platform Social Graph Extraction:** Captures official profiles on **LinkedIn**, **Instagram**, **Facebook**, **X (Twitter)**, **YouTube**, and **TikTok**.
- **Technology Stack Fingerprinting:** Identifies **Shopify**, **WooCommerce**, **WordPress**, **Next.js**, **Nuxt.js**, **React**, **Webflow**, **HubSpot**, **Google Tag Manager**, **GA4**, **Meta Pixel**, **Stripe**, **Intercom**, and **Cloudflare**.
- **Schema.org `JSON-LD` Entity Parsing:** Extracts structured `@type` declarations (`Organization`, `LocalBusiness`, `Product`, `WebSite`).
- **Low Compute Unit Consumption:** Built on pure async `httpx` (`< 25 MB` RAM overhead) rather than heavy headless browsers, allowing thousands of B2B domains to be enriched for fractions of a cent.

---

## 📥 Input Configuration

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

---

## 📤 Sample Output Record

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

---

## 🚀 Deploy to Apify Store in 3 Clicks (GitHub Integration)

1. Open [Apify Console → Actors → Development → Create new Actor](https://console.apify.com/actors).
2. Choose **Link Git Repository** and paste:
   `https://github.com/Tthanh2k6/apify-b2b-lead-and-contact-enricher`
3. Click **Build** → **Start** (to run the prefilled test) → **Publication** tab to publish on Apify Store!

---

## 🛠️ Integration with n8n, Make.com & Python

### Python (`apify-client`)
```python
from apify_client import ApifyClient

client = ApifyClient('YOUR_APIFY_TOKEN')
run = client.actor('thanh81646/b2b-lead-contact-and-tech-enricher').call(run_input={})
for item in client.dataset(run['defaultDatasetId']).iterate_items():
    print(item)
```

### n8n / Make.com Workflow
1. Add the official **Apify** node in **n8n** or **Make.com**.
2. Select **Run an Actor** and choose this Actor (`thanh81646/b2b-lead-contact-and-tech-enricher`).
3. Map the output Dataset items directly into **Google Sheets**, **HubSpot**, **Airtable**, **PostgreSQL / Supabase**, or **OpenAI Structured Outputs**.

---

## 💼 Need a Custom Scraper, Hidden API Extractor, or n8n / AI Workflow?

Built and maintained by **Trung Thanh Tran** (*Python, Playwright & AI Automation Developer*):
- 🚀 **Hire me on Upwork (1-Day Turnaround / Starter Packages Available):** [upwork.com/freelancers/trungthanhtrandev](https://www.upwork.com/freelancers/trungthanhtrandev)
- 💻 **GitHub Portfolio:** [github.com/Tthanh2k6](https://github.com/Tthanh2k6)
- 🌐 **3D Interactive Portfolio:** [portfolio-red-theta-65.vercel.app](https://portfolio-red-theta-65.vercel.app/)

---

## ⚖️ Legal & Independence Disclaimer

**Nominative Fair Use — Public Non-Authenticated Factual Data Only:** This Actor is an independent software utility that processes exclusively publicly accessible, non-authenticated web pages at the user's explicit direction. It does not bypass authentication barriers, login walls, or technical access controls, nor does it store or resell proprietary databases. Any platform or technology names mentioned (such as Shopify, WooCommerce, WordPress, HubSpot, LinkedIn, etc.) are trademarks of their respective owners and are referenced strictly for descriptive identification purposes (*nominative fair use*). Users act as independent Data Controllers and are solely responsible for ensuring their target URLs, rate limits, and downstream data usage comply with applicable regulations (including GDPR and CCPA).
