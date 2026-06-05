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

    def generate_portal_urls(self, user_query: str) -> dict:
        """
        Extracts search parameters from user query and builds realistic, 
        highly-targeted search queries for the platforms.
        """
        prompt = f"""
        Analyze this real estate query: "{user_query}"
        
        Generate rental search URLs for 99acres, NoBroker, and Housing.com.
        
        Rules:
        1. For NoBroker, the user wants properties within 15-20km of Oracle Tech Hub (Marathahalli/Kadubeesanahalli, Bangalore). 
           Generate a direct search parameter payload using key localities near Outer Ring Road. 
           Format exactly like this example for Bangalore localities (e.g., Marathahalli and Bellandur):
           https://www.nobroker.in/property/rent/bangalore/multiple?searchParam=W3sibGF0IjoxMi45NTY0NjcyLCJsb24iOjc3LjcwMDExOTMsInBsYWNlSWQiOiJDaElKeF96bHREb1NyanNSVzhVbV9mY0g3bW8iLCJwbGFjZU5hbWUiOiJNYXJhdGthaGFsbGkifSx7ImxhdCI6MTIuOTMwNjgxOCwibG9uIjo3Ny42Nzg0NDM0LCJwbGFjZUlkIjoiQ2hJSktYclFka2tScmpzUjN2OTlSMzZ2Y0VVIiwicGxhY2VOYW1lIjoiQmVsbGFuZHVyIn1d&sharedAccomodation=false&commercial=false
        
        2. For Housing.com, use a highly specific localized landing page instead of a generic city root:
           https://housing.com/rent/flats-for-rent-in-marathahalli-bangalore-P54w87sh672m69olp
           
        3. For 99acres, generate a functional structured rental string:
           https://www.99acres.com/property-for-rent-in-bangalore-ffid

        Return ONLY a raw JSON object with keys "99acres", "housing", and "nobroker". 
        Do not include markdown code fences or explanations.
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
                print(f"⚠️ AI URL generation failed ({e}). Using targeted fallbacks...")
                
        # Hardcoded targeted fallbacks if API limits spike
        return {
            "99acres": "https://www.99acres.com/property-for-rent-in-bangalore-ffid",
            "housing": "https://housing.com/rent/flats-for-rent-in-marathahalli-bangalore-P54w87sh672m69olp",
            "nobroker": "https://www.nobroker.in/property/rent/bangalore/multiple?searchParam=W3sibGF0IjoxMi45Mzk2NDA2LCJsb24iOjc3DoubleNzY5NzE4NDcsInBsYWNlSWQiOiJDaElKOTNsdVpyTVVyanNSR0pka0xhV0ptV28iLCJwbGFjZU5hbWUiOiJLYWR1YmVlc2FuYWhhbGxpIn0seyJsYXQiOjEyLjk1NjQ2NzIsImxvbiI6NzcuNzAwMTE5MywicGxhY2VJZCI6IkNoSUp4X3psdERvU3Jqc1JXOFVtX2ZjSDdtbyIsInBsYWNlTmFtZSI6Ik1hcmF0aGhhaGFsbGkifV0=&sharedAccomodation=false"
        }

    def analyze_listings(self, user_query, scraped_data):
        prompt = f"""
        You are an expert real estate aggregator. Deeply analyze the following data compiled across 99acres, Housing.com, and NoBroker.
        
        User Requirements: "{user_query}"
        
        Aggregated Source Data:
        {scraped_data}
        
        Filter, deduplicate (if the same flat is on multiple sites), and provide a cross-portal ranked list of the best matches.
        Include for each:
        1. Title / Locality & Source Portal (e.g., Found on NoBroker)
        2. Monthly Rent & Estimated Security Deposit
        3. Match Analysis: Highlight how well it fits proximity requirements (e.g., within 15km of Oracle), furnishing, orientation (facing), and community features.
        """

        if self.gemini_client:
            try:
                print("♊ Aggregating and sorting results via Gemini...")
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                return f"❌ Gemini Analysis Failed: {e}"
        return "❌ Gemini Client is not initialized."