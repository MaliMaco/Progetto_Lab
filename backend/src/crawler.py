from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# ── Tandfonline ──────────────────────────────────────────────────────────────
# Esclusi: bibliografie, appendici, figure, tabelle, equazioni, link "Open in
# new window", metriche, keywords.  Target: solo heading e paragrafi.
TANDFONLINE_EXCLUDED = """
    [id^='references'], [id^='appendix'], [id^='appendixes'],
    .references, .bibliography,
    #infos-holder, .summation-section,
    [class*='article-note'], [class*='article-metrics'], [class*='metrics'],
    figure, .figure, [class*='figure'],
    table, .table, [class*='table-wrap'],
    .disp-formula, [class*='formula'], [class*='equation'],
    [class*='open-in-window'], [class*='openInFullSize'],
    nav, header, footer,
    [class*='keyword'],
    .cookie-banner, #cookie-notice, [class*='cookie']
"""


def _md_generator():
    return DefaultMarkdownGenerator(
        options={"escape_html": False, "body_width": 0}
    )


'''

'''

async def parser_run(url: str):
    domain = url.split("/")[2]
    md_gen = _md_generator()

    # ── Wikipedia ────────────────────────────────────────────────────────────
    if domain == "en.wikipedia.org":
        browser_cfg = BrowserConfig(headless=True)
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p"],
            markdown_generator=md_gen,
            excluded_selector="""
                .infobox, .infobox-full-data, .sidebar, .navbox,
                .wikitable, table, .mw-editsection,
                [class*='you-may'], [class*='related'],
                .cookie-banner, #cookie-notice, [class*='cookie']
            """,
        )

    # ── ECB ──────────────────────────────────────────────────────────────────
    elif domain == "ecb.europa.eu":
        browser_cfg = BrowserConfig(headless=True)
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p"],
            markdown_generator=md_gen,
            excluded_selector="""
                table, [class*='you-may'], [class*='related'],
                .in-this-section, footer,
                nav, .navigation, .menu,
                .cookie-banner, #cookie-notice, [class*='cookie']
            """,
        )

    # ── Tandfonline ──────────────────────────────────────────────────────────
    elif domain == "www.tandfonline.com":
        browser_cfg = BrowserConfig(
            headless=True,
            viewport_width=1280,
            viewport_height=720,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "h4", "p"],
            markdown_generator=md_gen,
            excluded_selector=TANDFONLINE_EXCLUDED,
            wait_until="networkidle",
        )

    # ── Apple App Store ──────────────────────────────────────────────────────
    #Non inserito in domains.json, impraticabile.
    elif domain == "apps.apple.com":
        browser_cfg = BrowserConfig(headless=True)
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p"],
            markdown_generator=md_gen,
            cache_mode=CacheMode.BYPASS,
        )

    # ── Default ──────────────────────────────────────────────────────────────
    else:
        browser_cfg = BrowserConfig(headless=True)
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p"],
            markdown_generator=md_gen,
            excluded_selector="""
                .cookie-banner, #cookie-notice, [class*='cookie'],
                nav, footer, table
            """,
        )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=run_cfg)

    return result


async def html_parser_run(html: str, domain: str):
    """
    Parsing su HTML statico (raw:).
    Per Apple, l'HTML statico non contiene il contenuto renderizzato via JS
    (reviews, Editors' Choice), quindi il risultato sarà necessariamente
    inferiore al gold costruito con browser reale.
    """
    md_gen = _md_generator()
    browser_cfg = BrowserConfig(headless=True)

    # ── Wikipedia ────────────────────────────────────────────────────────────
    if domain == "en.wikipedia.org":
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p"],
            markdown_generator=md_gen,
            excluded_selector="""
                .infobox, .infobox-full-data, .sidebar, .navbox,
                .wikitable, table, .mw-editsection,
                [class*='you-may'], [class*='related'],
                .cookie-banner, #cookie-notice, [class*='cookie']
            """,
        )

    # ── ECB ──────────────────────────────────────────────────────────────────
    elif domain == "ecb.europa.eu":
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p"],
            markdown_generator=md_gen,
            excluded_selector="""
                table, [class*='you-may'], [class*='related'],
                .in-this-section, footer,
                nav, .navigation, .menu,
                .cookie-banner, #cookie-notice, [class*='cookie']
            """,
        )

    # ── Tandfonline ──────────────────────────────────────────────────────────
    elif domain == "www.tandfonline.com":
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "h4", "p"],
            markdown_generator=md_gen,
            excluded_selector=TANDFONLINE_EXCLUDED,
        )

    # ── Apple App Store ──────────────────────────────────────────────────────
    # L'HTML statico di Apple non include reviews (caricate via JS).
    # Usiamo section.shelf come unità di parsing escludendo le sezioni
    # note per essere rumore puro (More by, You Might Also Like, Events,
    # Ratings & Reviews header + shelf reviews adiacente).
    elif domain == "apps.apple.com":
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p"],
            markdown_generator=md_gen,
            excluded_selector="""
                nav, footer, button, script, style,
                .shelf-grid, .inforibbon-shelf-wrapper,
                .horizontal-shelf, .header-container
            """,
        )

    # ── Default ──────────────────────────────────────────────────────────────
    else:
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p"],
            markdown_generator=md_gen,
            excluded_selector="""
                .cookie-banner, #cookie-notice, [class*='cookie'],
                nav, footer, table
            """,
        )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=f"raw:{html}", config=run_cfg)

    return result