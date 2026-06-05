import asyncio
import random
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def fetch_property_listings(url: str) -> str:
    """
    Stealth scraper that navigates to home dashboards and handles automated 
    autocomplete typing interactions for complex portal architectures like NoBroker.
    """
    print(f"🌐 Launching crawler engine...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, # Keeping False so you can see it work!
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900}
        )
        
        page = await context.new_page()
        
        try:
            # Check if this is a custom structured NoBroker task
            if "nobroker.in" in url and "localities=" in url:
                from urllib.parse import urlparse, parse_qs, unquote
                parsed_url = urlparse(url)
                queries = parse_qs(parsed_url.query)
                locality = unquote(queries.get('localities', [''])[0].strip())
                
                print("⚡ Navigating to NoBroker Homepage...")
                await page.goto("https://www.nobroker.in/", wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(4)
                
                print(f"✍️ Typing neighborhood option: {locality}")
                
                # Target the text input via its human-readable placeholder attribute
                input_selector = page.get_by_placeholder("Search upto 3 localities, societies or landmarks")
                await input_selector.click()
                await asyncio.sleep(0.5)
                
                # Type the area out realistically
                await input_selector.type(locality, delay=150)
                await asyncio.sleep(2.5) # Wait for drop-down suggestion menu to pop open
                
                # Target and click the very first visible suggestion item in the dropdown menu
                dropdown_suggestion = page.locator(".autocomplete-dropdown-container, .pac-container, div[id*='suggestion']").get_by_text(locality, exact=False).first
                if await dropdown_suggestion.is_visible():
                    await dropdown_suggestion.click()
                else:
                    # Fallback: Press Arrow Down and Enter to select top choice
                    await input_selector.press("ArrowDown")
                    await asyncio.sleep(0.5)
                    await input_selector.press("Enter")
                
                await asyncio.sleep(1.5)

                # Locate and click the primary Red Search Button
                print("🖱️ Clicking search confirmation button...")
                search_btn = page.locator("button.prop-search-button, button:has-text('Search')").first
                await search_btn.click()
                await page.wait_for_load_state("load", timeout=60000)
                
            else:
                # Regular direct routing for 99acres and Housing
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Dismiss overlay popups if they get in the way
            await asyncio.sleep(6)
            try:
                for skip_text in ["Skip", "Got it"]:
                    btn = page.get_by_role("button", name=skip_text)
                    if await btn.is_visible():
                        await btn.click()
            except Exception:
                pass
                
            # Scroll down to trigger dynamic loading of listing cards
            for _ in range(4):
                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(1.5)

            html_content = await page.content()
            await browser.close()
            
            # Extract and parse clean text data for Gemini
            soup = BeautifulSoup(html_content, "html.parser")
            for element in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
                element.decompose()
                
            clean_text = soup.get_text(separator="\n")
            return "\n".join([line.strip() for line in clean_text.splitlines() if line.strip()])
            
        except Exception as e:
            await browser.close()
            print(f"❌ Scraping engine runner exception: {e}")
            return ""