"""
LeBonCoin — Gaming PC Scraper (Île-de-France)
Run with:  streamlit run leboncoin_gaming.py
Requires:
  pip install streamlit beautifulsoup4 lxml playwright playwright-stealth
  playwright install chromium
"""

import streamlit as st
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urlencode
import threading
import base64
import requests as _requests  # only for image proxying
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="LBC Gaming PCs — Île-de-France",
    page_icon="🎮",
    layout="wide",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS  (dark gaming aesthetic)
# ─────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d0f14;
    color: #e2e8f0;
  }

  h1, h2, h3 { font-family: 'Rajdhani', sans-serif !important; }

  /* hide default streamlit chrome */
  #MainMenu, footer, header { visibility: hidden; }

  /* top banner */
  .banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 60%, #0f172a 100%);
    border-bottom: 2px solid #6366f1;
    padding: 1.4rem 2rem 1rem;
    margin-bottom: 1.6rem;
    border-radius: 0 0 12px 12px;
  }
  .banner h1 {
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: 2px;
    color: #e0e7ff;
    margin: 0 0 .2rem;
  }
  .banner p { color: #94a3b8; font-size: .9rem; margin: 0; }

  /* result cards */
  .card {
    background: #141720;
    border: 1px solid #1e2433;
    border-radius: 12px;
    overflow: hidden;
    transition: transform .2s, border-color .2s;
    height: 100%;
  }
  .card:hover { transform: translateY(-4px); border-color: #6366f1; }
  .card img {
    width: 100%;
    height: 180px;
    object-fit: cover;
    background: #1a1f2e;
  }
  .card-body { padding: 12px 14px 14px; }
  .card-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: #e0e7ff;
    margin-bottom: 6px;
    line-height: 1.3;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .card-price {
    font-size: 1.25rem;
    font-weight: 700;
    color: #818cf8;
    font-family: 'Rajdhani', sans-serif;
    letter-spacing: 1px;
  }
  .card-meta { font-size: .78rem; color: #64748b; margin-top: 6px; }
  .card-meta span { margin-right: 10px; }
  .card-link {
    display: inline-block;
    margin-top: 10px;
    padding: 5px 14px;
    background: #1e1b4b;
    color: #a5b4fc;
    border-radius: 6px;
    font-size: .8rem;
    text-decoration: none;
    border: 1px solid #312e81;
    transition: background .15s;
  }
  .card-link:hover { background: #312e81; color: #e0e7ff; }

  /* tag badges */
  .tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 99px;
    font-size: .7rem;
    font-weight: 500;
    margin-right: 4px;
    margin-bottom: 4px;
  }
  .tag-pro  { background: #1e3a5f; color: #7dd3fc; }
  .tag-part { background: #14532d; color: #86efac; }

  /* stats bar */
  .stat-bar {
    background: #141720;
    border: 1px solid #1e2433;
    border-radius: 10px;
    padding: 14px 20px;
    margin-bottom: 1.4rem;
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
  }
  .stat { text-align: center; }
  .stat-val {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #818cf8;
  }
  .stat-label { font-size: .75rem; color: #64748b; }

  /* sidebar */
  section[data-testid="stSidebar"] {
    background: #0d0f14;
    border-right: 1px solid #1e2433;
  }
  section[data-testid="stSidebar"] label { color: #94a3b8 !important; }

  /* buttons */
  .stButton > button {
    background: linear-gradient(135deg, #4f46e5, #6366f1);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Rajdhani', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 1px;
    padding: .5rem 1.4rem;
    width: 100%;
  }
  .stButton > button:hover { opacity: .9; }

  /* spinner */
  .stSpinner > div { border-top-color: #6366f1 !important; }

  /* no results */
  .empty {
    text-align: center;
    padding: 4rem 2rem;
    color: #475569;
    font-size: 1rem;
  }
  .empty span { font-size: 3rem; display: block; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
BASE_SEARCH_URL = "https://www.leboncoin.fr/recherche"

PLACEHOLDER_IMG = (
    "https://placehold.co/400x180/141720/6366f1?text=No+Image&font=raleway"
)

SORT_OPTIONS = {
    "Plus récent d'abord": "time",
    "Prix croissant":      "price_asc",
    "Prix décroissant":    "price_desc",
}

# ─────────────────────────────────────────────
#  PLAYWRIGHT SCRAPING — real browser, bypasses Cloudflare
# ─────────────────────────────────────────────
def _fetch_with_uc(url: str) -> str:
    """
    Uses undetected-chromedriver to open a real Chrome that bypasses
    DataDome CAPTCHA. Runs in a plain thread — no asyncio needed.
    """
    result = {}

    def target():
        options = uc.ChromeOptions()
        # NO headless — DataDome reliably blocks headless Chrome.
        # A visible Chrome window will open briefly while scraping.
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=fr-FR")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = uc.Chrome(options=options, use_subprocess=True)
        try:
            driver.get(url)

            # Wait up to 30s for Next.js data to appear
            # (gives time for any JS challenge to resolve)
            import time
            deadline = time.time() + 30
            html = ""
            while time.time() < deadline:
                html = driver.page_source
                if "__NEXT_DATA__" in html:
                    break
                time.sleep(1)

            # Accept cookie banner if present
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "button[data-qa-id='rgpd-accept']")
                btn.click()
                time.sleep(0.5)
                html = driver.page_source
            except Exception:
                pass

            if "__NEXT_DATA__" not in html:
                # Save what we got for debugging
                import os
                dbg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_page.html")
                with open(dbg, "w", encoding="utf-8") as f:
                    f.write(html)
                raise RuntimeError(
                    "DataDome CAPTCHA toujours actif après 30s.\n"
                    "debug_page.html sauvegardé — vérifiez si une fenêtre Chrome "
                    "s'est bien ouverte pendant la recherche."
                )

            result["html"]    = html
            result["cookies"] = {
                c["name"]: c["value"]
                for c in driver.get_cookies()
            }
        finally:
            driver.quit()

    t = threading.Thread(target=target)
    t.start()
    t.join(timeout=40)

    if "html" not in result:
        raise RuntimeError(
            "Le navigateur n'a pas pu charger la page dans les temps impartis. "
            "Vérifiez votre connexion ou réessayez."
        )
    return result["html"], result.get("cookies", {})


def fetch_listings(keyword: str, price_min: int, price_max: int,
                   sort: str) -> list[dict]:
    """
    Launches undetected Chrome (in a thread) to bypass DataDome,
    then extracts the Next.js __NEXT_DATA__ JSON from the page.
    """
    params = {
        "text":     keyword,
        "category": "15",   # Informatique
        "regions":  "12",   # Île-de-France
        "sort":     sort,
    }
    if price_min > 0:
        params["price"] = f"{price_min}-{price_max if price_max < 9999 else 'max'}"
    elif price_max < 9999:
        params["price"] = f"0-{price_max}"

    url        = f"{BASE_SEARCH_URL}?{urlencode(params)}"
    html, cookies = _fetch_with_uc(url)
    # Store CDN cookies globally so proxy_image can use them
    import streamlit as _st
    _st.session_state["lbc_cookies"] = cookies

    soup       = BeautifulSoup(html, "lxml")

    # Save raw HTML for debugging
    import os
    debug_html = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_page.html")
    with open(debug_html, "w", encoding="utf-8") as hf:
        hf.write(html)

    # 1. Try the standard Next.js embed
    script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

    # 2. Fallback: find the largest <script> block containing "list_id"
    if not script_tag:
        for s in soup.find_all("script"):
            if s.string and "list_id" in s.string and len(s.string) > 1000:
                script_tag = s
                break

    if not script_tag:
        raise ValueError(
            "Impossible de trouver les données dans la page.\n"
            f"Le fichier debug_page.html a été sauvegardé dans {debug_html} — "
            "ouvrez-le dans un navigateur pour voir ce que LeBonCoin a retourné."
        )

    data    = json.loads(script_tag.string)

    # ── Debug: save the raw JSON so you can inspect the real structure ──
    import os
    debug_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_nextdata.json")
    with open(debug_path, "w", encoding="utf-8") as dbf:
        json.dump(data, dbf, ensure_ascii=False, indent=2)

    # Also save just the first ad for quick image-field inspection
    debug_ad_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_first_ad.json")

    # Walk every key in props looking for the ads list
    props = data.get("props", {}).get("pageProps", {})

    def find_ads(obj, depth=0):
        """Recursively search for the first list that looks like LBC ads."""
        if depth > 6:
            return None
        if isinstance(obj, list) and len(obj) > 0:
            first = obj[0]
            if isinstance(first, dict) and any(k in first for k in ("list_id", "subject", "price")):
                return obj
        if isinstance(obj, dict):
            for v in obj.values():
                found = find_ads(v, depth + 1)
                if found is not None:
                    return found
        return None

    ads_raw = find_ads(props) or find_ads(data) or []
    return ads_raw


# ─────────────────────────────────────────────
#  PARSE A SINGLE AD
# ─────────────────────────────────────────────
def parse_ad(ad: dict) -> dict:
    # Images — structure confirmed: thumb_url (str), urls_large (list)
    images    = ad.get("images", {})
    image_url = (
        images.get("thumb_url")                          # direct string ✅
        or (images.get("urls_large") or [None])[0]       # list → first item
        or (images.get("urls_thumb") or [None])[0]
        or (images.get("urls")       or [None])[0]
        or images.get("small_url")
        or None
    )

    # Price
    price_raw = ad.get("price", [])
    price     = price_raw[0] if isinstance(price_raw, list) and price_raw else (
                price_raw if isinstance(price_raw, (int, float)) else None)

    # Location
    loc        = ad.get("location", {})
    city       = loc.get("city", "")
    department = loc.get("department_id", "")

    # Date
    raw_date = ad.get("first_publication_date", "")
    try:
        dt       = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        date_str = dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        date_str = raw_date[:10] if raw_date else "–"

    # Owner type
    owner  = ad.get("owner", {})
    is_pro = owner.get("type", "").lower() == "pro"

    list_id = ad.get("list_id", "")
    return {
        "title":    ad.get("subject", "Sans titre"),
        "price":    price,
        "image":    image_url,
        "city":     city,
        "dept":     department,
        "date":     date_str,
        "url":      f"https://www.leboncoin.fr/ad/informatique/{list_id}",
        "is_pro":   is_pro,
    }



# ─────────────────────────────────────────────
#  IMAGE PROXY — fetch & embed as base64
# ─────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def proxy_image(url: str, _cookies: frozenset) -> str:
    """
    Fetches an image server-side using the live Chrome session cookies.
    Cookies passed as frozenset so st.cache_data can hash them.
    """
    if not url:
        return PLACEHOLDER_IMG
    try:
        cookies_dict = dict(_cookies)
        resp = _requests.get(
            url,
            headers={
                "Referer":         "https://www.leboncoin.fr/",
                "Origin":          "https://www.leboncoin.fr",
                "User-Agent":      (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept":          "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9",
                "Sec-Fetch-Dest":  "image",
                "Sec-Fetch-Mode":  "no-cors",
                "Sec-Fetch-Site":  "cross-site",
            },
            cookies=cookies_dict,
            timeout=10,
        )
        resp.raise_for_status()
        mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
        b64  = base64.b64encode(resp.content).decode()
        return f"data:{mime};base64,{b64}"
    except Exception as _e:
        import os as _os
        _log = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "debug_img_error.txt")
        with open(_log, "a") as _f:
            _f.write(f"URL: {url}\nError: {_e}\nCookies: {len(cookies_dict)} keys\n\n")
        return PLACEHOLDER_IMG


# ─────────────────────────────────────────────
#  RENDER A CARD  (via st.markdown)
# ─────────────────────────────────────────────
def render_card(ad: dict):
    price_str = f"{ad['price']:,} €".replace(",", " ") if ad["price"] else "Prix non précisé"
    raw_cookies = st.session_state.get("lbc_cookies", {})
    cookie_set  = frozenset(raw_cookies.items())
    img_url     = proxy_image(ad["image"], cookie_set) if ad["image"] else PLACEHOLDER_IMG
    tag_html  = (
        '<span class="tag tag-pro">Pro</span>'  if ad["is_pro"]  else
        '<span class="tag tag-part">Particulier</span>'
    )
    st.markdown(f"""
    <div class="card">
      <img src="{img_url}" alt="{ad['title']}" loading="lazy"
           onerror="this.src='{PLACEHOLDER_IMG}'">
      <div class="card-body">
        {tag_html}
        <div class="card-title">{ad['title']}</div>
        <div class="card-price">{price_str}</div>
        <div class="card-meta">
          <span>📍 {ad['city']} ({ad['dept']})</span>
          <span>🕐 {ad['date']}</span>
        </div>
        <a class="card-link" href="{ad['url']}" target="_blank">
          Voir l'annonce →
        </a>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SIDEBAR — FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎮 Filtres")
    st.markdown("---")

    keyword = st.text_input(
        "🔍 Mot-clé",
        value="pc gaming",
        placeholder="ex: rtx 4080, i9, alienware…",
    )

    st.markdown("**💶 Budget (€)**")
    col_min, col_max = st.columns(2)
    with col_min:
        price_min = st.number_input("Min", min_value=0, max_value=9999, value=0, step=50)
    with col_max:
        price_max = st.number_input("Max", min_value=0, max_value=9999, value=9999, step=50)

    sort_label = st.selectbox("📊 Tri", list(SORT_OPTIONS.keys()))

    st.markdown("---")
    search_btn = st.button("🔎 Rechercher")

    st.markdown("""
    <div style="margin-top:2rem;padding:10px 14px;background:#141720;
                border:1px solid #1e2433;border-radius:8px;font-size:.75rem;color:#475569">
      ⚠️ Ce scraper lit les pages HTML publiques de LeBonCoin.<br>
      Consultez leurs CGU avant usage intensif.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  BANNER
# ─────────────────────────────────────────────
st.markdown("""
<div class="banner">
  <h1>🎮 LeBonCoin Gaming PCs</h1>
  <p>Annonces d'ordinateurs gaming en Île-de-France — données en temps réel</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SEARCH & RESULTS
# ─────────────────────────────────────────────
if search_btn or "ads" not in st.session_state:
    with st.spinner("Récupération des annonces…"):
        try:
            sort_value = SORT_OPTIONS[sort_label]
            raw_ads = fetch_listings(
                keyword=keyword,
                price_min=price_min,
                price_max=price_max,
                sort=sort_value,
            )
            st.session_state["ads"]     = [parse_ad(a) for a in raw_ads]
            st.session_state["total"]   = len(raw_ads)
            st.session_state["keyword"] = keyword
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            st.session_state["ads"] = []

ads   = st.session_state.get("ads", [])
total = st.session_state.get("total", 0)

# ── Stats bar ────────────────────────────────
if ads:
    prices_known = [a["price"] for a in ads if a["price"]]
    avg_price    = int(sum(prices_known) / len(prices_known)) if prices_known else 0
    min_price    = min(prices_known) if prices_known else 0
    max_price    = max(prices_known) if prices_known else 0
    pros         = sum(1 for a in ads if a["is_pro"])

    st.markdown(f"""
    <div class="stat-bar">
      <div class="stat"><div class="stat-val">{len(ads)}</div><div class="stat-label">Annonces affichées</div></div>
      <div class="stat"><div class="stat-val">{total:,}</div><div class="stat-label">Total sur LBC</div></div>
      <div class="stat"><div class="stat-val">{avg_price:,} €</div><div class="stat-label">Prix moyen</div></div>
      <div class="stat"><div class="stat-val">{min_price:,} €</div><div class="stat-label">Prix min</div></div>
      <div class="stat"><div class="stat-val">{max_price:,} €</div><div class="stat-label">Prix max</div></div>
      <div class="stat"><div class="stat-val">{pros}</div><div class="stat-label">Vendeurs pro</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Grid ──────────────────────────────────
    cols_per_row = 3
    rows = [ads[i:i+cols_per_row] for i in range(0, len(ads), cols_per_row)]
    for row in rows:
        cols = st.columns(cols_per_row)
        for col, ad in zip(cols, row):
            with col:
                render_card(ad)

elif "ads" in st.session_state:
    st.markdown("""
    <div class="empty">
      <span>🔍</span>
      Aucune annonce trouvée pour ces critères.<br>
      Essayez d'élargir votre recherche ou d'augmenter le budget maximum.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="empty">
      <span>🎮</span>
      Utilisez les filtres à gauche et cliquez sur <strong>Rechercher</strong>.
    </div>
    """, unsafe_allow_html=True)
