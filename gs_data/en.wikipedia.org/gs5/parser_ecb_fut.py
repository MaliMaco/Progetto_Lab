import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os

md_path = os.path.join(os.path.dirname(__file__), "markdown_ecb_fut.md")
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
        
        # Scrivi markdown
        with open(md_path, 'w', encoding='utf-8') as markdown_file:
            markdown_file.write(result.markdown)
        
        # Scrivi HTML
        with open(html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(result.html)

if __name__ == "__main__":
    asyncio.run(main())