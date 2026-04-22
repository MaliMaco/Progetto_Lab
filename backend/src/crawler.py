from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import re

async def parser_run(url: str) -> any:

    pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'
    match = re.search(pattern_domain, url)
    domain = match.group(1)

    md_generator = DefaultMarkdownGenerator(
        options={
            "escape_html": False,
            "body_width": 0
        }
    )

    browser_config = BrowserConfig()

    if domain == "ecb.europa.eu":
        run_config = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "title", "p"],
            markdown_generator=md_generator,
            excluded_tags=['cookie-banner', 'cookie-consent'],
            excluded_selector='''
            .cookie-banner, #cookie-notice, [class*='cookie'],
            table, [class*='you-may'], [class*='related'],
            .in-this-section, footer,
            .nav, nav, .navigation, .menu
            '''
            )


    if domain == "en.wikipedia.org":
        run_config = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "title", "p"],
            markdown_generator=md_generator,
            excluded_tags=['cookie-banner', 'cookie-consent'],
            excluded_selector='''
            .cookie-banner, #cookie-notice, [class*='cookie'],
            .infobox, .infobox-full-data, .sidebar, .navbox, .wikitable, table,
            [class*='you-may'], [class*='related']
            '''
            )
        
    else:
        run_config = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "title", "p"],
            markdown_generator=md_generator,
            excluded_tags=['cookie-banner', 'cookie-consent'],
            excluded_selector='''
            .cookie-banner, #cookie-notice, [class*='cookie'],
            .infobox, .infobox-full-data, .sidebar, .navbox, .wikitable, table,
            [class*='you-may'], [class*='related']
            '''
            )


    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config
        )

    return result

async def html_parser_run(html: str) -> any:

    md_generator = DefaultMarkdownGenerator(
        options={
            "escape_html": False,
            "body_width": 0
        }
    )
    

    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        target_elements=["h1", "h2", "h3", "title", "p"],
        markdown_generator=md_generator,
        excluded_tags=['cookie-banner', 'cookie-consent'],
        excluded_selector=".cookie-banner, #cookie-notice, [class*='cookie']"
        )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=f"raw:{html}",
            config=run_config
        )

    return result