import asyncio
import sys
from scraper import fetch_property_listings
from search import LLMManager

async def main():
    llm = LLMManager()

    # If you type a query in the terminal command line, use it. Otherwise, prompt for it.
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        print("💡 What kind of property are you looking for?")
        user_query = input("👉 Enter requirements: ")

    if not user_query.strip():
        print("❌ Query cannot be empty.")
        return

    print("\n🔍 Step 1: LLM is interpreting query and generating target portal URL...")
    target_url = llm.generate_search_url(user_query)
    print(f"🎯 Target URL generated: {target_url}")
    
    print("\n🌐 Step 2: Launching browser engine to scrape current options...")
    scraped_text = await fetch_property_listings(target_url)
    
    if not scraped_text or len(scraped_text) < 200:
        print("❌ Scraper returned insufficient data. The site might be blocking or listing patterns have shifted.")
        return
        
    print("\n🧠 Step 3: Extracting and ranking the best matching properties...")
    analysis_results = llm.analyze_listings(user_query, scraped_text)
    
    print("\n" + "="*50)
    print("🎯 THE HIGHEST RANKED PROPERTIES FOR YOU")
    print("="*50)
    print(analysis_results)

if __name__ == "__main__":
    asyncio.run(main())