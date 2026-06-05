import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def fetch_property_listings(url: str) -> str:
    """
    Launches a visible (headful) browser session to mimic a genuine user,
    properly injecting anti-bot evasion scripts onto the context.
    """
    print(f"🌐 Opening stealth browser to fetch: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, # Changed to False so you can see if it gets blocked!
            args=[
                '--disable-blink-features=AutomationControlled',
                '--start-maximized'
            ]
        )
        
        # Create context
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US,en;q=0.9",
            timezone_id="Asia/Kolkata"
        )
        
        # ✅ FIX: evaluate_on_new_document belongs to CONTEXT, not PAGE
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()
        
        try:
            # Navigate to the portal
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Let it sit for a few seconds to let listings completely cook
            await asyncio.sleep(5)
            
            # Scroll to load dynamic listing cards
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(1.5)

            html_content = await page.content()
            await browser.close()
            
            soup = BeautifulSoup(html_content, "html.parser")
            
            if "Access Denied" in soup.get_text():
                print("❌ EdgeSuite/Akamai anti-bot wall is still blocking the request.")
                return "ERROR: Access Denied by website firewall."

            # Strip down elements
            for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                element.decompose()
                
            clean_text = soup.get_text(separator="\n")
            lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
            
            return "\n".join(lines)
            
        except Exception as e:
            await browser.close()
            print(f"❌ Scraping failed: {e}")
            return ""