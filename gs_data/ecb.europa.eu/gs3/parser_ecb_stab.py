import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
import os

html_path = os.path.join(os.path.dirname(__file__), "html_ecb_stab.txt")

async def main():
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig(
      css_selector="main",
    target_elements=[
        "h1",                                    # Titolo principale
        ".jumbo-box .content-box p",            # Paragrafo introduttivo
        ".splitter h3",                         # Domande (splitter)
        ".section",                             # INTERE section (preserva ordine interno)
        ".carousel",                            # INTERI carousel
        ".promo-box"                            # INTERO promo box finale
    ]
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.ecb.europa.eu/mopo/strategy/strategy-review/html/price-stability-objective.it.html",
            config=run_config
        )
        
        with open(html_path, 'w', encoding='utf-8') as html_file:
            html_file.write(result.html)

if __name__ == "__main__":
    asyncio.run(main())