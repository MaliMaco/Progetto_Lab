from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import re

async def parser_run(url: str) -> any:

    url_list = url.split("/")
    domain = url_list[2]

    md_generator = DefaultMarkdownGenerator(
        options={
            "escape_html": False,
            "body_width": 0
        }
    )

    browser_config = BrowserConfig()

    if domain == "ecb.europa.eu":

        run_config = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "title", "p"],
            markdown_generator=md_generator,
            excluded_tags=['cookie-banner', 'cookie-consent'],
            excluded_selector='''
            .cookie-banner, #cookie-notice, [class*='cookie'],
            table, [class*='you-may'], [class*='related'],
            .in-this-section, footer,
            .nav, nav, .navigation, .menu
            '''
            )


    elif domain == "en.wikipedia.org":

        run_config = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "title", "p"],
            markdown_generator=md_generator,
            excluded_tags=['cookie-banner', 'cookie-consent'],
            excluded_selector='''
            .cookie-banner, #cookie-notice, [class*='cookie'],
            .infobox, .infobox-full-data, .sidebar, .navbox, .wikitable, table,
            [class*='you-may'], [class*='related']
            '''
            )

    elif domain == "www.tandfonline.com":
        
        browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=720,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
        
        '''
        Configurazione di crawl4ai al fine di eliminare numerosi elementi presenti nella pagina
        non catturati nel gold text in quanto nascosti o annidati o non facilmente trasformabili in stringhe,
        come equazioni, figure, link per il reindirizzamento, etc...
        '''

        TANDFONLINE_EXCLUDED = """
                                    [id^='references'], [id^='appendix'], [id^='appendixes'],
                                    .references, .bibliography,
                                    #infos-holder, .summation-section,
                                    [class*='article-note'], [class*='article-metrics'], [class*='metrics'],
                                    figure, .figure, [class*='figure'],
                                    table, .table, [class*='table-wrap'],
                                    .disp-formula, [class*='formula'], [class*='equation'],
                                    [class*='open-in-window'], [class*='openInFullSize'],
                                    nav, header, footer,
                                    [class*='keyword'],
                                    .cookie-banner, #cookie-notice, [class*='cookie']
                                """

        run_config = CrawlerRunConfig(
        target_elements=["h1", "h2", "h3", "h4", "title", "p"],
        wait_until="networkidle",
        verbose=True,
        excluded_selector=TANDFONLINE_EXCLUDED
        )

    else:

        APPLE_EXCLUDED = """
        header, nav, footer, aside,
        table, button,

        [class*='review'],
        [class*='rating'],
        [class*='ratings'],
        [class*='star'],

        [class*='more-by'],
        [class*='related'],
        [class*='recommend'],

        [class*='privacy'],
        [class*='policy'],

        [class*='version'],
        [class*='history'],

        [class*='compatibility'],
        [class*='device'],

        [class*='language'],
        [class*='lang'],

        [class*='family-sharing'],

        [class*='screenshot'],
        [class*='carousel'],

        [class*='cookie']
        """

        run_config = CrawlerRunConfig(
        target_elements=[
            "h1","h2","h3",
            "p","li","span","div"
        ],
        markdown_generator=md_generator,
        excluded_selector=APPLE_EXCLUDED,
        wait_until="networkidle"
    )


    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_config
        )

    return result

async def html_parser_run(html: str, domain: str) -> any:

    md_generator = DefaultMarkdownGenerator(
        options={
            "escape_html": False,
            "body_width": 0
        }
    )
    
    if domain == "ecb.europa.eu":

        run_config = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "title", "p"],
            markdown_generator=md_generator,
            excluded_tags=['cookie-banner', 'cookie-consent'],
            excluded_selector='''
            .cookie-banner, #cookie-notice, [class*='cookie'],
            table, [class*='you-may'], [class*='related'],
            .in-this-section, footer,
            .nav, nav, .navigation, .menu
            '''
            )


    elif domain == "en.wikipedia.org":

        run_config = CrawlerRunConfig(
            target_elements=["h1", "h2", "h3", "title", "p"],
            markdown_generator=md_generator,
            excluded_tags=['cookie-banner', 'cookie-consent'],
            excluded_selector='''
            .cookie-banner, #cookie-notice, [class*='cookie'],
            .infobox, .infobox-full-data, .sidebar, .navbox, .wikitable, table,
            [class*='you-may'], [class*='related']
            '''
            )

    elif domain == "www.tandfonline.com":
        
        browser_config = BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=720,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
        
        TANDFONLINE_EXCLUDED = """
                                    [id^='references'], [id^='appendix'], [id^='appendixes'],
                                    .references, .bibliography,
                                    #infos-holder, .summation-section,
                                    [class*='article-note'], [class*='article-metrics'], [class*='metrics'],
                                    figure, .figure, [class*='figure'],
                                    table, .table, [class*='table-wrap'],
                                    .disp-formula, [class*='formula'], [class*='equation'],
                                    [class*='open-in-window'], [class*='openInFullSize'],
                                    nav, header, footer,
                                    [class*='keyword'],
                                    .cookie-banner, #cookie-notice, [class*='cookie']
                                """

        run_config = CrawlerRunConfig(
        target_elements=["h1", "h2", "h3", "h4" "title", "p"],
        wait_until="networkidle",
        verbose=True,
        excluded_selector=TANDFONLINE_EXCLUDED
        )

    else:

        APPLE_EXCLUDED = """
        header, nav, footer, aside,
        table, button,

        [class*='review'],
        [class*='rating'],
        [class*='ratings'],
        [class*='star'],

        [class*='more-by'],
        [class*='related'],
        [class*='recommend'],

        [class*='privacy'],
        [class*='policy'],

        [class*='version'],
        [class*='history'],

        [class*='compatibility'],
        [class*='device'],

        [class*='language'],
        [class*='lang'],

        [class*='family-sharing'],

        [class*='screenshot'],
        [class*='carousel'],

        [class*='cookie']
        """

        run_config = CrawlerRunConfig(
        target_elements=[
            "h1","h2","h3",
            "p","li","span","div"
        ],
        markdown_generator=md_generator,
        excluded_selector=APPLE_EXCLUDED,
        wait_until="networkidle"
    )

    browser_config = BrowserConfig(headless=True)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url=f"raw:{html}",
            config=run_config
        )

    return result