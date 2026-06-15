import sys
from pathlib import Path

# Aggiungi la cartella corrente al path
sys.path.insert(0, str(Path(__file__).parent))

from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator  # <--- MANCAVA!
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.models import StringCompatibleMarkdown
from types import SimpleNamespace
from bs4 import BeautifulSoup
import json as _json

'''
Esclusi: bibliografie, appendici, figure, tabelle, equazioni, link "Open in
 new window", metriche, keywords.  Target: solo heading e paragrafi.
 '''

TANDFONLINE_EXCLUDED = '''
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
'''


def _md_generator():
    return DefaultMarkdownGenerator(
        options={"escape_html": False, "body_width": 0}
    )


'''
_scrap_html_no_browser esegue scraping + generazione markdown su HTML grezzo
senza avviare un browser Playwright/Chromium. Utile per html_parser_run, permettendoci 
di risparmiare memoria.
'''


def _scrap_html_no_browser(html: str, run_cfg: CrawlerRunConfig):
    strategy = LXMLWebScrapingStrategy()
    scrape_result = strategy.scrap(
        url="raw:",
        html=html,
        target_elements=run_cfg.target_elements,
        excluded_selector=run_cfg.excluded_selector,
    )

    md_gen = run_cfg.markdown_generator or _md_generator()
    markdown_result = md_gen.generate_markdown(input_html=scrape_result.cleaned_html)

    res = SimpleNamespace()
    res.html = html
    res.cleaned_html = scrape_result.cleaned_html
    res.markdown = StringCompatibleMarkdown(markdown_result)
    res.status_code = 200
    return res


'''
Il metodo parser_run esegue il crawler di crawl4ai sull'url dato in input. 
In base al dominio di appartenenza dell'url verrà utilizzata una CrawlerRunConfig apposita.
'''

async def parser_run(url: str, crawler: AsyncWebCrawler = None):

    domain = url.split("/")[2]
    md_gen = _md_generator()

    if domain == "en.wikipedia.org":
        browser_cfg = BrowserConfig(headless=True)
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p", "ul"],
            markdown_generator=md_gen,
            excluded_selector="""
                .infobox, .infobox-full-data, .sidebar, .navbox,
                .wikitable, table, .mw-editsection,
                [class*='you-may'], [class*='related'],
                .cookie-banner, #cookie-notice, [class*='cookie'],
                #vector-toc-pinned-container, #vector-page-tools-pinned-container,
                #vector-appearance-pinned-container, .vector-pinnable-header,
                .vector-toc, #mw-panel-toc, .vector-menu,
                .mw-portlet, nav, [id*='vector-'], [class*='vector-pinnable']
            """,
        )

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

    
    elif domain == "apps.apple.com":
        browser_cfg = BrowserConfig(headless=True)
        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
        )
        if crawler is not None:
            crawl_result = await crawler.arun(url=url, config=run_cfg)
        else:
            async with AsyncWebCrawler(config=browser_cfg) as _crawler:
                crawl_result = await _crawler.arun(url=url, config=run_cfg)

        html = crawl_result.html
        parsed = await html_parser_run(html, domain, crawler=crawler)

        res = SimpleNamespace()
        res.html = html
        res.markdown = parsed.markdown
        res.status_code = getattr(crawl_result, "status_code", 200)
        return res

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

    if crawler is not None:
        result = await crawler.arun(url=url, config=run_cfg)
        return result

    async with AsyncWebCrawler(config=browser_cfg) as _crawler:
        result = await _crawler.arun(url=url, config=run_cfg)

    return result

'''
Il metodo html_parser_run esegue il crawler di crawl4ai sull'HTML grezzo 
dato in input, insieme al dominio necessario a scegliere la CrawlerRunConfig corretta.
'''


async def html_parser_run(html: str, domain: str, crawler: AsyncWebCrawler = None):

    md_gen = _md_generator()
    browser_cfg = BrowserConfig(headless=True)

    if domain == "en.wikipedia.org":
        browser_cfg = BrowserConfig(headless=True)
        run_cfg = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "p", "ul"],
            markdown_generator=md_gen,
            excluded_selector="""
                .infobox, .infobox-full-data, .sidebar, .navbox,
                .wikitable, table, .mw-editsection,
                [class*='you-may'], [class*='related'],
                .cookie-banner, #cookie-notice, [class*='cookie'],
                #vector-toc-pinned-container, #vector-page-tools-pinned-container,
                #vector-appearance-pinned-container, .vector-pinnable-header,
                .vector-toc, #mw-panel-toc, .vector-menu,
                .mw-portlet, nav, [id*='vector-'], [class*='vector-pinnable']
            """,
        )

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

    
    elif domain == "apps.apple.com":
    # L'HTML reale di Apple Store contiene i dati nel JSON-LD
        soup_apple = BeautifulSoup(html, "html.parser")
        ld_scripts = soup_apple.find_all("script", type="application/ld+json")
        text_parts = []
        for s in ld_scripts:
            try:
                jld = _json.loads(s.get_text())
                if jld.get("@type") == "SoftwareApplication":
                    if jld.get("name"):
                        text_parts.append(f"## {jld['name']}")
                    if jld.get("description"):
                        text_parts.append(jld["description"])
            except Exception:
                pass
        extracted = "\n\n".join(text_parts) if text_parts else ""
        res = SimpleNamespace()
        res.markdown = extracted
        return res

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

    # Se la config non richiede rendering JS (nessun wait_until/js_code/screenshot/...),
    # evitiamo del tutto l'avvio del browser: per html_parser_run l'HTML e' gia'
    # disponibile, quindi scraping + markdown possono essere fatti direttamente.
    needs_browser = any([
        run_cfg.wait_until and run_cfg.wait_until != "domcontentloaded",
        run_cfg.js_code,
        run_cfg.screenshot,
        run_cfg.pdf,
        run_cfg.scan_full_page,
        run_cfg.process_iframes,
        run_cfg.simulate_user,
        run_cfg.magic,
    ])

    if not needs_browser:
        return _scrap_html_no_browser(html, run_cfg)

    if crawler is not None:
        result = await crawler.arun(url=f"raw:{html}", config=run_cfg)
        return result

    async with AsyncWebCrawler(config=browser_cfg) as _crawler:
        result = await _crawler.arun(url=f"raw:{html}", config=run_cfg)

    return result