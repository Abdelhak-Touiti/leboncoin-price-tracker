# 🎮 leboncoin-price-tracker

> A real-time Streamlit dashboard that retrieves gaming PC listings from LeBonCoin (Île-de-France) using a real browser session, delivering live, filterable results in a custom dark gaming UI.

---

## 📌 Overview

LeBonCoin is France's largest classifieds marketplace, built as a modern Next.js application with standard bot-mitigation measures in place.

This project uses **`undetected-chromedriver`** to drive a real Chrome browser — the same way a regular user would visit the site — rather than relying on raw HTTP requests that lack proper browser context. Once the page loads, rather than parsing fragile HTML with CSS selectors, the scraper reads the **`__NEXT_DATA__` JSON blob** that Next.js embeds in every page for client-side hydration. This gives structured, reliable data that survives frontend redesigns.

The results are displayed inside a polished Streamlit app with a custom dark gaming aesthetic, live price statistics, and a card-based listing layout.

---

## ✨ Features

- 🌐 **Real browser session** — drives a visible Chrome instance via `undetected-chromedriver` for accurate, human-like page rendering
- 🧠 **Next.js `__NEXT_DATA__` extraction** — parses the embedded JSON payload instead of scraping raw HTML, making the scraper far more resilient to frontend redesigns
- 🔁 **Recursive ad-finder** — a depth-limited tree traversal algorithm that locates ad listings regardless of how deep or how differently LeBonCoin nests them in the JSON
- 🍪 **Session cookie forwarding for images** — captures live Chrome cookies and forwards them to a server-side image proxy, solving the cross-origin CDN authentication issue and embedding images as base64 directly in the UI
- 📊 **Live stats bar** — instantly computes average, min, and max prices plus pro vs. private seller breakdown on every search
- 🎨 **Custom dark gaming UI** — hand-crafted CSS injected into Streamlit with `Rajdhani` / `Inter` fonts, indigo accent colors, card hover animations, and a responsive 3-column grid
- 🗂️ **Debug artifacts** — automatically saves `debug_page.html` and `debug_nextdata.json` on each run for easy inspection and troubleshooting
- ⚡ **Streamlit caching** — `@st.cache_data` on the image proxy with `frozenset`-hashed cookies avoids redundant CDN fetches

---

## 🏗️ Architecture

```
User (Streamlit UI)
      │
      ▼
Sidebar filters (keyword, price range, sort)
      │
      ▼
fetch_listings()
  ├── _fetch_with_uc()          ← undetected-chromedriver in a Python thread
  │     ├── Launches real Chrome (non-headless)
  │     ├── Waits for __NEXT_DATA__ injection (up to 30s)
  │     └── Accepts RGPD cookie banner if present
  │
  ├── BeautifulSoup parses __NEXT_DATA__ script tag
  └── find_ads() — recursive JSON tree walker
        │
        ▼
parse_ad()   ← normalises each raw dict into a clean ad object
        │
        ▼
render_card()
  └── proxy_image()             ← server-side requests + Chrome session cookies
        └── base64-encoded image embedded in HTML card
```

---

## 🚀 Technical Highlights

### 1 — Real browser automation with `undetected-chromedriver`
Bot-mitigation systems work by fingerprinting browser signals (TLS, JavaScript environment, headless flags, timing patterns). Standard Selenium and Playwright setups are often flagged because they expose automation signals. `undetected-chromedriver` patches Chrome at the driver level to behave like a regular browser session. Combined with running a **visible window** (not `--headless`), the page renders exactly as it would for a human visitor.

### 2 — Next.js `__NEXT_DATA__` parsing instead of DOM scraping
Modern SPAs like LeBonCoin pre-serialize their full page state into a `<script id="__NEXT_DATA__">` tag for hydration. Parsing this JSON is dramatically more stable than CSS selectors — the DOM layout can change with any deploy, but the data schema changes far less often. This technique also yields richer data (all fields, not just what's rendered visibly).

### 3 — Recursive JSON tree traversal
The `find_ads()` function doesn't hardcode a path like `data["props"]["pageProps"]["searchData"]["ads"]`. Instead it recursively searches any nested dict/list structure for an object that looks like an ad (contains `list_id`, `subject`, or `price`). This makes the scraper **self-healing** — if LeBonCoin reorganises their API response, it will still find the ads.

### 4 — Server-side image proxy with live session cookies
LeBonCoin serves listing images from a CDN that requires valid session cookies. Simply rendering `<img src="...">` in the browser fails with a 403. The solution: after Chrome loads the page, the driver exports all cookies. These are stored in Streamlit's session state, then forwarded in a `requests.get()` call that fetches the image server-side, and the bytes are encoded as `data:image/...;base64,...` and embedded directly in the HTML card. No CORS issues, no broken images.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | Streamlit |
| Browser Automation | `undetected-chromedriver`, Selenium |
| HTML Parsing | BeautifulSoup 4 + lxml |
| Image Fetching | `requests` (server-side proxy) |
| Target Site | LeBonCoin — Île-de-France, category: Informatique |
| Language | Python 3.10+ |

---

## ⚙️ Installation

```bash
# 1. Clone
git clone https://github.com/Abdelhak-Touiti/leboncoin-price-tracker.git
cd leboncoin-price-tracker

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

> **Note:** A real Chrome browser window will briefly open during each search. This is intentional — the scraper renders the page as a normal user session would.

---

## 🖥️ Usage

1. Launch the app with `streamlit run app.py`
2. In the sidebar, enter a keyword (e.g. `RTX 4080`, `Alienware`, `pc gaming`)
3. Set a price range and sort order
4. Click **🔎 Rechercher**
5. Results appear as cards with image, price, location, date, and a direct link

---

## 📁 Project Structure

```
leboncoin-price-tracker/
├── app.py                  # Main Streamlit app
├── inspect_images.py       # Debug utility — inspects image fields in saved JSON
├── LICENSE                 # AGPL-3.0 license
├── LICENSE-COMMERCIAL.md   # Commercial licensing terms
├── .gitignore              # Excludes debug files and scraped data
├── debug_page.html         # Auto-saved raw HTML from last scrape (gitignored)
├── debug_nextdata.json     # Auto-saved __NEXT_DATA__ JSON from last scrape (gitignored)
└── debug_img_error.txt     # Auto-appended image proxy errors (gitignored)
```

---

## 📄 License

This project uses a **dual license** model:

- **Open-source use** — licensed under [AGPL-3.0](LICENSE). Free to use, study, and modify, provided any derivative work is also open-sourced under the same terms.
- **Commercial use** — if you intend to use this in a private or proprietary product, a commercial license is required. See [LICENSE-COMMERCIAL.md](LICENSE-COMMERCIAL.md) or contact the author.

---

## ⚠️ Disclaimer

This project is built for **educational and portfolio purposes** to demonstrate browser automation, data extraction, and data engineering skills. Always review a website's Terms of Service before scraping at scale. LeBonCoin's CGU apply.

---

## 👤 Author

Built by **Dr Abdelhak Touiti**
Data Engineering — Portfolio Project
[LinkedIn](https://www.linkedin.com/in/abdelhak-touiti/) · [GitHub](https://github.com/Abdelhak-Touiti)
