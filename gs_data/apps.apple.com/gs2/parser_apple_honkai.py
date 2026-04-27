import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup
import os
import re

html_path = os.path.join(os.path.dirname(__file__),"html_apple_honkai.txt")

async def main():
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://apps.apple.com/us/app/honkai-star-rail/id1599719154",
            config=run_config
        )
        
        soup = BeautifulSoup(result.html, 'html.parser')
        

        for platform_selector in soup.find_all('div', class_='platform-selector-container'):
            platform_selector.decompose()
        
        for platform_selector in soup.find_all('div', class_='platform-selector-dropdown'):
            platform_selector.decompose()
        
        for search in soup.find_all('div', class_='search-input-container'):
            search.decompose()
        
        for nav in soup.find_all('div', class_='navigation-items'):
            nav.decompose()
        
        for nav in soup.find_all('ul', class_='navigation-items__list'):
            nav.decompose()
        
        for nav_link in soup.find_all('a', href=re.compile(r'/us/iphone/(today|games|apps|arcade)')):
            nav_link.decompose()
        
        for nav_container in soup.find_all('div', class_='navigation-container'):
            nav_container.decompose()
        
       
        
        
        with open(html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(str(soup))
        
       
        print("=== MARKDOWN CONTENT (con recensioni) ===")
        if hasattr(result, 'markdown'):
            # filtra solo le righe superflue della navigazione
            lines = result.markdown.split('\n')
            skip_patterns = [
                "for iPhone", "Search", "Today", "Games", "Apps", "Arcade",
                "iPad", "Mac", "Vision", "Watch", "TV",
                "* [iPhone", "* [iPad", "* [Mac", "* [Vision", "* [Watch", "* [TV",
                "* [ Today", "* [ Games", "* [ Apps", "* [ Arcade",
                "Navigation", "platform-selector", "search-input"
            ]
            filtered_lines = []
            for line in lines:
                should_skip = False
                for pattern in skip_patterns:
                    if pattern.lower() in line.lower():
                        should_skip = True
                        break
                if not should_skip:
                    filtered_lines.append(line)
            print('\n'.join(filtered_lines))
        else:
            print("Markdown non disponibile")
        print("=== END MARKDOWN ===")

if __name__ == "__main__":
    asyncio.run(main())