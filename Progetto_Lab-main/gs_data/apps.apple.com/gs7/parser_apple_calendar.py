
import asyncio
import re
import os
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

# URL dell'app (modifica a piacere)
URL = "https://apps.apple.com/us/app/google-calendar-get-organized/id909319292"

def clean_text(el):
    """Rimuove spazi eccessivi dal testo di un elemento BeautifulSoup."""
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)) if el else ""

def find_section_by_heading(soup, heading_text):
    """Cerca una sezione partendo da un heading (h1/h2/h3) che contiene heading_text."""
    h = soup.find(lambda tag: tag.name in ["h1", "h2", "h3"] and heading_text.lower() in clean_text(tag).lower())
    if not h:
        return None
    sec = h.find_parent(lambda t: t.name in ["section", "div"] and t.get("data-test-id") in ["shelf-wrapper", "shelf"])
    return sec or h.parent

async def main():
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )
    
    run_config = CrawlerRunConfig(
        wait_until="networkidle",
        bypass_cache=False
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=URL, config=run_config)
        soup = BeautifulSoup(result.html, "lxml")

    # ---- Estrai i dati ----
    # Header: titolo, sottotitolo, prezzo
    header_sec = soup.find("section", {"data-test-id": "shelf-wrapper"})
    title = clean_text(header_sec.find("h1")) if header_sec else ""
    subtitle = ""
    price_label = ""
    if header_sec:
        st = header_sec.find("p", class_=re.compile("subtitle"))
        subtitle = clean_text(st) if st else ""
        at = header_sec.find("p", class_=re.compile("attributes"))
        price_label = clean_text(at) if at else ""

    # Valutazioni
    rating_section = soup.find("section", {"id": "productRatings"})
    rating_value = None
    rating_count = None
    if rating_section:
        avg = rating_section.find(attrs={"data-testid": "amp-rating__average-rating"})
        if avg and re.match(r"^\d+(\.\d+)?$", clean_text(avg)):
            rating_value = float(clean_text(avg))
        cnt = rating_section.find(attrs={"data-testid": "amp-rating__rating-count-text"})
        if cnt:
            txt = clean_text(cnt)
            m = re.search(r"([\d\.]+)\s*([KMB])?", txt, re.I)
            if m:
                num = float(m.group(1))
                suffix = m.group(2)
                if suffix:
                    mult = {"K": 1000, "M": 1000000, "B": 1000000000}.get(suffix.upper(), 1)
                    rating_count = int(num * mult)
                else:
                    rating_count = int(num)

    # Novità (What's New)
    whats_new_sec = find_section_by_heading(soup, "What’s New")
    whats_new = {}
    if whats_new_sec:
        note = whats_new_sec.find("p")
        meta = whats_new_sec.find("div", class_=re.compile("metadata"))
        version = None
        date = None
        if meta:
            v = meta.find("span")
            if v:
                mv = re.search(r"Version\s+([^\s]+)", clean_text(v))
                version = mv.group(1) if mv else clean_text(v)
            t = meta.find("time")
            date = t.get("datetime") if t and t.has_attr("datetime") else clean_text(t) if t else None
        whats_new = {
            "version": version,
            "date": date,
            "notes": clean_text(note) if note else ""
        }

    # Descrizione lunga
    long_desc = ""
    desc_section = soup.find("section", class_=re.compile("centered"))
    if desc_section:
        p = desc_section.find("p")
        if p:
            long_desc = clean_text(p)

    # Informazioni (tabella)
    info_section = soup.find("section", {"id": "information"})
    info = {
        "seller": None, "size": None, "category": None, "compatibility": None,
        "languages": [], "age_rating": None, "in_app_purchases": [], "copyright": None
    }
    def dd_after_dt(label):
        if not info_section:
            return None
        dt = info_section.find("dt", string=re.compile(label, re.I))
        if not dt:
            return None
        return dt.find_next_sibling("dd")

    seller_dd = dd_after_dt("Seller")
    if seller_dd:
        info["seller"] = clean_text(seller_dd)
    size_dd = dd_after_dt("Size")
    if size_dd:
        info["size"] = clean_text(size_dd)
    cat_dd = dd_after_dt("Category")
    if cat_dd:
        info["category"] = clean_text(cat_dd)
    compat_dd = dd_after_dt("Compatibility")
    if compat_dd:
        info["compatibility"] = clean_text(compat_dd)
    lang_dd = dd_after_dt("Languages")
    if lang_dd:
        ul = lang_dd.find("ul")
        if ul:
            langs = [clean_text(li) for li in ul.find_all("li")]
            final = []
            for item in langs:
                if "," in item and len(item) > 200:
                    final.extend([s.strip() for s in item.split(",") if s.strip()])
                else:
                    final.append(item)
            info["languages"] = final
    age_dd = dd_after_dt("Age Rating")
    if age_dd:
        info["age_rating"] = clean_text(age_dd)
    iap_dd = dd_after_dt("In-App Purchases")
    if iap_dd:
        for pair in iap_dd.select(".text-pair"):
            spans = pair.find_all("span")
            if len(spans) >= 2:
                info["in_app_purchases"].append({"name": clean_text(spans[0]), "price": clean_text(spans[1])})
    cr_dd = dd_after_dt("Copyright")
    if cr_dd:
        info["copyright"] = clean_text(cr_dd)

    # Privacy
    privacy_sec = find_section_by_heading(soup, "App Privacy")
    privacy_text = ""
    if privacy_sec:
        first_p = privacy_sec.find("p")
        if first_p:
            privacy_text = clean_text(first_p)

    # Link utili
    dev_site = None
    priv_link = None
    for a in soup.select('a[href]'):
        label = clean_text(a).lower()
        href = a["href"]
        if "developer website" in label:
            dev_site = href
        elif "privacy policy" in label:
            priv_link = href

    # ---- ESTRAZIONE RECENSIONI ----
    reviews = []
    reviews_section = soup.find("section", {"id": "allProductReviews"})
    if reviews_section:
        # Cerca tutti i container delle recensioni
        review_containers = reviews_section.select(".shelf-grid__list-item")
        for container in review_containers[:4]:  # Prime 4 recensioni
            # Titolo
            title_el = container.find("h3", class_=re.compile("title"))
            review_title = clean_text(title_el) if title_el else ""
            
            # Rating (stelle)
            stars_container = container.find("ol", class_=re.compile("stars"))
            rating = None
            if stars_container:
                aria_label = stars_container.get("aria-label", "")
                star_match = re.search(r"(\d+(?:\.\d+)?)\s*Stars?", aria_label)
                if star_match:
                    rating = float(star_match.group(1))
            
            # Autore
            author_el = container.find("p", class_=re.compile("author"))
            author = clean_text(author_el) if author_el else ""
            
            # Data
            date_el = container.find("time", class_=re.compile("date"))
            review_date = date_el.get("datetime", "") if date_el else ""
            
            # Testo della recensione
            # Il testo può essere in un <p> dentro .truncate-wrapper o direttamente
            text_el = container.find("p", attrs={"data-testid": "truncate-text"})
            if not text_el:
                text_el = container.find("div", class_=re.compile("content")).find("p") if container.find("div", class_=re.compile("content")) else None
            review_text = clean_text(text_el) if text_el else ""
            
            if review_title or review_text:
                reviews.append({
                    "title": review_title,
                    "rating": rating,
                    "author": author,
                    "date": review_date,
                    "text": review_text
                })

    # ---- Genera HTML pulito con recensioni ----
    def format_stars(rating):
        if rating is None:
            return "☆☆☆☆☆"
        full = int(rating)
        half = 1 if (rating - full) >= 0.5 else 0
        empty = 5 - full - half
        return "★" * full + "½" * half + "☆" * empty

    def format_rating_count(cnt):
        if cnt is None:
            return "No ratings"
        if cnt >= 1_000_000_000:
            return f"{cnt/1_000_000_000:.1f}B"
        if cnt >= 1_000_000:
            return f"{cnt/1_000_000:.1f}M"
        if cnt >= 1_000:
            return f"{cnt/1_000:.1f}K"
        return str(cnt)

    # Costruisci la sezione recensioni HTML
    reviews_html = ""
    if reviews:
        reviews_html = '<h2>User Reviews</h2>'
        for rev in reviews:
            reviews_html += f'''
            <div class="review">
                <div class="review-header">
                    <strong>{rev.get("author", "Anonymous")}</strong>
                    <span class="review-stars">{format_stars(rev.get("rating"))}</span>
                    <span class="review-date">{rev.get("date", "")[:10]}</span>
                </div>
                <div class="review-title">{rev.get("title", "")}</div>
                <div class="review-text">{rev.get("text", "")}</div>
            </div>
            <hr class="review-sep">
            '''
    else:
        reviews_html = '<p>No user reviews extracted.</p>'

    # Aggiungi stili per le recensioni
    extra_styles = '''
        .review {
            margin-bottom: 1.5rem;
            padding: 1rem;
            background: #fafafc;
            border-radius: 12px;
        }
        .review-header {
            display: flex;
            gap: 1rem;
            align-items: center;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }
        .review-stars {
            color: #ffb800;
            font-size: 0.9rem;
        }
        .review-date {
            color: #8e8e93;
            font-size: 0.8rem;
        }
        .review-title {
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .review-text {
            color: #3a3a3c;
            line-height: 1.4;
            font-size: 0.95rem;
        }
        .review-sep {
            margin: 1rem 0;
        }
    '''

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} – App Store Details</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            max-width: 1000px;
            margin: 2rem auto;
            padding: 1rem;
            background: #f5f5f7;
            color: #1c1c1e;
            line-height: 1.5;
        }}
        .card {{
            background: white;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 0.25rem;
        }}
        .subtitle {{
            color: #6c6c70;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }}
        .price {{
            background: #e5e5ea;
            display: inline-block;
            padding: 0.2rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-bottom: 1rem;
        }}
        .rating {{
            margin: 1rem 0;
            font-size: 1.2rem;
        }}
        .stars {{
            color: #ffb800;
            font-size: 1.4rem;
            letter-spacing: 2px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 1rem;
            background: #f9f9fc;
            padding: 1.2rem;
            border-radius: 16px;
            margin: 1.5rem 0;
        }}
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        .info-label {{
            font-size: 0.7rem;
            text-transform: uppercase;
            font-weight: 600;
            color: #8e8e93;
        }}
        .info-value {{
            font-size: 0.9rem;
            font-weight: 500;
        }}
        h2 {{
            font-size: 1.6rem;
            border-left: 4px solid #007aff;
            padding-left: 0.75rem;
            margin: 1.5rem 0 1rem 0;
        }}
        .whatsnew-meta {{
            color: #8e8e93;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }}
        .description {{
            white-space: pre-wrap;
            background: #fafafc;
            padding: 1rem;
            border-radius: 12px;
        }}
        hr {{
            margin: 1.5rem 0;
            border: none;
            border-top: 1px solid #e5e5ea;
        }}
        a {{
            color: #007aff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul.iap-list {{
            margin: 0;
            padding-left: 1.2rem;
        }}
        {extra_styles}
    </style>
</head>
<body>
<div class="card">
    <h1>{title}</h1>
    {f'<div class="subtitle">{subtitle}</div>' if subtitle else ''}
    {f'<div class="price">{price_label}</div>' if price_label else ''}

    <div class="rating">
        <span class="stars">{format_stars(rating_value)}</span>
        <span> {rating_value or '?'} </span>
        <span style="color: #6c6c70;">({format_rating_count(rating_count)} ratings)</span>
    </div>

    <div class="info-grid">
        <div class="info-item"><span class="info-label">DEVELOPER</span><span class="info-value">{info['seller'] or '—'}</span></div>
        <div class="info-item"><span class="info-label">CATEGORY</span><span class="info-value">{info['category'] or '—'}</span></div>
        <div class="info-item"><span class="info-label">SIZE</span><span class="info-value">{info['size'] or '—'}</span></div>
        <div class="info-item"><span class="info-label">COMPATIBILITY</span><span class="info-value">{info['compatibility'] or '—'}</span></div>
        <div class="info-item"><span class="info-label">LANGUAGES</span><span class="info-value">{', '.join(info['languages'][:3]) + (' + more' if len(info['languages'])>3 else '') if info['languages'] else '—'}</span></div>
        <div class="info-item"><span class="info-label">AGE RATING</span><span class="info-value">{info['age_rating'] or '—'}</span></div>
        {f'''
        <div class="info-item">
            <span class="info-label">IN-APP PURCHASES</span>
            <ul class="iap-list">
                {''.join(f'<li>{iap["name"]} – {iap["price"]}</li>' for iap in info['in_app_purchases'][:5])}
                {f'<li>+{len(info["in_app_purchases"])-5} more</li>' if len(info['in_app_purchases']) > 5 else ''}
            </ul>
        </div>
        ''' if info['in_app_purchases'] else ''}
        <div class="info-item"><span class="info-label">COPYRIGHT</span><span class="info-value">{info['copyright'] or '—'}</span></div>
    </div>

    <h2>Description</h2>
    <div class="description">{long_desc.replace(chr(10), '<br>') if long_desc else 'No description available.'}</div>

    <h2>What's New</h2>
    <div class="whatsnew-meta">Version {whats_new.get('version', '—')} – {whats_new.get('date', '')}</div>
    <div>{whats_new.get('notes', 'No release notes.')}</div>

    {reviews_html}

    <h2>App Privacy</h2>
    <div>{privacy_text if privacy_text else 'No privacy summary extracted.'}</div>

    <hr>
    <div>
        {f'<p><strong>Developer Website:</strong> <a href="{dev_site}" target="_blank">{dev_site}</a></p>' if dev_site else ''}
        {f'<p><strong>Privacy Policy:</strong> <a href="{priv_link}" target="_blank">{priv_link}</a></p>' if priv_link else ''}
    </div>
</div>
</body>
</html>"""

    output_file = "html_apple_calendar.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"✅ HTML pulito con recensioni generato: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())