import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os

html_path = os.path.join(os.path.dirname(__file__), "html_ecb_fut.txt")

async def main():
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(
    css_selector="main",
    target_elements=["h1", "h2", "h3", "p", "li"]
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.ecb.europa.eu/euro/banknotes/future_banknotes/redesign/html/index.it.html",
            config=run_config
        )

        with open(html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(result.html)

if __name__ == "__main__":
    asyncio.run(main())