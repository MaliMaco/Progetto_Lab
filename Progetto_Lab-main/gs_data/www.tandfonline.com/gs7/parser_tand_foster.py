import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os

html_path = os.path.join(os.path.dirname(__file__), "html_tand_methods.txt")


async def main():
    # conf per evitare 403
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=720,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # conf con header aggiuntivi
    run_config = CrawlerRunConfig(
        target_elements=["h1", "h2", "h3", "title", "p", 
                         "main", ".main-content", "article"],
        wait_until="networkidle",
        verbose=True,
        
        
        
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.tandfonline.com/doi/full/10.1080/00014788.2026.2625716#d1e2221",
            config=run_config
        )
        
        if result.success:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(result.html)
            print(f"✅ HTML salvato in: {html_path}")
            
            

if __name__ == "__main__":
    asyncio.run(main())