import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os
import re

md_path = os.path.join(os.path.dirname(__file__),"gs5/gs5_GS.txt")
html_path = os.path.join(os.path.dirname(__file__),"gs5/gs5.html")

async def main():
    markdown_file = open(md_path, 'w')
    html_file = open(html_path, 'w')

    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(target_elements=["h1", "h2", "h3", "title", "p"])

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.ecb.europa.eu/paym/cyber-resilience/fmi/html/index.en.html",
            config=run_config
        )
        md_text = result.markdown
        md_text = re.sub(r'\(\s*https?://[^)]*\)', ' ', md_text)
        md_text = re.sub(r'\[\d+\]', ' ', md_text)
        md_text = re.sub(r'[^a-zA-Z0-9]', ' ', md_text)
        markdown_file.write(md_text)
        markdown_file.flush()
        markdown_file.close()
        html_file.write(result.html)
        html_file.flush()
        html_file.close()
    


if __name__ == "__main__":
    asyncio.run(main())