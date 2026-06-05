import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def fetch_property_listings(url: str) -> str:
    """
    Launches an advanced humanized browser instance to mask automation footprints,
    preventing security walls from throwing Access Denied/Block screens.
    """
    print(f"🌐 Launching stealth crawler engine for: {url}")
    
    async with async_playwright() as p:
        # Keep headless=False to significantly cut down security triggers on Indian real estate portals
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors'
            ]
        )
        
        # Randomize user window sizes slightly so it doesn't look like an identical automated viewport
        width = random.randint(1366, 1920)
        height = random.randint(768, 1080)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": width, "height": height},
            locale="en-IN,en-US;q=0.9,en;q=0.8",
            timezone_id="Asia/Kolkata",
            extra_http_headers={
                "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
                "Referer": "https://www.google.com/"
            }
        )
        
        # Inject standard webdriver stealth fixes
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)
        
        page = await context.new_page()
        
        try:
            # Navigate with a generous human-like timeout limit
            await page.goto(url, wait_until="commit", timeout=90000)
            
            # Let the primary page scripts and layout frame stabilize
            await asyncio.sleep(random.uniform(4.5, 7.0))
            
            # Check if we landed on a defensive block frame early
            page_title = await page.title()
            if "Blocked" in page_title or "Security Alert" in page_title:
                print("⚠️ Early anti-bot block screen detected. Attempting page refresh switch...")
                await page.reload(wait_until="domcontentloaded")
                await asyncio.sleep(5)

            # Humanized natural chunk-scrolling down the screen to wake up lazy-loaded elements
            for _ in range(5):
                scroll_amount = random.randint(400, 700)
                await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                # Variable delay to match human scrolling behavior
                await asyncio.sleep(random.uniform(1.5, 3.0))

            html_content = await page.content()
            await browser.close()
            
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Verify body content check for blocks
            page_text = soup.get_text()
            if "Request Blocked" in page_text or "suspicious activity" in page_text:
                print("❌ Firewall block confirmed. Scraper signature was recognized.")
                return "ERROR: Access Denied by website firewall."

            # Strip script and styling structural weight
            for element in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
                element.decompose()
                
            clean_text = soup.get_text(separator="\n")
            lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
            
            return "\n".join(lines)
            
        except Exception as e:
            await browser.close()
            print(f"❌ Scraping engine timeout or exception: {e}")
            return ""