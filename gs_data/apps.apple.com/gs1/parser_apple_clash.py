import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup
import os
import re

html_path = os.path.join(os.path.dirname(__file__),"html_apple_clash.txt")

async def main():
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://apps.apple.com/us/app/clash-royale/id1053012308",
            config=run_config
        )
        
        soup = BeautifulSoup(result.html, 'html.parser')
        
        # rimuovi elementi di navigazione dall'HTML
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

        # header H1 da mantenere
        allowed_h1_texts = ["Clash Royale", "App Privacy"]
        
        allowed_h2_texts = [
            "Events", "Ratings & Reviews", "App Privacy", "Accessibility", 
            "Information", "Supports",
        ]
        
        allowed_h3_texts = []
        
    
      
        
        # Rimuovi header non consentiti
        for h1 in soup.find_all('h1'):
            if h1.get_text(strip=True) not in allowed_h1_texts:
                h1.decompose()
        
        for h2 in soup.find_all('h2'):
            if h2.get_text(strip=True) not in allowed_h2_texts:
                h2.decompose()
        
        for h3 in soup.find_all('h3'):
            if h3.get_text(strip=True) not in allowed_h3_texts:
                h3.decompose()
        
        # Salva l'HTML filtrato
        with open(html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(str(soup))
        
        # Stampa gli header mantenuti
        print("=== HEADER MANTENUTI ===")
        for h1 in soup.find_all('h1'):
            print(f"h1: {h1.get_text(strip=True)}")
        for h2 in soup.find_all('h2'):
            print(f"h2: {h2.get_text(strip=True)}")
        print("=== END ===\n")
        
        # ========== FILTRA IL MARKDOWN PER RIGHE ==========
        print("=== MARKDOWN CONTENT ===")
        if hasattr(result, 'markdown'):
            lines = result.markdown.split('\n')
            
            # Righe da saltare (quelle della navigazione)
            skip_patterns = [
                "for iPhone", "Search", "Today", "Games", "Apps", "Arcade",
                "iPad", "Mac", "Vision", "Watch", "TV",
                "* [iPhone", "* [iPad", "* [Mac", "* [Vision", "* [Watch", "* [TV",
                "* [ Today", "* [ Games", "* [ Apps", "* [ Arcade",
                "Navigation", "platform-selector", "search-input"
            ]
            
            filtered_lines = []
            for line in lines:
                # Salta le righe vuote all'inizio
                if not filtered_lines and not line.strip():
                    continue
                # Controlla se la riga contiene uno dei pattern da saltare
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