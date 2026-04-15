import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os
import re

md_path = os.path.join(os.path.dirname(__file__),"markdown_ecb.md")
html_path = os.path.join(os.path.dirname(__file__),"html_ecb.txt")

async def main():
    markdown_file = open(md_path, 'w')
    html_file = open(html_path, 'w')

    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(target_elements=["h1", "h2", "h3", "title", "p"])

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.ecb.europa.eu/mopo/intro/benefits/html/index.it.html",
            config=run_config
        )
        md_text = result.markdown
        md_text = re.sub(r'\(\s*https?://[^)]*\)', ' ', md_text)
        md_text = re.sub(r'\[\d+\]', ' ', md_text)
        md_text = re.sub(r'[^a-zA-Z0-9]', ' ', md_text)
        pattern_domain = r'^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,})(?::\d+)?'
        match = re.search(pattern_domain, "https://www.ecb.europa.eu/mopo/intro/benefits/html/index.it.html")
        print(match.group(1))
        markdown_file.write(md_text)
        markdown_file.flush()
        markdown_file.close()
        html_file.write(result.html)
        html_file.flush()
        html_file.close()
        pattern = r'<title>(.*?)</title>'
        match = re.search(pattern, result.html)
        print(match.group(1))
        

if __name__ == "__main__":
    asyncio.run(main())