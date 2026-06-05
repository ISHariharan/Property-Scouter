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

    print("\n🔍 Step 1: Running AI location mapping & expansion...")
    search_plan = llm.plan_search_targets(user_query)
    
    localities = search_plan.get("nobroker_localities", [])
    
    # Slicing localities into clean batches of max 3 items
    chunk_size = 3
    locality_chunks = [localities[i:i + chunk_size] for i in range(0, len(localities), chunk_size)]
    
    aggregated_raw_data = ""
    
    print("\n🌐 Step 2: Executing sequential cross-platform scraping runs...")

    # --- Crawl 99acres ---
    print("\n--- Crawling 99ACRES (Reliable Root Layout) ---")
    data_99 = await fetch_property_listings(search_plan.get("99acres_url"))
    if "ERROR:" not in data_99 and len(data_99) > 200:
        aggregated_raw_data += f"\n=== DATA FROM SOURCE: 99ACRES ===\n{data_99}\n"
    await asyncio.sleep(2)

    # --- Crawl Housing.com ---
    print("\n--- Crawling HOUSING.COM (Reliable Root Layout) ---")
    data_housing = await fetch_property_listings(search_plan.get("housing_url"))
    if "ERROR:" not in data_housing and len(data_housing) > 200:
        aggregated_raw_data += f"\n=== DATA FROM SOURCE: HOUSING ===\n{data_housing}\n"
    await asyncio.sleep(2)

    # --- Crawl NoBroker Chunks using the new selector strategy ---
    for index, chunk in enumerate(locality_chunks, start=1):
        print(f"\n--- Crawling NOBROKER (Batch #{index}: {', '.join(chunk)}) ---")
        
        # We pass a clear tracking identifier format to the scraper
        target_payload = f"https://www.nobroker.in/?localities={','.join(chunk)}"
        
        chunk_data = await fetch_property_listings(target_payload)
        if "ERROR:" in chunk_data or len(chunk_data) < 200:
            print(f"⚠️ Batch #{index} returned empty text data. Shifting forward.")
            continue
            
        aggregated_raw_data += f"\n=== DATA FROM SOURCE: NOBROKER BATCH {index} ===\n{chunk_data}\n"
        await asyncio.sleep(3)

    if len(aggregated_raw_data) < 500:
        print("\n❌ All portals returned zero readable properties.")
        return
        
    print("\n🧠 Step 3: Compiling, de-duplicating, and matching records...")
    analysis_results = llm.analyze_listings(user_query, aggregated_raw_data)
    
    print("\n" + "="*60)
    print("🎯 ULTIMATE MULTI-BATCH AGGREGATION RANKINGS")
    print("="*60)
    print(analysis_results)

if __name__ == "__main__":
    asyncio.run(main())