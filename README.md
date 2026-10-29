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
3. Click **Build** $\rightarrow$ **Start** (to run the prefilled test) $\rightarrow$ **Publication** tab to publish on Apify Store!
