
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os


html_path = os.path.join(os.path.dirname(__file__), "html_wiki_han.txt")

async def main():
    html_file = open(html_path, 'w')
    
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(target_elements=["h1", "h2", "h3", "title", "p", ".wikitable", ".infobox"])

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/Hannibal",
            config=run_config
        )
    
        with open(html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(result.html)

if __name__ == "__main__":
    asyncio.run(main())