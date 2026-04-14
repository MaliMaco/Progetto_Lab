from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os

async def run(url: str) -> any:

    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(target_elements=["h1", "h2", "h3", "title", "p"])

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config
        )