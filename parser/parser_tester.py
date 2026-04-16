import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os
import re
from pathlib import Path

md_path = os.path.join(os.path.dirname(__file__),"markdown_ecb.md")
html_path = os.path.join(os.path.dirname(__file__),"html_ecb.txt")
gs_path = os.path.join(Path(__file__).parent.parent, "gs_data/ECB/GS.json")
print(gs_path)

async def main():
    markdown_file = open(md_path, 'w')
    html_file = open(html_path, 'w')
    GS_file = open(gs_path, 'r')

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
        markdown_file.write(md_text)
        markdown_file.flush()
        markdown_file.close()
        html_file.write(result.cleaned_html)
        html_file.flush()
        html_file.close()
        text = GS_file.read()
        print(text[500:])
        

if __name__ == "__main__":
    asyncio.run(main())