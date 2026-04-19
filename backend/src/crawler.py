from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def parser_run(url: str) -> any:

    md_generator = DefaultMarkdownGenerator(
        options={
            "escape_html": False,
            "body_width": 0
        }
    )

    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(
        target_elements=["h1", "h2", "h3", "title", "p"],
        markdown_generator=md_generator,
        excluded_tags=['cookie-banner', 'cookie-consent'],
        excluded_selector=".cookie-banner, #cookie-notice, [class*='cookie']"
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