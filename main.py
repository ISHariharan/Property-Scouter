import asyncio
import sys
from scraper import fetch_property_listings
from search import LLMManager

async def main():
    llm = LLMManager()

    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        print("💡 What kind of property are you looking for?")
        user_query = input("👉 Enter requirements: ")

    if not user_query.strip():
        print("❌ Query cannot be empty.")
        return

    print("\n🔍 Step 1: Mapping multi-portal targets via LLM...")
    urls_to_scrape = llm.generate_portal_urls(user_query)
    
    aggregated_raw_data = ""
    
    print("\n🌐 Step 2: Initiating sequential cross-platform crawl...")
    for portal_name, target_url in urls_to_scrape.items():
        print(f"\n--- Crawling {portal_name.upper()} ---")
        site_data = await fetch_property_listings(target_url)
        
        if "ERROR:" in site_data or len(site_data) < 200:
            print(f"⚠️ Could not pull usable data from {portal_name}. Moving to next source.")
            continue
            
        # Append data to aggregate context block
        aggregated_raw_data += f"\n=== DATA FROM SOURCE: {portal_name.upper()} ===\n{site_data}\n"
        
        # A tiny safety delay between hitting different corporate firewalls
        await asyncio.sleep(2)

    if len(aggregated_raw_data) < 500:
        print("\n❌ All portals blocked the automated scraper or returned empty results.")
        return
        
    print("\n🧠 Step 3: De-duplicating and cross-analyzing platform results...")
    analysis_results = llm.analyze_listings(user_query, aggregated_raw_data)
    
    print("\n" + "="*60)
    print("🎯 CONSOLIDATED PORTAL RANKINGS (99ACRES / HOUSING / NOBROKER)")
    print("="*60)
    print(analysis_results)

if __name__ == "__main__":
    asyncio.run(main())