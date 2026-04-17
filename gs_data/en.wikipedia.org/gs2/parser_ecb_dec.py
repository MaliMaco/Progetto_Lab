import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os


md_path = os.path.join(os.path.dirname(__file__),"markdown_ecb_dec.md")
html_path = os.path.join(os.path.dirname(__file__),"html_ecb_dec.txt")

async def main():
    markdown_file = open(md_path, 'w')
    html_file = open(html_path, 'w')
    
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(
    css_selector="main",
    target_elements=[
        "h1",                           # Titolo principale
        "p",                          
        "h2",                           
        ".box",                         # (titolo + paragrafo insieme)
        ".splitter h3",                 
        ".headline",                  
        ".see-also-boxes h3",          
        ".see-also-boxes a"        
    ]
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.ecb.europa.eu/euro/digital_euro/features/html/index.it.html",
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