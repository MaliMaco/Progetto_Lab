import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os

html_path = os.path.join(os.path.dirname(__file__), "html_tand_pipeline.txt")


async def main():
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=720,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    run_config = CrawlerRunConfig(
        target_elements=["h1", "h2", "h3", "title", "p", 
                         "main", ".main-content", "article"],
        wait_until="networkidle",
        verbose=True,
        
        
        
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.tandfonline.com/doi/full/10.1080/08839514.2025.2519169#abstract",
            config=run_config
        )
        
        if result.success:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(result.html)
            print(f"✅ HTML salvato in: {html_path}")
            
            

if __name__ == "__main__":
    asyncio.run(main())