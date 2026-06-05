import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic, RateLimitError
from google import genai

load_dotenv()

class LLMManager:
    def __init__(self):
        # Initialize Claude (Optional)
        self.claude_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = Anthropic(api_key=self.claude_key) if self.claude_key else None
        
        # Initialize Gemini via the new Google GenAI SDK
        if os.getenv("GEMINI_API_KEY"):
            self.gemini_client = genai.Client()
        else:
            self.gemini_client = None

    def plan_search_targets(self, user_query: str) -> dict:
        """
        Extracts structural locations and returns a list of specific localities
        for chunk-based NoBroker payload building, along with standard roots for other sites.
        """
        prompt = f"""
        Analyze this real estate query: "{user_query}"
        
        We need to crawl NoBroker, 99acres, and Housing.com.
        NoBroker allows a maximum of 3 localities at a time. Brainstorm a broad, high-quality 
        list of 6 to 9 specific real estate neighborhoods/localities in Bangalore that best match the user's micro-location constraint 
        (e.g., if near Oracle Tech Hub Bangalore, include: Kadubeesanahalli, Marathahalli, Bellandur, Panathur, 
        Devarabisanahalli, HSR Layout, Sarjapur Road, Varthur, Munnekollal).
        
        Return ONLY a raw JSON object formatted exactly like this:
        {{
            "city": "bangalore",
            "nobroker_localities": ["Kadubeesanahalli", "Marathahalli", "Bellandur", "Panathur", "Devarabisanahalli", "HSR Layout"],
            "99acres_url": "https://www.99acres.com/property-for-rent-in-bangalore-ffid",
            "housing_url": "https://housing.com/in/rent/bangalore/bangalore"
        }}
        Do not include markdown code blocks, fences, or additional text.
        """
        
        if self.gemini_client:
            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                text = response.text.replace("```json", "").replace("```", "").strip()
                return json.loads(text)
            except Exception as e:
                print(f"⚠️ AI location expansion failed ({e}). Running hardcoded defaults...")
                
        # Default safety backup maps near Oracle Tech Hub if API spikes
        return {
            "city": "bangalore",
            "nobroker_localities": ["Kadubeesanahalli", "Marathahalli", "Bellandur", "Panathur", "Devarabisanahalli", "HSR Layout"],
            "99acres_url": "https://www.99acres.com/property-for-rent-in-bangalore-ffid",
            "housing_url": "https://housing.com/in/rent/bangalore/bangalore"
        }

    def analyze_listings(self, user_query, scraped_data):
        prompt = f"""
        You are an expert real estate aggregator. Deeply analyze the following data compiled across 99acres, Housing.com, and multiple targeted NoBroker location tracks.
        
        User Requirements: "{user_query}"
        
        Aggregated Source Data:
        {scraped_data}
        
        Filter, deduplicate properties, and provide a cross-portal ranked list of best matches.
        Include for each:
        1. Title / Locality & Source Portal
        2. Monthly Rent & Estimated Deposit
        3. Match Analysis: Highlight proximity metrics, furnishing state, orientation (facing), and ventilation features.
        """
        if self.gemini_client:
            try:
                print("♊ Cross-analyzing comprehensive records via Gemini...")
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                return f"❌ Gemini Analysis Failed: {e}"
        return "❌ Gemini Client is not initialized."