
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os


md_path = os.path.join(os.path.dirname(__file__), "markdown_wiki_ser.md")
html_path = os.path.join(os.path.dirname(__file__), "html_wiki_ser.txt")

async def main():
    markdown_file = open(md_path, 'w')
    html_file = open(html_path, 'w')
    
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(target_elements=["h1", "h2", "h3", "title", "p", ".wikitable", ".infobox"])

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://en.wikipedia.org/wiki/Serpico",
            config=run_config
        )
        with open(md_path, 'w', encoding='utf-8') as markdown_file:
            markdown_file.write(result.markdown)
        
        with open(html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(result.html)
        
        markdown_file.close()
        
        
        html_file.close()
        

if __name__ == "__main__":
    asyncio.run(main())